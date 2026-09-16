from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    track_id: str | None
    zone: str | None
    class_id: int | None = None


@dataclass(frozen=True)
class RuntimeResult:
    runtime_id: str
    provider: str
    model: str
    detections: tuple[Detection, ...]
    runtime_overhead_ms: float
    inference_truth: str
    notes: str
    runtime: str = ""
    device: str = ""
    captured_at: str | None = None
    inferred_at: str | None = None
    source: dict[str, Any] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    attestation: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProposedAction:
    action_id: str
    action_type: str
    target: str
    reason: str
    requires_approval: bool = True
    impact: str = "low"


@dataclass
class DemoTrace:
    trace_id: str
    scenario: str
    started_at: str
    runtime_id: str
    status: str
    stages: list[dict[str, Any]] = field(default_factory=list)
    proposed_action: ProposedAction | None = None
    decision: str | None = None
    verified: bool = False
    evidence_id: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    truth: dict[str, str] = field(default_factory=dict)
    lifecycle_events: list[dict[str, Any]] = field(default_factory=list)
    safe_state_verified: bool = False
    reverified: bool = False
    resume_count: int = 0
    frame_source: dict[str, Any] = field(default_factory=dict)
    inference: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
