from __future__ import annotations

import base64
import io
import json
import os
import threading
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

import guardian_demo.sima_adapter as sima_adapter_module
from guardian_demo.frame_input import FramePayload
from guardian_demo.modalix_pyneat_worker import _read_envelope, _write_response
from guardian_demo.runtime import SponsorRuntimeSlot
from guardian_demo.sima_adapter import (
    ModalixSshPyNeatBackend,
    SimaAdapterConfig,
    SimaEvidenceError,
    SimaLiveAdapter,
    SimaUnavailable,
    make_sima_sidecar_handler,
)
from guardian_demo.sima_contract import (
    ATTESTATION_KIND,
    LIVE_EVIDENCE_KIND,
    LIVE_EVIDENCE_SCHEMA,
    TELEMETRY_SOURCE,
    TRUTH_MEASURED,
    TRUTH_SIMULATED,
    TRUTH_UNVERIFIED,
    sha256_bytes,
    utc_now,
)

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlBzv8AAAAASUVORK5CYII="
)


def frame_payload(source_id: str = "laptop-webcam") -> FramePayload:
    return FramePayload.from_bytes(
        frame_id="frame-test-001",
        source_id=source_id,
        captured_at=utc_now().isoformat(),
        image_type="image/png",
        image_bytes=PNG_BYTES,
    )


class AttestedModalixBackend:
    def __init__(self) -> None:
        self.requests: list[dict] = []

    def infer(self, request_payload: dict) -> dict:
        self.requests.append(request_payload)
        image_bytes = base64.b64decode(request_payload["image_base64"])
        return {
            "schema": LIVE_EVIDENCE_SCHEMA,
            "evidence_kind": LIVE_EVIDENCE_KIND,
            "truth": TRUTH_MEASURED,
            "measured": True,
            "captured_at": request_payload["captured_at"],
            "inferred_at": utc_now().isoformat(),
            "model": request_payload["requested_model"],
            "runtime": "SiMa MLA runtime 2.1.3",
            "device": "SiMa.ai Modalix DevKit MLSoC",
            "source": {
                "frame_id": request_payload["frame_id"],
                "source_id": request_payload["source_id"],
                "sha256": sha256_bytes(image_bytes),
                "media_type": request_payload["image_type"],
                "width": request_payload["width"],
                "height": request_payload["height"],
            },
            "detections": [
                {
                    "label": "person",
                    "confidence": 0.91,
                    "bbox": [0.1, 0.2, 0.6, 0.9],
                    "track_id": "modalix-track-1",
                    "zone": "restricted-zone",
                }
            ],
            "telemetry": {
                "source": TELEMETRY_SOURCE,
                "latency_ms": 11.4,
                "fps": 41.0,
            },
            "attestation": {
                "kind": ATTESTATION_KIND,
                "runtime_verified": True,
                "device_verified": True,
                "evidence_id": "modalix-frame-proof-001",
            },
        }


class FixtureClaimBackend(AttestedModalixBackend):
    def infer(self, request_payload: dict) -> dict:
        result = super().infer(request_payload)
        result["attestation"] = {
            "kind": "SIMULATED_FIXTURE",
            "runtime_verified": False,
            "device_verified": False,
            "evidence_id": None,
        }
        return result


def test_fixture_mode_is_always_simulated_and_has_no_timing_claim() -> None:
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="fixture"))
    result = adapter.infer(scenario="safety-perimeter", frame=frame_payload())

    assert result["truth"] == TRUTH_SIMULATED
    assert result["measured"] is False
    assert result["telemetry"] == {}
    assert result["attestation"]["runtime_verified"] is False


def test_live_mode_without_backend_fails_closed_instead_of_import_fallback() -> None:
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="live"))

    assert adapter.health()["status"] == "BLOCKED"
    assert adapter.health()["truth"] == TRUTH_UNVERIFIED
    with pytest.raises(SimaUnavailable, match="not configured"):
        adapter.infer(scenario="safety-perimeter", frame=frame_payload())


def test_live_mode_accepts_only_matching_per_frame_modalix_proof() -> None:
    backend = AttestedModalixBackend()
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="live"), backend=backend)
    frame = frame_payload()

    result = adapter.infer(scenario="safety-perimeter", frame=frame)

    assert result["truth"] == TRUTH_MEASURED
    assert result["source"]["frame_id"] == frame.frame_id
    assert result["source"]["sha256"] == frame.sha256
    assert result["detections"][0]["bbox"] == [0.1, 0.2, 0.6, 0.9]
    assert len(backend.requests) == 1
    assert base64.b64decode(backend.requests[0]["image_base64"]) == PNG_BYTES


def test_fixture_shaped_response_cannot_claim_measured_runtime() -> None:
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="live"), backend=FixtureClaimBackend())

    with pytest.raises(SimaEvidenceError, match="attestation"):
        adapter.infer(scenario="safety-perimeter", frame=frame_payload())


def test_sima_sidecar_and_runtime_slot_preserve_frame_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = SimaLiveAdapter(
        SimaAdapterConfig(mode="live"),
        backend=AttestedModalixBackend(),
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_sima_sidecar_handler(adapter))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        with urlopen(f"{base_url}/health", timeout=2) as response:
            health = json.loads(response.read().decode("utf-8"))
        assert health["status"] == "READY"
        assert health["truth"] == TRUTH_UNVERIFIED

        monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", base_url)
        slot = SponsorRuntimeSlot("sima-slot", "SiMa.ai", "Modalix", "GUARDIAN_SIMA_RUNTIME_URL")
        frame = frame_payload()
        result = slot.infer_frame(scenario="warehouse-safety", frame=frame)

        assert result.inference_truth == TRUTH_MEASURED
        assert result.source["frame_id"] == frame.frame_id
        assert result.telemetry["latency_ms"] == 11.4
        assert result.detections[0].label == "person"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_sidecar_returns_explicit_unverified_503_when_modalix_is_unavailable() -> None:
    adapter = SimaLiveAdapter(SimaAdapterConfig(mode="live"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_sima_sidecar_handler(adapter))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    frame = frame_payload()
    payload = json.dumps({"scenario": "safety", **frame.to_transport()}).encode("utf-8")
    request = Request(
        f"http://{host}:{port}/infer",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with pytest.raises(HTTPError) as blocked:
            urlopen(request, timeout=2)
        assert blocked.value.code == 503
        body = json.loads(blocked.value.read().decode("utf-8"))
        assert body["truth"] == TRUTH_UNVERIFIED
        assert body["fail_closed"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_persistent_worker_reuses_session_and_recovers_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FlushCountingWriter:
        def __init__(self, stream: object, process: object) -> None:
            self.stream = stream
            self.process = process

        def write(self, data: bytes) -> int:
            return self.stream.write(data)

        def flush(self) -> None:
            self.process.flush_count += 1
            self.stream.flush()

        def close(self) -> None:
            self.stream.close()

    class PersistentWorkerProcess:
        def __init__(self, worker_number: int) -> None:
            request_read_fd, request_write_fd = os.pipe()
            response_read_fd, response_write_fd = os.pipe()
            self.stdin = os.fdopen(request_write_fd, "wb", buffering=0)
            self.stdout = os.fdopen(response_read_fd, "rb", buffering=0)
            self.stderr = io.BytesIO()
            self._request_read = os.fdopen(request_read_fd, "rb", buffering=0)
            response_stream = os.fdopen(response_write_fd, "wb", buffering=0)
            self._response_write = FlushCountingWriter(response_stream, self)
            self.worker_instance_id = f"modalix-worker-local-{worker_number}"
            self.flush_count = 0
            self.requests: list[tuple[dict, bytes]] = []
            self.worker_error: BaseException | None = None
            self._returncode: int | None = None
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

        def _run(self) -> None:
            sequence = 0
            model_sha256 = ""
            try:
                while True:
                    envelope = _read_envelope(
                        self._request_read,
                        json,
                        sima_adapter_module.struct,
                    )
                    if envelope is None:
                        break
                    request, image_bytes = envelope
                    self.requests.append((request, image_bytes))
                    if request.get("operation") == "initialize":
                        model_sha256 = request["expected_model_sha256"]
                        response = {
                            "worker_schema": sima_adapter_module.WORKER_SCHEMA,
                            "operation": "initialize",
                            "execution_status": "WORKER_READY",
                            "wire_protocol": sima_adapter_module.WORKER_WIRE_PROTOCOL,
                            "worker_instance_id": self.worker_instance_id,
                            "runtime_version": sima_adapter_module.EXPECTED_PYNEAT_VERSION,
                            "machine": "aarch64",
                            "model_sha256": model_sha256,
                            "model_load_count": 1,
                            "model_build_ms": 8.0,
                        }
                    else:
                        sequence += 1
                        response = {
                            "worker_schema": sima_adapter_module.WORKER_SCHEMA,
                            "operation": "infer",
                            "wire_protocol": sima_adapter_module.WORKER_WIRE_PROTOCOL,
                            "worker_instance_id": self.worker_instance_id,
                            "model_load_count": 1,
                            "model_rebuilt_for_frame": False,
                            "request_sequence": sequence,
                            "request_nonce": request.get("request_nonce"),
                            "frame_id": request.get("frame_id"),
                            "source_id": request.get("source_id"),
                            "source_sha256": request.get("source_sha256"),
                        }
                        if request.get("frame_id") == "frame-corrupt":
                            response.update(
                                execution_status="BLOCKED",
                                error_code="IMAGE_DECODE_FAILED",
                                error="worker could not decode a three-channel image",
                            )
                        else:
                            labels = {
                                "frame-one": "person",
                                "frame-two": "car",
                                "frame-recovered": "dog",
                            }
                            frame_id = str(request["frame_id"])
                            response.update(
                                execution_status="REAL_TARGET_MLA_DECODE_SUCCESS",
                                inferred_at=utc_now().isoformat(),
                                runtime_version=sima_adapter_module.EXPECTED_PYNEAT_VERSION,
                                python_version="3.10.0",
                                machine="aarch64",
                                model_sha256=model_sha256,
                                worker_startup_model_build_ms=8.0,
                                preprocessing_ms=1.0,
                                mla_inference_ms=2.0,
                                decode_ms=1.0,
                                output_tensor_count=10,
                                output_tensor_shapes=sima_adapter_module.EXPECTED_OUTPUT_SHAPES,
                                raw_output_sha256=sha256_bytes(frame_id.encode("utf-8")),
                                decode_method="YOLO26_ANCHOR_FREE_LTRB_SIGMOID_COCO80_CLASS_AWARE_NMS_V1",
                                confidence_floor=request["confidence_floor"],
                                policy_confidence_threshold=request["policy_confidence_threshold"],
                                nms_iou_threshold=request["nms_iou_threshold"],
                                pre_nms_top_k=request["pre_nms_top_k"],
                                post_nms_top_k=request["post_nms_top_k"],
                                detections=[
                                    {
                                        "label": labels[frame_id],
                                        "confidence": 0.91,
                                        "bbox": [0.1, 0.2, 0.6, 0.9],
                                        "track_id": f"track-{frame_id}",
                                        "zone": "restricted-zone",
                                    }
                                ],
                            )
                    _write_response(self._response_write, json, response)
                self._returncode = 0
            except BaseException as exc:
                self.worker_error = exc
                self._returncode = 1
            finally:
                self._response_write.close()
                self._request_read.close()

        def poll(self) -> int | None:
            return None if self._thread.is_alive() else self._returncode

        def wait(self, timeout: float | None = None) -> int:
            self._thread.join(timeout)
            if self._thread.is_alive():
                raise sima_adapter_module.subprocess.TimeoutExpired("fake-worker", timeout)
            return int(self._returncode or 0)

        def terminate(self) -> None:
            try:
                self.stdin.close()
            except OSError:
                pass

        kill = terminate

    processes: list[PersistentWorkerProcess] = []

    def fake_popen(*args: object, **kwargs: object) -> PersistentWorkerProcess:
        process = PersistentWorkerProcess(len(processes) + 1)
        processes.append(process)
        return process

    monkeypatch.setattr(sima_adapter_module.shutil, "which", lambda _: "ssh")
    monkeypatch.setattr(sima_adapter_module.subprocess, "Popen", fake_popen)
    backend = ModalixSshPyNeatBackend(
        SimaAdapterConfig(
            mode="live",
            transport="ssh",
            devkit_ip="192.168.1.20",
            timeout_sec=1.0,
        )
    )

    def worker_request(frame_id: str, source_id: str) -> dict:
        return {
            "frame_id": frame_id,
            "source_id": source_id,
            "captured_at": utc_now().isoformat(),
            "image_type": "image/png",
            "image_base64": base64.b64encode(PNG_BYTES).decode("ascii"),
            "width": 1,
            "height": 1,
            "source_sha256": sha256_bytes(PNG_BYTES),
            "request_nonce": f"nonce-{frame_id}",
            "requested_model": "yolo26m-seg-bf16-b1",
        }

    try:
        first = backend.infer(worker_request("frame-one", "camera-one"))
        second = backend.infer(worker_request("frame-two", "camera-two"))

        assert len(processes) == 1
        assert first["attestation"]["worker_instance_id"] == second["attestation"]["worker_instance_id"]
        assert first["attestation"]["request_sequence"] == 1
        assert second["attestation"]["request_sequence"] == 2
        assert first["source"]["frame_id"] == "frame-one"
        assert second["source"]["frame_id"] == "frame-two"
        assert first["detections"][0]["label"] == "person"
        assert second["detections"][0]["label"] == "car"

        with pytest.raises(SimaEvidenceError, match="IMAGE_DECODE_FAILED"):
            backend.infer(worker_request("frame-corrupt", "camera-corrupt"))

        recovered = backend.infer(worker_request("frame-recovered", "camera-recovered"))
        assert len(processes) == 1
        assert recovered["attestation"]["worker_instance_id"] == first["attestation"]["worker_instance_id"]
        assert recovered["attestation"]["request_sequence"] == 4
        assert recovered["source"]["frame_id"] == "frame-recovered"
        assert recovered["detections"][0]["label"] == "dog"
        assert [request["frame_id"] for request, _ in processes[0].requests[1:]] == [
            "frame-one",
            "frame-two",
            "frame-corrupt",
            "frame-recovered",
        ]
        assert processes[0].flush_count == 5
        assert processes[0].worker_error is None
    finally:
        backend.close()