from __future__ import annotations

import base64
import json
import threading
from datetime import datetime, timezone
from http.client import HTTPConnection
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from guardian_demo.frame_input import MAX_JSON_BODY_BYTES
from guardian_demo.server import ENGINE, build_server


PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlBzv8AAAAASUVORK5CYII="


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


def test_frame_route_is_bounded_and_fails_closed_without_modalix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GUARDIAN_SIMA_RUNTIME_URL", raising=False)
    ENGINE.reset()
    server, thread, base = _start_server()
    payload = {
        "scenario": "restricted_zone_entry",
        "frame_id": "frame-http-001",
        "source_id": "laptop-webcam",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "image_type": "image/png",
        "image_base64": PNG_BASE64,
        "width": 1,
        "height": 1,
    }
    try:
        status, _, body = _request(base, "/api/inference/frame", method="POST", payload=payload)
        assert status == 200
        state = json.loads(body)
        assert state["current"]["status"] == "INFERENCE_BLOCKED"
        assert state["current"]["truth"]["detections"] == "SPONSOR_RUNTIME_UNVERIFIED"
        assert state["current"]["proposed_action"] is None
        assert state["current"]["frame_source"]["sha256"]
    finally:
        _stop_server(server, thread)


def test_frame_route_rejects_non_allowlisted_source_and_oversized_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GUARDIAN_SIMA_RUNTIME_URL", raising=False)
    server, thread, base = _start_server()
    payload = {
        "scenario": "restricted_zone_entry",
        "frame_id": "frame-http-002",
        "source_id": "https://arbitrary.example/camera",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "image_type": "image/png",
        "image_base64": PNG_BASE64,
    }
    try:
        with pytest.raises(HTTPError) as invalid_source:
            _request(base, "/api/inference/frame", method="POST", payload=payload)
        assert invalid_source.value.code == 400

        host, port = server.server_address
        connection = HTTPConnection(host, port, timeout=2)
        connection.putrequest("POST", "/api/inference/frame")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(MAX_JSON_BODY_BYTES + 1))
        connection.endheaders()
        response = connection.getresponse()
        response_body = json.loads(response.read().decode("utf-8"))
        assert response.status == 413
        assert response.getheader("Connection") == "close"
        assert response_body == {"error": "request body too large", "fail_closed": True}
        connection.close()
    finally:
        _stop_server(server, thread)


def test_camera_catalog_exposes_ids_without_urls_or_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "GUARDIAN_CAMERA_SOURCES_JSON",
        json.dumps(
            {
                "home-nvr-2": {
                    "label": "Home camera 2",
                    "snapshot_url": "https://camera-proxy.invalid/snapshot",
                    "token_env": "CAMERA_TEST_TOKEN",
                }
            }
        ),
    )
    monkeypatch.setenv("CAMERA_TEST_TOKEN", "secret-not-for-browser")
    server, thread, base = _start_server()
    try:
        status, _, body = _request(base, "/api/camera/sources")
        assert status == 200
        catalog = json.loads(body)
        serialized = json.dumps(catalog)
        assert "home-nvr-2" in serialized
        assert "camera-proxy.invalid" not in serialized
        assert "secret-not-for-browser" not in serialized
        assert catalog["arbitrary_urls_allowed"] is False
        assert catalog["persistence"] == "NONE"
    finally:
        _stop_server(server, thread)


def test_judge_console_v2_contains_webcam_overlay_truth_and_receipt_contract() -> None:
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    html = (root / "app" / "index.html").read_text(encoding="utf-8")
    js = (root / "app" / "app.js").read_text(encoding="utf-8")

    for marker in (
        'id="cameraVideo"',
        'id="overlayCanvas"',
        'id="sourceSelect"',
        'id="receiptFrame"',
        'id="receiptReadback"',
        "HISTORICAL BENCHMARK",
        "CAMERA PREVIEW ≠ SiMa PROOF",
    ):
        assert marker in html
    assert "navigator.mediaDevices.getUserMedia" in js
    assert "/api/inference/frame" in js
    assert "/api/inference/source" in js
    assert "frameId !== lastSubmittedFrameId" in js
    assert "DENIED — NOTHING EXECUTED" in js
