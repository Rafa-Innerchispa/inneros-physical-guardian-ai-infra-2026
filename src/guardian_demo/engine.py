from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from .enrichment import GLOBAL_ENRICHMENT_ENGINE
from .frame_input import FramePayload
from .models import DemoTrace, ProposedAction
from .physical_io import PHYSICAL_IO
from .runtime import RUNTIME_SLOTS, runtime_catalog, runtime_result_to_dict
from .sima_contract import TRUTH_MEASURED, TRUTH_UNVERIFIED


SCENARIOS: dict[str, dict[str, Any]] = {
    "loitering_after_hours": {
        "title": "After-hours loitering",
        "event": "Motion persists inside restricted lobby after closing time",
        "zone": "restricted-lobby",
        "severity": "high",
        "reason_codes": ["AFTER_HOURS", "DWELL_THRESHOLD", "RESTRICTED_ZONE"],
        "required_labels": ["person"],
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
        "required_labels": ["person"],
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
        "required_labels": ["person"],
        "action": "dmx_attention",
        "target": "reference-attention-light",
    },
}

ALLOWED_ACTIONS = {"beacon_warning", "notify_operator", "dmx_attention"}
DENIED_ACTIONS = {"unlock_door", "disable_alarm", "arbitrary_shell", "open_gate"}
MIN_LIVE_POLICY_CONFIDENCE = 0.25


class GuardianDemoEngine:
    """Hackathon composition engine with an auditable interruptible action lifecycle.

    The permanent Guardian product owns camera, perception, tracking, temporal,
    policy and physical-I/O contracts. This class composes a bounded judge demo,
    labels simulated vs measured evidence explicitly, and adds event-specific
    human governance around interruption, safe state, re-verification and resume.
    """

    def __init__(self) -> None:
        self.current: DemoTrace | None = None
        self.latest_evidence: dict[str, Any] | None = None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_lifecycle(self, state: str, summary: str, truth: str) -> None:
        if not self.current:
            raise RuntimeError("no active trace")
        self.current.lifecycle_events.append(
            {
                "state": state,
                "at": self._now(),
                "summary": summary,
                "truth": truth,
            }
        )

    def catalog(self) -> dict[str, Any]:
        return {
            "scenarios": [
                {"id": scenario_id, "title": config["title"], "severity": config["severity"]}
                for scenario_id, config in SCENARIOS.items()
            ],
            "runtimes": runtime_catalog(),
            "physical_io": PHYSICAL_IO.status(),
            "safety": {
                "allowed_actions": sorted(ALLOWED_ACTIONS),
                "denied_actions": sorted(DENIED_ACTIONS),
                "approval_required": True,
                "resume_requires_reverification": True,
                "interrupt_enters_verified_safe_state": True,
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
        runtime_dict = runtime_result_to_dict(inference)
        enriched_dets = GLOBAL_ENRICHMENT_ENGINE.enrich_detections(runtime_dict.get("detections", []))
        runtime_dict["enriched_detections"] = enriched_dets
        trace.stages.append(
            {
                "stage": "UNDERSTAND",
                "status": "complete",
                "summary": f"{len(inference.detections)} tracked object(s) normalized",
                "runtime": runtime_dict,
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
        self._record_lifecycle(
            "PROPOSED",
            "Bounded action proposed; explicit human authorization is required",
            "DETERMINISTIC_RULE",
        )
        self.latest_evidence = self._make_evidence(final=False)
        return self.state()

    def run_frame(
        self,
        *,
        scenario: str,
        runtime_id: str,
        frame: FramePayload,
        source_truth: str,
    ) -> dict[str, Any]:
        """Run one submitted frame through the strict sponsor boundary.

        Failure is represented as an evidence-bearing blocked trace. No policy or
        approval proposal is created until matching measured per-frame proof has
        crossed both the sidecar and composition-layer validators.
        """

        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario: {scenario}")
        if runtime_id != "sima-slot":
            raise ValueError("camera frames must use the SiMa per-frame runtime")

        config = SCENARIOS[scenario]
        started = perf_counter()
        trace = DemoTrace(
            trace_id=f"trace-{uuid4().hex[:12]}",
            scenario=scenario,
            started_at=self._now(),
            runtime_id=runtime_id,
            status="INFERENCE_PENDING",
            frame_source={
                **frame.source_provenance(),
                "captured_at": frame.captured_at,
                "truth": source_truth,
            },
            truth={
                "camera_event": source_truth,
                "detections": TRUTH_UNVERIFIED,
                "temporal_reasoning": "PENDING_VERIFIED_PERCEPTION",
                "policy": "PENDING_VERIFIED_PERCEPTION",
                "physical_io": "NOT_EXECUTED",
                "timings": "NO_MODALIX_TELEMETRY",
            },
            stages=[
                {
                    "stage": "SEE",
                    "status": "complete",
                    "summary": f"Bounded frame accepted from allowlisted source {frame.source_id}",
                    "truth": source_truth,
                },
                {
                    "stage": "PERCEIVE",
                    "status": "running",
                    "summary": "Awaiting matching Modalix per-frame evidence",
                    "truth": TRUTH_UNVERIFIED,
                },
                {"stage": "UNDERSTAND", "status": "pending", "summary": "Temporal context locked", "truth": "PENDING"},
                {"stage": "DECIDE", "status": "pending", "summary": "Policy locked", "truth": "PENDING"},
                {"stage": "APPROVAL", "status": "pending", "summary": "No action proposed", "truth": "NOT_REQUESTED"},
                {"stage": "ACT", "status": "pending", "summary": "No action proposed", "truth": "NOT_EXECUTED"},
                {"stage": "VERIFY", "status": "pending", "summary": "No action to verify", "truth": "NOT_EXECUTED"},
                {"stage": "PROVE", "status": "pending", "summary": "Draft evidence only", "truth": "PARTIAL"},
            ],
        )
        self.current = trace

        runtime = RUNTIME_SLOTS[runtime_id]
        try:
            infer_frame = getattr(runtime, "infer_frame")
            inference = infer_frame(scenario=scenario, frame=frame)
        except (AttributeError, RuntimeError) as exc:
            trace.status = "INFERENCE_BLOCKED"
            trace.stages[1].update(
                status="blocked",
                summary=str(exc),
                truth=TRUTH_UNVERIFIED,
            )
            trace.metrics["frame_to_blocked_ms"] = round((perf_counter() - started) * 1000.0, 3)
            self._record_lifecycle(
                "INFERENCE_BLOCKED",
                "Per-frame SiMa proof was unavailable or invalid; policy and action remain locked",
                TRUTH_UNVERIFIED,
            )
            self.latest_evidence = self._make_evidence(final=False)
            return self.state()

        if inference.inference_truth != TRUTH_MEASURED:
            trace.status = "INFERENCE_BLOCKED"
            trace.stages[1].update(
                status="blocked",
                summary="Sponsor response was not verified as measured per-frame inference",
                truth=TRUTH_UNVERIFIED,
            )
            self._record_lifecycle(
                "INFERENCE_BLOCKED",
                "Non-measured inference cannot advance the live policy pipeline",
                TRUTH_UNVERIFIED,
            )
            self.latest_evidence = self._make_evidence(final=False)
            return self.state()

        runtime_dict = runtime_result_to_dict(inference)
        enriched_dets = GLOBAL_ENRICHMENT_ENGINE.enrich_detections(
            runtime_dict.get("detections", []),
            image_bytes=frame.image_bytes,
        )
        runtime_dict["enriched_detections"] = enriched_dets
        trace.inference = runtime_dict
        trace.truth["detections"] = TRUTH_MEASURED
        trace.truth["temporal_reasoning"] = "DETERMINISTIC_RULE_ON_VERIFIED_PERCEPTION"
        trace.truth["policy"] = "DETERMINISTIC_RULE_ON_VERIFIED_PERCEPTION"
        trace.truth["timings"] = (
            "MODALIX_RUNTIME_TELEMETRY"
            if inference.telemetry
            else "NO_MODALIX_TELEMETRY_SUPPLIED"
        )
        trace.stages[1].update(
            status="complete",
            summary=f"Modalix returned {len(inference.detections)} normalized detection(s) for this frame",
            runtime=runtime_dict,
            truth=TRUTH_MEASURED,
        )
        trace.metrics["max_detection_confidence"] = max(
            (detection.confidence for detection in inference.detections),
            default=0.0,
        )
        required_labels = set(config.get("required_labels", []))
        policy_detections = [
            detection
            for detection in inference.detections
            if detection.confidence >= MIN_LIVE_POLICY_CONFIDENCE
            and (not required_labels or detection.label in required_labels)
        ]
        if not policy_detections:
            trace.status = "POLICY_NOT_TRIGGERED"
            trace.truth["temporal_reasoning"] = "NOT_ESTABLISHED_FROM_LOW_CONFIDENCE_PERCEPTION"
            trace.truth["policy"] = "NO_ACTION_LOW_CONFIDENCE"
            has_non_required = any(d.label not in required_labels for d in inference.detections)
            policy_summary = (
                "Objects detected successfully. No configured security policy triggered. No action required."
                if has_non_required
                else "Detection below Guardian policy threshold. No action required."
            )
            trace.stages[2].update(
                status="blocked",
                summary=policy_summary,
                runtime=runtime_dict,
                truth="INSUFFICIENT_CONFIDENCE" if not has_non_required else "NO_POLICY_MATCH",
            )
            trace.stages[3].update(
                status="complete",
                summary="Policy evaluated fail-closed: no bounded action proposed",
                reason_codes=["LOW_CONFIDENCE_NO_ACTION" if not has_non_required else "NO_POLICY_TRIGGER"],
                truth="NO_ACTION",
            )
            trace.stages[4].update(
                status="not_requested",
                summary="Human approval was not requested because policy did not trigger",
                truth="NOT_REQUESTED",
            )
            trace.stages[5].update(
                status="safe_noop",
                summary="NOTHING EXECUTED",
                truth="NOT_EXECUTED",
            )
            trace.metrics["composition_to_no_action_ms"] = round(
                (perf_counter() - started) * 1000.0,
                3,
            )
            self._record_lifecycle(
                "POLICY_NOT_TRIGGERED",
                policy_summary,
                "NO_ACTION",
            )
            self.latest_evidence = self._make_evidence(final=False)
            return self.state()
        trace.stages[2].update(
            status="complete",
            summary=(
                f"{len(policy_detections)} required detection(s) crossed the policy threshold; "
                f"temporal policy context: {config['event']}"
            ),
            runtime=runtime_dict,
            truth="DETERMINISTIC_RULE_ON_VERIFIED_PERCEPTION",
        )
        trace.stages[3].update(
            status="complete",
            summary=f"Policy matched: {', '.join(config['reason_codes'])}",
            severity=config["severity"],
            reason_codes=config["reason_codes"],
            truth="DETERMINISTIC_RULE_ON_VERIFIED_PERCEPTION",
        )

        action = ProposedAction(
            action_id=f"action-{uuid4().hex[:10]}",
            action_type=config["action"],
            target=config["target"],
            reason=config["event"],
        )
        trace.proposed_action = action
        trace.status = "AWAITING_APPROVAL"
        trace.stages[4].update(
            status="blocked_on_human_approval",
            summary="Explicit human authorization required",
            truth="HUMAN_DECISION_PENDING",
        )
        trace.stages[5].update(
            status="blocked_on_human_approval",
            summary=f"Proposed bounded action: {action.action_type}",
            truth="NOT_EXECUTED",
        )
        trace.metrics["composition_to_proposal_ms"] = round((perf_counter() - started) * 1000.0, 3)
        trace.metrics["runtime_round_trip_ms"] = inference.runtime_overhead_ms
        if isinstance(inference.telemetry.get("latency_ms"), (int, float)):
            trace.metrics["sima_latency_ms"] = inference.telemetry["latency_ms"]
        if isinstance(inference.telemetry.get("fps"), (int, float)):
            trace.metrics["sima_fps"] = inference.telemetry["fps"]
        self._record_lifecycle(
            "PROPOSED",
            "Verified per-frame perception produced a bounded proposal; human authorization is required",
            "DETERMINISTIC_RULE_ON_VERIFIED_PERCEPTION",
        )
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

        self.current.decision = "APPROVED"
        self.current.status = "AUTHORIZED"
        for stage in self.current.stages:
            if stage["stage"] == "APPROVAL":
                stage.update(
                    status="complete",
                    summary="Human operator approved the bounded proposal",
                    truth="HUMAN_APPROVAL",
                )
        self._record_lifecycle(
            "AUTHORIZED",
            "Human operator authorized the bounded action",
            "HUMAN_APPROVAL",
        )
        self.current.status = "EXECUTING"
        self._record_lifecycle(
            "EXECUTING",
            "Bounded Physical I/O execution started",
            "MEASURED_COMPOSITION_OVERHEAD_ONLY",
        )

        started = perf_counter()
        physical_io_result: dict[str, object] | None = None
        io_status = PHYSICAL_IO.status()
        if PHYSICAL_IO.can_execute(action.action_type):
            if io_status["status"] == "INVALID_LOCAL_BRIDGE_CONFIG":
                return self._fail_action_safe(
                    "Physical I/O bridge configuration is invalid",
                    started=started,
                )
            if (
                self.current.truth.get("detections") == TRUTH_MEASURED
                and io_status["status"] != "READY_CONFIGURED"
            ):
                return self._fail_action_safe(
                    "Verified live inference cannot claim physical execution without a configured readback bridge",
                    started=started,
                )
            if io_status["status"] == "READY_CONFIGURED":
                try:
                    physical_io_result = PHYSICAL_IO.execute(action)
                except RuntimeError as exc:
                    return self._fail_action_safe(str(exc), started=started)

        physical_io_truth = (
            str(physical_io_result["truth"])
            if physical_io_result is not None
            else "SIMULATED_REFERENCE_IO"
        )
        self.current.truth["physical_io"] = physical_io_truth
        if physical_io_result is not None:
            self.current.metrics["physical_io_round_trip_ms"] = physical_io_result[
                "total_round_trip_ms"
            ]

        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                if physical_io_result is not None:
                    stage.update(
                        status="complete",
                        summary=(
                            "Permanent Physical I/O contract accepted "
                            f"{physical_io_result['contract_action']}"
                        ),
                        truth=physical_io_truth,
                    )
                else:
                    stage.update(
                        status="complete",
                        summary=f"Reference I/O accepted {action.action_type}",
                        truth="SIMULATED_REFERENCE_IO",
                    )
            elif stage["stage"] == "VERIFY":
                if physical_io_result is not None:
                    stage.update(
                        status="complete",
                        summary=(
                            "Permanent Physical I/O readback verified for "
                            f"{physical_io_result['contract_target']}"
                        ),
                        truth=physical_io_truth,
                    )
                else:
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
        self.current.safe_state_verified = False
        self.current.reverified = False
        self.current.status = "VERIFIED"
        self.current.metrics["approval_to_verification_ms"] = round((perf_counter() - started) * 1000.0, 3)
        self._record_lifecycle(
            "EXECUTION_VERIFIED",
            "Action execution completed with readback verification",
            physical_io_truth,
        )
        self.latest_evidence = self._make_evidence(final=True)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def interrupt(self) -> dict[str, Any]:
        if not self.current or not self.current.proposed_action:
            raise RuntimeError("no active action to interrupt")
        if self.current.status not in {"VERIFIED", "RESUMED_VERIFIED"}:
            raise RuntimeError(f"trace cannot be interrupted from state: {self.current.status}")

        action = self.current.proposed_action
        started = perf_counter()
        self._record_lifecycle(
            "INTERRUPTED",
            "Operator interrupt requested; Guardian must prove safe state before any resume",
            "HUMAN_INTERRUPT",
        )
        self.current.status = "INTERRUPTING"
        self.current.verified = False
        self.current.reverified = False
        self.current.safe_state_verified = False

        io_status = PHYSICAL_IO.status()
        safe_result: dict[str, object] | None = None
        safe_truth = "DETERMINISTIC_SAFE_NOOP"
        safe_cycle = f"safe-{self.current.resume_count}"

        if PHYSICAL_IO.can_execute(action.action_type):
            if io_status["status"] == "INVALID_LOCAL_BRIDGE_CONFIG":
                return self._fail_interrupt_safe(
                    "Physical I/O bridge configuration is invalid",
                    started=started,
                )
            if io_status["status"] == "READY_CONFIGURED":
                try:
                    safe_result = PHYSICAL_IO.enter_safe_state(action, cycle=safe_cycle)
                except RuntimeError as exc:
                    return self._fail_interrupt_safe(str(exc), started=started)
                safe_truth = str(safe_result["truth"])
            else:
                safe_truth = "SIMULATED_REFERENCE_IO"

        self.current.safe_state_verified = True
        self.current.truth["physical_io"] = safe_truth
        self.current.status = "SAFE_STATE_VERIFIED"
        self.current.metrics["interrupt_to_safe_state_ms"] = round(
            (perf_counter() - started) * 1000.0, 3
        )
        if safe_result is not None:
            self.current.metrics["safe_state_round_trip_ms"] = safe_result[
                "total_round_trip_ms"
            ]
        self._record_lifecycle(
            "SAFE_STATE_VERIFIED",
            "Interrupt completed and safe state readback was verified; resume remains locked",
            safe_truth,
        )
        self._set_interrupt_stage_state(
            act_status="interrupted_safe",
            act_summary="Execution interrupted; verified safe state applied",
            verify_status="reverification_required",
            verify_summary="Resume locked until safe state is re-verified",
            truth=safe_truth,
        )
        self.latest_evidence = self._make_evidence(final=False)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def reverify(self) -> dict[str, Any]:
        if not self.current or not self.current.proposed_action:
            raise RuntimeError("no interrupted action to re-verify")
        if self.current.status != "SAFE_STATE_VERIFIED" or not self.current.safe_state_verified:
            raise RuntimeError("resume precondition failed: verified safe state is required")

        action = self.current.proposed_action
        started = perf_counter()
        io_status = PHYSICAL_IO.status()
        reverify_result: dict[str, object] | None = None
        reverify_truth = "DETERMINISTIC_SAFE_NOOP"
        safe_cycle = f"safe-{self.current.resume_count}"

        if PHYSICAL_IO.can_execute(action.action_type):
            if io_status["status"] == "INVALID_LOCAL_BRIDGE_CONFIG":
                return self._fail_reverification("Physical I/O bridge configuration is invalid")
            if io_status["status"] == "READY_CONFIGURED":
                try:
                    reverify_result = PHYSICAL_IO.reverify_safe_state(action, cycle=safe_cycle)
                except RuntimeError as exc:
                    return self._fail_reverification(str(exc))
                reverify_truth = str(reverify_result["truth"])
            else:
                reverify_truth = "SIMULATED_REFERENCE_IO"

        self.current.reverified = True
        self.current.status = "REVERIFIED"
        self.current.truth["physical_io"] = reverify_truth
        self.current.metrics["safe_state_reverification_ms"] = round(
            (perf_counter() - started) * 1000.0, 3
        )
        self._record_lifecycle(
            "REVERIFIED",
            "Safe state was re-verified; explicit resume or cancel is now permitted",
            reverify_truth,
        )
        for stage in self.current.stages:
            if stage["stage"] == "VERIFY":
                stage.update(
                    status="complete",
                    summary="Safe state re-verified; resume gate unlocked",
                    truth=reverify_truth,
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="checkpoint",
                    summary="Re-verification checkpoint appended to evidence timeline",
                    truth="MEASURED_AND_LABELED",
                )
        self.latest_evidence = self._make_evidence(final=False)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def resume(self) -> dict[str, Any]:
        if not self.current or not self.current.proposed_action:
            raise RuntimeError("no interrupted action to resume")
        if self.current.status != "REVERIFIED" or not self.current.reverified:
            raise RuntimeError("resume denied until safe state has been re-verified")

        action = self.current.proposed_action
        next_resume = self.current.resume_count + 1
        self.current.status = "EXECUTING"
        self._record_lifecycle(
            "RESUMING",
            "Operator requested resume after successful re-verification",
            "HUMAN_COMMAND",
        )
        started = perf_counter()
        io_status = PHYSICAL_IO.status()
        physical_io_result: dict[str, object] | None = None
        resume_truth = "SIMULATED_REFERENCE_IO"

        if PHYSICAL_IO.can_execute(action.action_type):
            if io_status["status"] == "INVALID_LOCAL_BRIDGE_CONFIG":
                return self._fail_resume_safe("Physical I/O bridge configuration is invalid")
            if io_status["status"] == "READY_CONFIGURED":
                try:
                    physical_io_result = PHYSICAL_IO.execute(
                        action,
                        cycle=f"resume-{next_resume}",
                    )
                except RuntimeError as exc:
                    return self._fail_resume_safe(str(exc))
                resume_truth = str(physical_io_result["truth"])

        self.current.resume_count = next_resume
        self.current.verified = True
        self.current.safe_state_verified = False
        self.current.reverified = False
        self.current.status = "RESUMED_VERIFIED"
        self.current.truth["physical_io"] = resume_truth
        self.current.metrics["resume_to_verification_ms"] = round(
            (perf_counter() - started) * 1000.0, 3
        )
        if physical_io_result is not None:
            self.current.metrics["resume_physical_io_round_trip_ms"] = physical_io_result[
                "total_round_trip_ms"
            ]
        self._record_lifecycle(
            "RESUMED_VERIFIED",
            "Action resumed only after re-verification and completed with readback verification",
            resume_truth,
        )
        for stage in self.current.stages:
            if stage["stage"] == "APPROVAL":
                stage.update(
                    status="rejected",
                    summary="DENIED — NOTHING EXECUTED",
                    truth="HUMAN_REJECTION",
                )
            elif stage["stage"] == "ACT":
                stage.update(
                    status="complete",
                    summary=f"Bounded action resumed after re-verification (cycle {next_resume})",
                    truth=resume_truth,
                )
            elif stage["stage"] == "VERIFY":
                stage.update(
                    status="complete",
                    summary="Resumed action readback verified",
                    truth=resume_truth,
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="complete",
                    summary="Interrupt/reverify/resume lifecycle sealed in evidence bundle",
                    truth="MEASURED_AND_LABELED",
                )
        self.latest_evidence = self._make_evidence(final=True)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def cancel(self) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no interrupted action to cancel")
        if self.current.status not in {"SAFE_STATE_VERIFIED", "REVERIFIED"}:
            raise RuntimeError(f"trace cannot be cancelled from state: {self.current.status}")
        if not self.current.safe_state_verified:
            raise RuntimeError("cancel requires a verified safe state")

        self.current.decision = "CANCELLED"
        self.current.status = "CANCELLED_SAFE"
        self.current.verified = True
        self._record_lifecycle(
            "CANCELLED_SAFE",
            "Operator cancelled the interrupted action while verified safe state remained active",
            self.current.truth.get("physical_io", "DETERMINISTIC_SAFE_NOOP"),
        )
        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                stage.update(
                    status="cancelled_safe",
                    summary="Interrupted action cancelled; safe state remains active",
                    truth=self.current.truth.get("physical_io", "DETERMINISTIC_SAFE_NOOP"),
                )
            elif stage["stage"] == "VERIFY":
                stage.update(
                    status="complete",
                    summary="Verified safe state preserved after cancellation",
                    truth=self.current.truth.get("physical_io", "DETERMINISTIC_SAFE_NOOP"),
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="complete",
                    summary="Cancellation and safe-state evidence sealed",
                    truth="MEASURED_AND_LABELED",
                )
        self.latest_evidence = self._make_evidence(final=True)
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def _set_interrupt_stage_state(
        self,
        *,
        act_status: str,
        act_summary: str,
        verify_status: str,
        verify_summary: str,
        truth: str,
    ) -> None:
        if not self.current:
            raise RuntimeError("no active trace")
        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                stage.update(status=act_status, summary=act_summary, truth=truth)
            elif stage["stage"] == "VERIFY":
                stage.update(status=verify_status, summary=verify_summary, truth=truth)
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="checkpoint",
                    summary="Interrupt checkpoint appended to forensic evidence",
                    truth="MEASURED_AND_LABELED",
                )

    def _fail_action_safe(self, reason: str, *, started: float) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no active trace")
        self.current.decision = "APPROVED"
        self.current.verified = False
        self.current.status = "ACTION_FAILED_SAFE"
        self.current.truth["physical_io"] = "FAILED_CLOSED"
        self.current.metrics["approval_to_failure_ms"] = round(
            (perf_counter() - started) * 1000.0, 3
        )
        self._record_lifecycle(
            "EXECUTION_FAILED_SAFE",
            "Physical action failed closed; no verified output was accepted",
            "FAILED_CLOSED",
        )
        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                stage.update(
                    status="failed_safe",
                    summary="Physical I/O did not produce an accepted verified output",
                    truth="FAILED_CLOSED",
                )
            elif stage["stage"] == "VERIFY":
                stage.update(
                    status="failed_closed",
                    summary="Physical I/O readback could not be verified",
                    truth="FAILED_CLOSED",
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="complete",
                    summary="Fail-closed decision sealed in evidence bundle",
                    truth="MEASURED_AND_LABELED",
                )
        self.latest_evidence = self._make_evidence(final=True)
        self.latest_evidence["physical_io_failure"] = reason
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def _fail_interrupt_safe(self, reason: str, *, started: float) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no active trace")
        self.current.verified = False
        self.current.safe_state_verified = False
        self.current.reverified = False
        self.current.status = "INTERRUPTION_UNVERIFIED"
        self.current.truth["physical_io"] = "FAILED_CLOSED"
        self.current.metrics["interrupt_to_failure_ms"] = round(
            (perf_counter() - started) * 1000.0, 3
        )
        self._record_lifecycle(
            "SAFE_STATE_UNVERIFIED",
            "Interrupt was requested but safe-state readback could not be verified",
            "FAILED_CLOSED",
        )
        self._set_interrupt_stage_state(
            act_status="failed_safe",
            act_summary="Interrupt issued but verified safe state was not proven",
            verify_status="failed_closed",
            verify_summary="Resume denied because safe state is unverified",
            truth="FAILED_CLOSED",
        )
        self.latest_evidence = self._make_evidence(final=True)
        self.latest_evidence["physical_io_failure"] = reason
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def _fail_reverification(self, reason: str) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no active trace")
        self.current.reverified = False
        self.current.status = "REVERIFICATION_FAILED"
        self.current.truth["physical_io"] = "FAILED_CLOSED"
        self._record_lifecycle(
            "REVERIFICATION_FAILED",
            "Safe-state re-verification failed; resume remains denied",
            "FAILED_CLOSED",
        )
        for stage in self.current.stages:
            if stage["stage"] == "VERIFY":
                stage.update(
                    status="failed_closed",
                    summary="Safe state could not be re-verified; resume remains locked",
                    truth="FAILED_CLOSED",
                )
        self.latest_evidence = self._make_evidence(final=True)
        self.latest_evidence["physical_io_failure"] = reason
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def _fail_resume_safe(self, reason: str) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no active trace")
        self.current.verified = False
        self.current.status = "RESUME_FAILED_SAFE"
        self.current.truth["physical_io"] = "FAILED_CLOSED"
        self._record_lifecycle(
            "RESUME_FAILED_SAFE",
            "Resume execution failed closed after re-verification",
            "FAILED_CLOSED",
        )
        for stage in self.current.stages:
            if stage["stage"] == "ACT":
                stage.update(
                    status="failed_safe",
                    summary="Resume action failed; no verified resumed output accepted",
                    truth="FAILED_CLOSED",
                )
            elif stage["stage"] == "VERIFY":
                stage.update(
                    status="failed_closed",
                    summary="Resumed physical output could not be verified",
                    truth="FAILED_CLOSED",
                )
            elif stage["stage"] == "PROVE":
                stage.update(
                    status="complete",
                    summary="Failed resume sealed in forensic evidence",
                    truth="MEASURED_AND_LABELED",
                )
        self.latest_evidence = self._make_evidence(final=True)
        self.latest_evidence["physical_io_failure"] = reason
        self.current.evidence_id = self.latest_evidence["evidence_id"]
        return self.state()

    def reject(self) -> dict[str, Any]:
        if not self.current:
            raise RuntimeError("no active trace")
        if self.current.status != "AWAITING_APPROVAL":
            raise RuntimeError(f"trace is not awaiting approval: {self.current.status}")

        self.current.decision = "REJECTED"
        self.current.status = "REJECTED_SAFE"
        self._record_lifecycle(
            "REJECTED_SAFE",
            "Operator rejected the proposed action; no physical output was issued",
            "HUMAN_REJECTION",
        )
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
            "schema": "inneros.guardian.hackathon.evidence.v2",
            "trace_id": self.current.trace_id,
            "scenario": self.current.scenario,
            "runtime_id": self.current.runtime_id,
            "status": self.current.status,
            "decision": self.current.decision,
            "verified": self.current.verified,
            "safe_state_verified": self.current.safe_state_verified,
            "reverified": self.current.reverified,
            "resume_count": self.current.resume_count,
            "lifecycle_events": self.current.lifecycle_events,
            "stages": self.current.stages,
            "metrics": self.current.metrics,
            "truth": self.current.truth,
            "frame_source": self.current.frame_source,
            "inference": self.current.inference,
            "physical_io_bridge": PHYSICAL_IO.status(),
            "preexisting_product_boundary": "Rafa-Innerchispa/inneros-physical-guardian",
            "hackathon_composition_boundary": "Rafa-Innerchispa/inneros-physical-guardian-ai-infra-2026",
            "final": final,
            "sealed_at": self._now(),
        }
        digest_source = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evidence_id = "ev-" + hashlib.sha256(digest_source).hexdigest()[:20]
        return {"evidence_id": evidence_id, **body}
