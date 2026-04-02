"""
SRT/VTT subtitle → FilmGraph importer.

Creates a FilmGraph with the dialogue layer populated from subtitles.
No shots or scenes are created — just dialogue lines that can be merged
with a shot-level FilmGraph later.

Usage::

    from filmgraph.importers.srt import srt_to_filmgraph
    fg = srt_to_filmgraph("movie.srt", title="My Film")

CLI::

    python -m filmgraph.importers.srt movie.srt -o movie_subs.filmgraph.json
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from filmgraph.schema import (
    Audio,
    Character,
    DataSource,
    DialogueLine,
    Entities,
    FilmGraph,
    FilmMeta,
    Scene,
    Shot,
)


def _parse_srt_time(ts: str) -> float:
    """Parse SRT timestamp HH:MM:SS,mmm → float seconds."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, rest = parts
        return int(h) * 3600 + int(m) * 60 + float(rest)
    if len(parts) == 2:
        m, rest = parts
        return int(m) * 60 + float(rest)
    return float(ts)


def _parse_vtt_time(ts: str) -> float:
    """Parse VTT timestamp. Same as SRT but uses dot for millis."""
    return _parse_srt_time(ts.replace(".", ",", 1) if "." in ts else ts)


def _extract_speaker(text: str) -> tuple[Optional[str], str]:
    """Extract speaker from subtitle text patterns.

    Supports:
        - VTT voice tags: <v Speaker Name>text</v>
        - Prefix pattern: SPEAKER: text  or  [Speaker]: text
        - Prefix pattern: (Speaker) text
    """
    # VTT voice tag
    m = re.match(r"<v\s+([^>]+)>(.*?)(?:</v>)?$", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Bracket prefix: [Speaker Name]: text
    m = re.match(r"\[([^\]]+)\][:\s]\s*(.*)", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Parenthesis prefix: (Speaker) text
    m = re.match(r"\(([^)]+)\)[:\s]\s*(.*)", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # UPPERCASE prefix: SPEAKER: text (common in closed captions)
    m = re.match(r"^([A-Z][A-Z\s\-'\.]{1,25}):\s+(.*)", text, re.DOTALL)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    return None, text


def _to_char_id(name: str) -> str:
    """Convert a speaker name to a slug-format character ID."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_srt(content: str) -> list[DialogueLine]:
    """Parse SRT content into DialogueLine list."""
    blocks = re.split(r"\n\n+", content.strip())
    lines: list[DialogueLine] = []

    for block in blocks:
        block_lines = block.strip().split("\n")
        if len(block_lines) < 2:
            continue

        # Find timestamp line (skip sequence number)
        ts_line = None
        text_start = 0
        for i, line in enumerate(block_lines):
            if " --> " in line:
                ts_line = line
                text_start = i + 1
                break

        if ts_line is None:
            continue

        # Parse timestamps
        parts = ts_line.split(" --> ")
        if len(parts) != 2:
            continue

        start = _parse_srt_time(parts[0])
        end = _parse_srt_time(parts[1].split(" ")[0])  # strip positioning info

        # Join remaining lines as text, strip HTML tags
        text = " ".join(block_lines[text_start:])
        text = re.sub(r"<[^>]+>", "", text).strip()

        if not text:
            continue

        speaker, clean_text = _extract_speaker(text)
        speaker_id = _to_char_id(speaker) if speaker else None

        lines.append(DialogueLine(
            speaker=speaker_id,
            text=clean_text,
            start_time=start,
            end_time=end,
        ))

    return lines


def parse_vtt(content: str) -> list[DialogueLine]:
    """Parse WebVTT content into DialogueLine list."""
    # Strip WEBVTT header and metadata
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, count=1, flags=re.DOTALL)
    # Strip NOTE blocks
    content = re.sub(r"NOTE\n.*?\n\n", "", content, flags=re.DOTALL)
    # Strip STYLE blocks
    content = re.sub(r"STYLE\n.*?\n\n", "", content, flags=re.DOTALL)

    blocks = re.split(r"\n\n+", content.strip())
    lines: list[DialogueLine] = []

    for block in blocks:
        block_lines = block.strip().split("\n")
        if not block_lines:
            continue

        # Find timestamp line
        ts_line = None
        text_start = 0
        for i, line in enumerate(block_lines):
            if " --> " in line:
                ts_line = line
                text_start = i + 1
                break

        if ts_line is None:
            continue

        parts = ts_line.split(" --> ")
        if len(parts) != 2:
            continue

        start = _parse_vtt_time(parts[0])
        end = _parse_vtt_time(parts[1].split(" ")[0])

        raw_text = " ".join(block_lines[text_start:])

        # Extract speaker from raw text BEFORE stripping tags
        # (VTT voice tags like <v Alice> would be lost otherwise)
        speaker, clean_text = _extract_speaker(raw_text)

        # Now strip remaining HTML/VTT tags
        clean_text = re.sub(r"<[^>]+>", "", clean_text).strip()

        if not clean_text:
            continue

        speaker_id = _to_char_id(speaker) if speaker else None

        lines.append(DialogueLine(
            speaker=speaker_id,
            text=clean_text,
            start_time=start,
            end_time=end,
        ))

    return lines


def srt_to_filmgraph(
    path: str,
    *,
    title: Optional[str] = None,
    language: Optional[str] = None,
) -> FilmGraph:
    """Parse an SRT or VTT file and return a FilmGraph with dialogue layer.

    The result has no scenes/shots — only dialogue lines grouped into a
    single scene. Merge with a shot-level FilmGraph for full evaluation.
    """
    p = Path(path)
    content = p.read_text(encoding="utf-8")

    if p.suffix.lower() == ".vtt":
        dialogue_lines = parse_vtt(content)
    else:
        dialogue_lines = parse_srt(content)

    if not title:
        title = p.stem.replace("_", " ").replace("-", " ")

    # Apply language to all lines
    if language:
        for dl in dialogue_lines:
            dl.language = language

    # Extract unique speakers as characters
    char_ids: set[str] = set()
    for dl in dialogue_lines:
        if dl.speaker:
            char_ids.add(dl.speaker)

    characters = [Character(id=cid, name=cid.replace("-", " ").title()) for cid in sorted(char_ids)]

    # Duration from last subtitle end
    duration = max((dl.end_time for dl in dialogue_lines), default=0.0)

    # Create a single "scene" that holds all dialogue as shots with only audio
    # Each DialogueLine gets its own thin Shot so evaluation can match by time
    shots = [
        Shot(
            id=f"sub-{i+1:04d}",
            order=i + 1,
            start_time=dl.start_time,
            end_time=dl.end_time,
            audio=Audio(dialogue=[dl]),
        )
        for i, dl in enumerate(dialogue_lines)
    ]

    return FilmGraph(
        meta=FilmMeta(
            title=title,
            duration=duration,
            language=language,
            sources=[DataSource(layer="dialogue", source=f"subtitle-{p.suffix.lstrip('.')}")],
        ),
        entities=Entities(characters=characters),
        scenes=[
            Scene(
                id=1,
                title="Subtitles",
                summary=f"{len(dialogue_lines)} subtitle lines",
                start_time=dialogue_lines[0].start_time if dialogue_lines else 0.0,
                end_time=duration,
                shots=shots,
            )
        ] if dialogue_lines else [],
    )


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Convert SRT/VTT subtitles to FilmGraph JSON")
    ap.add_argument("path", help="Path to .srt or .vtt file")
    ap.add_argument("-o", "--output", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--language", default=None)
    args = ap.parse_args()

    fg = srt_to_filmgraph(args.path, title=args.title, language=args.language)
    out = args.output or Path(args.path).with_suffix(".filmgraph.json").name
    Path(out).write_text(fg.to_json(), encoding="utf-8")
    total_lines = sum(len(sh.audio.dialogue) for sc in fg.scenes for sh in sc.shots)
    print(f"✅ {total_lines} dialogue lines → {out}")
