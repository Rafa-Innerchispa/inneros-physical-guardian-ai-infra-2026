from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from guardian_demo.runtime import DeterministicLocalRuntime, RUNTIME_SLOTS, runtime_catalog


def test_deterministic_runtime_returns_owned_fixture_truth_label() -> None:
    runtime = DeterministicLocalRuntime()
    result = runtime.infer(
        scenario="repeated_access_attempt",
        frame_ref="fixture://repeated_access_attempt/frame-001",
    )

    assert result.runtime_id == "local-deterministic"
    assert result.inference_truth == "SIMULATED_FIXTURE"
    assert result.runtime_overhead_ms >= 0
    assert len(result.detections) == 1
    assert result.detections[0].track_id == "track-08"


def test_all_declared_hardware_slots_remain_unbenchmarked_until_integrated() -> None:
    catalog = runtime_catalog()
    sponsor_rows = [row for row in catalog if row["runtime_id"] != "local-deterministic"]

    assert {row["provider"] for row in sponsor_rows} == {"SiMa.ai", "Qualcomm", "Intel"}
    assert all(row["truth"] == "NOT_BENCHMARKED" for row in sponsor_rows)
    assert all(row["status"] == "AWAITING_ASSIGNED_HARDWARE_OR_SDK" for row in sponsor_rows)


def test_sponsor_placeholder_raises_instead_of_fabricating_inference() -> None:
    with pytest.raises(RuntimeError, match="cannot run until official hardware/SDK access"):
        RUNTIME_SLOTS["sima-slot"].infer(
            scenario="loitering_after_hours",
            frame_ref="fixture://loitering_after_hours/frame-001",
        )


def test_sponsor_bridge_rejects_non_loopback_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", "https://example.com/runtime")
    slot = RUNTIME_SLOTS["sima-slot"]

    assert slot.status()["status"] == "INVALID_LOCAL_BRIDGE_CONFIG"
    with pytest.raises(RuntimeError, match="loopback-only"):
        slot.infer(scenario="loitering_after_hours", frame_ref="fixture://frame")


def test_sponsor_bridge_can_normalize_local_sdk_sidecar(monkeypatch: pytest.MonkeyPatch) -> None:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            request_body = json.loads(self.rfile.read(length).decode("utf-8"))
            assert request_body["scenario"] == "restricted_zone_entry"
            payload = json.dumps(
                {
                    "model": "official-sdk-model",
                    "truth": "MEASURED_SPONSOR_RUNTIME",
                    "detections": [
                        {
                            "label": "person",
                            "confidence": 0.97,
                            "bbox": [0.1, 0.2, 0.4, 0.9],
                            "track_id": "sdk-track-1",
                            "zone": "equipment-zone",
                        }
                    ],
                    "notes": "fixture sidecar used only to validate the bridge contract",
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", f"http://{host}:{port}")

    try:
        slot = RUNTIME_SLOTS["sima-slot"]
        assert slot.status()["status"] == "READY"
        result = slot.infer(
            scenario="restricted_zone_entry",
            frame_ref="fixture://restricted_zone_entry/frame-001",
        )
        assert result.provider == "SiMa.ai"
        assert result.model == "official-sdk-model"
        assert result.inference_truth == "MEASURED_SPONSOR_RUNTIME"
        assert result.detections[0].track_id == "sdk-track-1"
        assert result.runtime_overhead_ms >= 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
