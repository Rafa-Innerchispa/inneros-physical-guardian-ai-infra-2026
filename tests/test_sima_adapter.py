from __future__ import annotations

import builtins
import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from guardian_demo.runtime import SponsorRuntimeSlot
from guardian_demo.sima_adapter import SimaAdapterConfig, SimaLiveAdapter, make_sima_sidecar_handler
from guardian_demo.sima_onsite import TRUTH_MEASURED, TRUTH_SIMULATED, TRUTH_UNVERIFIED


def test_sima_adapter_fixture_mode() -> None:
    config = SimaAdapterConfig(mode="fixture")
    adapter = SimaLiveAdapter(config)
    res = adapter.infer(scenario="safety-perimeter", frame_ref="cam-01")
    assert res["model"] == "yolo26m-seg-bf16-b1"
    assert res["truth"] == TRUTH_SIMULATED
    assert len(res["detections"]) == 2
    assert res["detections"][0]["label"] == "person"
    assert res["detections"][0]["confidence"] > 0.9


def test_sima_adapter_live_mode_fails_closed_without_target_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__

    def block_pyneat(name: str, *args: object, **kwargs: object) -> object:
        if name == "pyneat":
            raise ImportError("forced missing target-side pyneat")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", block_pyneat)
    config = SimaAdapterConfig(mode="live")
    adapter = SimaLiveAdapter(config)
    try:
        res = adapter.infer(scenario="safety-perimeter", frame_ref="cam-01")
    except RuntimeError as exc:
        message = str(exc).lower()
        assert "pyneat" in message or "closed" in message or "target" in message
        return

    assert res["truth"] == TRUTH_UNVERIFIED
    assert res.get("detections") in ([], None)
    assert res.get("latency_ms") is None


def test_fixture_with_historical_evidence_never_becomes_measured_runtime() -> None:
    evidence_path = Path(__file__).resolve().parents[1] / "docs" / "sima_measured_evidence.json"
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="fixture", evidence_path=evidence_path))

    res = adapter.infer(scenario="safety-perimeter", frame_ref="fixture://frame-001")

    assert res["truth"] != TRUTH_MEASURED
    assert res.get("certifies_live_frames") is not True
    assert res.get("live_telemetry") is not True


def test_sima_sidecar_http_server_and_runtime_slot(monkeypatch) -> None:
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="fixture"))
    handler_class = make_sima_sidecar_handler(adapter)

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    host, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"
    try:
        with urlopen(f"{base_url}/health", timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "OK"

        monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", base_url)
        slot = SponsorRuntimeSlot("sima-slot", "SiMa.ai", "Modalix", "GUARDIAN_SIMA_RUNTIME_URL")
        res = slot.infer(scenario="warehouse-safety", frame_ref="frame-100")
        assert res.runtime_id == "sima-slot"
        assert res.model == "yolo26m-seg-bf16-b1"
        assert len(res.detections) == 2
        assert res.detections[0].label == "person"
    finally:
        server.shutdown()
        server.server_close()
