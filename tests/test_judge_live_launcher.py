from __future__ import annotations

import importlib.util
import json
import time
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


def test_prerequisites_validation_pass() -> None:
    ok, errors = validate_prerequisites(strict_live=True)
    assert ok is True
    assert errors == []


def test_prerequisites_validation_fail_missing_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher_module, "EVIDENCE_FILE", tmp_path / "nonexistent.json")
    ok, errors = validate_prerequisites(strict_live=True)
    assert ok is False
    assert any("Evidence file missing" in e for e in errors)


def test_launch_and_cleanup_lifecycle() -> None:
    # 1. Launch on high test ports to avoid conflicts
    res = launch_live_stack(
        sidecar_port=18890,
        demo_port=18000,
        strict_live=True,
    )
    try:
        assert res["status"] == "READY"
        assert "18890" in res["sidecar_url"]
        assert "18000" in res["demo_ui_url"]
        assert len(res["pids"]) >= 1

        # 2. Test idempotent launch reuses running services
        res_reuse = launch_live_stack(
            sidecar_port=18890,
            demo_port=18000,
            strict_live=True,
        )
        assert res_reuse["status"] == "READY"
        assert "reused" in res_reuse["sidecar_state"]
        assert "reused" in res_reuse["demo_state"]

    finally:
        # 3. Clean scoped shutdown
        stopped = stop_scoped_services()
        assert len(stopped) >= 1
        assert all("stopped" in val or "terminated" in val for val in stopped.values())


def test_cli_stop_and_status() -> None:
    # CLI --status when stopped
    stop_scoped_services()
    rc_status = main(["--status", "--sidecar-port", "19990", "--demo-port", "19991"])
    assert rc_status == 1  # Exit code 1 when offline / blocked

    # CLI --stop is safe when nothing running
    rc_stop = main(["--stop"])
    assert rc_stop == 0
