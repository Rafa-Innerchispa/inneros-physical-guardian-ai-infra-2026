from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "sima_live_evidence"

sys.path.insert(0, str(SCRIPTS))
import sima_live_evidence_gate as gate  # noqa: E402


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_live_schema_example_passes_gate() -> None:
    payload = _load("live_schema_example.json")
    now = datetime(2026, 9, 15, 19, 5, 0, tzinfo=timezone.utc)
    result = gate.validate_live_evidence(payload, now=now)
    assert result.ok is True
    assert result.exit_code() == 0


def test_simulated_fixture_rejected_as_live() -> None:
    payload = _load("simulated_fixture.json")
    result = gate.validate_live_evidence(payload)
    assert result.ok is False
    truth = next(check for check in result.checks if check.name == "truth_is_live")
    assert truth.ok is False


def test_simulated_fixture_allowed_when_not_require_live() -> None:
    payload = _load("simulated_fixture.json")
    result = gate.validate_live_evidence(payload, require_live=False)
    assert result.ok is True


def test_malformed_bbox_fails() -> None:
    payload = _load("live_schema_example.json")
    payload["detections"][0]["bbox"] = [0.5, 0.5, 0.4, 0.4]
    result = gate.validate_live_evidence(payload)
    assert result.ok is False
    detection = next(check for check in result.checks if check.name == "detection_shape")
    assert detection.ok is False


def test_confidence_out_of_range_fails() -> None:
    payload = _load("live_schema_example.json")
    payload["detections"][0]["confidence"] = 1.2
    result = gate.validate_live_evidence(payload)
    assert result.ok is False


def test_stale_frame_fails() -> None:
    payload = _load("live_schema_example.json")
    payload["frame_timestamp"] = "2026-09-15T18:00:00+00:00"
    now = datetime(2026, 9, 15, 19, 5, 0, tzinfo=timezone.utc)
    result = gate.validate_live_evidence(payload, now=now)
    assert result.ok is False
    fresh = next(check for check in result.checks if check.name == "frame_is_fresh")
    assert fresh.ok is False


def test_non_sima_runtime_fails() -> None:
    payload = _load("live_schema_example.json")
    payload["sponsor_runtime"] = "intel_openvino"
    result = gate.validate_live_evidence(payload)
    assert result.ok is False
    sponsor = next(check for check in result.checks if check.name == "sponsor_is_sima")
    assert sponsor.ok is False


def test_zero_detections_fails() -> None:
    payload = _load("live_schema_example.json")
    payload["detections"] = []
    result = gate.validate_live_evidence(payload)
    assert result.ok is False


def test_measured_metrics_without_provenance_fails() -> None:
    payload = _load("live_schema_example.json")
    payload.pop("metrics_provenance", None)
    result = gate.validate_live_evidence(payload)
    assert result.ok is False
    metrics = next(check for check in result.checks if check.name == "measured_metrics_have_provenance")
    assert metrics.ok is False


def test_cli_pass_and_fail_examples() -> None:
    pass_proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "sima_live_evidence_gate.py"), str(FIXTURES / "live_schema_example.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert pass_proc.returncode == 0
    assert "PASS" in pass_proc.stdout

    fail_proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "sima_live_evidence_gate.py"), str(FIXTURES / "simulated_fixture.json")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert fail_proc.returncode == 2
    assert "FAIL" in fail_proc.stdout
