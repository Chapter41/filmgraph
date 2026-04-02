"""
Pipeline timeline JSON → FilmGraph importer.

Converts the pipeline's internal timeline format (as returned by the
/api/projects/{id}/timeline endpoint) into FilmGraph.

Usage::

    from filmgraph.importers.timeline import timeline_to_filmgraph

    timeline = requests.get(f"{BASE}/api/projects/{pid}/timeline").json()["timeline"]
    fg = timeline_to_filmgraph(timeline)

CLI::

    python -m filmgraph.importers.timeline --timeline-json dump.json -o output.filmgraph.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from filmgraph.schema import (
    Audio,
    Character,
    Cinematography,
    DataSource,
    DialogueLine,
    Editorial,
    Entities,
    FilmGraph,
    FilmMeta,
    Scene,
    Shot,
    Visual,
)
from filmgraph.vocabulary import CameraAngle, CameraMovement, ShotSize, ShotType


def timeline_to_filmgraph(
    timeline: dict[str, Any],
    *,
    title: Optional[str] = None,
) -> FilmGraph:
    """Convert pipeline timeline JSON to FilmGraph.

    Handles two pipeline formats:
      1. scene_adv output: {scenes: [{scene_number, shots: [...]}]}
      2. MovieTimeline serialized: {chapters: [{scenes: [...]}]}

    Args:
        timeline: The raw timeline dict from the pipeline API.
        title: Override film title (defaults to timeline metadata if present).
    """
    meta_raw = timeline.get("meta", timeline.get("metadata", {}))
    film_title = title or meta_raw.get("title", "Untitled")

    # Detect format: scenes or chapters
    scenes_raw = timeline.get("scenes", [])
    chapters_raw = timeline.get("chapters", [])

    # If chapters format (MovieTimeline), flatten chapters → scenes
    if chapters_raw and not scenes_raw:
        for ch in chapters_raw:
            ch_scenes = ch.get("scenes", [])
            for cs in ch_scenes:
                cs.setdefault("scene_number", cs.get("order", 0))
                cs.setdefault("title", ch.get("title", ""))
                cs.setdefault("characters", ch.get("characters", []))
            scenes_raw.extend(ch_scenes)

    # Duration
    duration = (
        max((s.get("end_time", 0) for s in scenes_raw), default=0.0)
        if scenes_raw else meta_raw.get("duration", meta_raw.get("total_duration", 0.0))
    )

    # Characters — from top-level or aggregated from scenes
    chars_raw = timeline.get("characters", [])
    if not chars_raw:
        # Collect from scene-level
        all_char_names: set[str] = set()
        for sc in scenes_raw:
            for name in sc.get("characters", []):
                all_char_names.add(name)
            for sh in sc.get("shots", []):
                for name in sh.get("visible_characters", sh.get("characters", [])):
                    all_char_names.add(name)
        chars_raw = [{"name": n, "id": n.lower().replace(" ", "-")} for n in sorted(all_char_names)]

    characters = [
        Character(
            id=c.get("id", c.get("name", "").lower().replace(" ", "-")),
            name=c.get("name", "Unknown"),
            description=c.get("description"),
        )
        for c in chars_raw
    ]

    # Pipeline shot_type → FilmGraph ShotSize mapping
    # Only values that describe *how much of the subject fills the frame*
    _SHOT_TYPE_TO_SIZE = {
        "extreme_wide": "EWS",
        "wide": "WS",
        "medium_wide": "MWS",
        "medium_long": "MLS",
        "full": "MLS",  # Full shot ≈ medium long shot
        "medium": "MS",
        "medium_close_up": "MCU",
        "close_up": "CU",
        "extreme_close_up": "ECU",
        "insert": "INSERT",
        "aerial": "AERIAL",
        "other": "OTHER",
    }

    # Pipeline shot_type values that are compositional *types*, not sizes.
    # These go into Cinematography.shot_type instead of shot_size.
    _SHOT_TYPE_TO_TYPE = {
        "single": "single",
        "two_shot": "two-shot",
        "group": "group",
        "over_the_shoulder": "over-the-shoulder",
        "over_shoulder": "over-the-shoulder",
        "point_of_view": "point-of-view",
        "establishing": "establishing",
        "reaction": "reaction",
        "cutaway": "cutaway",
        "master": "master",
        "tracking": None,  # tracking is a camera movement, not a shot type
    }

    _CAM_MOVEMENT_MAP = {
        "static": "static",
        "pan": "pan",
        "tilt": "tilt",
        "dolly": "dolly",
        "dolly_in": "push-in",
        "dolly_out": "pull-out",
        "truck": "truck",
        "tracking": "tracking",
        "handheld": "handheld",
        "steadicam": "steadicam",
        "crane": "crane",
        "drone": "drone",
        "zoom": "zoom",
        "whip_pan": "whip-pan",
    }

    _CAM_ANGLE_MAP = {
        "eye_level": "eye-level",
        "high_angle": "high-angle",
        "low_angle": "low-angle",
        "birds_eye": "birds-eye",
        "worms_eye": "worms-eye",
        "dutch_angle": "dutch-angle",
        "overhead": "overhead",
        "ground_level": "ground-level",
    }

    # ── Helper: build a Shot from a dict (works for both nested shots and scene-as-shot) ──
    def _build_shot(sh: dict[str, Any], fallback_order: int = 0) -> Shot:
        """Convert a shot-level dict to a FilmGraph Shot."""
        cine = Cinematography()

        # 1. Explicit shot_size field (new pipeline output)
        raw_size = sh.get("shot_size")
        if raw_size:
            mapped_size = _SHOT_TYPE_TO_SIZE.get(raw_size, raw_size)
            try:
                cine.shot_size = ShotSize(mapped_size if mapped_size == mapped_size.upper() else mapped_size.upper())
            except ValueError:
                pass

        # 2. shot_type / scene_type → ShotSize or ShotType
        raw_type = sh.get("shot_type") or sh.get("scene_type") or (sh.get("shot_size") if not raw_size else None)
        if raw_type:
            if raw_type in _SHOT_TYPE_TO_TYPE:
                mapped_type = _SHOT_TYPE_TO_TYPE[raw_type]
                if mapped_type:
                    try:
                        cine.shot_type = ShotType(mapped_type)
                    except ValueError:
                        pass
                else:
                    cine.camera_movement = CameraMovement.TRACKING
            elif raw_type in _SHOT_TYPE_TO_SIZE and cine.shot_size is None:
                try:
                    cine.shot_size = ShotSize(_SHOT_TYPE_TO_SIZE[raw_type])
                except ValueError:
                    pass
            elif cine.shot_size is None:
                try:
                    cine.shot_size = ShotSize(raw_type.upper())
                except ValueError:
                    pass

        # camera_movement
        raw_cm = sh.get("camera_movement")
        if raw_cm:
            mapped_cm = _CAM_MOVEMENT_MAP.get(raw_cm, raw_cm)
            try:
                cine.camera_movement = CameraMovement(mapped_cm)
            except ValueError:
                cine.camera_movement = CameraMovement.OTHER

        # camera_angle
        raw_angle = sh.get("camera_angle")
        if raw_angle:
            mapped_angle = _CAM_ANGLE_MAP.get(raw_angle, raw_angle)
            try:
                cine.camera_angle = CameraAngle(mapped_angle)
            except ValueError:
                pass

        visual = Visual(
            description=sh.get("description") or None,
            dominant_colors=sh.get("dominant_colors", []),
            lighting=sh.get("lighting") or None,
        )

        dialogue_lines = []
        for dl in sh.get("dialogue", sh.get("dialogue_lines", [])):
            dialogue_lines.append(DialogueLine(
                speaker=dl.get("speaker"),
                text=dl.get("text", ""),
                start_time=dl.get("start_time", sh.get("start_time", 0)),
                end_time=dl.get("end_time", sh.get("end_time", 0)),
            ))
        audio = Audio(dialogue=dialogue_lines)

        editorial_kwargs = {}
        if sh.get("confidence") or sh.get("thumbnail_path"):
            editorial_kwargs["editorial"] = Editorial(
                confidence=sh.get("confidence"),
                thumbnail_path=sh.get("thumbnail_path") or sh.get("clip_path"),
            )

        order = sh.get("order", fallback_order)
        return Shot(
            id=sh.get("id", f"sh-{order}"),
            order=order,
            start_time=sh.get("start_time", 0),
            end_time=sh.get("end_time", 0),
            cinematography=cine,
            visual=visual,
            audio=audio,
            characters_visible=sh.get("visible_characters", sh.get("characters", [])),
            emotional_tone=sh.get("emotional_tone"),
            source="pipeline",
            **editorial_kwargs,
        )

    # ── Detect: are these "scenes" actually individual shots? ──
    # Pipeline scene_adv output has `scene_type` / `camera_movement` on the scene
    # level with no nested `shots` array. In this case each "scene" IS a shot.
    scenes_are_shots = (
        scenes_raw
        and not any(sc.get("shots") for sc in scenes_raw)
        and any(sc.get("scene_type") or sc.get("camera_movement") for sc in scenes_raw)
    )

    # Scenes → FilmGraph scenes
    scenes: list[Scene] = []

    if scenes_are_shots:
        # Group pipeline "scenes" (shots) by chapter boundaries
        if chapters_raw:
            for ch in chapters_raw:
                ch_id = ch.get("id", ch.get("chapter_number", 0))
                ch_start = float(ch.get("start_time", 0))
                ch_end = float(ch.get("end_time", 0))
                ch_title = ch.get("title", f"Chapter {ch_id}")

                ch_shots = []
                for sc in scenes_raw:
                    sc_start = float(sc.get("start_time", 0))
                    if ch_start <= sc_start < ch_end:
                        ch_shots.append(_build_shot(sc, fallback_order=len(ch_shots) + 1))

                scene_chars = ch.get("characters", [])
                scenes.append(Scene(
                    id=ch_id,
                    title=ch_title,
                    summary=ch.get("summary", ch_title),
                    start_time=ch_start,
                    end_time=ch_end,
                    location=ch.get("location") or ch.get("setting_context"),
                    characters=scene_chars,
                    mood=ch.get("mood"),
                    themes=ch.get("themes", []),
                    shots=ch_shots,
                ))
        else:
            # No chapters — put all shots in one scene
            all_shots = [_build_shot(sc, fallback_order=i + 1) for i, sc in enumerate(scenes_raw)]
            if all_shots:
                scenes.append(Scene(
                    id=1,
                    title="Full Film",
                    summary=f"All {len(all_shots)} shots",
                    start_time=all_shots[0].start_time,
                    end_time=all_shots[-1].end_time,
                    shots=all_shots,
                ))
    else:
        # Standard format: scenes with nested shots
        for sc in scenes_raw:
            shots: list[Shot] = []
            for sh in sc.get("shots", []):
                shots.append(_build_shot(sh))

            scene_chars = sc.get("characters", [])
            scene_id = sc.get("id", sc.get("scene_number", 0))

            scenes.append(Scene(
                id=scene_id,
                title=sc.get("title", f"Scene {scene_id}"),
                summary=sc.get("summary", sc.get("title", "")),
                start_time=sc.get("start_time", 0),
                end_time=sc.get("end_time", 0),
                location=sc.get("location") or sc.get("setting_context"),
                characters=scene_chars,
                mood=sc.get("mood"),
                themes=sc.get("themes", []),
                shots=shots,
            ))

    return FilmGraph(
        meta=FilmMeta(
            title=film_title,
            duration=duration,
            sources=[DataSource(layer="all", source="pipeline")],
        ),
        entities=Entities(characters=characters),
        scenes=scenes,
    )


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Convert pipeline timeline to FilmGraph")
    ap.add_argument("--timeline-json", required=True, help="Path to timeline JSON dump")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    tl = json.loads(Path(args.timeline_json).read_text())
    fg = timeline_to_filmgraph(tl, title=args.title)

    out = args.output or "pipeline.filmgraph.json"
    Path(out).write_text(fg.to_json(), encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"✅ {len(fg.scenes)} scenes, {total_shots} shots → {out}")
