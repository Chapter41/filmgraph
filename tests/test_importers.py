"""Test the SRT/VTT importer (no external deps needed)."""

from filmgraph.importers.srt import parse_srt, parse_vtt, srt_to_filmgraph
from filmgraph import ShotSize


_SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:03,500
ALICE: Hello, how are you?

2
00:00:04,000 --> 00:00:06,200
BOB: I'm fine, thanks.

3
00:00:10,500 --> 00:00:12,000
Just a line with no speaker.
"""

_SAMPLE_VTT = """\
WEBVTT

1
00:00:01.000 --> 00:00:03.500
<v Alice>Hello, how are you?</v>

2
00:00:04.000 --> 00:00:06.200
<v Bob>I'm fine, thanks.</v>
"""


def test_parse_srt():
    lines = parse_srt(_SAMPLE_SRT)
    assert len(lines) == 3
    assert lines[0].speaker == "alice"
    assert lines[0].text == "Hello, how are you?"
    assert lines[0].start_time == 1.0
    assert lines[0].end_time == 3.5
    assert lines[1].speaker == "bob"
    assert lines[2].speaker is None


def test_parse_vtt():
    lines = parse_vtt(_SAMPLE_VTT)
    assert len(lines) == 2
    assert lines[0].speaker == "alice"
    assert lines[1].speaker == "bob"
    assert lines[0].text == "Hello, how are you?"


def test_srt_to_filmgraph(tmp_path):
    srt_file = tmp_path / "test.srt"
    srt_file.write_text(_SAMPLE_SRT)
    fg = srt_to_filmgraph(str(srt_file), title="Test", language="en")

    assert fg.meta.title == "Test"
    assert fg.meta.language == "en"
    assert len(fg.scenes) == 1
    assert len(fg.scenes[0].shots) == 3
    assert fg.entities.characters[0].id in ("alice", "bob")
