"""Tests for prufrock.assemble. The model call is replaced, and every input
file is synthetic: placeholder text, placeholder names ("Person A")."""

import json

import pytest

from prufrock import assemble

FILLER = "Synthetic transcription line for testing only. " * 20  # > 500 characters


def _tree(tmp_path, transcription=FILLER):
    src = tmp_path / "src"
    out_dir = src / "prufrock-output"
    (out_dir / "faces").mkdir(parents=True)
    (out_dir / "transcriptions").mkdir()
    (out_dir / "manifest.json").write_text(
        json.dumps({"summary": {"photo": 3, "document": 0}})
    )
    (out_dir / "faces" / "face-clusters.json").write_text(
        json.dumps(
            {
                "clusters": [
                    {"id": 1, "name": "Person A", "face_count": 2},
                    {"id": 2, "name": None, "face_count": 1},
                ]
            }
        )
    )
    (out_dir / "timeline.json").write_text(
        json.dumps([{"date": "1990-01-02"}, {"date": "1995-03-04"}])
    )
    (out_dir / "timeline.md").write_text("# Timeline\nsynthetic")
    if transcription is not None:
        (out_dir / "transcriptions" / "batch-001.md").write_text(transcription)
    return src


def test_load_json_missing_returns_none(tmp_path):
    assert assemble.load_json(tmp_path / "nope.json") is None


def test_analyze_threads_too_little_text():
    assert assemble.analyze_threads("short", "Client") is None
    assert assemble.analyze_threads("", "Client") is None


def test_analyze_threads_truncates_long_text(monkeypatch):
    seen = {}

    def fake_complete(system, user, level, timeout_s, max_tokens):
        seen.update(user=user, level=level, timeout_s=timeout_s, max_tokens=max_tokens)
        return "threads"

    monkeypatch.setattr(assemble, "complete", fake_complete)
    text = "a" * 60_000 + "b" * 60_000
    assert assemble.analyze_threads(text, "Client") == "threads"
    assert "[... middle sections omitted for length ...]" in seen["user"]
    assert seen["user"].startswith("Client: Client\n\n---\n\n" + "a" * 50_000)
    assert seen["user"].endswith("b" * 50_000)
    assert (seen["level"], seen["timeout_s"], seen["max_tokens"]) == (
        "standard",
        300,
        4096,
    )


def test_full_assembly(monkeypatch, tmp_path):
    src = _tree(tmp_path)
    monkeypatch.setattr(
        assemble, "complete", lambda *a, **k: "## Thread one\nsynthetic"
    )
    out = tmp_path / "deliverable"
    assemble.run_assemble(src, out, "Client")

    index = (out / "INDEX.md").read_text()
    assert index.startswith("# Client — Prufrock Archive")
    assert "**Total items processed:** 3" in index
    assert "- Photos: 3" in index
    assert "Documents" not in index
    assert "- **Person A**: 2 appearance(s)" in index
    assert "1 unidentified person(s)" in index
    assert "**Date range:** 1990-01-02 to 1995-03-04" in index
    assert "**Years covered:** 1990, 1995" in index
    assert "## Thread one" in index
    assert (out / "transcriptions.md").read_text().startswith(FILLER)
    assert (out / "timeline.md").read_text() == "# Timeline\nsynthetic"
    assert (
        (out / "memoir-threads.md")
        .read_text()
        .startswith("# Client — Narrative Thread Analysis")
    )


def test_thread_failure_is_marked_and_exits_1(monkeypatch, tmp_path):
    src = _tree(tmp_path)

    def boom(*a, **k):
        raise RuntimeError("synthetic model failure")

    monkeypatch.setattr(assemble, "complete", boom)
    out = tmp_path / "deliverable"
    with pytest.raises(SystemExit) as exc:
        assemble.run_assemble(src, out, "Client")
    assert exc.value.code == 1
    index = (out / "INDEX.md").read_text()
    assert (
        "*Thread analysis FAILED: synthetic model failure. Re-run assemble.*" in index
    )
    assert not (out / "memoir-threads.md").exists()


def test_too_little_text_gets_a_blank_scaffold(monkeypatch, tmp_path):
    src = _tree(tmp_path, transcription="tiny")
    out = tmp_path / "deliverable"
    assemble.run_assemble(src, out, "Client")
    index = (out / "INDEX.md").read_text()
    assert "Too little transcribed text" in index
    assert "### Suggested Threads" in index


def test_empty_source_lists_every_missing_step(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "deliverable"
    assemble.run_assemble(src, out, "Client")
    index = (out / "INDEX.md").read_text()
    assert "No transcriptions found" in index
    assert "No face clustering found" in index
    assert "No timeline found" in index
    assert "No transcriptions available for thread analysis" in index


def test_clusters_found_by_search_and_no_timeline_markdown(monkeypatch, tmp_path):
    src = tmp_path / "src"
    other = src / "prufrock-output" / "elsewhere"
    other.mkdir(parents=True)
    (other / "face-clusters.json").write_text(
        json.dumps({"clusters": [{"id": 1, "name": None, "face_count": 1}]})
    )
    (src / "prufrock-output" / "timeline.json").write_text(
        json.dumps([{"date": "2001-01-01"}])
    )
    out = tmp_path / "deliverable"
    assemble.run_assemble(src, out, "Client")
    index = (out / "INDEX.md").read_text()
    assert "1 unidentified person(s)" in index
    assert "Person A" not in index
    assert "**Total events:** 1" in index
    assert not (out / "timeline.md").exists()


def test_named_only_clusters(tmp_path):
    src = tmp_path / "src"
    faces = src / "prufrock-output" / "faces"
    faces.mkdir(parents=True)
    (faces / "face-clusters.json").write_text(
        json.dumps({"clusters": [{"id": 1, "name": "Person B", "face_count": 4}]})
    )
    out = tmp_path / "deliverable"
    assemble.run_assemble(src, out, "Client")
    index = (out / "INDEX.md").read_text()
    assert "- **Person B**: 4 appearance(s)" in index
    assert "unidentified" not in index
