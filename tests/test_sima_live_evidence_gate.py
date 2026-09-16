from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import timedelta
from pathlib import Path

from guardian_demo.sima_contract import (
    ATTESTATION_KIND,
    LIVE_EVIDENCE_KIND,
    LIVE_EVIDENCE_SCHEMA,
    TELEMETRY_SOURCE,
    TRUTH_MEASURED,
    utc_now,
)

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
GATE_SCRIPT = SCRIPTS_DIR / "sima_live_evidence_gate.py"

spec = importlib.util.spec_from_file_location("sima_live_evidence_gate", GATE_SCRIPT)
gate_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate_module)

validate_evidence = gate_module.validate_evidence
validate_frame_evidence = gate_module.validate_frame_evidence
main = gate_module.main


def historical_record(source_bytes: bytes) -> dict:
    return {
        "schema": "inneros.guardian.sima.evidence.v1",
        "evidence_kind": "HISTORICAL_BENCHMARK",
        "truth": TRUTH_MEASURED,
        "measured": True,
        "hardware": "SiMa.ai Modalix DevKit MLSoC",
        "model": "yolo26m-seg-bf16-b1",
        "sample_count": 30,
        "metrics": {
            "latency_p50_ms": 27.6,
            "latency_p95_ms": 28.06,
            "fps": 36.23,
        },
        "source_json_sha256": hashlib.sha256(source_bytes).hexdigest(),
    }


def live_record(source_bytes: bytes, *, captured_at: str | None = None) -> dict:
    timestamp = captured_at or utc_now().isoformat()
    return {
        "schema": LIVE_EVIDENCE_SCHEMA,
        "evidence_kind": LIVE_EVIDENCE_KIND,
        "truth": TRUTH_MEASURED,
        "measured": True,
        "captured_at": timestamp,
        "inferred_at": utc_now().isoformat(),
        "model": "yolo26m-seg-bf16-b1",
        "runtime": "SiMa MLA 2.1.3",
        "device": "SiMa Modalix DevKit",
        "source": {
            "frame_id": "frame-gate-1",
            "source_id": "laptop-webcam",
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
            "media_type": "image/png",
            "width": 1,
            "height": 1,
        },
        "detections": [{"label": "person", "confidence": 0.92, "bbox": [0.1, 0.2, 0.7, 0.9]}],
        "telemetry": {"source": TELEMETRY_SOURCE, "latency_ms": 12.2, "fps": 40.0},
        "attestation": {
            "kind": ATTESTATION_KIND,
            "runtime_verified": True,
            "device_verified": True,
            "evidence_id": "proof-frame-gate-1",
        },
    }


def test_historical_gate_requires_kind_and_raw_source_file(tmp_path: Path) -> None:
    raw = b'{"benchmark":"raw"}'
    source = tmp_path / "raw.json"
    source.write_bytes(raw)
    record = historical_record(raw)

    valid, errors = validate_evidence(record, strict_measured=True, source_file_to_check=source)
    assert valid is True
    assert errors == []

    valid_without_source, errors_without_source = validate_evidence(record, strict_measured=True)
    assert valid_without_source is False
    assert any("raw source benchmark file" in error for error in errors_without_source)


def test_historical_benchmark_cannot_certify_a_live_frame(tmp_path: Path) -> None:
    raw = b"historical"
    source = tmp_path / "frame.png"
    source.write_bytes(raw)

    valid, errors = validate_frame_evidence(
        historical_record(raw),
        source_file_to_check=source,
    )
    assert valid is False
    assert any(LIVE_EVIDENCE_SCHEMA in error for error in errors)
    assert any("frame source provenance" in error for error in errors)


def test_live_gate_accepts_fresh_matching_source_bytes(tmp_path: Path) -> None:
    frame = b"current-frame-bytes"
    source = tmp_path / "frame.png"
    source.write_bytes(frame)

    valid, errors = validate_frame_evidence(live_record(frame), source_file_to_check=source)

    assert valid is True
    assert errors == []


def test_live_gate_rejects_stale_missing_source_and_malformed_detection(tmp_path: Path) -> None:
    frame = b"current-frame-bytes"
    record = live_record(
        frame,
        captured_at=(utc_now() - timedelta(minutes=3)).isoformat(),
    )
    record["detections"] = [
        {"label": "person", "confidence": 1.5, "bbox": [0.1, 0.1, 0.8, 0.8]},
        {"label": "person", "confidence": 0.8, "bbox": [0.9, 0.1, 0.2, 0.8]},
    ]

    valid, errors = validate_frame_evidence(record, source_file_to_check=None)

    assert valid is False
    assert any("captured_at is stale" in error for error in errors)
    assert any("requires the source frame bytes" in error for error in errors)
    assert any("confidence must be between 0 and 1" in error for error in errors)
    assert any("positive area" in error for error in errors)


def test_live_gate_rejects_fabricated_truth_or_missing_attestation(tmp_path: Path) -> None:
    frame = b"current-frame-bytes"
    source = tmp_path / "frame.png"
    source.write_bytes(frame)
    record = live_record(frame)
    record["truth"] = "SIMULATED_SPONSOR_SDK"
    record.pop("attestation")

    valid, errors = validate_frame_evidence(record, source_file_to_check=source)

    assert valid is False
    assert any("measured sponsor-runtime truth" in error for error in errors)
    assert any("runtime attestation" in error for error in errors)


def test_cli_supports_separate_historical_and_live_modes(tmp_path: Path) -> None:
    raw = b'{"benchmark":"raw"}'
    raw_file = tmp_path / "raw.json"
    raw_file.write_bytes(raw)
    historical_file = tmp_path / "historical.json"
    historical_file.write_text(json.dumps(historical_record(raw)), encoding="utf-8")
    assert main([str(historical_file), "--source-file", str(raw_file)]) == 0

    frame = b"current-frame-bytes"
    frame_file = tmp_path / "frame.png"
    frame_file.write_bytes(frame)
    live_file = tmp_path / "live.json"
    live_file.write_text(json.dumps(live_record(frame)), encoding="utf-8")
    assert main([str(live_file), "--live-frame", "--source-file", str(frame_file)]) == 0


def test_cli_execution_fails_on_missing_evidence_file() -> None:
    assert main(["/nonexistent/file.json"]) == 2
