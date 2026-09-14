from __future__ import annotations

import json
import threading
from http import HTTPStatus
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from guardian_demo.engine import GuardianDemoEngine
from guardian_demo.server import ENGINE, build_server
from guardian_demo.voice import GuardianVoiceRouter, classify_voice_intent, speechmatics_status


def _post(base: str, path: str, payload: dict) -> dict:
    request = Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=3) as response:  # nosec B310 - ephemeral loopback test only
        return json.loads(response.read().decode("utf-8"))


def test_voice_intents_are_bounded_and_approval_is_never_allowed() -> None:
    assert classify_voice_intent("interrupt the action")["intent"] == "interrupt_action"
    assert classify_voice_intent("re-verify safe state")["intent"] == "reverify_safe_state"
    assert classify_voice_intent("resume the action")["intent"] == "resume_action"
    assert classify_voice_intent("cancel action")["intent"] == "cancel_action"
    assert classify_voice_intent("show camera 3") == {
        "intent": "show_camera",
        "allowed": True,
        "camera": 3,
    }

    for transcript in (
        "approve the action",
        "authorize and resume",
        "execute it now",
        "unlock the door",
        "disable the alarm",
    ):
        result = classify_voice_intent(transcript)
        assert result["allowed"] is False
        assert result["intent"] == "denied_voice_action"


def test_voice_status_never_returns_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "speechmatics-secret-must-not-leak"
    monkeypatch.setenv("SPEECHMATICS_API_KEY", secret)
    status = speechmatics_status()
    serialized = json.dumps(status)
    assert status["credential_configured"] is True
    assert status["voice_can_approve"] is False
    assert secret not in serialized


def test_voice_resume_remains_locked_until_reverification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GUARDIAN_PHYSICAL_IO_URL", raising=False)
    engine = GuardianDemoEngine()
    voice = GuardianVoiceRouter(engine)
    engine.run("loitering_after_hours")
    engine.approve()

    interrupted = voice.route("interrupt the action")
    assert interrupted["state"]["current"]["status"] == "SAFE_STATE_VERIFIED"
    assert interrupted["transcript_persisted"] is False
    assert interrupted["raw_audio_persisted"] is False

    with pytest.raises(RuntimeError, match="re-verified"):
        voice.route("resume the action")

    reverified = voice.route("re-verify safe state")
    assert reverified["state"]["current"]["status"] == "REVERIFIED"
    resumed = voice.route("resume the action")
    assert resumed["state"]["current"]["status"] == "RESUMED_VERIFIED"


def test_voice_denied_action_fails_closed_without_changing_guardian_state() -> None:
    engine = GuardianDemoEngine()
    voice = GuardianVoiceRouter(engine)
    before = engine.state()
    result = voice.route("approve and execute the action")
    assert result["ok"] is False
    assert result["fail_closed"] is True
    assert result["voice_can_approve"] is False
    assert result["state"] == before


def test_http_voice_route_is_client_reported_and_cannot_approve(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GUARDIAN_PHYSICAL_IO_URL", raising=False)
    ENGINE.reset()
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"

    try:
        result = _post(
            base,
            "/api/voice/intent",
            {"transcript": "approve the action", "provider": "speechmatics"},
        )
        assert result["allowed"] is False
        assert result["fail_closed"] is True
        assert result["truth"] == "CLIENT_REPORTED_TRANSCRIPT"
        assert result["voice_can_approve"] is False

        status_request = Request(base + "/api/voice/status", method="GET")
        with urlopen(status_request, timeout=3) as response:  # nosec B310 - loopback test only
            assert response.status == HTTPStatus.OK
            status = json.loads(response.read().decode("utf-8"))
        assert status["provider"] == "speechmatics"
        assert status["voice_can_approve"] is False

        _post(
            base,
            "/api/demo/run",
            {"scenario": "loitering_after_hours", "runtime_id": "local-deterministic"},
        )
        with pytest.raises(HTTPError) as exc_info:
            _post(
                base,
                "/api/voice/intent",
                {"transcript": "resume the action", "provider": "speechmatics"},
            )
        assert exc_info.value.code == HTTPStatus.BAD_REQUEST
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        ENGINE.reset()
