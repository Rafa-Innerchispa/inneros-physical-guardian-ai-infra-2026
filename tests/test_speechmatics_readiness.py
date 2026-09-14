from __future__ import annotations

import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from guardian_demo.server import ENGINE, build_server


REPO_ROOT = Path(__file__).resolve().parents[1]


def _voice_request(base: str, transcript: str, headers: dict[str, str] | None = None) -> dict:
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    request = Request(
        base + "/api/voice/intent",
        data=json.dumps({"transcript": transcript, "provider": "speechmatics"}).encode("utf-8"),
        method="POST",
        headers=request_headers,
    )
    with urlopen(request, timeout=3) as response:  # nosec B310 - ephemeral loopback test only
        return json.loads(response.read().decode("utf-8"))


def test_live_truth_requires_bridge_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GUARDIAN_VOICE_BRIDGE_TOKEN", "ephemeral-test-token")
    ENGINE.reset()
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"

    try:
        manual = _voice_request(base, "show camera 2")
        assert manual["truth"] == "CLIENT_REPORTED_TRANSCRIPT"

        live = _voice_request(
            base,
            "show camera 2",
            {"X-Guardian-Voice-Bridge": "ephemeral-test-token"},
        )
        assert live["truth"] == "SPEECHMATICS_LIVE_TRANSCRIPT"

        forged = _voice_request(
            base,
            "show camera 2",
            {"X-Guardian-Voice-Bridge": "wrong-token"},
        )
        assert forged["truth"] == "CLIENT_REPORTED_TRANSCRIPT"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        ENGINE.reset()


def test_judge_ui_loads_bounded_speechmatics_panel() -> None:
    index = (REPO_ROOT / "app" / "index.html").read_text(encoding="utf-8")
    voice_js = (REPO_ROOT / "app" / "voice.js").read_text(encoding="utf-8")

    assert '<script src="/voice.js" defer></script>' in index
    assert "SPEECHMATICS BONUS" in voice_js
    assert "Voice can never approve" in voice_js
    assert "/api/voice/status" in voice_js
    assert "/api/voice/intent" in voice_js
    assert "CLIENT_REPORTED_TRANSCRIPT" not in voice_js or "not proof" in voice_js.lower()


def test_live_script_never_hardcodes_api_key() -> None:
    script = (REPO_ROOT / "scripts" / "speechmatics_voice_live.py").read_text(encoding="utf-8")
    assert "SPEECHMATICS_API_KEY" in script
    assert "owner_vault:speechmatics/api_key" not in script
    assert "api_key = os.environ.get" in script
    assert "raw audio" in script.lower()
