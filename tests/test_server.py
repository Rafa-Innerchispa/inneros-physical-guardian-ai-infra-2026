from __future__ import annotations

import base64
import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from guardian_demo.server import ENGINE, build_server


def _request(
    base: str,
    path: str,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        base + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urlopen(req, timeout=3) as response:  # nosec B310 - loopback test server only
        return response.status, response.headers.get("Content-Type", ""), response.read().decode("utf-8")


def _start_server() -> tuple[object, threading.Thread, str]:
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def _stop_server(server: object, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
    ENGINE.reset()


def test_local_http_server_serves_health_ui_and_demo_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GUARDIAN_DEMO_USER", raising=False)
    monkeypatch.delenv("GUARDIAN_DEMO_PASSWORD", raising=False)
    ENGINE.reset()
    server, thread, base = _start_server()

    try:
        status, content_type, body = _request(base, "/api/health")
        assert status == 200
        assert "application/json" in content_type
        assert json.loads(body)["ok"] is True

        status, content_type, body = _request(base, "/")
        assert status == 200
        assert "text/html" in content_type
        assert "Physical Guardian" in body
        assert "See. Understand. Decide. Act. Verify. Prove." in body

        status, _, body = _request(
            base,
            "/api/demo/run",
            method="POST",
            payload={"scenario": "loitering_after_hours", "runtime_id": "local-deterministic"},
        )
        assert status == 200
        assert json.loads(body)["current"]["status"] == "AWAITING_APPROVAL"

        status, _, body = _request(base, "/api/action/approve", method="POST", payload={})
        assert status == 200
        approved = json.loads(body)
        assert approved["current"]["status"] == "VERIFIED"
        assert approved["latest_evidence"]["evidence_id"].startswith("ev-")
    finally:
        _stop_server(server, thread)


def test_optional_basic_auth_protects_ui_and_actions_but_not_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GUARDIAN_DEMO_USER", "judge")
    monkeypatch.setenv("GUARDIAN_DEMO_PASSWORD", "temporary-secret")
    server, thread, base = _start_server()
    token = base64.b64encode(b"judge:temporary-secret").decode("ascii")

    try:
        status, _, body = _request(base, "/api/health")
        assert status == 200
        assert json.loads(body)["access_control"] == "enabled"

        with pytest.raises(HTTPError) as unauthorized:
            _request(base, "/")
        assert unauthorized.value.code == 401
        assert unauthorized.value.headers.get("WWW-Authenticate", "").startswith("Basic")

        status, content_type, body = _request(base, "/", headers={"Authorization": f"Basic {token}"})
        assert status == 200
        assert "text/html" in content_type
        assert "Physical Guardian" in body

        with pytest.raises(HTTPError) as blocked_action:
            _request(base, "/api/action/approve", method="POST", payload={})
        assert blocked_action.value.code == 401
    finally:
        _stop_server(server, thread)
