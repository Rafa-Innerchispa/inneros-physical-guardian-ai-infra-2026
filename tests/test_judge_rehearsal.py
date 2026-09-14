from __future__ import annotations

import pytest

from guardian_demo.physical_io import ENV_VAR as PHYSICAL_IO_ENV
from guardian_demo.rehearsal import EXPECTED_LIFECYCLE, run_judge_rehearsal


def _clear_live_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(PHYSICAL_IO_ENV, raising=False)
    monkeypatch.delenv("GUARDIAN_SIMA_RUNTIME_URL", raising=False)


def test_offline_rehearsal_proves_governed_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_live_env(monkeypatch)
    result = run_judge_rehearsal()

    assert result["ok"] is True
    assert result["mode"] == "OFFLINE_REHEARSAL"
    assert result["lifecycle"] == EXPECTED_LIFECYCLE
    assert result["detections_truth"] == "SIMULATED_FIXTURE"
    assert result["physical_io_truth"] == "SIMULATED_REFERENCE_IO"
    assert result["evidence_id"]
    assert all(check["ok"] for check in result["checks"])


def test_strict_physical_gate_rejects_simulated_reference_io(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_live_env(monkeypatch)
    result = run_judge_rehearsal(require_live_physical=True)

    assert result["ok"] is False
    strict = next(check for check in result["checks"] if check["name"] == "physical_io_is_live_and_verified")
    assert strict["ok"] is False
    assert strict["observed"] == "SIMULATED_REFERENCE_IO"


def test_strict_sponsor_gate_rejects_fixture_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_live_env(monkeypatch)
    result = run_judge_rehearsal(require_measured_sponsor=True)

    assert result["ok"] is False
    strict = next(check for check in result["checks"] if check["name"] == "sponsor_inference_is_measured")
    assert strict["ok"] is False
    assert strict["observed"] == "SIMULATED_FIXTURE"
