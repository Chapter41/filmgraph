"""
FilmGraph → CSV shot-list exporter.

Produces a flat CSV with one row per shot, useful for review in spreadsheet
tools, logging to analytics warehouses, or feeding into tools that speak
tabular data.

Columns::

    scene_id, scene_title, shot_id, shot_order, start_time, end_time,
    duration, timecode_in, timecode_out, shot_size, shot_type,
    camera_movement, camera_angle, description, dialogue, characters

Usage::

    from filmgraph.exporters.csv_export import filmgraph_to_csv
    csv_text = filmgraph_to_csv(fg)

CLI::

    python -m filmgraph.exporters.csv_export movie.filmgraph.json -o shots.csv
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

from filmgraph.schema import FilmGraph


_COLUMNS = [
    "scene_id",
    "scene_title",
    "shot_id",
    "shot_order",
    "start_time",
    "end_time",
    "duration",
    "timecode_in",
    "timecode_out",
    "shot_size",
    "shot_type",
    "camera_movement",
    "camera_angle",
    "description",
    "dialogue",
    "characters",
]


def filmgraph_to_csv(fg: FilmGraph) -> str:
    """Render a FilmGraph as a CSV shot list."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_COLUMNS, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()

    name_lookup = {c.id: c.name for c in fg.entities.characters}

    for scene in fg.scenes:
        for shot in scene.shots:
            cine = shot.cinematography

            dialogue_text = " | ".join(
                f"{name_lookup.get(dl.speaker, dl.speaker)}: {dl.text}"
                if dl.speaker else dl.text
                for dl in shot.audio.dialogue
            )

            characters = ", ".join(
                name_lookup.get(c, c) for c in shot.characters_visible
            )

            writer.writerow({
                "scene_id": scene.id,
                "scene_title": scene.title,
                "shot_id": shot.id,
                "shot_order": shot.order,
                "start_time": shot.start_time,
                "end_time": shot.end_time,
                "duration": round(shot.end_time - shot.start_time, 3),
                "timecode_in": shot.timecode_in or "",
                "timecode_out": shot.timecode_out or "",
                "shot_size": cine.shot_size.value if cine.shot_size else "",
                "shot_type": cine.shot_type.value if cine.shot_type else "",
                "camera_movement": cine.camera_movement.value if cine.camera_movement else "",
                "camera_angle": cine.camera_angle.value if cine.camera_angle else "",
                "description": shot.visual.description or "",
                "dialogue": dialogue_text,
                "characters": characters,
            })

    return buf.getvalue()


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert FilmGraph to CSV shot list")
    ap.add_argument("input", help="Path to .filmgraph.json file")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    fg = FilmGraph.from_json(Path(args.input).read_text(encoding="utf-8"))
    text = filmgraph_to_csv(fg)
    out = args.output or str(Path(args.input).with_suffix(".csv"))
    Path(out).write_text(text, encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"{total_shots} shots -> {out}")
