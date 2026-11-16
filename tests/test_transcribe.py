"""Tests for prufrock.transcribe. The model call is replaced; page images and
their text are synthetic placeholders generated here."""

import pytest

from prufrock import transcribe


def _pages(tmp_path, n):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(n):
        (src / f"page-{i:02d}.jpg").write_bytes(b"synthetic")
    (src / "notes.txt").write_text("not an image")
    return src


def test_safe_name_quotes_and_strips_control_characters(tmp_path):
    p = tmp_path / "bad\x07name.jpg"
    assert transcribe.safe_name(p) == '"bad?name.jpg"'


def test_safe_name_caps_length(tmp_path):
    p = tmp_path / ("x" * 200)
    assert transcribe.safe_name(p) == '"' + "x" * 120 + '"'


def test_transcribe_batch_adds_context_and_labels(monkeypatch, tmp_path):
    seen = {}

    def fake_complete(system, user, images, level, timeout_s):
        seen.update(
            system=system, user=user, images=images, level=level, timeout_s=timeout_s
        )
        return "reply"

    monkeypatch.setattr(transcribe, "complete", fake_complete)
    img = tmp_path / "p.jpg"
    assert transcribe.transcribe_batch([img], "Synthetic context") == "reply"
    assert seen["system"].endswith(
        "Additional context from the client:\nSynthetic context"
    )
    assert 'Page file: "p.jpg"' in seen["user"]
    assert seen["images"] == [img]
    assert seen["level"] == "standard"
    assert seen["timeout_s"] == 600


def test_transcribe_batch_without_context(monkeypatch, tmp_path):
    monkeypatch.setattr(transcribe, "complete", lambda system, user, **k: system)
    assert (
        transcribe.transcribe_batch([tmp_path / "p.jpg"], None)
        == transcribe.SYSTEM_PROMPT
    )


def test_no_images_returns_quietly(tmp_path):
    src = tmp_path / "empty"
    src.mkdir()
    out = tmp_path / "out"
    transcribe.run_transcribe(src, out, 10, None)
    assert out.is_dir()
    assert list(out.iterdir()) == []


def test_all_batches_succeed(monkeypatch, tmp_path):
    src = _pages(tmp_path, 3)
    ctx_file = tmp_path / "context.txt"
    ctx_file.write_text("Synthetic context from a file")
    out = tmp_path / "out"
    out.mkdir()
    (out / "FAILED-batches.md").write_text("stale")
    contexts = []

    def fake_batch(batch, context):
        contexts.append(context)
        return "Transcribed: " + ",".join(p.name for p in batch)

    monkeypatch.setattr(transcribe, "transcribe_batch", fake_batch)
    transcribe.run_transcribe(src, out, 2, str(ctx_file))

    assert contexts == ["Synthetic context from a file"] * 2
    assert (out / "batch-001.md").read_text().startswith("# Transcription Batch 1\n")
    assert "page-02.jpg" in (out / "batch-002.md").read_text()
    merged = (out / "all-transcriptions.md").read_text()
    assert merged.split("\n\n---\n\n") == [
        "Transcribed: page-00.jpg,page-01.jpg",
        "Transcribed: page-02.jpg",
    ]
    assert not (out / "FAILED-batches.md").exists()


def test_failed_batch_is_listed_kept_out_and_exits_1(monkeypatch, tmp_path):
    src = _pages(tmp_path, 2)
    out = tmp_path / "out"
    out.mkdir()
    (out / "all-transcriptions.md").write_text("stale")

    def fake_batch(batch, context):
        if batch[0].name == "page-01.jpg":
            raise RuntimeError("synthetic failure")
        return "ok text"

    monkeypatch.setattr(transcribe, "transcribe_batch", fake_batch)
    with pytest.raises(SystemExit) as exc:
        transcribe.run_transcribe(src, out, 1, "inline context")
    assert exc.value.code == 1
    assert (out / "all-transcriptions.md").read_text() == "ok text"
    report = (out / "FAILED-batches.md").read_text()
    assert "## Batch 2" in report
    assert "Files: page-01.jpg" in report
    assert "Error: synthetic failure" in report


def test_every_batch_failing_writes_no_merged_file(monkeypatch, tmp_path):
    src = _pages(tmp_path, 1)
    out = tmp_path / "out"
    out.mkdir()
    (out / "all-transcriptions.md").write_text("stale")

    def fake_batch(batch, context):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(transcribe, "transcribe_batch", fake_batch)
    with pytest.raises(SystemExit):
        transcribe.run_transcribe(src, out, 5, None)
    assert not (out / "all-transcriptions.md").exists()
    assert (out / "FAILED-batches.md").exists()
