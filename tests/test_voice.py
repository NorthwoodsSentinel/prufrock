"""Tests for prufrock.voice. Whisper and the model call are replaced; every
transcript is synthetic placeholder text written here."""

import json
import subprocess

import pytest

from prufrock import voice

TRANSCRIPT = "Synthetic speaker sentence about gardens. Another synthetic sentence! Gardens again?"


class FakeProc:
    def __init__(self, stderr=""):
        self.stderr = stderr


def test_transcribe_audio_renames_whisper_output(monkeypatch, tmp_path):
    audio = tmp_path / "talk.mp3"
    audio.write_bytes(b"synthetic")
    seen = {}

    def fake_run(argv, capture_output, text, timeout, check):
        seen["argv"] = argv
        assert check is False
        (tmp_path / "talk.txt").write_text(TRANSCRIPT)
        return FakeProc()

    monkeypatch.setattr(subprocess, "run", fake_run)
    path = voice.transcribe_audio(audio, tmp_path)
    assert path == tmp_path / "zoom-transcript.txt"
    assert path is not None
    assert path.read_text() == TRANSCRIPT
    assert seen["argv"][0] == "whisper"


def test_transcribe_audio_missing_output(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: FakeProc(stderr="synthetic"))
    assert voice.transcribe_audio(tmp_path / "talk.mp3", tmp_path) is None


def test_transcribe_audio_without_whisper(monkeypatch, tmp_path):
    def missing(*a, **k):
        raise FileNotFoundError("whisper")

    monkeypatch.setattr(subprocess, "run", missing)
    assert voice.transcribe_audio(tmp_path / "talk.mp3", tmp_path) is None


def test_transcribe_audio_other_failure(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(subprocess, "run", boom)
    assert voice.transcribe_audio(tmp_path / "talk.mp3", tmp_path) is None


def test_analyze_voice_parses_json_and_truncates(monkeypatch):
    seen = {}

    def fake_complete(system, user, level, timeout_s, max_tokens):
        seen["user"] = user
        return 'Here it is: {"vocabulary_patterns": ["synthetic"]} done'

    monkeypatch.setattr(voice, "complete", fake_complete)
    result = voice.analyze_voice("w" * 90_000, "Speaker")
    assert result == {"vocabulary_patterns": ["synthetic"]}
    assert "\n\n[...]\n\n" in seen["user"]


def test_analyze_voice_without_json_keeps_raw_text(monkeypatch):
    monkeypatch.setattr(voice, "complete", lambda *a, **k: "plain synthetic analysis")
    assert voice.analyze_voice(TRANSCRIPT, "Speaker") == {
        "raw_analysis": "plain synthetic analysis"
    }


def test_analyze_voice_failure_returns_none(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("synthetic")

    monkeypatch.setattr(voice, "complete", boom)
    assert voice.analyze_voice(TRANSCRIPT, "Speaker") is None


def test_run_voice_from_text_file(monkeypatch, tmp_path):
    src = tmp_path / "talk.md"
    src.write_text(TRANSCRIPT)
    out = tmp_path / "out"
    monkeypatch.setattr(voice, "analyze_voice", lambda t, c: {"raw_analysis": "x"})
    voice.run_voice(src, out, "Speaker")
    profile = json.loads((out / "voice-profile.json").read_text())
    assert profile["raw_analysis"] == "x"
    stats = profile["statistics"]
    assert stats["total_words"] == len(TRANSCRIPT.split())
    assert ["gardens", 2] in stats["top_distinctive_words"]


def test_run_voice_from_audio(monkeypatch, tmp_path):
    src = tmp_path / "talk.wav"
    src.write_bytes(b"synthetic")
    out = tmp_path / "out"

    def fake_transcribe(audio, output_dir):
        p = output_dir / "zoom-transcript.txt"
        p.write_text(TRANSCRIPT)
        return p

    monkeypatch.setattr(voice, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(voice, "analyze_voice", lambda t, c: {"k": "v"})
    voice.run_voice(src, out, "Speaker")
    assert json.loads((out / "voice-profile.json").read_text())["k"] == "v"


def test_run_voice_audio_transcription_failed(monkeypatch, tmp_path):
    src = tmp_path / "talk.wav"
    src.write_bytes(b"synthetic")
    out = tmp_path / "out"
    monkeypatch.setattr(voice, "transcribe_audio", lambda a, o: None)
    voice.run_voice(src, out, "Speaker")
    assert not (out / "voice-profile.json").exists()


def test_run_voice_unsupported_file(tmp_path):
    src = tmp_path / "talk.xyz"
    src.write_text("x")
    out = tmp_path / "out"
    voice.run_voice(src, out, "Speaker")
    assert list(out.iterdir()) == []


def test_run_voice_from_directory(monkeypatch, tmp_path):
    src = tmp_path / "dir"
    src.mkdir()
    (src / "a.txt").write_text("First synthetic part.")
    (src / "b.srt").write_text("Second synthetic part.")
    (src / "c.bin").write_bytes(b"ignored")
    seen = {}

    def fake_analyze(t, c):
        seen["t"] = t
        return {"k": "v"}

    monkeypatch.setattr(voice, "analyze_voice", fake_analyze)
    voice.run_voice(src, tmp_path / "out", "Speaker")
    assert seen["t"] == "First synthetic part.\n\n---\n\nSecond synthetic part."


def test_run_voice_empty_directory(tmp_path):
    src = tmp_path / "dir"
    src.mkdir()
    out = tmp_path / "out"
    voice.run_voice(src, out, "Speaker")
    assert list(out.iterdir()) == []


def test_run_voice_missing_source(tmp_path):
    out = tmp_path / "out"
    voice.run_voice(tmp_path / "absent", out, "Speaker")
    assert list(out.iterdir()) == []


def test_run_voice_analysis_failure_writes_stats_only_and_exits_1(
    monkeypatch, tmp_path
):
    src = tmp_path / "talk.txt"
    src.write_text("")
    out = tmp_path / "out"
    out.mkdir()
    (out / "voice-profile.json").write_text("{}")
    monkeypatch.setattr(voice, "analyze_voice", lambda t, c: None)
    with pytest.raises(SystemExit) as exc:
        voice.run_voice(src, out, "Speaker")
    assert exc.value.code == 1
    assert not (out / "voice-profile.json").exists()
    stats = json.loads((out / "voice-stats.json").read_text())["statistics"]
    assert stats["avg_sentence_length"] == 0
