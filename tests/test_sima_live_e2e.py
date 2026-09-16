from __future__ import annotations

import base64
import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from guardian_demo.engine import GuardianDemoEngine
from guardian_demo.frame_input import FramePayload
from guardian_demo.physical_io import ENV_VAR as PHYSICAL_ENV_VAR
from guardian_demo.sima_adapter import SimaAdapterConfig, SimaLiveAdapter, make_sima_sidecar_handler
from guardian_demo.sima_contract import (
    ATTESTATION_KIND,
    LIVE_EVIDENCE_KIND,
    LIVE_EVIDENCE_SCHEMA,
    TELEMETRY_SOURCE,
    TRUTH_MEASURED,
    sha256_bytes,
    utc_now,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlBzv8AAAAASUVORK5CYII="
)


class PerFrameBackend:
    def infer(self, request_payload: dict) -> dict:
        source_bytes = base64.b64decode(request_payload["image_base64"])
        return {
            "schema": LIVE_EVIDENCE_SCHEMA,
            "evidence_kind": LIVE_EVIDENCE_KIND,
            "truth": TRUTH_MEASURED,
            "measured": True,
            "captured_at": request_payload["captured_at"],
            "inferred_at": utc_now().isoformat(),
            "model": request_payload["requested_model"],
            "runtime": "SiMa MLA 2.1.3",
            "device": "SiMa Modalix DevKit",
            "source": {
                "frame_id": request_payload["frame_id"],
                "source_id": request_payload["source_id"],
                "sha256": sha256_bytes(source_bytes),
                "media_type": request_payload["image_type"],
                "width": request_payload["width"],
                "height": request_payload["height"],
            },
            "detections": [{"label": "person", "confidence": 0.96, "bbox": [0.2, 0.1, 0.7, 0.95]}],
            "telemetry": {"source": TELEMETRY_SOURCE, "latency_ms": 10.0, "fps": 42.0},
            "attestation": {
                "kind": ATTESTATION_KIND,
                "runtime_verified": True,
                "device_verified": True,
                "evidence_id": "modalix-e2e-frame-proof",
            },
        }


class PhysicalIOHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
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


def test_current_frame_to_modalix_to_approval_to_readback_e2e(monkeypatch: pytest.MonkeyPatch) -> None:
    sima_adapter = SimaLiveAdapter(
        SimaAdapterConfig(mode="live"),
        backend=PerFrameBackend(),
    )
    sima_server = ThreadingHTTPServer(("127.0.0.1", 0), make_sima_sidecar_handler(sima_adapter))
    sima_thread = threading.Thread(target=sima_server.serve_forever, daemon=True)
    sima_thread.start()

    io_server = ThreadingHTTPServer(("127.0.0.1", 0), PhysicalIOHandler)
    io_thread = threading.Thread(target=io_server.serve_forever, daemon=True)
    io_thread.start()

    try:
        sima_host, sima_port = sima_server.server_address
        io_host, io_port = io_server.server_address
        monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", f"http://{sima_host}:{sima_port}")
        monkeypatch.setenv(PHYSICAL_ENV_VAR, f"http://{io_host}:{io_port}")
        frame = FramePayload.from_bytes(
            frame_id="frame-e2e-001",
            source_id="laptop-webcam",
            captured_at=utc_now().isoformat(),
            image_type="image/png",
            image_bytes=PNG_BYTES,
        )

        engine = GuardianDemoEngine()
        proposed = engine.run_frame(
            scenario="restricted_zone_entry",
            runtime_id="sima-slot",
            frame=frame,
            source_truth="LAPTOP_WEBCAM_CLIENT_CAPTURE",
        )
        assert proposed["current"]["status"] == "AWAITING_APPROVAL"
        assert proposed["current"]["truth"]["detections"] == TRUTH_MEASURED
        assert proposed["current"]["inference"]["source"]["frame_id"] == frame.frame_id

        approved = engine.approve()
        assert approved["current"]["status"] == "VERIFIED"
        assert approved["current"]["truth"]["physical_io"] == "PRODUCT_HTTP_READBACK"
        assert approved["latest_evidence"]["frame_source"]["sha256"] == frame.sha256
        assert approved["latest_evidence"]["inference"]["attestation"]["evidence_id"] == "modalix-e2e-frame-proof"
    finally:
        sima_server.shutdown()
        sima_server.server_close()
        sima_thread.join(timeout=3)
        io_server.shutdown()
        io_server.server_close()
        io_thread.join(timeout=3)


def test_live_trace_does_not_simulate_physical_verification_when_bridge_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sima_adapter = SimaLiveAdapter(
        SimaAdapterConfig(mode="live"),
        backend=PerFrameBackend(),
    )
    sima_server = ThreadingHTTPServer(("127.0.0.1", 0), make_sima_sidecar_handler(sima_adapter))
    sima_thread = threading.Thread(target=sima_server.serve_forever, daemon=True)
    sima_thread.start()
    try:
        host, port = sima_server.server_address
        monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", f"http://{host}:{port}")
        monkeypatch.delenv(PHYSICAL_ENV_VAR, raising=False)
        frame = FramePayload.from_bytes(
            frame_id="frame-e2e-002",
            source_id="laptop-webcam",
            captured_at=utc_now().isoformat(),
            image_type="image/png",
            image_bytes=PNG_BYTES,
        )
        engine = GuardianDemoEngine()
        engine.run_frame(
            scenario="restricted_zone_entry",
            runtime_id="sima-slot",
            frame=frame,
            source_truth="LAPTOP_WEBCAM_CLIENT_CAPTURE",
        )

        blocked = engine.approve()

        assert blocked["current"]["status"] == "ACTION_FAILED_SAFE"
        assert blocked["current"]["verified"] is False
        assert blocked["current"]["truth"]["physical_io"] == "FAILED_CLOSED"
    finally:
        sima_server.shutdown()
        sima_server.server_close()
        sima_thread.join(timeout=3)
