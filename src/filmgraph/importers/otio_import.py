"""
OpenTimelineIO → FilmGraph importer.

Reads any OTIO-supported format (EDL, FCP XML, AAF, ALE, native .otio)
and converts the timeline into a FilmGraph with shot-level granularity.

Supported formats (via opentimelineio + plugins):
  .edl   — CMX3600 Edit Decision List (Avid, DaVinci Resolve)
  .xml   — Final Cut Pro XML (FCP 7/X)
  .aaf   — Advanced Authoring Format (Avid Media Composer)
  .ale   — Avid Log Exchange
  .otio  — Native OpenTimelineIO

Usage::

    from filmgraph.importers.otio_import import otio_to_filmgraph
    fg = otio_to_filmgraph("my_edit.edl", title="My Film")

CLI::

    python -m filmgraph.importers.otio_import my_edit.edl -o output.filmgraph.json
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

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
from filmgraph.vocabulary import CameraMovement, ShotSize, Transition


# ─── OTIO time helpers ───────────────────────────────────────────────────

def _rt_to_sec(rt) -> float:
    """Convert OTIO RationalTime to seconds."""
    return rt.to_seconds()


def _rt_to_tc(rt) -> Optional[str]:
    """Convert OTIO RationalTime to SMPTE timecode string."""
    try:
        return rt.to_timecode()
    except Exception:
        return None


# ─── Transition mapping ──────────────────────────────────────────────────

_TRANSITION_MAP = {
    "SMPTE_Dissolve": Transition.DISSOLVE,
    "Cross_Dissolve": Transition.DISSOLVE,
    "Dip_to_Color": Transition.FADE_TO_BLACK,
    "Fade": Transition.FADE_IN,
    "Wipe": Transition.WIPE,
}


# ─── Marker → metadata extraction ────────────────────────────────────────

def _extract_marker_metadata(markers) -> dict:
    """Extract any useful metadata from OTIO markers on a clip."""
    meta = {}
    for marker in markers:
        name = marker.name.strip() if marker.name else ""
        if name:
            meta.setdefault("markers", []).append({
                "name": name,
                "color": str(marker.color) if marker.color else None,
            })
    return meta


# ─── Main importer ───────────────────────────────────────────────────────

def otio_to_filmgraph(
    file_path: str,
    *,
    title: Optional[str] = None,
    frame_rate: Optional[float] = None,
    language: Optional[str] = None,
    adapter_name: Optional[str] = None,
) -> FilmGraph:
    """Read any OTIO-supported timeline and convert to FilmGraph.

    Args:
        file_path: Path to EDL, XML, AAF, ALE, or .otio file.
        title: Film/project title (defaults to timeline name or filename).
        frame_rate: Override frame rate (auto-detected from file if possible).
        language: ISO language code.
        adapter_name: Force a specific OTIO adapter (auto-detected by default).
    """
    import opentimelineio as otio

    # Read timeline using OTIO's adapter system
    kwargs = {}
    if adapter_name:
        kwargs["adapter_name"] = adapter_name

    result = otio.adapters.read_from_file(file_path, **kwargs)

    # Handle both Timeline and SerializableCollection
    if isinstance(result, otio.schema.Timeline):
        timelines = [result]
    elif isinstance(result, otio.schema.SerializableCollection):
        timelines = [t for t in result if isinstance(t, otio.schema.Timeline)]
    else:
        timelines = [result]

    if not timelines:
        return FilmGraph(
            meta=FilmMeta(title=title or Path(file_path).stem, duration=0.0),
        )

    timeline = timelines[0]

    # Resolve title
    if not title:
        title = timeline.name or Path(file_path).stem

    # Detect frame rate from first clip
    detected_rate = None
    for track in timeline.video_tracks():
        for child in track:
            if hasattr(child, "duration") and child.duration():
                detected_rate = child.duration().rate
                break
        if detected_rate:
            break
    fps = frame_rate or detected_rate or 24.0

    # Extract clips from video tracks
    shots: list[Shot] = []
    order = 1
    prev_transition: Optional[Transition] = None

    for track in timeline.video_tracks():
        for child in track:
            # Handle transitions
            if isinstance(child, otio.schema.Transition):
                transition_type = child.transition_type or ""
                prev_transition = _TRANSITION_MAP.get(
                    transition_type, Transition.OTHER
                )
                continue

            # Skip gaps/filler
            if isinstance(child, otio.schema.Gap):
                continue

            if not isinstance(child, otio.schema.Clip):
                continue

            # Timeline range (position in the edit)
            try:
                range_in_parent = child.range_in_parent()
                start_sec = _rt_to_sec(range_in_parent.start_time)
                duration_sec = _rt_to_sec(range_in_parent.duration)
                end_sec = start_sec + duration_sec
            except Exception:
                continue

            # Source timecodes
            tc_in = None
            tc_out = None
            if child.source_range:
                tc_in = _rt_to_tc(child.source_range.start_time)
                src_end = child.source_range.start_time + child.source_range.duration
                tc_out = _rt_to_tc(src_end)

            # Clip name → visual description
            clip_name = child.name or ""

            # Source clip reference
            source_clip = None
            if child.media_reference and hasattr(child.media_reference, "target_url"):
                source_clip = child.media_reference.target_url

            # Editorial metadata
            editorial = Editorial(
                transition_in=prev_transition,
                source_clip=source_clip,
            )
            prev_transition = None  # consumed

            # Extract markers
            custom = _extract_marker_metadata(child.markers)

            shots.append(Shot(
                id=f"otio-{order:04d}",
                order=order,
                start_time=start_sec,
                end_time=end_sec,
                timecode_in=tc_in,
                timecode_out=tc_out,
                visual=Visual(description=clip_name if clip_name else None),
                editorial=editorial,
                source="otio",
                custom=custom,
            ))
            order += 1

    # Duration
    duration = shots[-1].end_time if shots else 0.0

    # Source file extension for provenance
    suffix = Path(file_path).suffix.lstrip(".").lower()
    source_label = {
        "edl": "edl",
        "xml": "fcp-xml",
        "aaf": "aaf",
        "ale": "ale",
    }.get(suffix, f"otio/{suffix}")

    return FilmGraph(
        meta=FilmMeta(
            title=title,
            duration=duration,
            frame_rate=fps,
            language=language,
            sources=[DataSource(layer="editorial", source=source_label)],
        ),
        entities=Entities(),
        scenes=[
            Scene(
                id=1,
                title=f"Full Timeline ({suffix.upper()})",
                summary=f"{len(shots)} clips from {Path(file_path).name}",
                start_time=shots[0].start_time if shots else 0.0,
                end_time=shots[-1].end_time if shots else 0.0,
                shots=shots,
            )
        ] if shots else [],
    )


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Convert EDL/XML/AAF/OTIO to FilmGraph JSON"
    )
    ap.add_argument("file", help="Path to EDL, FCP XML, AAF, ALE, or .otio file")
    ap.add_argument("-o", "--output", default=None, help="Output .filmgraph.json path")
    ap.add_argument("--title", default=None, help="Film/project title")
    ap.add_argument("--fps", type=float, default=None, help="Frame rate override")
    ap.add_argument("--language", default=None)
    args = ap.parse_args()

    fg = otio_to_filmgraph(
        args.file, title=args.title, frame_rate=args.fps, language=args.language
    )

    out = args.output or Path(args.file).with_suffix(".filmgraph.json").name
    Path(out).write_text(fg.to_json(), encoding="utf-8")
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"✅ {total_shots} clips → {out}")
