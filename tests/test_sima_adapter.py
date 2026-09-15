from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest

from guardian_demo.runtime import SponsorRuntimeSlot
from guardian_demo.sima_adapter import SimaAdapterConfig, SimaLiveAdapter, make_sima_sidecar_handler
from guardian_demo.sima_onsite import TRUTH_MEASURED, TRUTH_SIMULATED


def test_sima_adapter_fixture_mode() -> None:
    config = SimaAdapterConfig(mode="fixture")
    adapter = SimaLiveAdapter(config)
    res = adapter.infer(scenario="safety-perimeter", frame_ref="cam-01")
    assert res["model"] == "yolo26m-seg-bf16-b1"
    assert res["truth"] == TRUTH_SIMULATED
    assert len(res["detections"]) == 2
    assert res["detections"][0]["label"] == "person"
    assert res["detections"][0]["confidence"] > 0.9


def test_sima_adapter_live_mode() -> None:
    config = SimaAdapterConfig(mode="live")
    adapter = SimaLiveAdapter(config)
    res = adapter.infer(scenario="safety-perimeter", frame_ref="cam-01")
    assert res["model"] == "yolo26m-seg-bf16-b1"
    assert res["truth"] in {TRUTH_MEASURED, TRUTH_SIMULATED}
    assert len(res["detections"]) >= 1


def test_sima_sidecar_http_server_and_runtime_slot(monkeypatch) -> None:
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="fixture"))
    handler_class = make_sima_sidecar_handler(adapter)
    
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    host, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"
    try:
        # Test /health
        with urlopen(f"{base_url}/health", timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "OK"

        # Test with SponsorRuntimeSlot
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
