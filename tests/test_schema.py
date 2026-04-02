"""Core schema round-trip tests."""

from filmgraph import (
    FilmGraph,
    FilmMeta,
    Scene,
    Shot,
    Cinematography,
    Visual,
    Audio,
    DialogueLine,
    Character,
    Entities,
    ShotSize,
    CameraMovement,
    CameraAngle,
    Transition,
)


def _make_filmgraph() -> FilmGraph:
    """Build a minimal but complete FilmGraph for testing."""
    return FilmGraph(
        meta=FilmMeta(title="Test Film", duration=120.0, frame_rate=24.0),
        entities=Entities(
            characters=[Character(id="alice", name="Alice")],
        ),
        scenes=[
            Scene(
                id=1,
                title="Opening",
                summary="Alice enters",
                start_time=0.0,
                end_time=60.0,
                characters=["alice"],
                shots=[
                    Shot(
                        id="sh-001",
                        order=1,
                        start_time=0.0,
                        end_time=8.5,
                        cinematography=Cinematography(
                            shot_size=ShotSize.WS,
                            camera_movement=CameraMovement.STATIC,
                            camera_angle=CameraAngle.EYE_LEVEL,
                        ),
                        visual=Visual(description="Wide shot of a room"),
                        audio=Audio(
                            dialogue=[
                                DialogueLine(
                                    speaker="alice",
                                    text="Hello.",
                                    start_time=2.0,
                                    end_time=3.5,
                                )
                            ]
                        ),
                        characters_visible=["alice"],
                    ),
                    Shot(
                        id="sh-002",
                        order=2,
                        start_time=8.5,
                        end_time=15.0,
                        cinematography=Cinematography(
                            shot_size=ShotSize.CU,
                            camera_movement=CameraMovement.PUSH_IN,
                        ),
                    ),
                ],
            ),
        ],
    )


def test_round_trip():
    """to_json → from_json preserves all data."""
    fg = _make_filmgraph()
    json_str = fg.to_json(indent=2)
    restored = FilmGraph.from_json(json_str)

    assert restored.meta.title == "Test Film"
    assert restored.meta.duration == 120.0
    assert len(restored.scenes) == 1
    assert len(restored.scenes[0].shots) == 2
    assert restored.scenes[0].shots[0].cinematography.shot_size == ShotSize.WS
    assert restored.scenes[0].shots[0].audio.dialogue[0].text == "Hello."
    assert restored.entities.characters[0].name == "Alice"


def test_computed_fields():
    """duration and shot_count are computed correctly."""
    fg = _make_filmgraph()
    scene = fg.scenes[0]
    assert scene.duration == 60.0
    assert scene.shot_count == 2
    assert scene.shots[0].duration == 8.5
    assert scene.shots[1].duration == 6.5


def test_to_json_strips_empty():
    """to_json excludes None values and empty collections."""
    fg = FilmGraph(
        meta=FilmMeta(title="Minimal", duration=10.0),
        scenes=[
            Scene(
                id=1,
                title="Scene",
                summary="Test",
                start_time=0,
                end_time=10,
                shots=[
                    Shot(id="sh-1", order=1, start_time=0, end_time=5),
                ],
            )
        ],
    )
    json_str = fg.to_json()
    assert '"characters"' not in json_str  # empty list stripped
    assert '"events"' not in json_str  # empty list stripped
    assert '"visual_style"' not in json_str  # None stripped


def test_vocabulary_round_trip():
    """All enum values serialize and deserialize correctly."""
    for size in ShotSize:
        fg = FilmGraph(
            meta=FilmMeta(title="t", duration=1),
            scenes=[
                Scene(
                    id=1, title="s", summary="s", start_time=0, end_time=1,
                    shots=[
                        Shot(
                            id="x", order=1, start_time=0, end_time=1,
                            cinematography=Cinematography(shot_size=size),
                        )
                    ],
                )
            ],
        )
        restored = FilmGraph.from_json(fg.to_json())
        assert restored.scenes[0].shots[0].cinematography.shot_size == size


def test_schema_version():
    """Default schema_version is set."""
    fg = _make_filmgraph()
    assert fg.schema_version == "filmgraph/v1"
    data = fg.to_json()
    assert "filmgraph/v1" in data
