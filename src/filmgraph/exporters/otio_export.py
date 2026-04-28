"""
FilmGraph → OpenTimelineIO exporter.

Writes any OTIO-supported format (EDL, FCP XML, AAF, native .otio)
from a FilmGraph. Shots become Clips on a single video track. The
optional editorial transitions on each shot are emitted as OTIO
Transition objects between clips.

Supported formats (via opentimelineio + plugins):
  .edl   — CMX3600 Edit Decision List (Avid, DaVinci Resolve)
  .xml   — Final Cut Pro XML (FCP 7/X)
  .aaf   — Advanced Authoring Format (Avid Media Composer)
  .otio  — Native OpenTimelineIO

Usage::

    from filmgraph.exporters.otio_export import filmgraph_to_otio
    filmgraph_to_otio(fg, "output.edl")

CLI::

    python -m filmgraph.exporters.otio_export movie.filmgraph.json -o movie.edl
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from filmgraph.schema import FilmGraph, Shot
from filmgraph.vocabulary import Transition


_TRANSITION_REVERSE = {
    Transition.DISSOLVE: "SMPTE_Dissolve",
    Transition.FADE_IN: "Fade",
    Transition.FADE_OUT: "Fade",
    Transition.FADE_TO_BLACK: "Dip_to_Color",
    Transition.WIPE: "Wipe",
}


def _build_timeline(fg: FilmGraph, *, frame_rate: float):
    """Build an OTIO Timeline from a FilmGraph."""
    import opentimelineio as otio

    timeline = otio.schema.Timeline(name=fg.meta.title)
    track = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    timeline.tracks.append(track)

    shots: list[Shot] = [sh for sc in fg.scenes for sh in sc.shots]

    for shot in shots:
        # Emit a transition if the shot declares an incoming one
        trans = shot.editorial.transition_in
        if trans and trans != Transition.CUT:
            transition_type = _TRANSITION_REVERSE.get(trans, "SMPTE_Dissolve")
            # 12-frame default; OTIO needs non-zero in/out durations
            half = otio.opentime.RationalTime(6, frame_rate)
            track.append(otio.schema.Transition(
                transition_type=transition_type,
                in_offset=half,
                out_offset=half,
            ))

        duration_sec = max(0.0, shot.end_time - shot.start_time)
        duration = otio.opentime.RationalTime.from_seconds(duration_sec, frame_rate)
        start = otio.opentime.RationalTime.from_seconds(shot.start_time, frame_rate)

        source_range = otio.opentime.TimeRange(start_time=start, duration=duration)

        clip_name = shot.visual.description or shot.id
        # Truncate very long descriptions for EDL compatibility
        if len(clip_name) > 80:
            clip_name = clip_name[:77] + "..."

        media_ref = None
        if shot.editorial.source_clip:
            media_ref = otio.schema.ExternalReference(
                target_url=shot.editorial.source_clip
            )

        clip = otio.schema.Clip(
            name=clip_name,
            source_range=source_range,
            media_reference=media_ref,
        )
        track.append(clip)

    return timeline


def filmgraph_to_otio(
    fg: FilmGraph,
    output_path: str,
    *,
    frame_rate: Optional[float] = None,
    adapter_name: Optional[str] = None,
) -> str:
    """Write a FilmGraph to any OTIO-supported timeline format.

    Args:
        fg: The FilmGraph to export.
        output_path: Destination file (.edl, .xml, .aaf, .otio).
        frame_rate: Frame rate for time conversions (defaults to fg.meta.frame_rate or 24).
        adapter_name: Force a specific OTIO adapter.

    Returns the output path.
    """
    import opentimelineio as otio

    fps = frame_rate or fg.meta.frame_rate or 24.0
    timeline = _build_timeline(fg, frame_rate=fps)

    kwargs = {}
    if adapter_name:
        kwargs["adapter_name"] = adapter_name

    otio.adapters.write_to_file(timeline, output_path, **kwargs)
    return output_path


# ─── CLI ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Convert FilmGraph to EDL/XML/AAF/OTIO"
    )
    ap.add_argument("input", help="Path to .filmgraph.json file")
    ap.add_argument("-o", "--output", required=True,
                    help="Output path (.edl, .xml, .aaf, .otio)")
    ap.add_argument("--fps", type=float, default=None)
    ap.add_argument("--adapter", default=None, help="Force OTIO adapter name")
    args = ap.parse_args()

    fg = FilmGraph.from_json(Path(args.input).read_text(encoding="utf-8"))
    filmgraph_to_otio(fg, args.output, frame_rate=args.fps, adapter_name=args.adapter)
    total_shots = sum(s.shot_count for s in fg.scenes)
    print(f"{total_shots} clips -> {args.output}")
