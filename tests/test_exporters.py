"""Tests for FilmGraph exporters and round-tripping with importers."""
from __future__ import annotations

import csv
import io
import json

import pytest

from filmgraph import (
    Audio,
    CameraAngle,
    CameraMovement,
    Character,
    Cinematography,
    DialogueLine,
    Entities,
    FilmGraph,
    FilmMeta,
    MusicCue,
    Scene,
    Shot,
    ShotSize,
    ShotType,
    Transition,
    Visual,
    Editorial,
)


# ─── Fixture helpers ─────────────────────────────────────────────────────

def _sample_fg() -> FilmGraph:
    """Build a mid-complexity FilmGraph covering all exporter paths."""
    return FilmGraph(
        meta=FilmMeta(
            title="Test Film",
            duration=20.0,
            frame_rate=24.0,
            language="en",
        ),
        entities=Entities(
            characters=[
                Character(id="alice", name="Alice"),
                Character(id="bob", name="Bob"),
            ]
        ),
        scenes=[
            Scene(
                id=1,
                title="Opening",
                summary="Alice and Bob meet",
                start_time=0.0,
                end_time=20.0,
                characters=["alice", "bob"],
                location="Café",
                mood="warm",
                shots=[
                    Shot(
                        id="sh-001",
                        order=1,
                        start_time=0.0,
                        end_time=5.0,
                        timecode_in="01:00:00:00",
                        timecode_out="01:00:05:00",
                        cinematography=Cinematography(
                            shot_size=ShotSize.WS,
                            shot_type=ShotType.ESTABLISHING,
                            camera_movement=CameraMovement.STATIC,
                            camera_angle=CameraAngle.EYE_LEVEL,
                        ),
                        visual=Visual(description="Wide shot of the café"),
                        audio=Audio(
                            dialogue=[
                                DialogueLine(
                                    speaker="alice",
                                    text="Hello, Bob.",
                                    start_time=1.0,
                                    end_time=2.5,
                                    language="en",
                                )
                            ],
                            music_cues=[MusicCue(label="soft piano")],
                        ),
                        characters_visible=["alice", "bob"],
                        editorial=Editorial(source_clip="clip_001.mov"),
                    ),
                    Shot(
                        id="sh-002",
                        order=2,
                        start_time=5.0,
                        end_time=10.0,
                        cinematography=Cinematography(
                            shot_size=ShotSize.CU,
                            shot_type=ShotType.OTS,
                            camera_movement=CameraMovement.PUSH_IN,
                        ),
                        visual=Visual(description="Close-up over Alice's shoulder"),
                        audio=Audio(
                            dialogue=[
                                DialogueLine(
                                    speaker="bob",
                                    text="Good to see you.",
                                    start_time=6.0,
                                    end_time=7.5,
                                )
                            ]
                        ),
                        characters_visible=["bob"],
                        editorial=Editorial(transition_in=Transition.DISSOLVE),
                    ),
                    Shot(
                        id="sh-003",
                        order=3,
                        start_time=10.0,
                        end_time=20.0,
                        visual=Visual(description="Exterior street"),
                        custom={"scene_change": True},
                    ),
                ],
            )
        ],
    )


@pytest.fixture
def fg() -> FilmGraph:
    return _sample_fg()


# ─── SRT / VTT ────────────────────────────────────────────────────────────

def test_srt_export_basic(fg: FilmGraph):
    from filmgraph.exporters.srt import filmgraph_to_srt

    text = filmgraph_to_srt(fg)
    assert "00:00:01,000 --> 00:00:02,500" in text
    assert "ALICE: Hello, Bob." in text
    assert "BOB: Good to see you." in text


def test_srt_roundtrip_with_importer(fg: FilmGraph, tmp_path):
    from filmgraph.exporters.srt import filmgraph_to_srt
    from filmgraph.importers.srt import srt_to_filmgraph

    srt_path = tmp_path / "out.srt"
    srt_path.write_text(filmgraph_to_srt(fg), encoding="utf-8")

    restored = srt_to_filmgraph(str(srt_path), title="Test Film")
    lines = [
        dl
        for sc in restored.scenes
        for sh in sc.shots
        for dl in sh.audio.dialogue
    ]
    assert len(lines) == 2
    assert lines[0].speaker == "alice"
    assert lines[0].text == "Hello, Bob."
    assert lines[1].speaker == "bob"


def test_vtt_export(fg: FilmGraph):
    from filmgraph.exporters.srt import filmgraph_to_vtt

    text = filmgraph_to_vtt(fg)
    assert text.startswith("WEBVTT")
    assert "<v Alice>Hello, Bob.</v>" in text
    assert "00:00:01.000 --> 00:00:02.500" in text


def test_vtt_roundtrip(fg: FilmGraph, tmp_path):
    from filmgraph.exporters.srt import filmgraph_to_vtt
    from filmgraph.importers.srt import srt_to_filmgraph

    vtt_path = tmp_path / "out.vtt"
    vtt_path.write_text(filmgraph_to_vtt(fg), encoding="utf-8")

    restored = srt_to_filmgraph(str(vtt_path))
    lines = [
        dl
        for sc in restored.scenes
        for sh in sc.shots
        for dl in sh.audio.dialogue
    ]
    assert lines[0].speaker == "alice"
    assert lines[0].text == "Hello, Bob."


def test_srt_excludes_empty():
    """Empty FilmGraph produces empty-ish SRT, no errors."""
    from filmgraph.exporters.srt import filmgraph_to_srt

    empty = FilmGraph(meta=FilmMeta(title="Empty", duration=0.0))
    assert filmgraph_to_srt(empty).strip() == ""


# ─── Timeline JSON ────────────────────────────────────────────────────────

def test_timeline_roundtrip(fg: FilmGraph):
    from filmgraph.exporters.timeline import filmgraph_to_timeline
    from filmgraph.importers.timeline import timeline_to_filmgraph

    data = filmgraph_to_timeline(fg)
    assert data["meta"]["title"] == "Test Film"
    assert len(data["scenes"]) == 1
    assert len(data["scenes"][0]["shots"]) == 3

    restored = timeline_to_filmgraph(data)
    assert restored.meta.title == "Test Film"
    assert len(restored.scenes) == 1
    sc = restored.scenes[0]
    assert sc.location == "Café"
    assert len(sc.shots) == 3
    assert sc.shots[0].cinematography.shot_size == ShotSize.WS
    assert sc.shots[1].cinematography.shot_type == ShotType.OTS
    assert sc.shots[1].cinematography.camera_movement == CameraMovement.PUSH_IN
    assert sc.shots[0].audio.dialogue[0].speaker == "alice"
    assert "alice" in sc.shots[0].characters_visible


# ─── Ground truth JSON ────────────────────────────────────────────────────

def test_ground_truth_roundtrip(fg: FilmGraph, tmp_path):
    from filmgraph.exporters.ground_truth import filmgraph_to_ground_truth
    from filmgraph.importers.ground_truth import ground_truth_to_filmgraph

    data = filmgraph_to_ground_truth(fg)
    assert data["movie_name"] == "Test Film"
    assert data["fps"] == 24.0
    assert len(data["scenes"]) == 1

    gt_path = tmp_path / "gt.json"
    gt_path.write_text(json.dumps(data), encoding="utf-8")

    restored = ground_truth_to_filmgraph(str(gt_path))
    assert restored.meta.title == "Test Film"
    assert len(restored.scenes[0].shots) == 3
    # OTS should survive the round-trip
    assert restored.scenes[0].shots[1].cinematography.shot_type == ShotType.OTS


# ─── CCSL docx ────────────────────────────────────────────────────────────

def test_ccsl_docx_roundtrip(fg: FilmGraph, tmp_path):
    pytest.importorskip("docx")
    from filmgraph.exporters.ccsl import filmgraph_to_ccsl
    from filmgraph.importers.ccsl import ccsl_to_filmgraph

    out = tmp_path / "ccsl.docx"
    filmgraph_to_ccsl(fg, str(out))
    assert out.exists()

    restored = ccsl_to_filmgraph(str(out))
    # We should recover all 3 shots
    total_shots = sum(s.shot_count for s in restored.scenes)
    assert total_shots == 3
    # First shot should have a recognisable WS size
    assert restored.scenes[0].shots[0].cinematography.shot_size == ShotSize.WS


# ─── Dialogbuch docx ──────────────────────────────────────────────────────

def test_dialogbuch_docx_roundtrip(fg: FilmGraph, tmp_path):
    pytest.importorskip("docx")
    from filmgraph.exporters.dialogbuch import filmgraph_to_dialogbuch
    from filmgraph.importers.dialogbuch import dialogbuch_to_filmgraph

    out = tmp_path / "db.docx"
    filmgraph_to_dialogbuch(fg, str(out))
    assert out.exists()

    restored = dialogbuch_to_filmgraph(str(out))
    total_lines = sum(
        len(sh.audio.dialogue) for sc in restored.scenes for sh in sc.shots
    )
    assert total_lines == 2

    speakers = {
        dl.speaker
        for sc in restored.scenes
        for sh in sc.shots
        for dl in sh.audio.dialogue
    }
    assert speakers == {"alice", "bob"}


# ─── AD script docx ──────────────────────────────────────────────────────

def test_ad_script_docx_roundtrip(fg: FilmGraph, tmp_path):
    pytest.importorskip("docx")
    from filmgraph.exporters.ad_script import filmgraph_to_ad
    from filmgraph.importers.ad_script import ad_to_filmgraph

    out = tmp_path / "ad.docx"
    filmgraph_to_ad(fg, str(out))
    assert out.exists()

    restored = ad_to_filmgraph(str(out))
    # All three shots have visual descriptions, so all three should survive
    total_shots = sum(s.shot_count for s in restored.scenes)
    assert total_shots == 3
    descriptions = [
        sh.visual.description
        for sc in restored.scenes
        for sh in sc.shots
    ]
    assert any("café" in (d or "").lower() for d in descriptions)


# ─── OTIO (EDL / FCP XML / OTIO native) ──────────────────────────────────

def test_otio_roundtrip_native(fg: FilmGraph, tmp_path):
    pytest.importorskip("opentimelineio")
    from filmgraph.exporters.otio_export import filmgraph_to_otio
    from filmgraph.importers.otio_import import otio_to_filmgraph

    out = tmp_path / "timeline.otio"
    filmgraph_to_otio(fg, str(out))
    assert out.exists()

    restored = otio_to_filmgraph(str(out))
    total_shots = sum(s.shot_count for s in restored.scenes)
    assert total_shots == 3


def test_otio_export_edl(fg: FilmGraph, tmp_path):
    otio = pytest.importorskip("opentimelineio")
    if "cmx_3600" not in otio.adapters.available_adapter_names():
        pytest.skip("OTIO cmx_3600 adapter plugin not installed")
    from filmgraph.exporters.otio_export import filmgraph_to_otio

    out = tmp_path / "edit.edl"
    filmgraph_to_otio(fg, str(out))
    assert out.exists()
    content = out.read_text()
    assert content.strip()


# ─── CSV ──────────────────────────────────────────────────────────────────

def test_csv_export(fg: FilmGraph):
    from filmgraph.exporters.csv_export import filmgraph_to_csv

    text = filmgraph_to_csv(fg)
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0]["shot_id"] == "sh-001"
    assert rows[0]["shot_size"] == "WS"
    assert rows[0]["description"] == "Wide shot of the café"
    assert "Alice: Hello, Bob." in rows[0]["dialogue"]
    assert "Alice" in rows[0]["characters"]


# ─── Markdown ────────────────────────────────────────────────────────────

def test_markdown_export(fg: FilmGraph):
    from filmgraph.exporters.markdown import filmgraph_to_markdown

    md = filmgraph_to_markdown(fg)
    assert md.startswith("# Test Film")
    assert "## Characters" in md
    assert "**Alice**" in md
    assert "### Scene 1: Opening" in md
    assert "Wide shot of the café" in md
    assert "Hello, Bob." in md
