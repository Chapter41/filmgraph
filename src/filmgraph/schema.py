"""
FilmGraph Schema — Pydantic models for structured film analysis.

Hierarchy:  FilmGraph → Scene → Shot
Layers:     cinematography · visual · audio · editorial

Zero dependencies beyond pydantic. No framework coupling.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, computed_field

from filmgraph.vocabulary import (
    CameraAngle,
    CameraMovement,
    ShotSize,
    ShotType,
    Transition,
)


# ─── Film metadata ───────────────────────────────────────────────────────


class DataSource(BaseModel):
    """Provenance: which tool/model produced a data layer."""

    layer: str = Field(description="e.g. 'shots', 'visual', 'dialogue'")
    source: str = Field(description="e.g. 'pyscenedetect', 'gemini-2.0-flash'")
    version: Optional[str] = None
    date: Optional[str] = None


class FilmMeta(BaseModel):
    """Top-level metadata about the film."""

    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    duration: float = Field(description="Total duration in seconds")
    frame_rate: Optional[float] = None
    resolution: Optional[str] = Field(default=None, description="e.g. '1920x1080'")
    language: Optional[str] = None
    sources: list[DataSource] = Field(default_factory=list)


# ─── Entities ─────────────────────────────────────────────────────────────


class Character(BaseModel):
    """A character in the film, referenced by id."""

    id: str = Field(description="Slug, e.g. 'john-smith'")
    name: str
    actor: Optional[str] = None
    description: Optional[str] = None
    aliases: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list, description="e.g. protagonist, antagonist")
    appearances: list[int] = Field(default_factory=list, description="Scene IDs")
    quotes: list[dict[str, Any]] = Field(default_factory=list, description="[{text, timestamp}]")
    relations: list[dict[str, Any]] = Field(default_factory=list, description="[{related_to, relation}]")


class Location(BaseModel):
    """A location / setting."""

    id: str
    name: str
    type: Optional[str] = Field(default=None, description="INT, EXT, INT/EXT")
    description: Optional[str] = None


class Entities(BaseModel):
    """Reusable entities referenced by ID from scenes and shots."""

    characters: list[Character] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)


# ─── Shot layers ──────────────────────────────────────────────────────────


class Cinematography(BaseModel):
    """Camera and framing metadata for a shot."""

    shot_size: Optional[ShotSize] = None
    shot_type: Optional[ShotType] = None
    camera_angle: Optional[CameraAngle] = None
    camera_movement: Optional[CameraMovement] = None
    lens: Optional[str] = Field(default=None, description="e.g. '35mm', 'wide'")
    depth_of_field: Optional[str] = Field(default=None, description="shallow, deep")
    composition: list[str] = Field(default_factory=list, description="e.g. rule-of-thirds, symmetry")
    notes: Optional[str] = None


class Visual(BaseModel):
    """What's visible in the frame."""

    description: Optional[str] = None
    dominant_colors: list[str] = Field(default_factory=list)
    lighting: Optional[str] = None
    visual_style: Optional[str] = None


class DialogueLine(BaseModel):
    """A spoken line within a shot."""

    speaker: Optional[str] = Field(default=None, description="Character ID")
    text: str
    start_time: float
    end_time: float
    language: Optional[str] = None
    words: list[dict[str, Any]] = Field(
        default_factory=list, description="[{word, start, end, confidence}]"
    )


class MusicCue(BaseModel):
    """A music or sound design cue within a shot."""

    label: str = Field(description="e.g. 'threatening music', 'calm piano'")
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    type: Optional[str] = Field(
        default=None, description="'score', 'diegetic', 'sfx', 'ambient'"
    )


class Audio(BaseModel):
    """Audio metadata for a shot."""

    dialogue: list[DialogueLine] = Field(default_factory=list)
    sound: Optional[str] = Field(default=None, description="Ambient / SFX description")
    music_cues: list[MusicCue] = Field(
        default_factory=list, description="Structured music/sound cues"
    )


class Editorial(BaseModel):
    """Post-production metadata for a shot."""

    transition_in: Optional[Transition] = None
    transition_out: Optional[Transition] = None
    source_clip: Optional[str] = None
    thumbnail_path: Optional[str] = None
    confidence: Optional[float] = Field(
        default=None, description="ML confidence for auto-detected cut"
    )


# ─── Shot ─────────────────────────────────────────────────────────────────


class Shot(BaseModel):
    """A single visual shot — the atomic unit.

    Spans from one cut to the next. Metadata is organized into typed
    layers that can be independently populated.
    """

    id: str
    order: int
    start_time: float
    end_time: float

    # Timecode: human-readable SMPTE format, OTIO-compatible
    timecode_in: Optional[str] = Field(
        default=None, description="SMPTE timecode, e.g. '01:23:45:12'"
    )
    timecode_out: Optional[str] = Field(
        default=None, description="SMPTE timecode end"
    )

    # Layers
    cinematography: Cinematography = Field(default_factory=Cinematography)
    visual: Visual = Field(default_factory=Visual)
    audio: Audio = Field(default_factory=Audio)
    editorial: Editorial = Field(default_factory=Editorial)

    # References
    characters_visible: list[str] = Field(
        default_factory=list, description="Character IDs in frame"
    )
    emotional_tone: Optional[str] = None

    # Provenance
    source: Optional[str] = Field(
        default=None, description="Origin: 'ccsl', 'pipeline', 'manual', 'subtitle'"
    )
    verified: Optional[bool] = Field(
        default=None, description="Human-verified?"
    )

    # Escape hatch
    custom: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


# ─── Scene ────────────────────────────────────────────────────────────────


class Scene(BaseModel):
    """A narrative scene containing shots.

    Scene boundaries come from narrative analysis.
    Shots come from visual cut detection.
    """

    id: int
    title: str
    summary: str
    start_time: float
    end_time: float

    # References
    location: Optional[str] = Field(default=None, description="Location ID or name")
    characters: list[str] = Field(default_factory=list, description="Character IDs")

    # Narrative
    mood: Optional[str] = None
    themes: list[str] = Field(default_factory=list)

    # Scene-level visual summary
    visual_style: Optional[str] = None
    lighting_style: Optional[str] = None
    setting_context: Optional[str] = None
    visual_motifs: list[str] = Field(default_factory=list)

    # Shots
    shots: list[Shot] = Field(default_factory=list)

    # Dialogue (all lines in the scene, also present on individual shots)
    dialogue: list[DialogueLine] = Field(default_factory=list)

    # Escape hatch
    custom: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @computed_field
    @property
    def shot_count(self) -> int:
        return len(self.shots)


# ─── Events ───────────────────────────────────────────────────────────────


class Event(BaseModel):
    """A significant plot event or turning point."""

    id: str
    name: str
    description: str
    timestamp: float
    scene_id: Optional[int] = None
    characters_involved: list[str] = Field(default_factory=list)


# ─── FilmGraph (root) ─────────────────────────────────────────────────────


class FilmGraph(BaseModel):
    """Root document for structured film analysis.

    Usage::

        from filmgraph import FilmGraph

        fg = FilmGraph.model_validate_json(path.read_text())
        for scene in fg.scenes:
            for shot in scene.shots:
                print(shot.cinematography.shot_size, shot.visual.description)

        path.write_text(fg.model_dump_json(indent=2, exclude_none=True))
    """

    schema_version: str = Field(default="filmgraph/v1")
    meta: FilmMeta
    entities: Entities = Field(default_factory=Entities)
    scenes: list[Scene] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)

    def to_json(self, **kwargs: Any) -> str:
        """Serialize to compact JSON, excluding None and empty collections."""
        import json as _json

        defaults = {"exclude_none": True}
        defaults.update(kwargs)
        indent = defaults.pop("indent", 2)
        data = self.model_dump(**defaults)

        def _strip_empty(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: _strip_empty(v) for k, v in obj.items()
                        if v is not None and v != [] and v != {}}
            if isinstance(obj, list):
                return [_strip_empty(item) for item in obj]
            return obj

        return _json.dumps(_strip_empty(data), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> FilmGraph:
        """Parse from JSON string."""
        return cls.model_validate_json(json_str)

    def json_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for the format."""
        return self.model_json_schema()
