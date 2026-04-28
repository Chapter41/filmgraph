<div align="center">

# FilmGraph

**A structured data format for film analysis.**

[![PyPI](https://img.shields.io/pypi/v/filmgraph?color=%2334D058&label=pypi)](https://pypi.org/project/filmgraph/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[Install](#install) · [Quick Start](#quick-start) · [Schema](#schema) · [Importers](#importers) · [Exporters](#exporters) · [Docs](https://Chapter41.github.io/filmgraph)

</div>

---

## Why FilmGraph?

The film industry relies on dozens of incompatible formats — CCSLs in Word documents, Dialogbücher, SRT subtitles, EDLs, XML timelines, proprietary pipeline outputs. Building tools that work across these formats means spending more time parsing than analyzing.

FilmGraph is a single JSON schema that captures shots, scenes, dialogue, cinematography, characters, locations, and narrative events. Zero dependencies beyond Pydantic. One format for your entire pipeline.

```json
{
  "schema_version": "filmgraph/v1",
  "meta": { "title": "Lost Killers", "duration": 5731.2 },
  "scenes": [{
    "id": 1, "title": "Opening", "start_time": 0, "end_time": 142.5,
    "shots": [{
      "id": "sh-001", "order": 1, "start_time": 0, "end_time": 8.3,
      "cinematography": { "shot_size": "WS", "camera_movement": "static" },
      "visual": { "description": "Wide establishing shot of Berlin skyline at dusk" },
      "audio": { "dialogue": [{ "speaker": "narrator", "text": "Berlin, 1998.", "start_time": 2.1, "end_time": 4.5 }] }
    }]
  }]
}
```

## Install

```bash
pip install filmgraph
```

With importers for `.docx` files (CCSL, Dialogbuch, AD scripts):

```bash
pip install filmgraph[docx]
```

With OpenTimelineIO support (EDL, FCP XML, AAF):

```bash
pip install filmgraph[otio]
```

## Quick Start

```python
from pathlib import Path
from filmgraph import FilmGraph, Scene, Shot, ShotSize, CameraMovement

# Load
fg = FilmGraph.from_json(Path("movie.filmgraph.json").read_text())

# Traverse
for scene in fg.scenes:
    print(f"{scene.title} ({scene.shot_count} shots)")
    for shot in scene.shots:
        print(f"  {shot.cinematography.shot_size}  {shot.visual.description}")

# Save
Path("movie.filmgraph.json").write_text(fg.to_json(indent=2))
```

## Schema

```
FilmGraph
├── meta: FilmMeta            # title, duration, resolution, data sources
├── entities: Entities         # characters, locations (referenced by ID)
├── scenes: [Scene]            # narrative segments
│   ├── shots: [Shot]          # atomic visual units (cut to cut)
│   │   ├── cinematography     # shot_size, camera_movement, camera_angle
│   │   ├── visual             # description, colors, lighting
│   │   ├── audio              # dialogue lines, music cues, SFX
│   │   └── editorial          # transitions, confidence, thumbnail
│   └── dialogue: [DialogueLine]
└── events: [Event]            # plot turning points
```

### Controlled Vocabularies

Every categorical field uses a controlled enum with an `OTHER` fallback for extensibility.

| Enum | Values |
|------|--------|
| **ShotSize** | `ECU` · `BCU` · `CU` · `MCU` · `MS` · `MLS` · `MWS` · `WS` · `EWS` · `INSERT` · `AERIAL` · `OTHER` |
| **ShotType** | `single` · `two-shot` · `group` · `over-the-shoulder` · `point-of-view` · `reaction` · `establishing` · `insert` · `cutaway` · `master` · `other` |
| **CameraMovement** | `static` · `pan` · `tilt` · `dolly` · `truck` · `tracking` · `handheld` · `crane` · `drone` · `zoom` · `whip-pan` · `push-in` · `pull-out` · `arc` · `rack-focus` · `steadicam` · `other` |
| **CameraAngle** | `eye-level` · `high-angle` · `low-angle` · `birds-eye` · `worms-eye` · `dutch-angle` · `overhead` · `ground-level` · `other` |
| **Transition** | `cut` · `dissolve` · `fade-in` · `fade-out` · `fade-to-black` · `wipe` · `match-cut` · `jump-cut` · `j-cut` · `l-cut` · `smash-cut` · `other` |

## Importers

Convert industry formats into FilmGraph with a single function call:

```python
from filmgraph.importers.ccsl import ccsl_to_filmgraph
from filmgraph.importers.srt import srt_to_filmgraph

fg = ccsl_to_filmgraph("FTR3_BloodyTennis.docx")
fg = srt_to_filmgraph("movie.srt", title="My Film")
```

| Importer | Function | Input | Extra |
|----------|----------|-------|-------|
| **CCSL** | `ccsl_to_filmgraph()` | `.docx` shot lists | `pip install filmgraph[docx]` |
| **Dialogbuch** | `dialogbuch_to_filmgraph()` | German dubbing scripts `.docx` | `pip install filmgraph[docx]` |
| **AD Script** | `ad_to_filmgraph()` | Audio description scripts `.docx` | `pip install filmgraph[docx]` |
| **SRT/VTT** | `srt_to_filmgraph()` | Subtitle files | — |
| **Pipeline** | `timeline_to_filmgraph()` | Pipeline JSON output | — |
| **OTIO** | `otio_to_filmgraph()` | EDL, FCP XML, AAF | `pip install filmgraph[otio]` |

Each importer also works as a CLI:

```bash
python -m filmgraph.importers.ccsl input.docx -o output.filmgraph.json
python -m filmgraph.importers.srt movie.srt -o subs.filmgraph.json
```

## Exporters

Go the other direction — render a FilmGraph as the industry format of your choice:

```python
from filmgraph.exporters.srt import filmgraph_to_srt
from filmgraph.exporters.ccsl import filmgraph_to_ccsl

Path("movie.srt").write_text(filmgraph_to_srt(fg))
filmgraph_to_ccsl(fg, "movie_ccsl.docx")
```

| Exporter | Function | Output | Extra |
|----------|----------|--------|-------|
| **SRT/VTT** | `filmgraph_to_srt()` / `filmgraph_to_vtt()` | Subtitles | — |
| **CCSL** | `filmgraph_to_ccsl()` | `.docx` shot list | `pip install filmgraph[docx]` |
| **Dialogbuch** | `filmgraph_to_dialogbuch()` | German dubbing script `.docx` | `pip install filmgraph[docx]` |
| **AD Script** | `filmgraph_to_ad()` | Audio description `.docx` | `pip install filmgraph[docx]` |
| **Pipeline** | `filmgraph_to_timeline()` | Pipeline JSON | — |
| **Ground Truth** | `filmgraph_to_ground_truth()` | Bloody Tennis-style JSON fixture | — |
| **OTIO** | `filmgraph_to_otio()` | EDL, FCP XML, AAF, `.otio` | `pip install filmgraph[otio]` |
| **CSV** | `filmgraph_to_csv()` | Flat shot-list CSV | — |
| **Markdown** | `filmgraph_to_markdown()` | Human-readable report | — |

Every exporter also works as a CLI:

```bash
python -m filmgraph.exporters.srt movie.filmgraph.json -o movie.srt
python -m filmgraph.exporters.ccsl movie.filmgraph.json -o movie_ccsl.docx
python -m filmgraph.exporters.otio_export movie.filmgraph.json -o edit.edl
python -m filmgraph.exporters.markdown movie.filmgraph.json -o report.md
```

## Build a FilmGraph Programmatically

```python
from filmgraph import *

fg = FilmGraph(
    meta=FilmMeta(title="My Film", duration=5400.0),
    entities=Entities(characters=[
        Character(id="alice", name="Alice"),
        Character(id="bob", name="Bob"),
    ]),
    scenes=[
        Scene(
            id=1,
            title="Opening",
            summary="Alice meets Bob",
            start_time=0,
            end_time=120,
            shots=[
                Shot(
                    id="sh-001",
                    order=1,
                    start_time=0,
                    end_time=8.5,
                    cinematography=Cinematography(
                        shot_size=ShotSize.WS,
                        camera_movement=CameraMovement.STATIC,
                    ),
                    visual=Visual(description="Wide shot of a café"),
                    audio=Audio(dialogue=[
                        DialogueLine(
                            speaker="alice",
                            text="Is this seat taken?",
                            start_time=3.0,
                            end_time=5.2,
                        ),
                    ]),
                ),
            ],
        ),
    ],
)

print(fg.to_json(indent=2))
```

## JSON Schema

Generate the full JSON Schema for validation or code generation:

```python
import json
from filmgraph import FilmGraph

schema = FilmGraph.model_json_schema()
print(json.dumps(schema, indent=2))
```

## Contributing

Contributions welcome. Please open an issue first to discuss what you'd like to change.

## License

[MIT](LICENSE) · Made by [Chapter41](https://chapter41.de)
