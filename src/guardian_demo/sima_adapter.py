from __future__ import annotations

import atexit
import base64
import binascii
import hashlib
import ipaddress
import json
import logging
import os
import re
import secrets
import shlex
import shutil
import struct
import subprocess
import threading
from collections import deque
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from guardian_demo.frame_input import MAX_JSON_BODY_BYTES, FramePayload
from guardian_demo.sima_contract import (
    LIVE_EVIDENCE_KIND,
    LIVE_EVIDENCE_SCHEMA,
    TRUTH_SIMULATED,
    TRUTH_UNVERIFIED,
    normalize_detection,
    utc_now,
    validate_live_evidence,
)

logger = logging.getLogger(__name__)

MODALIX_INFER_URL_ENV = "GUARDIAN_SIMA_MODALIX_INFER_URL"
MAX_RUNTIME_RESPONSE_BYTES = 256_000
MAX_WORKER_ENVELOPE_BYTES = 1_100_000
MAX_WORKER_HEADER_BYTES = 32_000
WORKER_SCHEMA = "inneros.guardian.sima.modalix-worker.v2"
WORKER_WIRE_PROTOCOL = "GUARDIAN_LENGTH_PREFIXED_METADATA_IMAGE_V1"
MODALIX_MODEL_ARCHIVE = "/media/nvme/models/yolo26m-seg-bf16-b1.tar.gz"
MODALIX_MODEL_SHA256 = "41bebbecca2f20de40c76d4bc6656c3fe369f9c139929dad93922492efa9b591"
MODALIX_REMOTE_PYTHON = "/home/sima/pyneat/bin/python"
EXPECTED_PYNEAT_VERSION = "0.4.0"
EXPECTED_OUTPUT_SHAPES = [
    [80, 80, 4],
    [40, 40, 4],
    [20, 20, 4],
    [80, 80, 80],
    [40, 40, 80],
    [20, 20, 80],
    [80, 80, 32],
    [40, 40, 32],
    [20, 20, 32],
    [160, 160, 32],
]
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SSH_USER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,31}$")


class SimaUnavailable(RuntimeError):
    """The configured SiMa inference boundary cannot serve this frame."""


class SimaEvidenceError(RuntimeError):
    """A runtime response failed the per-frame provenance contract."""


class SimaFrameBackend(Protocol):
    def infer(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class SimaDetection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    track_id: str = "fixture-track-01"
    zone: str = "fixture-zone"

    def to_dict(self) -> dict[str, Any]:
        return normalize_detection(
            {
                "label": self.label,
                "confidence": self.confidence,
                "bbox": list(self.bbox),
                "track_id": self.track_id,
                "zone": self.zone,
            }
        )


@dataclass
class SimaAdapterConfig:
    mode: str = "fixture"  # "live" or "fixture"
    transport: str = "auto"  # "auto", "ssh", or "http"
    devkit_ip: str = ""
    model_name: str = "yolo26m-seg-bf16-b1"
    hardware: str = "SiMa.ai Modalix DevKit MLSoC"
    runtime_name: str = "SiMa.ai MLA runtime"
    conf_threshold: float = 0.25
    telemetry_confidence_floor: float = 0.0001
    nms_iou_threshold: float = 0.45
    pre_nms_top_k: int = 300
    max_detections: int = 100
    inference_url: str | None = None
    ssh_user: str = "sima"
    ssh_port: int = 22
    model_archive: str = MODALIX_MODEL_ARCHIVE
    model_sha256: str = MODALIX_MODEL_SHA256
    remote_python: str = MODALIX_REMOTE_PYTHON
    expected_pyneat_version: str = EXPECTED_PYNEAT_VERSION
    timeout_sec: float = 45.0


class ModalixHttpBackend:
    """Explicit HTTP boundary to the operator-configured Modalix service.

    The destination is configuration, never request data. It must be the exact
    configured DevKit address and cannot carry credentials, query data, or
    fragments. Configuration alone never upgrades truth: every response still
    has to satisfy the per-frame evidence contract.
    """

    requires_strong_attestation = True

    def __init__(self, url: str, *, devkit_ip: str, timeout_sec: float) -> None:
        parsed = urlparse(url)
        try:
            expected_ip = str(ipaddress.ip_address(devkit_ip.strip()))
            supplied_ip = str(ipaddress.ip_address(parsed.hostname or ""))
        except ValueError as exc:
            raise ValueError("Modalix inference URL must target the configured DevKit IP") from exc
        if parsed.scheme not in {"http", "https"} or supplied_ip != expected_ip:
            raise ValueError("Modalix inference URL must target the configured DevKit IP")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Modalix inference URL cannot contain credentials, query data, or fragments")
        if not parsed.path or parsed.path == "/":
            raise ValueError("Modalix inference URL requires an explicit inference path")
        self._url = url
        self._timeout_sec = timeout_sec

    def infer(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(request_payload, separators=(",", ":")).encode("utf-8")
        request = Request(
            self._url,
            data=body,
            method="POST",
            headers={
                "Accept": "application/json",
                "Cache-Control": "no-store",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_sec) as response:  # nosec B310 - exact DevKit IP validated above
                if response.status != HTTPStatus.OK:
                    raise SimaUnavailable(f"Modalix runtime returned HTTP {response.status}")
                if response.headers.get_content_type().lower() != "application/json":
                    raise SimaEvidenceError("Modalix runtime response is not JSON")
                encoded = response.read(MAX_RUNTIME_RESPONSE_BYTES + 1)
        except (SimaUnavailable, SimaEvidenceError):
            raise
        except Exception as exc:
            raise SimaUnavailable(f"Modalix runtime transport failed: {type(exc).__name__}") from exc
        if len(encoded) > MAX_RUNTIME_RESPONSE_BYTES:
            raise SimaEvidenceError("Modalix runtime response exceeds the bounded contract")
        try:
            result = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SimaEvidenceError("Modalix runtime response contains malformed JSON") from exc
        if not isinstance(result, dict):
            raise SimaEvidenceError("Modalix runtime response must be a JSON object")
        return result


class ModalixSshPyNeatBackend:
    """Run the proven PyNeat path in one persistent, bounded SSH session.

    The in-memory worker builds the model once, then accepts length-prefixed
    metadata and raw frames. It calls ``runner.run([tensor])`` per frame,
    decodes those same ten heads, and returns NDJSON metadata only.
    """

    requires_strong_attestation = True

    def __init__(self, config: SimaAdapterConfig) -> None:
        try:
            self._devkit_ip = str(ipaddress.ip_address(config.devkit_ip.strip()))
        except ValueError as exc:
            raise ValueError("SSH transport requires a valid Modalix DevKit IP") from exc
        if not _SSH_USER_RE.fullmatch(config.ssh_user):
            raise ValueError("SSH transport requires a bounded target user")
        if isinstance(config.ssh_port, bool) or not 1 <= config.ssh_port <= 65535:
            raise ValueError("SSH transport requires a valid target port")
        if config.remote_python != MODALIX_REMOTE_PYTHON:
            raise ValueError("SSH transport remote Python must match the proven PyNeat runtime")
        if (
            not config.model_archive.startswith("/media/nvme/models/")
            or not config.model_archive.endswith(".tar.gz")
        ):
            raise ValueError("SSH transport model archive is outside the allowlisted target path")
        if not _SHA256_RE.fullmatch(config.model_sha256):
            raise ValueError("SSH transport requires the exact target model SHA-256")
        if not 0.0 < config.telemetry_confidence_floor <= config.conf_threshold <= 1.0:
            raise ValueError("SiMa confidence thresholds are invalid")
        if not 0.0 < config.nms_iou_threshold < 1.0:
            raise ValueError("SiMa NMS threshold is invalid")
        if not 1 <= config.pre_nms_top_k <= 2_000:
            raise ValueError("SiMa pre-NMS limit is invalid")
        if not 1 <= config.max_detections <= config.pre_nms_top_k:
            raise ValueError("SiMa detection limit is invalid")

        worker_path = Path(__file__).with_name("modalix_pyneat_worker.py")
        try:
            worker_source = worker_path.read_bytes()
        except OSError as exc:
            raise ValueError("Modalix PyNeat worker is unavailable") from exc
        self._worker_sha256 = hashlib.sha256(worker_source).hexdigest()
        encoded_worker = base64.b64encode(worker_source).decode("ascii")
        remote_code = (
            'exec(compile(__import__("base64").b64decode("'
            + encoded_worker
            + '"),"<guardian-modalix-worker>","exec"))'
        )
        self._remote_command = (
            "SIMA_ALLOW_INPUTSTREAM_CPU_TO_EV74_COPY=1 "
            + shlex.quote(config.remote_python)
            + " -c "
            + shlex.quote(remote_code)
        )
        self._ssh_binary = shutil.which("ssh")
        if not self._ssh_binary:
            raise ValueError("OpenSSH client is unavailable for Modalix transport")
        self._ssh_target = f"{config.ssh_user}@{self._devkit_ip}"
        self._ssh_port = config.ssh_port
        self._timeout_sec = config.timeout_sec
        self._config = config
        self._lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._responses: Queue[bytes | None] | None = None
        self._stderr_lines: deque[bytes] = deque(maxlen=16)
        self._worker_instance_id: str | None = None
        self._worker_model_build_ms: float | None = None
        self._last_request_sequence = 0
        atexit.register(self.close)

    def describe(self) -> str:
        process = self._process
        if process is not None and process.poll() is None and self._worker_instance_id:
            return "MODALIX_SSH_PYNEAT_PERSISTENT_WARM"
        return "MODALIX_SSH_PYNEAT_PERSISTENT_CONFIGURED"

    def _safe_worker_error(self) -> str:
        detail = (
            self._stderr_lines[-1].decode("utf-8", errors="replace")[:240]
            if self._stderr_lines
            else "no target diagnostic"
        )
        return detail.replace("\r", " ").replace("\n", " ")

    def _command(self) -> list[str]:
        return [
            self._ssh_binary,
            "-T",
            "-p",
            str(self._ssh_port),
            "-oBatchMode=yes",
            "-oClearAllForwardings=yes",
            "-oConnectTimeout=5",
            "-oServerAliveInterval=5",
            "-oServerAliveCountMax=1",
            "-oStrictHostKeyChecking=yes",
            self._ssh_target,
            self._remote_command,
        ]

    @staticmethod
    def _pump_stdout(stream, responses: Queue[bytes | None]) -> None:
        try:
            while True:
                line = stream.readline(MAX_RUNTIME_RESPONSE_BYTES + 2)
                if not line:
                    break
                responses.put(line)
        finally:
            responses.put(None)

    def _pump_stderr(self, stream) -> None:
        while True:
            line = stream.readline(1024)
            if not line:
                return
            self._stderr_lines.append(line.rstrip())

    @staticmethod
    def _encode_envelope(payload: dict[str, Any], image_bytes: bytes) -> bytes:
        header = dict(payload)
        header["image_size"] = len(image_bytes)
        encoded_header = json.dumps(header, separators=(",", ":")).encode("utf-8")
        if not encoded_header or len(encoded_header) > MAX_WORKER_HEADER_BYTES:
            raise SimaEvidenceError("Modalix worker metadata exceeds the bounded contract")
        envelope_size = 4 + len(encoded_header) + len(image_bytes)
        if envelope_size > MAX_WORKER_ENVELOPE_BYTES:
            raise SimaEvidenceError("Modalix worker request exceeds the bounded contract")
        return (
            struct.pack(">I", envelope_size)
            + struct.pack(">I", len(encoded_header))
            + encoded_header
            + image_bytes
        )

    def _stop_worker_locked(self, *, graceful: bool) -> None:
        process = self._process
        self._process = None
        self._responses = None
        self._worker_instance_id = None
        self._worker_model_build_ms = None
        self._last_request_sequence = 0
        if process is None:
            return
        try:
            if graceful and process.poll() is None and process.stdin is not None:
                process.stdin.write(struct.pack(">I", 0))
                process.stdin.flush()
            process.wait(timeout=1.0)
        except Exception:
            try:
                process.terminate()
                process.wait(timeout=0.5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except Exception:
                pass

    def close(self) -> None:
        try:
            with self._lock:
                self._stop_worker_locked(graceful=True)
        except Exception:
            pass

    def _read_response_locked(self) -> dict[str, Any]:
        responses = self._responses
        process = self._process
        if responses is None or process is None:
            raise SimaUnavailable("Modalix persistent worker is not running")
        try:
            encoded = responses.get(timeout=self._timeout_sec)
        except Empty as exc:
            self._stop_worker_locked(graceful=False)
            raise SimaUnavailable("Modalix persistent worker timed out") from exc
        if encoded is None:
            diagnostic = self._safe_worker_error()
            self._stop_worker_locked(graceful=False)
            raise SimaUnavailable("Modalix persistent worker exited: " + diagnostic)
        if (
            not encoded.endswith(b"\n")
            or len(encoded) > MAX_RUNTIME_RESPONSE_BYTES + 1
        ):
            self._stop_worker_locked(graceful=False)
            raise SimaEvidenceError("Modalix persistent worker response is empty or oversized")
        try:
            response = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._stop_worker_locked(graceful=False)
            raise SimaEvidenceError("Modalix persistent worker response is malformed") from exc
        if not isinstance(response, dict):
            self._stop_worker_locked(graceful=False)
            raise SimaEvidenceError("Modalix persistent worker response must be an object")
        return response

    def _exchange_locked(
        self,
        payload: dict[str, Any],
        image_bytes: bytes,
    ) -> dict[str, Any]:
        process = self._process
        if process is None or process.poll() is not None or process.stdin is None:
            self._stop_worker_locked(graceful=False)
            raise SimaUnavailable("Modalix persistent worker is unavailable")
        packet = self._encode_envelope(payload, image_bytes)
        try:
            process.stdin.write(packet)
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self._stop_worker_locked(graceful=False)
            raise SimaUnavailable("Modalix persistent worker transport failed") from exc
        return self._read_response_locked()

    def _ensure_worker_locked(self) -> None:
        process = self._process
        if (
            process is not None
            and process.poll() is None
            and self._worker_instance_id is not None
        ):
            return
        self._stop_worker_locked(graceful=False)
        self._stderr_lines.clear()
        responses: Queue[bytes | None] = Queue()
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            process = subprocess.Popen(
                self._command(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                creationflags=creationflags,
            )
        except OSError as exc:
            raise SimaUnavailable(
                f"Modalix SSH worker failed to start: {type(exc).__name__}"
            ) from exc
        self._process = process
        self._responses = responses
        if process.stdout is None or process.stderr is None:
            self._stop_worker_locked(graceful=False)
            raise SimaUnavailable("Modalix SSH worker pipes are unavailable")
        threading.Thread(
            target=self._pump_stdout,
            args=(process.stdout, responses),
            daemon=True,
            name="guardian-modalix-stdout",
        ).start()
        threading.Thread(
            target=self._pump_stderr,
            args=(process.stderr,),
            daemon=True,
            name="guardian-modalix-stderr",
        ).start()

        ready = self._exchange_locked(
            {
                "operation": "initialize",
                "model_archive": self._config.model_archive,
                "expected_model_sha256": self._config.model_sha256,
            },
            b"",
        )
        worker_id = ready.get("worker_instance_id")
        build_ms = ready.get("model_build_ms")
        valid_ready = (
            ready.get("worker_schema") == WORKER_SCHEMA
            and ready.get("wire_protocol") == WORKER_WIRE_PROTOCOL
            and ready.get("execution_status") == "WORKER_READY"
            and ready.get("runtime_version") == self._config.expected_pyneat_version
            and str(ready.get("machine", "")).lower() in {"aarch64", "arm64"}
            and ready.get("model_sha256") == self._config.model_sha256
            and ready.get("model_load_count") == 1
            and isinstance(worker_id, str)
            and worker_id.startswith("modalix-worker-")
            and len(worker_id) <= 80
            and isinstance(build_ms, (int, float))
            and not isinstance(build_ms, bool)
            and float(build_ms) > 0.0
        )
        if not valid_ready:
            self._stop_worker_locked(graceful=False)
            raise SimaEvidenceError("Modalix persistent worker initialization proof is invalid")
        self._worker_instance_id = worker_id
        self._worker_model_build_ms = float(build_ms)
        self._last_request_sequence = 0

    def _invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        encoded_image = payload.get("image_base64")
        if not isinstance(encoded_image, str) or not encoded_image:
            raise SimaEvidenceError("Modalix worker request is missing image bytes")
        try:
            image_bytes = base64.b64decode(encoded_image, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise SimaEvidenceError("Modalix worker image payload is malformed") from exc
        if hashlib.sha256(image_bytes).hexdigest() != payload.get("source_sha256"):
            raise SimaEvidenceError("Modalix worker source SHA-256 mismatch before transport")
        metadata = dict(payload)
        metadata.pop("image_base64", None)
        with self._lock:
            self._ensure_worker_locked()
            worker = self._exchange_locked(metadata, image_bytes)
            expected_sequence = self._last_request_sequence + 1
            session_proof_valid = (
                worker.get("worker_schema") == WORKER_SCHEMA
                and worker.get("wire_protocol") == WORKER_WIRE_PROTOCOL
                and worker.get("operation") == "infer"
                and worker.get("worker_instance_id") == self._worker_instance_id
                and worker.get("model_load_count") == 1
                and worker.get("model_rebuilt_for_frame") is False
                and worker.get("request_sequence") == expected_sequence
                and worker.get("request_nonce") == metadata.get("request_nonce")
                and worker.get("frame_id") == metadata.get("frame_id")
                and worker.get("source_id") == metadata.get("source_id")
                and worker.get("source_sha256") == metadata.get("source_sha256")
            )
            if not session_proof_valid:
                self._stop_worker_locked(graceful=False)
                raise SimaEvidenceError(
                    "Modalix persistent worker session or frame provenance proof is invalid"
                )
            self._last_request_sequence = expected_sequence
            if worker.get("execution_status") != "REAL_TARGET_MLA_DECODE_SUCCESS":
                error_code = worker.get("error_code")
                safe_code = (
                    error_code
                    if isinstance(error_code, str) and re.fullmatch(r"[A-Z0-9_]{1,64}", error_code)
                    else "FRAME_INFERENCE_FAILED"
                )
                raise SimaEvidenceError(f"Modalix worker blocked frame: {safe_code}")
            return worker

    def infer(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        source_sha256 = request_payload.get("source_sha256")
        request_nonce = request_payload.get("request_nonce")
        worker_request = {
            **request_payload,
            "operation": "infer",
            "model_archive": self._config.model_archive,
            "expected_model_sha256": self._config.model_sha256,
            "confidence_floor": self._config.telemetry_confidence_floor,
            "policy_confidence_threshold": self._config.conf_threshold,
            "nms_iou_threshold": self._config.nms_iou_threshold,
            "pre_nms_top_k": self._config.pre_nms_top_k,
            "post_nms_top_k": self._config.max_detections,
        }
        worker = self._invoke(worker_request)
        if worker.get("worker_schema") != WORKER_SCHEMA:
            raise SimaEvidenceError("Modalix worker schema mismatch")
        if worker.get("wire_protocol") != WORKER_WIRE_PROTOCOL:
            raise SimaEvidenceError("Modalix worker wire protocol mismatch")
        if worker.get("request_nonce") != request_nonce:
            raise SimaEvidenceError("Modalix worker request nonce mismatch")
        if worker.get("frame_id") != request_payload.get("frame_id"):
            raise SimaEvidenceError("Modalix worker frame identity mismatch")
        if worker.get("source_id") != request_payload.get("source_id"):
            raise SimaEvidenceError("Modalix worker source identity mismatch")
        if worker.get("source_sha256") != source_sha256:
            raise SimaEvidenceError("Modalix worker source SHA-256 mismatch")
        if worker.get("model_sha256") != self._config.model_sha256:
            raise SimaEvidenceError("Modalix worker model SHA-256 mismatch")
        if worker.get("runtime_version") != self._config.expected_pyneat_version:
            raise SimaEvidenceError("Modalix worker PyNeat version mismatch")
        if str(worker.get("machine", "")).lower() not in {"aarch64", "arm64"}:
            raise SimaEvidenceError("Modalix worker target architecture mismatch")
        if worker.get("output_tensor_count") != 10:
            raise SimaEvidenceError("Modalix worker output tensor count mismatch")
        if worker.get("output_tensor_shapes") != EXPECTED_OUTPUT_SHAPES:
            raise SimaEvidenceError("Modalix worker output tensor shapes mismatch")
        raw_output_sha256 = worker.get("raw_output_sha256")
        if not isinstance(raw_output_sha256, str) or not _SHA256_RE.fullmatch(raw_output_sha256):
            raise SimaEvidenceError("Modalix worker raw-output digest is missing")
        if worker.get("decode_method") != (
            "YOLO26_ANCHOR_FREE_LTRB_SIGMOID_COCO80_CLASS_AWARE_NMS_V1"
        ):
            raise SimaEvidenceError("Modalix worker decode method mismatch")
        detections_raw = worker.get("detections")
        if not isinstance(detections_raw, list) or not detections_raw:
            raise SimaEvidenceError("Modalix worker returned no decoded detections")
        detections = [normalize_detection(item, index) for index, item in enumerate(detections_raw)]
        inferred_at = worker.get("inferred_at")
        evidence_material = "|".join(
            (str(request_nonce), str(source_sha256), raw_output_sha256, str(inferred_at))
        ).encode("utf-8")
        evidence_id = "modalix-" + hashlib.sha256(evidence_material).hexdigest()[:32]
        return {
            "schema": LIVE_EVIDENCE_SCHEMA,
            "evidence_kind": LIVE_EVIDENCE_KIND,
            "truth": "MEASURED_SPONSOR_RUNTIME",
            "measured": True,
            "captured_at": request_payload.get("captured_at"),
            "inferred_at": inferred_at,
            "model": request_payload.get("requested_model"),
            "runtime": f"PyNeat {worker['runtime_version']} / SiMa MLA",
            "device": self._config.hardware,
            "source": {
                "frame_id": request_payload.get("frame_id"),
                "source_id": request_payload.get("source_id"),
                "sha256": source_sha256,
                "media_type": request_payload.get("image_type"),
                "width": request_payload.get("width"),
                "height": request_payload.get("height"),
            },
            "detections": detections,
            "telemetry": {
                "source": "MODALIX_RUNTIME",
                "latency_ms": worker.get("mla_inference_ms"),
                "model_build_ms": worker.get("worker_startup_model_build_ms"),
                "preprocessing_ms": worker.get("preprocessing_ms"),
                "decode_ms": worker.get("decode_ms"),
            },
            "attestation": {
                "kind": "SIMA_MODALIX_RUNTIME",
                "runtime_verified": True,
                "device_verified": True,
                "evidence_id": evidence_id,
                "transport": "SSH_STRICT_HOST_KEY",
                "request_nonce": request_nonce,
                "model_sha256": self._config.model_sha256,
                "worker_sha256": self._worker_sha256,
                "raw_output_sha256": raw_output_sha256,
                "output_tensor_count": worker.get("output_tensor_count"),
                "output_tensor_shapes": worker.get("output_tensor_shapes"),
                "decode_method": worker.get("decode_method"),
                "confidence_floor": worker.get("confidence_floor"),
                "policy_confidence_threshold": worker.get("policy_confidence_threshold"),
                "nms_iou_threshold": worker.get("nms_iou_threshold"),
                "pre_nms_top_k": worker.get("pre_nms_top_k"),
                "post_nms_top_k": worker.get("post_nms_top_k"),
                "execution_status": worker.get("execution_status"),
                "wire_protocol": worker.get("wire_protocol"),
                "worker_instance_id": worker.get("worker_instance_id"),
                "model_load_count": worker.get("model_load_count"),
                "model_rebuilt_for_frame": worker.get("model_rebuilt_for_frame"),
                "request_sequence": worker.get("request_sequence"),
            },
            "notes": "Fresh frame executed by the target-side PyNeat runner and decoded from the same raw outputs.",
        }


class SimaLiveAdapter:
    """Per-frame, fail-closed bridge to SiMa MLA on Modalix.

    Fixture mode is deliberately simulated. Live mode has no fixture fallback:
    an unavailable backend, ImportError in an external runtime, or invalid proof
    is returned as BLOCKED/UNVERIFIED by the HTTP boundary.
    """

    def __init__(
        self,
        config: SimaAdapterConfig | None = None,
        *,
        backend: SimaFrameBackend | None = None,
    ) -> None:
        self.config = config or SimaAdapterConfig()
        if self.config.mode not in {"live", "fixture"}:
            raise ValueError("SiMa adapter mode must be live or fixture")
        if self.config.transport not in {"auto", "ssh", "http"}:
            raise ValueError("SiMa adapter transport must be auto, ssh, or http")
        self._configuration_error: str | None = None
        self.backend = backend
        configured_url = self.config.inference_url or os.environ.get(MODALIX_INFER_URL_ENV, "").strip()
        transport = self.config.transport
        if transport == "auto":
            transport = "http" if configured_url else ("ssh" if self.config.devkit_ip else "auto")
        if self.config.mode == "live" and self.backend is None and transport == "http":
            try:
                if not configured_url:
                    raise ValueError("Modalix HTTP transport requires an inference URL")
                self.backend = ModalixHttpBackend(
                    configured_url,
                    devkit_ip=self.config.devkit_ip,
                    timeout_sec=self.config.timeout_sec,
                )
            except ValueError as exc:
                self._configuration_error = str(exc)
        elif self.config.mode == "live" and self.backend is None and transport == "ssh":
            try:
                self.backend = ModalixSshPyNeatBackend(self.config)
            except ValueError as exc:
                self._configuration_error = str(exc)

    def health(self) -> dict[str, Any]:
        if self.config.mode == "fixture":
            return {
                "status": "DEGRADED",
                "truth": TRUTH_SIMULATED,
                "mode": "fixture",
                "model": self.config.model_name,
                "backend": "SIMULATED_FIXTURE",
            }
        if self._configuration_error:
            return {
                "status": "BLOCKED",
                "truth": TRUTH_UNVERIFIED,
                "mode": "live",
                "model": self.config.model_name,
                "backend": "INVALID_CONFIG",
            }
        backend_description = "NOT_CONFIGURED"
        if self.backend is not None:
            describe = getattr(self.backend, "describe", None)
            backend_description = describe() if callable(describe) else "CONFIGURED_FOR_PER_FRAME"
        return {
            "status": "READY" if self.backend is not None else "BLOCKED",
            "truth": TRUTH_UNVERIFIED,
            "mode": "live",
            "model": self.config.model_name,
            "backend": backend_description,
        }

    def infer(self, *, scenario: str, frame: FramePayload) -> dict[str, Any]:
        if not isinstance(scenario, str) or not scenario.strip() or len(scenario) > 96:
            raise ValueError("scenario must be a bounded string")
        if self.config.mode == "live":
            return self._infer_live(scenario=scenario, frame=frame)
        return self._infer_fixture(scenario=scenario, frame=frame)

    def _infer_fixture(self, *, scenario: str, frame: FramePayload) -> dict[str, Any]:
        detections = [
            SimaDetection("person", 0.912, (0.352, 0.156, 0.510, 0.781)),
            SimaDetection("forklift", 0.865, (0.650, 0.420, 0.890, 0.820), "fixture-track-02"),
        ]
        return {
            "schema": LIVE_EVIDENCE_SCHEMA,
            "evidence_kind": LIVE_EVIDENCE_KIND,
            "truth": TRUTH_SIMULATED,
            "measured": False,
            "captured_at": frame.captured_at,
            "inferred_at": utc_now().isoformat(),
            "model": self.config.model_name,
            "runtime": "DETERMINISTIC_FIXTURE",
            "device": "NO_MODALIX_DEVICE",
            "source": frame.source_provenance(),
            "detections": [d.to_dict() for d in detections],
            "telemetry": {},
            "attestation": {
                "kind": "SIMULATED_FIXTURE",
                "runtime_verified": False,
                "device_verified": False,
                "evidence_id": None,
            },
            "notes": f"Simulated fixture for {scenario}; never eligible for measured truth.",
        }

    def _infer_live(self, *, scenario: str, frame: FramePayload) -> dict[str, Any]:
        if self._configuration_error:
            raise SimaUnavailable("Modalix runtime configuration is invalid")
        if self.backend is None:
            raise SimaUnavailable("Modalix per-frame inference backend is not configured")

        request_nonce = secrets.token_hex(16)
        try:
            raw = self.backend.infer(
                {
                    "scenario": scenario,
                    "requested_model": self.config.model_name,
                    "request_nonce": request_nonce,
                    "source_sha256": frame.sha256,
                    **frame.to_transport(),
                }
            )
        except ImportError as exc:
            raise SimaUnavailable("SiMa runtime dependency is unavailable") from exc
        if not isinstance(raw, dict):
            raise SimaEvidenceError("Modalix backend must return a JSON object")
        if getattr(self.backend, "requires_strong_attestation", False):
            attestation = raw.get("attestation")
            if not isinstance(attestation, dict):
                raise SimaEvidenceError("Modalix strong attestation is missing")
            if attestation.get("request_nonce") != request_nonce:
                raise SimaEvidenceError("Modalix strong attestation nonce mismatch")
            if attestation.get("model_sha256") != self.config.model_sha256:
                raise SimaEvidenceError("Modalix strong attestation model mismatch")
            if attestation.get("output_tensor_count") != 10:
                raise SimaEvidenceError("Modalix strong attestation output count mismatch")
            if attestation.get("output_tensor_shapes") != EXPECTED_OUTPUT_SHAPES:
                raise SimaEvidenceError("Modalix strong attestation output shapes mismatch")
            raw_output_sha256 = attestation.get("raw_output_sha256")
            if not isinstance(raw_output_sha256, str) or not _SHA256_RE.fullmatch(raw_output_sha256):
                raise SimaEvidenceError("Modalix strong attestation raw-output digest is missing")
            if attestation.get("execution_status") != "REAL_TARGET_MLA_DECODE_SUCCESS":
                raise SimaEvidenceError("Modalix strong attestation execution status is invalid")
        valid, errors = validate_live_evidence(
            raw,
            source_bytes=frame.image_bytes,
            expected_frame_id=frame.frame_id,
            expected_source_id=frame.source_id,
            expected_model=self.config.model_name,
            expected_media_type=frame.image_type,
            expected_dimensions=(frame.width, frame.height),
        )
        if not valid:
            raise SimaEvidenceError("Modalix per-frame evidence rejected: " + "; ".join(errors))

        result = dict(raw)
        result["detections"] = [
            normalize_detection(item, index)
            for index, item in enumerate(raw.get("detections", []))
        ]
        return result


def make_sima_sidecar_handler(adapter: SimaLiveAdapter) -> type[BaseHTTPRequestHandler]:
    class SimaSidecarHandler(BaseHTTPRequestHandler):
        server_version = "GuardianSiMaSidecar/2.0"

        def log_message(self, fmt: str, *args: object) -> None:
            logger.info("[sima-sidecar] " + fmt, *args)

        def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path in {"/health", "/healthz"}:
                self._send_json(adapter.health())
                return
            self._send_json({"error": "unknown route"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/infer":
                self._send_json({"error": "unknown route"}, HTTPStatus.NOT_FOUND)
                return
            try:
                if self.headers.get_content_type().lower() != "application/json":
                    raise ValueError("Content-Type must be application/json")
                length = int(self.headers.get("Content-Length", "0") or "0")
                if length <= 0 or length > MAX_JSON_BODY_BYTES:
                    raise ValueError("frame request body is empty or exceeds the bounded contract")
                parsed = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(parsed, dict):
                    raise ValueError("frame request must be a JSON object")
                frame = FramePayload.from_json(parsed)
                result = adapter.infer(scenario=parsed.get("scenario", "default"), frame=frame)
                self._send_json(result)
            except SimaUnavailable as exc:
                self._send_json(
                    {"status": "BLOCKED", "truth": TRUTH_UNVERIFIED, "fail_closed": True, "error": str(exc)},
                    HTTPStatus.SERVICE_UNAVAILABLE,
                )
            except SimaEvidenceError as exc:
                self._send_json(
                    {"status": "BLOCKED", "truth": TRUTH_UNVERIFIED, "fail_closed": True, "error": str(exc)},
                    HTTPStatus.BAD_GATEWAY,
                )
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._send_json({"error": str(exc), "fail_closed": True}, HTTPStatus.BAD_REQUEST)

    return SimaSidecarHandler
