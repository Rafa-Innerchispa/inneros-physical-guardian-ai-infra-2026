from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from guardian_demo.physical_io import ENV_VAR as PHYSICAL_ENV_VAR
from guardian_demo.rehearsal import run_judge_rehearsal
from guardian_demo.sima_adapter import SimaAdapterConfig, SimaLiveAdapter, make_sima_sidecar_handler

EVIDENCE_FILE = Path(__file__).resolve().parents[1] / "docs" / "sima_measured_evidence.json"


class MockPhysicalIOHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
        identity = {
            key: payload[key]
            for key in ("action_id", "idempotency_key", "action_type", "target_id")
            if key in payload
        }
        if self.path == "/v1/action":
            resp = {**identity, "ok": True, "accepted": True, "truth": "PRODUCT_HTTP_READBACK"}
        elif self.path == "/v1/verify":
            resp = {**identity, "ok": True, "verified": True, "truth": "PRODUCT_HTTP_READBACK"}
        else:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = json.dumps(resp).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_sima_live_e2e_strict_judge_rehearsal(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Start SiMa Live Sidecar
    adapter = SimaLiveAdapter(
        SimaAdapterConfig(
            mode="live",
            evidence_path=EVIDENCE_FILE,
        )
    )
    sima_handler = make_sima_sidecar_handler(adapter)
    sima_server = ThreadingHTTPServer(("127.0.0.1", 0), sima_handler)
    s_host, s_port = sima_server.server_address
    sima_thread = threading.Thread(target=sima_server.serve_forever, daemon=True)
    sima_thread.start()

    # 2. Start Physical I/O Contract Server
    io_server = ThreadingHTTPServer(("127.0.0.1", 0), MockPhysicalIOHandler)
    io_host, io_port = io_server.server_address
    io_thread = threading.Thread(target=io_server.serve_forever, daemon=True)
    io_thread.start()

    try:
        monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", f"http://{s_host}:{s_port}")
        monkeypatch.setenv(PHYSICAL_ENV_VAR, f"http://{io_host}:{io_port}")

        # 3. Run full strict judge rehearsal
        result = run_judge_rehearsal(
            scenario="restricted_zone_entry",
            runtime_id="sima-slot",
            require_live_physical=True,
            require_measured_sponsor=True,
        )

        assert result["ok"] is True
        assert result["mode"] == "STRICT_LIVE_GATE"
        assert result["runtime_id"] == "sima-slot"
        assert result["detections_truth"] == "MEASURED_SPONSOR_RUNTIME"
        assert result["physical_io_truth"] == "PRODUCT_HTTP_READBACK"
        assert bool(result["evidence_id"]) is True
        assert result["checks"][-1]["name"] == "sponsor_inference_is_measured"
        assert result["checks"][-1]["ok"] is True
        assert result["checks"][-2]["name"] == "physical_io_is_live_and_verified"
        assert result["checks"][-2]["ok"] is True

    finally:
        sima_server.shutdown()
        sima_server.server_close()
        sima_thread.join(timeout=3)
        io_server.shutdown()
        io_server.server_close()
        io_thread.join(timeout=3)
