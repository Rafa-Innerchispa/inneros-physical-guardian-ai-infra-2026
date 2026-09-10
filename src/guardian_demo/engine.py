from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from .models import DemoTrace, ProposedAction
from .runtime import RUNTIME_SLOTS, runtime_catalog, runtime_result_to_dict


SCENARIOS: dict[str, dict[str, Any]] = {
    "loitering_after_hours": {
        "title": "After-hours loitering",
        "event": "Motion persists inside restricted lobby after closing time",
        "zone": "restricted-lobby",
        "severity": "high",
        "reason_codes": ["AFTER_HOURS", "DWELL_THRESHOLD", "RESTRICTED_ZONE"],
        "dwell_seconds": 48,
        "action": "beacon_warning",
        "target": "reference-low-voltage-beacon",
    },
    "repeated_access_attempt": {
        "title": "Repeated access attempt",
        "event": "Repeated presence detected at service entry within policy window",
        "zone": "service-entry",
        "severity": "medium",
        "reason_codes": ["REPEATED_PRESENCE", "ACCESS_WINDOW", "REVIEW_REQUIRED"],
        "attempts": 3,
        "action": "notify_operator",
        "target": "operator-console",
    },
    "restricted_zone_entry": {
        "title": "Restricted equipment zone entry",
        "event": "Tracked person crosses into equipment-only zone",
        "zone": "equipment-zone",
        "severity": "high",
        "reason_codes": ["ZONE_TRANSITION", "RESTRICTED_ZONE", "POLICY_MATCH"],
        "action": "dmx_attention",
        "target": "reference-attention-light",
    },
}

ALLOWED_ACTIONS = {"beacon_warning", "notify_operator", "dmx_attention"}
DENIED_ACTIONS = {"unlock_door", "disable_alarm", "arbitrary_shell", "open_gate"}


class GuardianDemoEngine:
    """Hackathon composition engine.

    The permanent Guardian product owns camera, perception, tracking, temporal,
    policy and physical-I/O contracts. This class only composes a bounded judge
    demonstration and labels simulated vs measured evidence explicitly.
    """

    def __init__(self) -> None:
        self.current: DemoTrace | None = None
        self.latest_evidence: dict[str, Any] | None = None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def catalog(self) -> dict[str, Any]:
        return {
            "scenarios": [
                {"id": scenario_id, "title": config["title"], "severity": config["severity"]}
                for scenario_id, config in SCENARIOS.items()
            ],
            "runtimes": runtime_catalog(),
            "safety": {
                "allowed_actions": sorted(ALLOWED_ACTIONS),
                "denied_actions": sorted(DENIED_ACTIONS),
                "approval_required": True,
            },
        }

    def reset(self) -> dict[str, Any]:
        self.current = None
        self.latest_evidence = None
        return self.state()

    def state(self) -> dict[str, Any]:
        return {
            "mode": "JUDGE_DEMO",
            "build_window": "LIVE",
            "current": self.current.to_dict() if self.current else None,
            "latest_evidence": self.latest_evidence,
        }

    def run(self, scenario: str, runtime_id: str = "local-deterministic") -> dict[str, Any]:
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        if runtime_id not in RUNTIME_SLOTS:
            raise ValueError(f"unknown runtime: {runtime_id}")

        config = SCENARIOS[scenario]
        trace = DemoTrace(
            trace_id=f"trace-{uuid4().hex[:12]}",
            scenario=scenario,
            started_at=self._now(),
            runtime_id=runtime_id,
            status="AWAITING_APPROVAL",
            truth={
                "camera_event": "SIMULATED_FIXTURE",
                "detections": "PENDING_RUNTIME",
                "temporal_reasoning": "DETERMINISTIC_RULE",
                "policy": "DETERMINISTIC_RULE",
                "physical_io": "NOT_EXECUTED",
                "timings": "MEASURED_COMPOSITION_OVERHEAD_ONLY",
            },
        )

        started = perf_counter()
        trace.stages.append(
            {
                "stage": "SEE",
                "status": "complete",
                "summary": config["event"],
                "source": "offline-owned-fixture",
                "truth": "SIMULATED_FIXTURE",
            }
        )

        inference = RUNTIME_SLOTS[runtime_id].infer(
            scenario=scenario,
            frame_ref=f"fixture://{scenario}/frame-001",
        )
        trace.truth["detections"] = inference.inference_truth
        trace.stages.append(
            {
                "stage": "UNDERSTAND",
                "status": "complete",
                "summary": f"{len(inference.detections)} tracked object(s) normalized",
                "runtime": runtime_result_to_dict(inference),
                "truth": inference.inference_truth,
            }
        )

        trace.stages.append(
            {
                "stage": "DECIDE",
                "status": "complete",
                "summary": f"Policy matched: {', '.join(config['reason_codes'])}",
                "severity": config["severity"],
                "reason_codes": config["reason_codes"],
                "truth": "DETERMINISTIC_RULE",
            }
        )

        action = ProposedAction(
            action_id=f"action-{uuid4().hex[:10]}",
            action_type=config["action"],
            target=config["target"],
            reason=config["event"],
        )
        trace.proposed_action = action
        trace.stages.append(
            {
                "stage": "ACT",
                "status": "blocked_on_human_approval",
                "summary": f"Proposed bounded action: {action.action_type}",
                "truth": "NOT_EXECUTED",
            }
        )
        trace.stages.append(
            {
                "stage": "VERIFY",
                "status": "pending",
                "summary": "Awaiting action execution and readback",
                "truth": "NOT_EXECUTED",
            }
        )
        trace.stages.append(
            {
                "stage": "PROVE",
                "status": "pending",
                "summary": "Evidence bundle finalizes after operator decision",
                "truth": "PARTIAL",
            }
        )
        trace.metrics["composition_to_proposal_ms"] = round((perf_counter() - started) * 1000.0, 3)
        trace.metrics["runtime_round_trip_ms"] = inference.runtime_overhead_ms
        self.current = trace
        self.latest_evidence = self._make_evidence(final=False)
        return self.state()

    def approve(self) -> dict[str, Any]:
        if not self.current or not self.current.proposed_action:
            raise RuntimeError("no proposed action to approve")
        if self.current.status != "AWAITING_APPROVAL":
            raise RuntimeError(f"trace is not awaiting approval: {self.current.status}")

        action = self.current.proposed_action
        if action.action_type in DENIED_ACTIONS or action.action_type not in ALLOWED_ACTIONS:
            raise PermissionError(f"action denied by bounded demo policy: {action.action_type}")

        started = perf_counter()
        self.current.decision = "APPROVED"
        self.current.truth["physical_io"] = "SIMULATED_REFERENCE_IO"
        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                stage.update(
                    status="complete",
                    summary=f"Reference I/O accepted {action.action_type}",
                    truth="SIMULATED_REFERENCE_IO",
                )
            elif stage["stage"] == "VERIFY":
                stage.update(
                    status="complete",
                    summary=f"Readback matched expected state for {action.target}",
                    truth="SIMULATED_REFERENCE_IO",
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="complete",
                    summary="Forensic evidence bundle sealed",
                    truth="MEASURED_AND_LABELED",
                )

        self.current.verified = True
        self.current.status = "VERIFIED"
        self.current.metrics["approval_to_verification_ms"] = round((perf_counter() - started) * 1000.0, 3)
        self.latest_evidence = self._make_evidence(final=True)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def reject(self) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no active trace")
        if self.current.status != "AWAITING_APPROVAL":
            raise RuntimeError(f"trace is not awaiting approval: {self.current.status}")

        self.current.decision = "REJECTED"
        self.current.status = "REJECTED_SAFE"
        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                stage.update(
                    status="rejected",
                    summary="Operator rejected action; no physical output issued",
                    truth="NOT_EXECUTED",
                )
            elif stage["stage"] == "VERIFY":
                stage.update(
                    status="safe_noop",
                    summary="Verified no action was issued",
                    truth="DETERMINISTIC_RULE",
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="complete",
                    summary="Rejected decision sealed in evidence bundle",
                    truth="MEASURED_AND_LABELED",
                )
        self.latest_evidence = self._make_evidence(final=True)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def _make_evidence(self, *, final: bool) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no trace available")
        body = {
            "schema": "inneros.guardian.hackathon.evidence.v1",
            "trace_id": self.current.trace_id,
            "scenario": self.current.scenario,
            "runtime_id": self.current.runtime_id,
            "status": self.current.status,
            "decision": self.current.decision,
            "verified": self.current.verified,
            "stages": self.current.stages,
            "metrics": self.current.metrics,
            "truth": self.current.truth,
            "preexisting_product_boundary": "Rafa-Innerchispa/inneros-physical-guardian",
            "hackathon_composition_boundary": "Rafa-Innerchispa/inneros-physical-guardian-ai-infra-2026",
            "final": final,
            "sealed_at": self._now(),
        }
        digest_source = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evidence_id = "ev-" + hashlib.sha256(digest_source).hexdigest()[:20]
        return {"evidence_id": evidence_id, **body}
