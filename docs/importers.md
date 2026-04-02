# Importers

FilmGraph ships with importers for common film industry formats. Each converts a specific source into a `FilmGraph` object.

## CCSL (Combined Continuity & Spotting List)

Parses `.docx` shot lists used in post-production. Supports two layouts:

- **Reel-banner format** — multi-reel SMPTE timecodes with `REEL X` headers
- **Shot-number format** — flat table with Shot# | Timing | Description | Dialogue

```python
from filmgraph.importers.ccsl import ccsl_to_filmgraph

fg = ccsl_to_filmgraph("FTR3_BloodyTennis.docx", fps=24.0, tc_offset=-44.42)
```

Requires: `pip install filmgraph[docx]`

## Dialogbuch (German Dubbing Script)

Parses German dubbing scripts with alternating timestamp + speaker: dialogue lines.

```python
from filmgraph.importers.dialogbuch import dialogbuch_to_filmgraph

fg = dialogbuch_to_filmgraph("100_FRIEDA_Dialogbuch.docx", language="de")
```

Requires: `pip install filmgraph[docx]`

## AD Script (Audio Description)

Parses German audio description scripts (Hörfilmfassung) with single timecodes and visual descriptions.

```python
from filmgraph.importers.ad_script import ad_to_filmgraph

fg = ad_to_filmgraph("lost_killers_ad.docx")
```

Requires: `pip install filmgraph[docx]`

## SRT / VTT Subtitles

Creates a FilmGraph with the dialogue layer populated from subtitles. Supports speaker extraction from VTT voice tags, bracket prefixes, and UPPERCASE: prefixes.

```python
from filmgraph.importers.srt import srt_to_filmgraph

fg = srt_to_filmgraph("movie.srt", title="My Film", language="en")
fg = srt_to_filmgraph("movie.vtt")  # WebVTT also supported
```

No extra dependencies needed.

## Pipeline Timeline

Converts internal pipeline JSON output (scene_adv or MovieTimeline format) into FilmGraph.

```python
from filmgraph.importers.timeline import timeline_to_filmgraph

raw = requests.get(f"{BASE}/api/projects/{pid}/timeline").json()
fg = timeline_to_filmgraph(raw["timeline"], title="My Film")
```

No extra dependencies needed.

## OpenTimelineIO (EDL, FCP XML, AAF)

Reads any OTIO-supported timeline format and converts to FilmGraph with shot-level granularity.

```python
from filmgraph.importers.otio_import import otio_to_filmgraph

fg = otio_to_filmgraph("my_edit.edl", title="My Film")
fg = otio_to_filmgraph("timeline.xml")    # FCP XML
fg = otio_to_filmgraph("project.aaf")     # Avid
```

Requires: `pip install filmgraph[otio]`

## CLI Usage

Every importer works as a CLI module:

```bash
python -m filmgraph.importers.ccsl input.docx -o output.filmgraph.json
python -m filmgraph.importers.srt movie.srt -o subs.filmgraph.json
python -m filmgraph.importers.dialogbuch script.docx -o dialogbuch.filmgraph.json
python -m filmgraph.importers.ad_script ad.docx -o ad.filmgraph.json
python -m filmgraph.importers.otio_import edit.edl -o edit.filmgraph.json
python -m filmgraph.importers.timeline --timeline-json dump.json -o output.filmgraph.json
```
