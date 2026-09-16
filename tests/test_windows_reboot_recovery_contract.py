from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "windows_reboot_recovery.ps1").read_text(encoding="utf-8")


def test_windows_recovery_does_not_start_or_fake_sima() -> None:
    assert "does not start, SSH into, reconfigure" in SCRIPT
    assert 'Remove-Item Env:\\GUARDIAN_SIMA_RUNTIME_URL' in SCRIPT
    assert '"OFFLINE_UNVERIFIED"' in SCRIPT
    assert "starts_sima_hardware = $false" in SCRIPT
    assert "uses_historical_evidence_as_live = $false" in SCRIPT


def test_windows_recovery_refuses_to_kill_unknown_port_owner() -> None:
    assert "Refusing to kill or replace an unknown process" in SCRIPT
    assert "kills_unknown_processes = $false" in SCRIPT


def test_windows_recovery_loads_only_guardian_prefixed_private_config() -> None:
    assert "^GUARDIAN_[A-Z0-9_]+$" in SCRIPT
    assert "$env:LOCALAPPDATA" in SCRIPT
    assert "guardian-recovery.env" in SCRIPT
    assert "secrets_written_to_repo = $false" in SCRIPT


def test_windows_recovery_reports_camera_sima_and_guardian_state() -> None:
    assert "/api/health" in SCRIPT
    assert "/api/system/status" in SCRIPT
    assert "/api/camera/sources" in SCRIPT
    assert "camera_configured" in SCRIPT
    assert "sima_online" in SCRIPT
    assert "guardian_ready" in SCRIPT
