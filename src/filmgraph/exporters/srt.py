"""
FilmGraph → SRT/VTT subtitle exporter.

Emits all dialogue lines in the FilmGraph as standard SubRip (.srt) or
WebVTT (.vtt) subtitle files. Speaker names (resolved from the character
entity list when possible) are included as prefixes on SRT and as VTT
voice tags on VTT.

Usage::

    from filmgraph.exporters.srt import filmgraph_to_srt, filmgraph_to_vtt

    srt_text = filmgraph_to_srt(fg)
    vtt_text = filmgraph_to_vtt(fg)

CLI::

    python -m filmgraph.exporters.srt movie.filmgraph.json -o movie.srt
    python -m filmgraph.exporters.srt movie.filmgraph.json -o movie.vtt --format vtt
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from filmgraph.schema import DialogueLine, FilmGraph


def _format_srt_time(seconds: float) -> str:
    """Seconds → HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    h = total_ms // 3_600_000
    m = (total_ms % 3_600_000) // 60_000
    s = (total_ms % 60_000) // 1000
    ms = total_ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_vtt_time(seconds: float) -> str:
    """Seconds → HH:MM:SS.mmm."""
    return _format_srt_time(seconds).replace(",", ".")


def _collect_dialogue(fg: FilmGraph) -> list[DialogueLine]:
    """Gather all dialogue lines across scenes and shots, time-sorted, de-duped."""
    seen: set[tuple[float, float, Optional[str], str]] = set()
    lines: list[DialogueLine] = []

    def _add(dl: DialogueLine) -> None:
        key = (dl.start_time, dl.end_time, dl.speaker, dl.text)
        if key in seen:
            return
        seen.add(key)
        lines.append(dl)

    for scene in fg.scenes:
        for dl in scene.dialogue:
            _add(dl)
        for shot in scene.shots:
            for dl in shot.audio.dialogue:
                _add(dl)

    lines.sort(key=lambda dl: (dl.start_time, dl.end_time))
    return lines


def _speaker_display_name(fg: FilmGraph, speaker_id: Optional[str]) -> Optional[str]:
    """Resolve a speaker ID to its display name via the character list."""
    if not speaker_id:
        return None
    for char in fg.entities.characters:
        if char.id == speaker_id:
            return char.name
    return speaker_id.replace("-", " ").title()


def filmgraph_to_srt(fg: FilmGraph, *, include_speakers: bool = True) -> str:
    """Render a FilmGraph as an SRT subtitle document."""
    blocks: list[str] = []
    for i, dl in enumerate(_collect_dialogue(fg), 1):
        ts = f"{_format_srt_time(dl.start_time)} --> {_format_srt_time(dl.end_time)}"
        text = dl.text
        if include_speakers and dl.speaker:
            name = _speaker_display_name(fg, dl.speaker)
            if name:
                text = f"{name.upper()}: {text}"
        blocks.append(f"{i}\n{ts}\n{text}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def filmgraph_to_vtt(fg: FilmGraph, *, include_speakers: bool = True) -> str:
    """Render a FilmGraph as a WebVTT subtitle document."""
    out: list[str] = ["WEBVTT", ""]
    for i, dl in enumerate(_collect_dialogue(fg), 1):
        ts = f"{_format_vtt_time(dl.start_time)} --> {_format_vtt_time(dl.end_time)}"
        text = dl.text
        if include_speakers and dl.speaker:
            name = _speaker_display_name(fg, dl.speaker)
            if name:
                text = f"<v {name}>{text}</v>"
        out.append(str(i))
        out.append(ts)
        out.append(text)
        out.append("")
    return "\n".join(out)


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert FilmGraph to SRT/VTT subtitles")
    ap.add_argument("input", help="Path to .filmgraph.json file")
    ap.add_argument("-o", "--output", default=None, help="Output path")
    ap.add_argument("--format", choices=["srt", "vtt"], default=None,
                    help="Output format (auto-detected from extension)")
    ap.add_argument("--no-speakers", action="store_true",
                    help="Omit speaker prefixes/tags")
    args = ap.parse_args()

    fg = FilmGraph.from_json(Path(args.input).read_text(encoding="utf-8"))

    fmt = args.format
    if not fmt and args.output:
        fmt = "vtt" if args.output.lower().endswith(".vtt") else "srt"
    fmt = fmt or "srt"

    if fmt == "vtt":
        text = filmgraph_to_vtt(fg, include_speakers=not args.no_speakers)
    else:
        text = filmgraph_to_srt(fg, include_speakers=not args.no_speakers)

    out = args.output or str(Path(args.input).with_suffix(f".{fmt}"))
    Path(out).write_text(text, encoding="utf-8")
    total = sum(
        1
        for sc in fg.scenes
        for sh in sc.shots
        for _ in sh.audio.dialogue
    )
    print(f"{total} dialogue lines -> {out}")
