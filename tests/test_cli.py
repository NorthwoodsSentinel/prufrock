"""Tests for prufrock.cli: each command passes its arguments and its default
output path to the stage it runs. The stages are replaced with recorders."""

import pytest
from click.testing import CliRunner

from prufrock import cli


@pytest.fixture
def calls(monkeypatch):
    seen = []
    for name in (
        "run_intake",
        "run_transcribe",
        "run_faces",
        "run_timeline",
        "run_assemble",
        "run_voice",
        "run_companion",
    ):
        monkeypatch.setattr(cli, name, lambda *a, _n=name: seen.append((_n, a)))
    return seen


def invoke(*args):
    result = CliRunner().invoke(cli.cli, [str(a) for a in args])
    assert result.exit_code == 0, result.output
    return result


def test_group_help():
    assert "Your life. Your voice. Your book." in invoke("--help").output


def test_intake_default_and_explicit_output(calls, tmp_path):
    invoke("intake", tmp_path)
    invoke("intake", tmp_path, "-o", tmp_path / "x")
    assert calls == [
        ("run_intake", (tmp_path, tmp_path / "prufrock-output")),
        ("run_intake", (tmp_path, tmp_path / "x")),
    ]


def test_transcribe(calls, tmp_path):
    invoke("transcribe", tmp_path, "--batch-size", 3, "--context", "ctx")
    assert calls == [
        (
            "run_transcribe",
            (tmp_path, tmp_path / "prufrock-output" / "transcriptions", 3, "ctx"),
        )
    ]


def test_faces(calls, tmp_path):
    invoke("faces", tmp_path, "--tolerance", 0.5)
    assert calls == [
        ("run_faces", (tmp_path, tmp_path / "prufrock-output" / "faces", 0.5))
    ]


def test_timeline(calls, tmp_path):
    invoke("timeline", tmp_path)
    assert calls == [
        ("run_timeline", (tmp_path, tmp_path / "prufrock-output" / "timeline.md"))
    ]


def test_assemble(calls, tmp_path):
    invoke("assemble", tmp_path, "--client-name", "Client")
    assert calls == [
        (
            "run_assemble",
            (tmp_path, tmp_path / "prufrock-output" / "deliverable", "Client"),
        )
    ]


def test_voice_from_directory(calls, tmp_path):
    invoke("voice", tmp_path, "--client-name", "Client")
    assert calls == [
        ("run_voice", (tmp_path, tmp_path / "prufrock-output" / "voice", "Client"))
    ]


def test_voice_from_file(calls, tmp_path):
    f = tmp_path / "talk.txt"
    f.write_text("synthetic")
    invoke("voice", f, "--client-name", "Client")
    assert calls == [
        ("run_voice", (f, tmp_path / "talk" / "prufrock-output" / "voice", "Client"))
    ]


def test_companion(calls, tmp_path):
    invoke("companion", tmp_path, "--client-name", "Client")
    assert calls == [
        (
            "run_companion",
            (tmp_path, tmp_path / "prufrock-output" / "companion", "Client"),
        )
    ]
