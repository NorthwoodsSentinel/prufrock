"""LLM backend for Prufrock.

Default backend is the PAI fleet: requests go through fleet_bridge.ts to PAI's
Inference.ts, which runs on the Claude subscription, not an API key.

PRUFROCK_BACKEND=api switches to the Anthropic API directly (needs
ANTHROPIC_API_KEY and the `anthropic` package). That path is for people who
run Prufrock without a PAI install; it is never used unless asked for.
"""

import base64
import json
import os
import shutil
import subprocess
from pathlib import Path

BRIDGE = Path(__file__).with_name("fleet_bridge.ts")
API_MODEL = "claude-sonnet-4-6"

MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class LLMError(RuntimeError):
    pass


def backend() -> str:
    return os.environ.get("PRUFROCK_BACKEND", "fleet").strip().lower()


def complete(
    system: str,
    user: str,
    images: list[Path] | None = None,
    level: str = "standard",
    timeout_s: int = 300,
    max_tokens: int = 8192,
) -> str:
    """Return the model's text reply. Raises LLMError on failure."""
    images = [Path(p).resolve() for p in (images or [])]
    b = backend()
    if b == "fleet":
        return _fleet(system, user, images, level, timeout_s)
    if b == "api":
        return _api(system, user, images, max_tokens)
    raise LLMError(f"unknown PRUFROCK_BACKEND: {b!r} (use 'fleet' or 'api')")


def _fleet(
    system: str, user: str, images: list[Path], level: str, timeout_s: int
) -> str:
    bun = shutil.which("bun")
    if not bun:
        raise LLMError(
            "bun not found on PATH; the fleet backend needs it (or set PRUFROCK_BACKEND=api)"
        )
    req = {
        "system": system,
        "user": user,
        "images": [str(p) for p in images],
        "level": level,
        "timeoutMs": timeout_s * 1000,
    }
    try:
        proc = subprocess.run(
            [bun, str(BRIDGE)],
            input=json.dumps(req),
            capture_output=True,
            text=True,
            timeout=timeout_s + 30,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise LLMError(f"fleet bridge timed out after {timeout_s + 30}s")
    try:
        reply = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        raise LLMError(
            f"fleet bridge returned non-JSON (exit {proc.returncode}): {proc.stdout[:200]} {proc.stderr[:200]}"
        )
    if not reply.get("ok"):
        raise LLMError(
            f"fleet inference failed: {reply.get('error') or proc.stderr[:300]}"
        )
    text = reply.get("text") or ""
    if not text.strip():
        raise LLMError("fleet inference returned empty text")
    return text


def _api(system: str, user: str, images: list[Path], max_tokens: int) -> str:
    try:
        from anthropic import Anthropic
    except ImportError:
        raise LLMError(
            "PRUFROCK_BACKEND=api needs the anthropic package: pip install anthropic"
        )
    content = []
    for p in images:
        data = base64.standard_b64encode(p.read_bytes()).decode("utf-8")
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": MEDIA_TYPES.get(p.suffix.lower(), "image/jpeg"),
                    "data": data,
                },
            }
        )
    content.append({"type": "text", "text": user})
    resp = Anthropic().messages.create(
        model=API_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    text = resp.content[0].text if resp.content else ""  # pyright: ignore[reportAttributeAccessIssue]  # a text reply is asked for; any other block still raises, as before
    if not text.strip():
        raise LLMError("API returned empty text")
    return text
