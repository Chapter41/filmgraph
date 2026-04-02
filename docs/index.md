# FilmGraph

A minimal, structured data format for film analysis.

Read the full documentation at [Chapter41.github.io/filmgraph](https://Chapter41.github.io/filmgraph).

## Install

```bash
pip install filmgraph
```

## Quick Start

```python
from filmgraph import FilmGraph, Shot, Scene, ShotSize

fg = FilmGraph.from_json(Path("movie.filmgraph.json").read_text())

for scene in fg.scenes:
    for shot in scene.shots:
        print(shot.cinematography.shot_size, shot.visual.description)
```

See the [Schema Reference](schema.md) for full details.
