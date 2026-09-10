from __future__ import annotations

import pytest

from guardian_demo.engine import GuardianDemoEngine
from guardian_demo.models import ProposedAction


def test_catalog_exposes_ready_fallback_and_fail_closed_sponsor_slots() -> None:
    engine = GuardianDemoEngine()
    catalog = engine.catalog()
    by_id = {row["runtime_id"]: row for row in catalog["runtimes"]}

    assert by_id["local-deterministic"]["status"] == "READY"
    assert by_id["local-deterministic"]["truth"] == "SIMULATED_FIXTURE"
    assert by_id["sima-slot"]["status"] == "AWAITING_ASSIGNED_HARDWARE_OR_SDK"
    assert by_id["qualcomm-slot"]["truth"] == "NOT_BENCHMARKED"
    assert by_id["intel-slot"]["truth"] == "NOT_BENCHMARKED"
    assert "unlock_door" in catalog["safety"]["denied_actions"]


def test_full_approve_flow_is_bounded_verified_and_evidenced() -> None:
    engine = GuardianDemoEngine()
    state = engine.run("loitering_after_hours")
    trace = state["current"]

    assert trace["status"] == "AWAITING_APPROVAL"
    assert trace["proposed_action"]["action_type"] == "beacon_warning"
    assert trace["truth"]["detections"] == "SIMULATED_FIXTURE"
    assert trace["truth"]["physical_io"] == "NOT_EXECUTED"
    assert trace["metrics"]["composition_to_proposal_ms"] >= 0
    assert [stage["stage"] for stage in trace["stages"]] == [
        "SEE",
        "UNDERSTAND",
        "DECIDE",
        "ACT",
        "VERIFY",
        "PROVE",
    ]

    approved = engine.approve()
    trace = approved["current"]
    evidence = approved["latest_evidence"]

    assert trace["status"] == "VERIFIED"
    assert trace["decision"] == "APPROVED"
    assert trace["verified"] is True
    assert trace["truth"]["physical_io"] == "SIMULATED_REFERENCE_IO"
    assert trace["metrics"]["approval_to_verification_ms"] >= 0
    assert evidence["evidence_id"].startswith("ev-")
    assert evidence["verified"] is True
    assert evidence["final"] is True
    assert evidence["preexisting_product_boundary"] == "Rafa-Innerchispa/inneros-physical-guardian"
    assert evidence["hackathon_composition_boundary"].endswith("inneros-physical-guardian-ai-infra-2026")


def test_reject_flow_records_safe_noop() -> None:
    engine = GuardianDemoEngine()
    engine.run("restricted_zone_entry")
    rejected = engine.reject()

    assert rejected["current"]["status"] == "REJECTED_SAFE"
    assert rejected["current"]["decision"] == "REJECTED"
    assert rejected["current"]["verified"] is False
    verify = next(stage for stage in rejected["current"]["stages"] if stage["stage"] == "VERIFY")
    assert verify["status"] == "safe_noop"
    assert rejected["latest_evidence"]["final"] is True


def test_sponsor_slot_cannot_be_selected_before_real_access() -> None:
    engine = GuardianDemoEngine()
    with pytest.raises(RuntimeError, match="cannot run until official hardware/SDK access"):
        engine.run("loitering_after_hours", "sima-slot")


def test_dangerous_action_cannot_pass_approval_gate() -> None:
    engine = GuardianDemoEngine()
    engine.run("loitering_after_hours")
    assert engine.current is not None
    engine.current.proposed_action = ProposedAction(
        action_id="action-test-denied",
        action_type="unlock_door",
        target="door-controller",
        reason="test must fail closed",
    )

    with pytest.raises(PermissionError, match="denied"):
        engine.approve()
