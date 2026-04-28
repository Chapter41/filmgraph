"""
FilmGraph — A minimal, structured data format for film analysis.

    from filmgraph import FilmGraph, Shot, Scene, ShotSize, CameraMovement
"""

from filmgraph.schema import (
    FilmGraph,
    FilmMeta,
    DataSource,
    Entities,
    Character,
    Location,
    Scene,
    Shot,
    Cinematography,
    Visual,
    Audio,
    MusicCue,
    DialogueLine,
    Editorial,
    Event,
)
from filmgraph.vocabulary import (
    ShotSize,
    ShotType,
    CameraMovement,
    CameraAngle,
    Transition,
)

__version__ = "0.1.2"

__all__ = [
    "FilmGraph",
    "FilmMeta",
    "DataSource",
    "Entities",
    "Character",
    "Location",
    "Scene",
    "Shot",
    "Cinematography",
    "Visual",
    "Audio",
    "MusicCue",
    "DialogueLine",
    "Editorial",
    "Event",
    "ShotSize",
    "ShotType",
    "CameraMovement",
    "CameraAngle",
    "Transition",
]
