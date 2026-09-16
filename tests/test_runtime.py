from __future__ import annotations

import pytest

from guardian_demo.runtime import DeterministicLocalRuntime, RUNTIME_SLOTS, runtime_catalog


def test_deterministic_runtime_returns_owned_fixture_truth_label() -> None:
    runtime = DeterministicLocalRuntime()
    result = runtime.infer(
        scenario="repeated_access_attempt",
        frame_ref="fixture://repeated_access_attempt/frame-001",
    )

    assert result.runtime_id == "local-deterministic"
    assert result.inference_truth == "SIMULATED_FIXTURE"
    assert result.runtime_overhead_ms >= 0
    assert len(result.detections) == 1
    assert result.detections[0].track_id == "track-08"


def test_all_declared_hardware_slots_are_unverified_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_var in (
        "GUARDIAN_SIMA_RUNTIME_URL",
        "GUARDIAN_QUALCOMM_RUNTIME_URL",
        "GUARDIAN_INTEL_RUNTIME_URL",
    ):
        monkeypatch.delenv(env_var, raising=False)

    catalog = runtime_catalog()
    sponsor_rows = [row for row in catalog if row["runtime_id"] != "local-deterministic"]

    assert {row["provider"] for row in sponsor_rows} == {"SiMa.ai", "Qualcomm", "Intel"}
    assert all(row["truth"] == "SPONSOR_RUNTIME_UNVERIFIED" for row in sponsor_rows)
    assert all(row["status"] == "OFFLINE" for row in sponsor_rows)


def test_sima_legacy_frame_reference_path_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="requires submitted frame bytes"):
        RUNTIME_SLOTS["sima-slot"].infer(
            scenario="loitering_after_hours",
            frame_ref="fixture://loitering_after_hours/frame-001",
        )


def test_sponsor_bridge_rejects_non_loopback_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GUARDIAN_SIMA_RUNTIME_URL", "https://example.com/runtime")
    slot = RUNTIME_SLOTS["sima-slot"]

    assert slot.status()["status"] == "INVALID_LOCAL_BRIDGE_CONFIG"
    with pytest.raises(RuntimeError, match="loopback-only"):
        slot.infer(scenario="loitering_after_hours", frame_ref="fixture://frame")
