from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from guardian_demo.models import ProposedAction
from guardian_demo.physical_io import ENV_VAR, PhysicalIOBridge
from guardian_demo.runtime import SponsorRuntimeSlot


def _start_server(handler: type[BaseHTTPRequestHandler]) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def _stop_server(server: ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


class _JsonHandler(BaseHTTPRequestHandler):
    response_payload: dict[str, Any] = {}
    captured_request: dict[str, Any] | None = None

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or "0")
        type(self).captured_request = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        body = json.dumps(type(self).response_payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_sponsor_bridge_rejects_malformed_confidence() -> None:
    _JsonHandler.response_payload = {
        "model": "yolo26m-seg-bf16-b1",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "frame_ref": "camera://judge/frame-001",
        "source_ref": "camera://judge",
        "detections": [
            {"label": "person", "confidence": 1.25, "bbox": [0.1, 0.2, 0.4, 0.8]},
        ],
    }
    server, thread, base = _start_server(_JsonHandler)
    try:
        slot = SponsorRuntimeSlot("sima-slot", "SiMa.ai", "Modalix", "GUARDIAN_SIMA_RUNTIME_URL")
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", base)
            with pytest.raises(RuntimeError, match="confidence|detection|fail"):
                slot.infer(scenario="restricted_zone_entry", frame_ref="camera://judge/frame-001")
    finally:
        _stop_server(server, thread)


def test_sponsor_bridge_rejects_source_frame_mismatch() -> None:
    _JsonHandler.response_payload = {
        "model": "yolo26m-seg-bf16-b1",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "frame_ref": "camera://judge/frame-999",
        "source_ref": "camera://other",
        "detections": [
            {"label": "person", "confidence": 0.91, "bbox": [0.1, 0.2, 0.4, 0.8]},
        ],
    }
    server, thread, base = _start_server(_JsonHandler)
    try:
        slot = SponsorRuntimeSlot("sima-slot", "SiMa.ai", "Modalix", "GUARDIAN_SIMA_RUNTIME_URL")
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", base)
            with pytest.raises(RuntimeError, match="frame|source|mismatch"):
                slot.infer(scenario="restricted_zone_entry", frame_ref="camera://judge/frame-001")
    finally:
        _stop_server(server, thread)


class _PhysicalTruthHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _read(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read()
        identity = {
            key: payload[key]
            for key in ("action_id", "idempotency_key", "action_type", "target_id")
            if key in payload
        }
        if self.path == "/v1/action":
            self._send({**identity, "ok": True, "accepted": True, "truth": "UNKNOWN_PHYSICAL_TRUTH"})
            return
        if self.path == "/v1/verify":
            self._send({**identity, "ok": True, "verified": True, "truth": "UNKNOWN_PHYSICAL_TRUTH"})
            return
        self.send_error(HTTPStatus.NOT_FOUND)


def test_physical_io_unknown_truth_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    server, thread, base = _start_server(_PhysicalTruthHandler)
    try:
        monkeypatch.setenv(ENV_VAR, base)
        bridge = PhysicalIOBridge()
        with pytest.raises(RuntimeError, match="truth|unknown|closed"):
            bridge.execute(
                ProposedAction(
                    action_id="action-unknown-truth",
                    action_type="beacon_warning",
                    target="reference-low-voltage-beacon",
                    reason="unknown physical truth must not normalize to live",
                )
            )
    finally:
        _stop_server(server, thread)
