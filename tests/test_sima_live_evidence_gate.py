from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
GATE_SCRIPT = SCRIPTS_DIR / "sima_live_evidence_gate.py"

spec = importlib.util.spec_from_file_location("sima_live_evidence_gate", GATE_SCRIPT)
gate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate_module)

validate_evidence = gate_module.validate_evidence
main = gate_module.main


def test_gate_accepts_valid_measured_evidence() -> None:
    valid_record = {
        "schema": "inneros.guardian.sima.evidence.v1",
        "truth": "MEASURED_SPONSOR_RUNTIME",
        "measured": True,
        "hardware": "SiMa.ai Modalix DevKit MLSoC",
        "model": "yolo26m-seg-bf16-b1",
        "sample_count": 30,
        "metrics": {
            "latency_p50_ms": 27.6,
            "latency_p95_ms": 28.06,
            "fps": 36.23,
        },
        "source_json_sha256": "0e699c16a18a195e1f31d23e40fb0f199a7df3315e76ff9d4be0752aae15ec72",
    }
    is_valid, errors = validate_evidence(valid_record, strict_measured=True)
    assert is_valid is True
    assert errors == []


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

    # But passes when simulated is allowed
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
        "sample_count": 1,  # too few samples
        "metrics": {
            "latency_p50_ms": 50.0,
            "latency_p95_ms": 20.0,  # p50 > p95 is invalid
        },
        "source_json_sha256": "c" * 64,
        "detections": [
            {
                "label": "person",
                "confidence": 1.5,  # > 1.0 invalid
                "bbox": [10, 20, 30, 40],
            }
        ],
    }
    is_valid, errors = validate_evidence(bad_metrics)
    assert is_valid is False
    assert any("sample_count must be an integer >= 3" in e for e in errors)
    assert any("cannot be greater than latency_p95_ms" in e for e in errors)
    assert any("invalid confidence" in e for e in errors)


def test_cli_execution_pass(tmp_path: Path) -> None:
    evidence_file = tmp_path / "valid_evidence.json"
    evidence_file.write_text(
        json.dumps({
            "schema": "inneros.guardian.sima.evidence.v1",
            "truth": "MEASURED_SPONSOR_RUNTIME",
            "measured": True,
            "hardware": "SiMa.ai Modalix DevKit MLSoC",
            "model": "yolo26m-seg-bf16-b1",
            "sample_count": 30,
            "metrics": {
                "latency_p50_ms": 27.6,
                "latency_p95_ms": 28.06,
                "fps": 36.23,
            },
            "source_json_sha256": "d" * 64,
        }),
        encoding="utf-8",
    )
    rc = main([str(evidence_file)])
    assert rc == 0


def test_cli_execution_fail_on_missing_file() -> None:
    rc = main(["/nonexistent/file.json"])
    assert rc == 2
