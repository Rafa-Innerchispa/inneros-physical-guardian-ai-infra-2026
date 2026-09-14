from __future__ import annotations

from typing import Any

from .engine import GuardianDemoEngine

EXPECTED_LIFECYCLE = [
    "PROPOSED",
    "AUTHORIZED",
    "EXECUTING",
    "EXECUTION_VERIFIED",
    "INTERRUPTED",
    "SAFE_STATE_VERIFIED",
    "REVERIFIED",
    "RESUMING",
    "RESUMED_VERIFIED",
]

LIVE_PHYSICAL_TRUTH = {
    "PRODUCT_HTTP_READBACK",
    "REAL_LOW_VOLTAGE_HARDWARE",
}


def run_judge_rehearsal(
    *,
    scenario: str = "restricted_zone_entry",
    runtime_id: str = "local-deterministic",
    require_live_physical: bool = False,
    require_measured_sponsor: bool = False,
) -> dict[str, Any]:
    """Exercise the exact governed lifecycle used in the judge demo.

    The default mode is an offline-safe rehearsal and is allowed to use fixtures.
    Strict flags turn the same harness into a truth gate for the onsite demo:
    simulated inference or simulated Physical I/O cannot accidentally pass as live.
    """

    engine = GuardianDemoEngine()
    checks: list[dict[str, Any]] = []

    proposed = engine.run(scenario, runtime_id=runtime_id)
    checks.append(
        {
            "name": "proposal_waits_for_human",
            "ok": proposed["current"]["status"] == "AWAITING_APPROVAL",
            "observed": proposed["current"]["status"],
        }
    )

    approved = engine.approve()
    checks.append(
        {
            "name": "approved_action_is_verified",
            "ok": approved["current"]["status"] == "VERIFIED",
            "observed": approved["current"]["status"],
        }
    )

    interrupted = engine.interrupt()
    checks.append(
        {
            "name": "interrupt_reaches_verified_safe_state",
            "ok": interrupted["current"]["status"] == "SAFE_STATE_VERIFIED"
            and interrupted["current"]["safe_state_verified"] is True,
            "observed": interrupted["current"]["status"],
        }
    )

    resume_blocked = False
    resume_error = ""
    try:
        engine.resume()
    except RuntimeError as exc:
        resume_blocked = True
        resume_error = str(exc)
    checks.append(
        {
            "name": "resume_fails_closed_before_reverification",
            "ok": resume_blocked,
            "observed": resume_error or "resume unexpectedly allowed",
        }
    )

    reverified = engine.reverify()
    checks.append(
        {
            "name": "safe_state_is_reverified",
            "ok": reverified["current"]["status"] == "REVERIFIED"
            and reverified["current"]["reverified"] is True,
            "observed": reverified["current"]["status"],
        }
    )

    resumed = engine.resume()
    current = resumed["current"]
    lifecycle = [event["state"] for event in current["lifecycle_events"]]
    detections_truth = str(current["truth"].get("detections", "UNKNOWN"))
    physical_truth = str(current["truth"].get("physical_io", "UNKNOWN"))
    evidence = resumed.get("latest_evidence") or {}

    checks.extend(
        [
            {
                "name": "resume_completes_with_verification",
                "ok": current["status"] == "RESUMED_VERIFIED" and current["verified"] is True,
                "observed": current["status"],
            },
            {
                "name": "lifecycle_order_is_exact",
                "ok": lifecycle == EXPECTED_LIFECYCLE,
                "observed": lifecycle,
            },
            {
                "name": "final_evidence_is_sealed",
                "ok": evidence.get("final") is True and bool(evidence.get("evidence_id")),
                "observed": evidence.get("evidence_id"),
            },
        ]
    )

    if require_live_physical:
        checks.append(
            {
                "name": "physical_io_is_live_and_verified",
                "ok": physical_truth in LIVE_PHYSICAL_TRUTH,
                "observed": physical_truth,
            }
        )

    if require_measured_sponsor:
        checks.append(
            {
                "name": "sponsor_inference_is_measured",
                "ok": detections_truth == "MEASURED_SPONSOR_RUNTIME",
                "observed": detections_truth,
            }
        )

    ok = all(bool(check["ok"]) for check in checks)
    return {
        "ok": ok,
        "mode": "STRICT_LIVE_GATE" if (require_live_physical or require_measured_sponsor) else "OFFLINE_REHEARSAL",
        "scenario": scenario,
        "runtime_id": runtime_id,
        "detections_truth": detections_truth,
        "physical_io_truth": physical_truth,
        "evidence_id": evidence.get("evidence_id"),
        "lifecycle": lifecycle,
        "checks": checks,
    }
