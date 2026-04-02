"""
Bloody Tennis ground_truth.json → FilmGraph converter.

One-time conversion utility for the existing hand-verified ground truth
fixture format into FilmGraph. This is specific to the GT schema used in
tests/fixtures/bloody_tennis/ground_truth.json.

Usage::

    from filmgraph.importers.ground_truth import ground_truth_to_filmgraph
    fg = ground_truth_to_filmgraph("tests/fixtures/bloody_tennis/ground_truth.json")

CLI::

    python -m filmgraph.importers.ground_truth tests/fixtures/bloody_tennis/ground_truth.json
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
    Entities,
    FilmGraph,
    FilmMeta,
    MusicCue,
    Scene,
    Shot,
    Visual,
)
from filmgraph.vocabulary import CameraAngle, CameraMovement, ShotSize, ShotType

# Reuse the same maps from ccsl importer
_SHOT_SIZE_MAP: dict[str, ShotSize] = {
    "ECU": ShotSize.ECU,
    "BCU": ShotSize.BCU,
    "CU": ShotSize.CU,
    "MCU": ShotSize.MCU,
    "MS": ShotSize.MS,
    "MLS": ShotSize.MLS,
    "MWS": ShotSize.MWS,
    "LS": ShotSize.WS,
    "WS": ShotSize.WS,
    "EWS": ShotSize.EWS,
    "ELS": ShotSize.EWS,
    "AERIAL": ShotSize.AERIAL,
    "DRONE": ShotSize.AERIAL,
    "INSERT": ShotSize.INSERT,
    "OTS": ShotSize.OTHER,  # OTS is a shot type, not size — compound parsed below
}

# Shot types that get misclassified as shot_size in GT
_SHOT_TYPE_FROM_SIZE: dict[str, ShotType] = {
    "OTS": ShotType.OTS,
}

# Shot size tokens to extract from descriptions for compound parsing
_SIZE_TOKENS: set[str] = set(_SHOT_SIZE_MAP.keys()) - {"OTS"}

_CAMERA_MOVEMENT_MAP: dict[str, CameraMovement] = {
    "STATIC": CameraMovement.STATIC,
    "PAN": CameraMovement.PAN,
    "TILT": CameraMovement.TILT,
    "DOLLY": CameraMovement.DOLLY,
    "DOLY": CameraMovement.DOLLY,
    "TRUCK": CameraMovement.TRUCK,
    "TRACKING": CameraMovement.TRACKING,
    "TRACK": CameraMovement.TRACKING,
    "HANDHELD": CameraMovement.HANDHELD,
    "STEADICAM": CameraMovement.STEADICAM,
    "CRANE": CameraMovement.CRANE,
    "DRONE": CameraMovement.DRONE,
    "ZOOM": CameraMovement.ZOOM,
}

_CAMERA_ANGLE_MAP: dict[str, CameraAngle] = {
    "LOW ANGLE": CameraAngle.LOW,
    "HIGH ANGLE": CameraAngle.HIGH,
}


def _to_char_id(name: str) -> str:
    """Slugify a character name."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def ground_truth_to_filmgraph(
    path: str,
) -> FilmGraph:
    """Convert a ground_truth.json fixture into FilmGraph."""
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))

    movie_name = data.get("movie_name", Path(path).stem)
    language = data.get("language")
    fps = data.get("fps", 24)
    calibration_offset = data.get("calibration_offset", 0.0)

    # Collect all unique character names across all shots
    all_char_names: set[str] = set()
    for sc in data.get("scenes", []):
        for ch in sc.get("characters", []):
            all_char_names.add(ch)
        for sh in sc.get("shots", []):
            for ch in sh.get("characters", []):
                all_char_names.add(ch)

    characters = [
        Character(id=_to_char_id(name), name=name)
        for name in sorted(all_char_names)
    ]
    char_id_map = {name: _to_char_id(name) for name in all_char_names}

    # Convert scenes
    scenes: list[Scene] = []
    for sc in data.get("scenes", []):
        shots: list[Shot] = []
        for sh in sc.get("shots", []):
            # Shot size
            raw_ss = sh.get("shot_size")
            shot_size = _SHOT_SIZE_MAP.get(raw_ss.upper()) if raw_ss else None

            # Camera movement — CCSL convention: empty = static (locked camera)
            raw_cm = sh.get("camera_movement")
            if raw_cm:
                camera_movement = _CAMERA_MOVEMENT_MAP.get(raw_cm.upper())
            else:
                camera_movement = CameraMovement.STATIC

            # Camera angle from modifier
            raw_mod = sh.get("modifier")
            camera_angle = _CAMERA_ANGLE_MAP.get(raw_mod.upper()) if raw_mod else None

            # Shot type — detect OTS from description or shot_size field
            shot_type: Optional[ShotType] = None
            if raw_ss and raw_ss.upper() in _SHOT_TYPE_FROM_SIZE:
                shot_type = _SHOT_TYPE_FROM_SIZE[raw_ss.upper()]
                # OTS is a shot_type, not shot_size — parse real size from description
                shot_size = None
                desc_upper = sh.get("description", "").upper()
                import re as _re
                for token in _re.split(r'[\s,]+', desc_upper):
                    if token in _SIZE_TOKENS and token in _SHOT_SIZE_MAP:
                        shot_size = _SHOT_SIZE_MAP[token]
                        break

            cine = Cinematography(
                shot_size=shot_size,
                camera_movement=camera_movement,
                camera_angle=camera_angle,
                shot_type=shot_type,
            )

            visual = Visual(description=sh.get("description"))

            # Dialogue
            dialogue_lines = [
                DialogueLine(
                    speaker=char_id_map.get(dl.get("speaker", ""), dl.get("speaker")),
                    text=dl.get("text", ""),
                    start_time=dl.get("start_time", sh.get("start_time", 0)),
                    end_time=dl.get("end_time", sh.get("end_time", 0)),
                    language=language,
                )
                for dl in sh.get("dialogue_lines", [])
            ]

            # Music cues
            music_raw = sh.get("music_sfx")
            music_cues = [MusicCue(label=music_raw)] if music_raw else []

            audio = Audio(
                dialogue=dialogue_lines,
                music_cues=music_cues,
            )

            chars_visible = [char_id_map[c] for c in sh.get("characters", []) if c in char_id_map]

            shots.append(Shot(
                id=f"s{sc['order']}-{sh['order']:03d}",
                order=sh["order"],
                start_time=sh["start_time"],
                end_time=sh["end_time"],
                cinematography=cine,
                visual=visual,
                audio=audio,
                characters_visible=chars_visible,
                source=sh.get("source"),
                verified=sh.get("verified"),
            ))

        scene_chars = [char_id_map[c] for c in sc.get("characters", []) if c in char_id_map]
        scenes.append(Scene(
            id=sc["order"],
            title=sc.get("name", f"Scene {sc['order']}"),
            summary=sc.get("summary") or f"Segment {sc['order']}",
            start_time=sc["start_time"],
            end_time=sc["end_time"],
            location=sc.get("location"),
            characters=scene_chars,
            shots=shots,
        ))

    # Duration
    duration = max((sc.end_time for sc in scenes), default=0.0)

    sources = [DataSource(layer="all", source=data.get("ccsl_source", "ground-truth"))]

    return FilmGraph(
        meta=FilmMeta(
            title=movie_name,
            duration=duration,
            frame_rate=float(fps),
            language=language,
            sources=sources,
        ),
        entities=Entities(characters=characters),
        scenes=scenes,
    )


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert ground_truth.json to FilmGraph")
    ap.add_argument("path", help="Path to ground_truth.json")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    fg = ground_truth_to_filmgraph(args.path)
    out = args.output or str(Path(args.path).with_suffix(".filmgraph.json"))
    Path(out).write_text(fg.to_json(), encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"✅ {len(fg.scenes)} scenes, {total_shots} shots → {out}")
