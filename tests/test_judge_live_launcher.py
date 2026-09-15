from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
LAUNCHER_SCRIPT = SCRIPTS_DIR / "judge_live_launcher.py"

spec = importlib.util.spec_from_file_location("judge_live_launcher", LAUNCHER_SCRIPT)
launcher_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher_module)

launch_live_stack = launcher_module.launch_live_stack
stop_scoped_services = launcher_module.stop_scoped_services
validate_prerequisites = launcher_module.validate_prerequisites
main = launcher_module.main


def test_prerequisites_validation_rejects_historical_benchmark_for_strict_live() -> None:
    ok, errors = validate_prerequisites(strict_live=True)
    assert ok is False
    assert any("HISTORICAL_BENCHMARK" in e or "MEASURED_SPONSOR_RUNTIME" in e for e in errors)


def test_prerequisites_validation_fail_missing_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher_module, "EVIDENCE_FILE", tmp_path / "nonexistent.json")
    ok, errors = validate_prerequisites(strict_live=True)
    assert ok is False
    assert any("Evidence file missing" in e for e in errors)


def test_strict_live_launch_blocks_without_target_proof() -> None:
    res = launch_live_stack(
        sidecar_port=18890,
        demo_port=18000,
        strict_live=True,
    )
    assert res["status"] == "BLOCKED"
    assert res.get("pids", []) == []
    assert any("HISTORICAL_BENCHMARK" in e or "MEASURED_SPONSOR_RUNTIME" in e for e in res["errors"])

    stopped = stop_scoped_services()
    assert stopped == {}


def test_cli_stop_and_status() -> None:
    stop_scoped_services()
    rc_status = main(["--status", "--sidecar-port", "19990", "--demo-port", "19991"])
    assert rc_status == 1

    rc_stop = main(["--stop"])
    assert rc_stop == 0
