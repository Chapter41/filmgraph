# Exporters

FilmGraph ships with exporters for every format the importers accept, plus a few extras. Each converts a `FilmGraph` object into an external format for handoff to editorial, localisation, or reporting tools.

## SRT / VTT Subtitles

Emits all dialogue lines as standard SubRip (.srt) or WebVTT (.vtt) subtitle files. Speaker names are prefixed (SRT) or wrapped in voice tags (VTT).

```python
from filmgraph.exporters.srt import filmgraph_to_srt, filmgraph_to_vtt

srt_text = filmgraph_to_srt(fg)
vtt_text = filmgraph_to_vtt(fg)
```

No extra dependencies needed.

## CCSL (.docx)

Writes a Combined Continuity & Spotting List in the flat `Shot# | Timing | Description | Dialogue` layout.

```python
from filmgraph.exporters.ccsl import filmgraph_to_ccsl

filmgraph_to_ccsl(fg, "movie_ccsl.docx", fps=24.0)
```

Requires: `pip install filmgraph[docx]`

## Dialogbuch (.docx)

Writes a German-style dubbing script with alternating timestamp and speaker-prefixed dialogue lines. Only shots containing dialogue are emitted.

```python
from filmgraph.exporters.dialogbuch import filmgraph_to_dialogbuch

filmgraph_to_dialogbuch(fg, "episode_dialogbuch.docx")
```

Requires: `pip install filmgraph[docx]`

## AD Script (.docx)

Writes a German audio description script with timecoded visual descriptions and quoted dialogue snippets.

```python
from filmgraph.exporters.ad_script import filmgraph_to_ad

filmgraph_to_ad(fg, "lost_killers_ad.docx")
```

Requires: `pip install filmgraph[docx]`

## Pipeline Timeline JSON

Produces the internal pipeline format consumed by `timeline_to_filmgraph`. Round-trip compatible with the importer.

```python
from filmgraph.exporters.timeline import filmgraph_to_timeline

data = filmgraph_to_timeline(fg)
```

No extra dependencies needed.

## Ground Truth JSON

Emits the Bloody Tennis-style hand-verified ground truth schema used by `ground_truth_to_filmgraph`. Useful for snapshotting a curated FilmGraph into the legacy fixture format.

```python
from filmgraph.exporters.ground_truth import filmgraph_to_ground_truth

data = filmgraph_to_ground_truth(fg)
```

No extra dependencies needed.

## OpenTimelineIO (EDL, FCP XML, AAF, .otio)

Writes any OTIO-supported timeline format. Shots become clips; transitions become OTIO Transition objects.

```python
from filmgraph.exporters.otio_export import filmgraph_to_otio

filmgraph_to_otio(fg, "output.otio")
filmgraph_to_otio(fg, "output.edl")   # requires the CMX-3600 adapter plugin
filmgraph_to_otio(fg, "output.xml")   # requires the FCP7 XML adapter plugin
```

Requires: `pip install filmgraph[otio]`. EDL / FCP XML / AAF output additionally require the corresponding OTIO adapter plugins.

## CSV Shot List

Emits one row per shot for review in spreadsheet tools. Columns: `scene_id, scene_title, shot_id, shot_order, start_time, end_time, duration, timecode_in, timecode_out, shot_size, shot_type, camera_movement, camera_angle, description, dialogue, characters`.

```python
from filmgraph.exporters.csv_export import filmgraph_to_csv

csv_text = filmgraph_to_csv(fg)
```

No extra dependencies needed.

## Markdown Report

Produces a human-readable breakdown — title, meta, characters, scene-by-scene shot list. Handy for GitHub previews and issue trackers.

```python
from filmgraph.exporters.markdown import filmgraph_to_markdown

md = filmgraph_to_markdown(fg)
```

No extra dependencies needed.

## CLI Usage

Every exporter also works as a CLI module:

```bash
python -m filmgraph.exporters.srt movie.filmgraph.json -o movie.srt
python -m filmgraph.exporters.srt movie.filmgraph.json -o movie.vtt --format vtt
python -m filmgraph.exporters.ccsl movie.filmgraph.json -o movie_ccsl.docx
python -m filmgraph.exporters.dialogbuch movie.filmgraph.json -o dialogbuch.docx
python -m filmgraph.exporters.ad_script movie.filmgraph.json -o ad.docx
python -m filmgraph.exporters.timeline movie.filmgraph.json -o timeline.json
python -m filmgraph.exporters.ground_truth movie.filmgraph.json -o ground_truth.json
python -m filmgraph.exporters.otio_export movie.filmgraph.json -o edit.edl
python -m filmgraph.exporters.csv_export movie.filmgraph.json -o shots.csv
python -m filmgraph.exporters.markdown movie.filmgraph.json -o report.md
```
