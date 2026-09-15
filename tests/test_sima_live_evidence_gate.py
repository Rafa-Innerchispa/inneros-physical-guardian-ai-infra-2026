from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
GATE_SCRIPT = SCRIPTS_DIR / "sima_live_evidence_gate.py"

spec = importlib.util.spec_from_file_location("sima_live_evidence_gate", GATE_SCRIPT)
gate_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gate_module
spec.loader.exec_module(gate_module)

validate_evidence = gate_module.validate_evidence
main = gate_module.main


def test_gate_accepts_valid_measured_evidence_with_source_proof(tmp_path: Path) -> None:
    source_file = tmp_path / "real_inference_results.json"
    source_file.write_text(
        json.dumps({"target": "modalix", "frames": [{"frame_ref": "cam-01/frame-001"}]}),
        encoding="utf-8",
    )
    source_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
    valid_record = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "captured_at": "2026-09-15T21:49:00+00:00",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "certifies_live_frames": True,
        "live_telemetry": True,
        "hardware": "SiMa.ai Modalix DevKit MLSoC",
        "model": "yolo26m-seg-bf16-b1",
        "sample_count": 30,
        "metrics": {
            "latency_p50_ms": 27.6,
            "latency_p95_ms": 28.06,
            "fps": 36.23,
        },
        "source_json_sha256": source_sha,
    }
    is_valid, errors = validate_evidence(
        valid_record,
        strict_measured=True,
        source_file_to_check=source_file,
    )
    assert is_valid is True
    assert errors == []


def test_gate_rejects_strict_live_without_target_source_proof() -> None:
    record = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "captured_at": "2026-09-15T21:49:00+00:00",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "certifies_live_frames": True,
        "live_telemetry": True,
        "hardware": "SiMa.ai Modalix DevKit MLSoC",
        "model": "yolo26m-seg-bf16-b1",
        "sample_count": 30,
        "metrics": {"latency_p50_ms": 27.6, "latency_p95_ms": 28.06, "fps": 36.23},
        "source_json_sha256": "d" * 64,
    }
    is_valid, errors = validate_evidence(record, strict_measured=True)
    assert is_valid is False
    assert any("source" in err.lower() and "proof" in err.lower() for err in errors)


def test_gate_rejects_stale_or_missing_freshness_for_strict_live() -> None:
    stale_record = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "captured_at": "2026-01-01T00:00:00+00:00",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "certifies_live_frames": True,
        "live_telemetry": True,
        "hardware": "SiMa.ai Modalix DevKit MLSoC",
        "model": "yolo26m-seg-bf16-b1",
        "sample_count": 30,
        "metrics": {"latency_p50_ms": 27.6, "latency_p95_ms": 28.06, "fps": 36.23},
        "source_json_sha256": "e" * 64,
    }
    missing_timestamp = dict(stale_record)
    missing_timestamp.pop("captured_at")

    for candidate in (stale_record, missing_timestamp):
        is_valid, errors = validate_evidence(candidate, strict_measured=True)
        assert is_valid is False
        assert any("captured_at" in err or "fresh" in err.lower() or "stale" in err.lower() for err in errors)


def test_gate_rejects_simulated_in_strict_mode() -> None:
    simulated_record = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "truth": "SIMULATED_SPONSOR_SDK",
        "measured": False,
        "hardware": "SiMa.ai Modalix DevKit MLSoC",
        "model": "yolo26m-seg-bf16-b1",
        "sample_count": 10,
        "metrics": {
            "latency_p50_ms": 5.0,
            "latency_p95_ms": 7.0,
        },
        "source_json_sha256": "a" * 64,
    }
    is_valid, errors = validate_evidence(simulated_record, strict_measured=True)
    assert is_valid is False
    assert any("Strict measured mode requires truth='MEASURED_SPONSOR_RUNTIME'" in e for e in errors)

    is_valid_allowed, _ = validate_evidence(simulated_record, strict_measured=False)
    assert is_valid_allowed is True


def test_gate_rejects_invalid_schema() -> None:
    bad_record = {
        "schema": "wrong.schema.v99",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "hardware": "SiMa Modalix",
        "model": "yolo26m",
        "sample_count": 5,
        "metrics": {"latency_p50_ms": 10.0, "latency_p95_ms": 12.0},
        "source_json_sha256": "b" * 64,
    }
    is_valid, errors = validate_evidence(bad_record)
    assert is_valid is False
    assert any("Invalid schema" in e for e in errors)


def test_gate_rejects_invalid_metrics_or_confidence() -> None:
    bad_metrics = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "hardware": "SiMa Modalix",
        "model": "yolo26m",
        "sample_count": 1,
        "metrics": {
            "latency_p50_ms": 50.0,
            "latency_p95_ms": 20.0,
        },
        "source_json_sha256": "c" * 64,
        "detections": [
            {
                "label": "person",
                "confidence": 1.5,
                "bbox": [10, 20, 30, 40],
            }
        ],
    }
    is_valid, errors = validate_evidence(bad_metrics)
    assert is_valid is False
    assert any("sample_count must be an integer >= 3" in e for e in errors)
    assert any("cannot be greater than latency_p95_ms" in e for e in errors)
    assert any("invalid confidence" in e for e in errors)


def test_gate_rejects_malformed_bbox_semantics() -> None:
    bad_bbox = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "hardware": "SiMa Modalix",
        "model": "yolo26m",
        "sample_count": 3,
        "metrics": {"latency_p50_ms": 20.0, "latency_p95_ms": 21.0},
        "source_json_sha256": "f" * 64,
        "detections": [
            {"label": "person", "confidence": 0.7, "bbox": [0.8, 0.2, 0.1, 0.9]},
            {"label": "forklift", "confidence": 0.7, "bbox": [-0.1, 0.2, 0.4, 0.5]},
        ],
    }
    is_valid, errors = validate_evidence(bad_bbox)
    assert is_valid is False
    assert any("bbox" in err.lower() for err in errors)


def test_cli_execution_pass(tmp_path: Path) -> None:
    evidence_file = tmp_path / "valid_evidence.json"
    source_file = tmp_path / "real_inference_results.json"
    source_file.write_text(json.dumps({"target": "modalix", "frames": ["frame-100"]}), encoding="utf-8")
    source_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
    evidence_file.write_text(
        json.dumps({
            "schema": "inneros.guardian.sima.evidence.v1",
            "captured_at": "2026-09-15T21:49:00+00:00",
            "truth": "MEASURED_SPONSOR_RUNTIME",
            "measured": True,
            "certifies_live_frames": True,
            "live_telemetry": True,
            "hardware": "SiMa.ai Modalix DevKit MLSoC",
            "model": "yolo26m-seg-bf16-b1",
            "sample_count": 30,
            "metrics": {
                "latency_p50_ms": 27.6,
                "latency_p95_ms": 28.06,
                "fps": 36.23,
            },
            "source_json_sha256": source_sha,
        }),
        encoding="utf-8",
    )
    rc = main([str(evidence_file), "--source-file", str(source_file)])
    assert rc == 0


def test_cli_execution_fail_on_missing_file() -> None:
    rc = main(["/nonexistent/file.json"])
    assert rc == 2


def test_repo_evidence_is_historical_benchmark_not_live_telemetry() -> None:
    evidence_file = Path(__file__).resolve().parents[1] / "docs" / "sima_measured_evidence.json"
    data = json.loads(evidence_file.read_text(encoding="utf-8"))

    assert data["truth"] == "HISTORICAL_BENCHMARK"
    assert data["certifies_live_frames"] is False
    assert data["live_telemetry"] is False
    assert data["metrics"]["latency_p50_ms"] == 27.6
    assert data["metrics"]["latency_p95_ms"] == 28.06
    assert data["metrics"]["fps"] == 36.23

    is_valid, errors = validate_evidence(data, strict_measured=True)
    assert is_valid is False
    assert any("strict" in err.lower() or "historical" in err.lower() for err in errors)
