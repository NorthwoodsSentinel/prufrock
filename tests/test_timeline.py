"""Tests for prufrock.timeline. Dates and text are synthetic; the EXIF image
is generated here with a made-up timestamp."""

import json
import sys

from PIL import Image

from prufrock import timeline


def test_parse_year():
    assert timeline.parse_year("96") == 1996
    assert timeline.parse_year("05") == 2005
    assert timeline.parse_year("1950") == 1950
    assert timeline.parse_year("2200") is None


def test_extract_every_format():
    text = (
        "On 3/4/1999 something. Then March 5, 2001 and 2002-06-07 too.\n"
        "Short 1/2/96 here. Bad 13/40/1999 and 1/1/2200 and 1/1/1700."
    )
    dates = {d["date"] for d in timeline.extract_dates_from_text(text)}
    assert dates == {"1999-03-04", "2001-03-05", "2002-06-07", "1996-01-02"}
    one = timeline.extract_dates_from_text("x 2002-06-07 y")[0]
    assert one == {
        "date": "2002-06-07",
        "raw": "2002-06-07",
        "context": "x 2002-06-07 y",
    }


def _exif_jpeg(path, stamp):
    exif = Image.Exif()
    exif[0x0132] = stamp  # Image DateTime
    Image.new("RGB", (4, 4)).save(path, exif=exif)


def test_exif_dates(tmp_path):
    _exif_jpeg(tmp_path / "a.jpg", "2003:04:05 06:07:08")
    _exif_jpeg(tmp_path / "b.jpg", "not a date")
    Image.new("RGB", (4, 4)).save(tmp_path / "c.jpg")
    (tmp_path / "d.png").write_bytes(b"skipped by extension")
    found = timeline.extract_exif_dates(tmp_path)
    assert found == [
        {
            "date": "2003-04-05",
            "raw": "2003:04:05 06:07:08",
            "context": "EXIF from a.jpg",
            "source": "a.jpg",
        }
    ]


def test_exif_without_exifread(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "exifread", None)
    assert timeline.extract_exif_dates(tmp_path) == []


def test_run_timeline(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.md").write_text(
        "Written 2/3/1990 | then 2/3/1990 again later.\nAnd 1985-01-01."
    )
    (src / "b.md").write_text("No dates here.")
    _exif_jpeg(src / "p.jpg", "1970:01:02 00:00:00")
    out = tmp_path / "out" / "timeline.md"
    timeline.run_timeline(src, out)

    lines = out.read_text().splitlines()
    assert lines[0] == "# Timeline"
    assert lines[1] == "## Constructed from 2 transcription(s) and EXIF data"
    rows = [line for line in lines if line.startswith("| 19")]
    assert [r.split(" | ")[0] for r in rows] == [
        "| 1970-01-02",
        "| 1985-01-01",
        "| 1990-02-03",
    ]
    assert "/" in rows[2]
    data = json.loads(out.with_suffix(".json").read_text())
    assert [d["date"] for d in data] == ["1970-01-02", "1985-01-01", "1990-02-03"]


def test_run_timeline_deduplicates(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.md").write_text("Same 2002-06-07 line")
    (src / "b.md").write_text("Same 2002-06-07 line")
    out = tmp_path / "timeline.md"
    timeline.run_timeline(src, out)
    data = json.loads(out.with_suffix(".json").read_text())
    assert len(data) == 1


def test_run_timeline_no_dates(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out" / "timeline.md"
    timeline.run_timeline(src, out)
    assert not out.exists()
