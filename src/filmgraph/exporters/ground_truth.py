"""
FilmGraph → ground_truth.json exporter.

Emits the Bloody Tennis-style hand-verified ground truth schema that is
consumed by `ground_truth_to_filmgraph`. Useful for snapshotting a
curated FilmGraph into the legacy fixture format used in evaluations.

Usage::

    from filmgraph.exporters.ground_truth import filmgraph_to_ground_truth
    data = filmgraph_to_ground_truth(fg)

CLI::

    python -m filmgraph.exporters.ground_truth movie.filmgraph.json -o ground_truth.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from filmgraph.schema import FilmGraph


def filmgraph_to_ground_truth(fg: FilmGraph) -> dict[str, Any]:
    """Serialize a FilmGraph to the ground_truth.json fixture format."""
    name_lookup = {c.id: c.name for c in fg.entities.characters}

    def _name(cid: str) -> str:
        return name_lookup.get(cid, cid)

    scenes_out: list[dict[str, Any]] = []
    for scene in fg.scenes:
        shots_out: list[dict[str, Any]] = []
        for shot in scene.shots:
            cine = shot.cinematography

            shot_dict: dict[str, Any] = {
                "order": shot.order,
                "start_time": shot.start_time,
                "end_time": shot.end_time,
                "description": shot.visual.description or "",
            }

            if cine.shot_size:
                shot_dict["shot_size"] = cine.shot_size.value
            if cine.camera_movement:
                shot_dict["camera_movement"] = cine.camera_movement.value.upper()
            if cine.camera_angle:
                shot_dict["modifier"] = cine.camera_angle.value.upper()
            if cine.shot_type:
                # Legacy GT stores OTS in the shot_size slot
                if cine.shot_type.value == "over-the-shoulder":
                    shot_dict["shot_size"] = "OTS"

            if shot.characters_visible:
                shot_dict["characters"] = [_name(c) for c in shot.characters_visible]

            if shot.audio.dialogue:
                shot_dict["dialogue_lines"] = [
                    {
                        "speaker": _name(dl.speaker) if dl.speaker else None,
                        "text": dl.text,
                        "start_time": dl.start_time,
                        "end_time": dl.end_time,
                    }
                    for dl in shot.audio.dialogue
                ]

            if shot.audio.music_cues:
                shot_dict["music_sfx"] = shot.audio.music_cues[0].label

            if shot.source:
                shot_dict["source"] = shot.source
            if shot.verified is not None:
                shot_dict["verified"] = shot.verified

            shots_out.append(shot_dict)

        scene_dict: dict[str, Any] = {
            "order": scene.id,
            "name": scene.title,
            "summary": scene.summary,
            "start_time": scene.start_time,
            "end_time": scene.end_time,
            "characters": [_name(c) for c in scene.characters],
            "shots": shots_out,
        }
        if scene.location:
            scene_dict["location"] = scene.location
        scenes_out.append(scene_dict)

    data: dict[str, Any] = {
        "movie_name": fg.meta.title,
        "scenes": scenes_out,
    }
    if fg.meta.language:
        data["language"] = fg.meta.language
    if fg.meta.frame_rate:
        data["fps"] = fg.meta.frame_rate

    return data


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert FilmGraph to ground_truth.json")
    ap.add_argument("input", help="Path to .filmgraph.json file")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    fg = FilmGraph.from_json(Path(args.input).read_text(encoding="utf-8"))
    data = filmgraph_to_ground_truth(fg)
    out = args.output or str(Path(args.input).with_suffix(".ground_truth.json"))
    Path(out).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"{len(fg.scenes)} scenes, {total_shots} shots -> {out}")
