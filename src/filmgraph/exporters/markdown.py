"""
FilmGraph → Markdown report exporter.

Produces a human-readable breakdown of the film: title, meta, characters,
and a scene-by-scene, shot-by-shot list. Handy for handoffs, GitHub
previews, or pasting into issue trackers.

Usage::

    from filmgraph.exporters.markdown import filmgraph_to_markdown
    md = filmgraph_to_markdown(fg)

CLI::

    python -m filmgraph.exporters.markdown movie.filmgraph.json -o report.md
"""
from __future__ import annotations

from pathlib import Path

from filmgraph.schema import FilmGraph


def _fmt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    h = total_ms // 3_600_000
    m = (total_ms % 3_600_000) // 60_000
    s = (total_ms % 60_000) // 1000
    ms = total_ms % 1000
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
    return f"{m:02d}:{s:02d}.{ms:03d}"


def filmgraph_to_markdown(fg: FilmGraph) -> str:
    """Render a FilmGraph as a Markdown report."""
    name_lookup = {c.id: c.name for c in fg.entities.characters}
    lines: list[str] = []

    # Header
    lines.append(f"# {fg.meta.title}")
    lines.append("")
    if fg.meta.original_title and fg.meta.original_title != fg.meta.title:
        lines.append(f"*Original title:* {fg.meta.original_title}")
    meta_bits: list[str] = []
    if fg.meta.year:
        meta_bits.append(f"**Year:** {fg.meta.year}")
    if fg.meta.duration:
        meta_bits.append(f"**Duration:** {_fmt_time(fg.meta.duration)}")
    if fg.meta.frame_rate:
        meta_bits.append(f"**FPS:** {fg.meta.frame_rate:g}")
    if fg.meta.language:
        meta_bits.append(f"**Language:** {fg.meta.language}")
    if fg.meta.resolution:
        meta_bits.append(f"**Resolution:** {fg.meta.resolution}")
    if meta_bits:
        lines.append(" · ".join(meta_bits))
    lines.append("")

    # Characters
    if fg.entities.characters:
        lines.append("## Characters")
        lines.append("")
        for c in fg.entities.characters:
            bits = [f"**{c.name}**"]
            if c.actor:
                bits.append(f"_{c.actor}_")
            if c.description:
                bits.append(c.description)
            lines.append(f"- {' — '.join(bits)}")
        lines.append("")

    # Scenes and shots
    lines.append("## Scenes")
    lines.append("")
    for scene in fg.scenes:
        header = f"### Scene {scene.id}: {scene.title}"
        lines.append(header)
        lines.append("")
        lines.append(
            f"*{_fmt_time(scene.start_time)} – {_fmt_time(scene.end_time)}*"
            f" · {scene.shot_count} shots"
        )
        if scene.summary:
            lines.append("")
            lines.append(scene.summary)
        if scene.characters:
            names = [name_lookup.get(c, c) for c in scene.characters]
            lines.append("")
            lines.append(f"**Characters:** {', '.join(names)}")
        if scene.location:
            lines.append(f"**Location:** {scene.location}")
        if scene.mood:
            lines.append(f"**Mood:** {scene.mood}")
        lines.append("")

        for shot in scene.shots:
            cine = shot.cinematography
            tag_bits: list[str] = []
            if cine.shot_size:
                tag_bits.append(cine.shot_size.value)
            if cine.shot_type:
                tag_bits.append(cine.shot_type.value)
            if cine.camera_movement:
                tag_bits.append(cine.camera_movement.value)
            if cine.camera_angle:
                tag_bits.append(cine.camera_angle.value)
            tags = f" `{' · '.join(tag_bits)}`" if tag_bits else ""

            lines.append(
                f"- **Shot {shot.order}** "
                f"({_fmt_time(shot.start_time)}–{_fmt_time(shot.end_time)}){tags}"
            )
            if shot.visual.description:
                lines.append(f"  - {shot.visual.description}")
            for dl in shot.audio.dialogue:
                name = (
                    name_lookup.get(dl.speaker, dl.speaker.replace("-", " ").title())
                    if dl.speaker else "—"
                )
                lines.append(f"  - _{name}:_ {dl.text}")
        lines.append("")

    # Events
    if fg.events:
        lines.append("## Events")
        lines.append("")
        for event in fg.events:
            lines.append(
                f"- **{_fmt_time(event.timestamp)} – {event.name}:** {event.description}"
            )
        lines.append("")

    return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert FilmGraph to Markdown report")
    ap.add_argument("input", help="Path to .filmgraph.json file")
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()

    fg = FilmGraph.from_json(Path(args.input).read_text(encoding="utf-8"))
    text = filmgraph_to_markdown(fg)
    out = args.output or str(Path(args.input).with_suffix(".md"))
    Path(out).write_text(text, encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"{total_shots} shots -> {out}")
