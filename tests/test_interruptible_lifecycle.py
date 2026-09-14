from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from guardian_demo.engine import GuardianDemoEngine
from guardian_demo.physical_io import ENV_VAR as PHYSICAL_IO_ENV
from guardian_demo.server import ENGINE, build_server


class _PhysicalContractHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.server.calls.append((self.path, payload))  # type: ignore[attr-defined]
        identity = {
            key: payload[key]
            for key in ("action_id", "idempotency_key", "action_type", "target_id")
        }
        if self.path == "/v1/action":
            response = {**identity, "ok": True, "accepted": True}
        elif self.path == "/v1/verify":
            response = {
                **identity,
                "ok": True,
                "verified": True,
                "truth": "PRODUCT_HTTP_READBACK",
            }
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = json.dumps(response).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _request(base: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        base + path,
        data=data,
        method="POST" if data is not None else "GET",
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=3) as response:  # nosec B310 - ephemeral loopback test only
        return json.loads(response.read().decode("utf-8"))


def test_interrupt_requires_reverification_before_resume(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PHYSICAL_IO_ENV, raising=False)
    engine = GuardianDemoEngine()
    engine.run("loitering_after_hours")
    engine.approve()

    interrupted = engine.interrupt()
    trace = interrupted["current"]
    assert trace["status"] == "SAFE_STATE_VERIFIED"
    assert trace["safe_state_verified"] is True
    assert trace["reverified"] is False
    assert interrupted["latest_evidence"]["final"] is False

    with pytest.raises(RuntimeError, match="re-verified"):
        engine.resume()

    reverified = engine.reverify()
    assert reverified["current"]["status"] == "REVERIFIED"
    assert reverified["current"]["reverified"] is True

    resumed = engine.resume()
    assert resumed["current"]["status"] == "RESUMED_VERIFIED"
    assert resumed["current"]["verified"] is True
    assert resumed["current"]["resume_count"] == 1
    assert resumed["latest_evidence"]["final"] is True

    states = [event["state"] for event in resumed["current"]["lifecycle_events"]]
    assert states == [
        "PROPOSED",
        "AUTHORIZED",
        "EXECUTING",
        "EXECUTION_VERIFIED",
        "INTERRUPTED",
        "SAFE_STATE_VERIFIED",
        "REVERIFIED",
        "RESUMING",
        "RESUMED_VERIFIED",
    ]


def test_interrupted_action_can_be_cancelled_in_verified_safe_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PHYSICAL_IO_ENV, raising=False)
    engine = GuardianDemoEngine()
    engine.run("restricted_zone_entry")
    engine.approve()
    engine.interrupt()

    cancelled = engine.cancel()
    assert cancelled["current"]["status"] == "CANCELLED_SAFE"
    assert cancelled["current"]["safe_state_verified"] is True
    assert cancelled["latest_evidence"]["final"] is True
    assert cancelled["current"]["lifecycle_events"][-1]["state"] == "CANCELLED_SAFE"

    with pytest.raises(RuntimeError, match="resume denied"):
        engine.resume()


def test_real_bridge_interrupt_reverify_resume_uses_distinct_identities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _PhysicalContractHandler)
    server.calls = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    monkeypatch.setenv(PHYSICAL_IO_ENV, f"http://{host}:{port}")

    try:
        engine = GuardianDemoEngine()
        engine.run("loitering_after_hours")
        engine.approve()
        engine.interrupt()
        engine.reverify()
        state = engine.resume()

        assert state["current"]["status"] == "RESUMED_VERIFIED"
        assert state["current"]["truth"]["physical_io"] == "PRODUCT_HTTP_READBACK"
        calls = server.calls  # type: ignore[attr-defined]
        assert [path for path, _ in calls] == [
            "/v1/action",
            "/v1/verify",
            "/v1/action",
            "/v1/verify",
            "/v1/verify",
            "/v1/action",
            "/v1/verify",
        ]
        initial_id = calls[0][1]["action_id"]
        safe_id = calls[2][1]["action_id"]
        reverify_id = calls[4][1]["action_id"]
        resume_id = calls[5][1]["action_id"]
        assert safe_id == f"{initial_id}-safe-0"
        assert reverify_id == safe_id
        assert resume_id == f"{initial_id}-resume-1"
        assert calls[2][1]["parameters"] == {"state": "off"}
        assert calls[5][1]["parameters"] == {"state": "on"}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_lifecycle_routes_fail_closed_until_reverification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PHYSICAL_IO_ENV, raising=False)
    ENGINE.reset()
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"

    try:
        _request(
            base,
            "/api/demo/run",
            {"scenario": "loitering_after_hours", "runtime_id": "local-deterministic"},
        )
        _request(base, "/api/action/approve", {})
        interrupted = _request(base, "/api/action/interrupt", {})
        assert interrupted["current"]["status"] == "SAFE_STATE_VERIFIED"

        with pytest.raises(HTTPError) as exc_info:
            _request(base, "/api/action/resume", {})
        assert exc_info.value.code == HTTPStatus.BAD_REQUEST

        reverified = _request(base, "/api/action/reverify", {})
        assert reverified["current"]["status"] == "REVERIFIED"
        resumed = _request(base, "/api/action/resume", {})
        assert resumed["current"]["status"] == "RESUMED_VERIFIED"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        ENGINE.reset()
