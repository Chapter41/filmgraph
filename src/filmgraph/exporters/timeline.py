"""
FilmGraph → pipeline timeline JSON exporter.

Produces the internal pipeline format (scene_adv-style) consumed by
`timeline_to_filmgraph`. Round-trip compatible with the importer.

Usage::

    from filmgraph.exporters.timeline import filmgraph_to_timeline
    data = filmgraph_to_timeline(fg)

CLI::

    python -m filmgraph.exporters.timeline movie.filmgraph.json -o timeline.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filmgraph.schema import FilmGraph, Shot
from filmgraph.vocabulary import CameraAngle, CameraMovement, ShotSize, ShotType


# Reverse mappings from the importer's internal tables.
_SIZE_TO_PIPELINE = {
    ShotSize.EWS: "extreme_wide",
    ShotSize.WS: "wide",
    ShotSize.MWS: "medium_wide",
    ShotSize.MLS: "medium_long",
    ShotSize.MS: "medium",
    ShotSize.MCU: "medium_close_up",
    ShotSize.CU: "close_up",
    ShotSize.BCU: "close_up",
    ShotSize.ECU: "extreme_close_up",
    ShotSize.INSERT: "insert",
    ShotSize.AERIAL: "aerial",
    ShotSize.OTHER: "other",
}

_TYPE_TO_PIPELINE = {
    ShotType.SINGLE: "single",
    ShotType.TWO_SHOT: "two_shot",
    ShotType.GROUP: "group",
    ShotType.OTS: "over_the_shoulder",
    ShotType.POV: "point_of_view",
    ShotType.REACTION: "reaction",
    ShotType.ESTABLISHING: "establishing",
    ShotType.CUTAWAY: "cutaway",
    ShotType.MASTER: "master",
}

_MOVEMENT_TO_PIPELINE = {
    CameraMovement.STATIC: "static",
    CameraMovement.PAN: "pan",
    CameraMovement.TILT: "tilt",
    CameraMovement.DOLLY: "dolly",
    CameraMovement.PUSH_IN: "dolly_in",
    CameraMovement.PULL_OUT: "dolly_out",
    CameraMovement.TRUCK: "truck",
    CameraMovement.TRACKING: "tracking",
    CameraMovement.HANDHELD: "handheld",
    CameraMovement.STEADICAM: "steadicam",
    CameraMovement.CRANE: "crane",
    CameraMovement.DRONE: "drone",
    CameraMovement.ZOOM: "zoom",
    CameraMovement.WHIP_PAN: "whip_pan",
}

_ANGLE_TO_PIPELINE = {
    CameraAngle.EYE_LEVEL: "eye_level",
    CameraAngle.HIGH: "high_angle",
    CameraAngle.LOW: "low_angle",
    CameraAngle.BIRD: "birds_eye",
    CameraAngle.WORM: "worms_eye",
    CameraAngle.DUTCH: "dutch_angle",
    CameraAngle.OVERHEAD: "overhead",
    CameraAngle.GROUND: "ground_level",
}


def _shot_to_dict(shot: Shot) -> dict[str, Any]:
    cine = shot.cinematography
    d: dict[str, Any] = {
        "id": shot.id,
        "order": shot.order,
        "start_time": shot.start_time,
        "end_time": shot.end_time,
    }

    if cine.shot_size:
        d["shot_size"] = _SIZE_TO_PIPELINE.get(cine.shot_size, cine.shot_size.value)
    if cine.shot_type:
        d["shot_type"] = _TYPE_TO_PIPELINE.get(cine.shot_type, cine.shot_type.value)
    if cine.camera_movement:
        d["camera_movement"] = _MOVEMENT_TO_PIPELINE.get(
            cine.camera_movement, cine.camera_movement.value
        )
    if cine.camera_angle:
        d["camera_angle"] = _ANGLE_TO_PIPELINE.get(cine.camera_angle, cine.camera_angle.value)

    if shot.visual.description:
        d["description"] = shot.visual.description
    if shot.visual.dominant_colors:
        d["dominant_colors"] = shot.visual.dominant_colors
    if shot.visual.lighting:
        d["lighting"] = shot.visual.lighting

    if shot.audio.dialogue:
        d["dialogue"] = [
            {
                "speaker": dl.speaker,
                "text": dl.text,
                "start_time": dl.start_time,
                "end_time": dl.end_time,
            }
            for dl in shot.audio.dialogue
        ]

    if shot.characters_visible:
        d["visible_characters"] = list(shot.characters_visible)
    if shot.emotional_tone:
        d["emotional_tone"] = shot.emotional_tone

    if shot.editorial.confidence is not None:
        d["confidence"] = shot.editorial.confidence
    if shot.editorial.thumbnail_path:
        d["thumbnail_path"] = shot.editorial.thumbnail_path

    return d


def filmgraph_to_timeline(fg: FilmGraph) -> dict[str, Any]:
    """Serialize a FilmGraph into the pipeline timeline JSON format."""
    meta: dict[str, Any] = {
        "title": fg.meta.title,
        "duration": fg.meta.duration,
    }
    if fg.meta.frame_rate:
        meta["frame_rate"] = fg.meta.frame_rate
    if fg.meta.resolution:
        meta["resolution"] = fg.meta.resolution
    if fg.meta.language:
        meta["language"] = fg.meta.language

    scenes: list[dict[str, Any]] = []
    for scene in fg.scenes:
        scenes.append({
            "id": scene.id,
            "scene_number": scene.id,
            "title": scene.title,
            "summary": scene.summary,
            "start_time": scene.start_time,
            "end_time": scene.end_time,
            "location": scene.location,
            "characters": list(scene.characters),
            "mood": scene.mood,
            "themes": list(scene.themes),
            "shots": [_shot_to_dict(sh) for sh in scene.shots],
        })

    characters = [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
        }
        for c in fg.entities.characters
    ]

    return {
        "meta": meta,
        "characters": characters,
        "scenes": scenes,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Convert FilmGraph to pipeline timeline JSON"
    )
    ap.add_argument("input", help="Path to .filmgraph.json file")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    fg = FilmGraph.from_json(Path(args.input).read_text(encoding="utf-8"))
    data = filmgraph_to_timeline(fg)
    out = args.output or str(Path(args.input).with_suffix(".timeline.json"))
    Path(out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"{len(fg.scenes)} scenes, {total_shots} shots -> {out}")
