"""Tests for prufrock.llm: the fleet backend (default) and the opt-in API backend.

Nothing here reaches a model. The fleet bridge subprocess and the anthropic
package are replaced with fakes, so each test pins one branch of the
fail-loudly behaviour that commit c70792d introduced. All text is synthetic.
"""

import json
import subprocess
import sys
import types
from pathlib import Path

import pytest

from prufrock import llm


class FakeProc:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


@pytest.fixture
def bun(monkeypatch):
    monkeypatch.setattr(llm.shutil, "which", lambda name: "/fake/bin/bun")


def test_backend_defaults_to_fleet(monkeypatch):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    assert llm.backend() == "fleet"


def test_backend_is_normalised(monkeypatch):
    monkeypatch.setenv("PRUFROCK_BACKEND", "  API ")
    assert llm.backend() == "api"


def test_unknown_backend_raises(monkeypatch):
    monkeypatch.setenv("PRUFROCK_BACKEND", "other")
    with pytest.raises(llm.LLMError, match="unknown PRUFROCK_BACKEND"):
        llm.complete("sys", "user")


def test_fleet_needs_bun(monkeypatch):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    monkeypatch.setattr(llm.shutil, "which", lambda name: None)
    with pytest.raises(llm.LLMError, match="bun not found"):
        llm.complete("sys", "user")


def test_fleet_sends_one_request_and_returns_text(monkeypatch, bun, tmp_path):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    image = tmp_path / "page.png"
    image.write_bytes(b"synthetic")
    seen = {}

    def fake_run(argv, input, capture_output, text, timeout, check):
        seen["argv"] = argv
        assert check is False
        seen["req"] = json.loads(input)
        seen["timeout"] = timeout
        return FakeProc(stdout=json.dumps({"ok": True, "text": "synthetic reply"}))

    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    out = llm.complete("sys", "user", images=[image], level="fast", timeout_s=10)
    assert out == "synthetic reply"
    assert seen["argv"] == ["/fake/bin/bun", str(llm.BRIDGE)]
    assert seen["req"] == {
        "system": "sys",
        "user": "user",
        "images": [str(image.resolve())],
        "level": "fast",
        "timeoutMs": 10_000,
    }
    assert seen["timeout"] == 40


def test_fleet_timeout_raises(monkeypatch, bun):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="bun", timeout=1)

    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    with pytest.raises(llm.LLMError, match="timed out after 31s"):
        llm.complete("sys", "user", timeout_s=1)


def test_fleet_non_json_raises(monkeypatch, bun):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    monkeypatch.setattr(
        llm.subprocess, "run", lambda *a, **k: FakeProc(stdout="not json", returncode=1)
    )
    with pytest.raises(llm.LLMError, match="non-JSON"):
        llm.complete("sys", "user")


def test_fleet_empty_stdout_is_a_failure(monkeypatch, bun):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    monkeypatch.setattr(
        llm.subprocess, "run", lambda *a, **k: FakeProc(stdout="", stderr="boom")
    )
    with pytest.raises(llm.LLMError, match="fleet inference failed: boom"):
        llm.complete("sys", "user")


def test_fleet_reported_error_raises(monkeypatch, bun):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    monkeypatch.setattr(
        llm.subprocess,
        "run",
        lambda *a, **k: FakeProc(stdout=json.dumps({"ok": False, "error": "no route"})),
    )
    with pytest.raises(llm.LLMError, match="no route"):
        llm.complete("sys", "user")


def test_fleet_empty_text_raises(monkeypatch, bun):
    monkeypatch.delenv("PRUFROCK_BACKEND", raising=False)
    monkeypatch.setattr(
        llm.subprocess,
        "run",
        lambda *a, **k: FakeProc(stdout=json.dumps({"ok": True, "text": "   "})),
    )
    with pytest.raises(llm.LLMError, match="empty text"):
        llm.complete("sys", "user")


def _fake_anthropic(monkeypatch, content, seen):
    class Messages:
        def create(self, **kwargs):
            seen.update(kwargs)
            return types.SimpleNamespace(content=content)

    class Anthropic:
        def __init__(self):
            self.messages = Messages()

    module = types.ModuleType("anthropic")
    module.Anthropic = Anthropic  # type: ignore[attr-defined]  # a stand-in module built at runtime
    monkeypatch.setitem(sys.modules, "anthropic", module)


def test_api_backend_sends_images_and_text(monkeypatch, tmp_path):
    monkeypatch.setenv("PRUFROCK_BACKEND", "api")
    png = tmp_path / "a.png"
    png.write_bytes(b"synthetic-png")
    odd = tmp_path / "b.unknown"
    odd.write_bytes(b"synthetic-other")
    seen = {}
    _fake_anthropic(monkeypatch, [types.SimpleNamespace(text="api reply")], seen)
    out = llm.complete("sys", "user", images=[png, odd], max_tokens=7)
    assert out == "api reply"
    assert seen["model"] == llm.API_MODEL
    assert seen["max_tokens"] == 7
    assert seen["system"] == "sys"
    content = seen["messages"][0]["content"]
    assert [c["type"] for c in content] == ["image", "image", "text"]
    assert content[0]["source"]["media_type"] == "image/png"
    assert content[1]["source"]["media_type"] == "image/jpeg"
    assert content[2]["text"] == "user"


def test_api_backend_empty_reply_raises(monkeypatch):
    monkeypatch.setenv("PRUFROCK_BACKEND", "api")
    _fake_anthropic(monkeypatch, [], {})
    with pytest.raises(llm.LLMError, match="API returned empty text"):
        llm.complete("sys", "user")


def test_api_backend_needs_anthropic(monkeypatch):
    monkeypatch.setenv("PRUFROCK_BACKEND", "api")
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(llm.LLMError, match="needs the anthropic package"):
        llm.complete("sys", "user")


def test_bridge_path_is_beside_the_module():
    assert llm.BRIDGE == Path(llm.__file__).with_name("fleet_bridge.ts")
    assert llm.BRIDGE.is_file()
