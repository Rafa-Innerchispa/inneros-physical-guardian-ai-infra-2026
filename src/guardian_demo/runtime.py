from __future__ import annotations

import json
import os
from dataclasses import asdict
from time import perf_counter
from typing import Any, Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import Detection, RuntimeResult


class ChallengeRuntime(Protocol):
    runtime_id: str
    provider: str

    def infer(self, *, scenario: str, frame_ref: str) -> RuntimeResult:
        ...

    def status(self) -> dict[str, str]:
        ...


SCENARIO_DETECTIONS: dict[str, tuple[Detection, ...]] = {
    "loitering_after_hours": (
        Detection("person", 0.94, (0.42, 0.18, 0.62, 0.91), "track-17", "restricted-lobby"),
    ),
    "repeated_access_attempt": (
        Detection("person", 0.91, (0.31, 0.16, 0.51, 0.90), "track-08", "service-entry"),
    ),
    "restricted_zone_entry": (
        Detection("person", 0.96, (0.55, 0.20, 0.76, 0.93), "track-21", "equipment-zone"),
    ),
}


class DeterministicLocalRuntime:
    """Offline-safe demo runtime.

    It intentionally does not claim model inference. The returned detections are a
    deterministic fixture; only Python composition overhead is measured live.
    """

    runtime_id = "local-deterministic"
    provider = "InnerOS demo fixture"

    def status(self) -> dict[str, str]:
        return {
            "runtime_id": self.runtime_id,
            "provider": self.provider,
            "target": "offline deterministic demo",
            "status": "READY",
            "truth": "SIMULATED_FIXTURE",
        }

    def infer(self, *, scenario: str, frame_ref: str) -> RuntimeResult:
        started = perf_counter()
        detections = SCENARIO_DETECTIONS.get(scenario, SCENARIO_DETECTIONS["loitering_after_hours"])
        checksum_work = sum(int(d.confidence * 1000) for d in detections) + len(frame_ref)
        if checksum_work < 0:  # pragma: no cover - keeps fixture work explicit
            raise RuntimeError("unreachable")
        overhead_ms = (perf_counter() - started) * 1000.0
        return RuntimeResult(
            runtime_id=self.runtime_id,
            provider=self.provider,
            model="deterministic-fixture-v1",
            detections=detections,
            runtime_overhead_ms=round(overhead_ms, 4),
            inference_truth="SIMULATED_FIXTURE",
            notes="Detections are deterministic demo fixtures; only composition overhead is measured live.",
        )


class SponsorRuntimeSlot:
    """Local-only bridge to an official sponsor SDK/runtime sidecar.

    Each sponsor integration can live in its own SDK-specific process. The judge
    application talks only to a tiny JSON contract on loopback, preventing SDK
    churn from leaking into the Guardian demo core.
    """

    def __init__(self, runtime_id: str, provider: str, target: str, env_var: str) -> None:
        self.runtime_id = runtime_id
        self.provider = provider
        self.target = target
        self.env_var = env_var

    def _configured_url(self) -> str | None:
        raw = os.environ.get(self.env_var, "").strip()
        if not raw:
            return None
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            raise RuntimeError(f"{self.env_var} must use http or https")
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise RuntimeError(f"{self.env_var} must point to a loopback-only sponsor sidecar")
        return raw.rstrip("/")

    def status(self) -> dict[str, str]:
        try:
            configured = bool(self._configured_url())
        except RuntimeError:
            return {
                "runtime_id": self.runtime_id,
                "provider": self.provider,
                "target": self.target,
                "status": "INVALID_LOCAL_BRIDGE_CONFIG",
                "truth": "NOT_BENCHMARKED",
            }
        return {
            "runtime_id": self.runtime_id,
            "provider": self.provider,
            "target": self.target,
            "status": "READY" if configured else "AWAITING_ASSIGNED_HARDWARE_OR_SDK",
            "truth": "BRIDGE_DECLARED" if configured else "NOT_BENCHMARKED",
        }

    @staticmethod
    def _parse_detection(item: dict[str, Any]) -> Detection:
        bbox_raw = item.get("bbox", [0, 0, 1, 1])
        if not isinstance(bbox_raw, list) or len(bbox_raw) != 4:
            raise RuntimeError("sponsor sidecar detection bbox must contain four values")
        return Detection(
            label=str(item.get("label", "object")),
            confidence=float(item.get("confidence", 0.0)),
            bbox=tuple(float(value) for value in bbox_raw),
            track_id=str(item.get("track_id", "runtime-track")),
            zone=str(item.get("zone", "unassigned")),
        )

    def infer(self, *, scenario: str, frame_ref: str) -> RuntimeResult:
        base_url = self._configured_url()
        if not base_url:
            raise RuntimeError(
                f"{self.provider} runtime is a declared integration slot and cannot run until official hardware/SDK access is available."
            )

        payload = json.dumps({"scenario": scenario, "frame_ref": frame_ref}).encode("utf-8")
        request = Request(
            base_url + "/infer",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        started = perf_counter()
        try:
            with urlopen(request, timeout=5) as response:  # nosec B310 - loopback URL validated above
                raw = json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # network/SDK boundary is converted to an explicit fail-closed error
            raise RuntimeError(f"{self.provider} local runtime bridge failed: {exc}") from exc

        if not isinstance(raw, dict):
            raise RuntimeError("sponsor sidecar response must be a JSON object")
        detections_raw = raw.get("detections")
        if not isinstance(detections_raw, list):
            raise RuntimeError("sponsor sidecar response requires a detections list")
        detections = tuple(self._parse_detection(item) for item in detections_raw if isinstance(item, dict))
        if not detections:
            raise RuntimeError("sponsor sidecar returned no valid detections for this demo scenario")

        truth = str(raw.get("truth", "SPONSOR_RUNTIME_UNVERIFIED"))
        allowed_truth = {
            "MEASURED_SPONSOR_RUNTIME",
            "SPONSOR_RUNTIME_UNVERIFIED",
            "SIMULATED_SPONSOR_SDK",
        }
        if truth not in allowed_truth:
            truth = "SPONSOR_RUNTIME_UNVERIFIED"

        return RuntimeResult(
            runtime_id=self.runtime_id,
            provider=self.provider,
            model=str(raw.get("model", "sponsor-runtime")),
            detections=detections,
            runtime_overhead_ms=round((perf_counter() - started) * 1000.0, 4),
            inference_truth=truth,
            notes=str(raw.get("notes", "Result supplied by configured local sponsor SDK sidecar.")),
        )


RUNTIME_SLOTS: dict[str, ChallengeRuntime] = {
    "local-deterministic": DeterministicLocalRuntime(),
    "sima-slot": SponsorRuntimeSlot(
        "sima-slot", "SiMa.ai", "Modalix / Palette path", "GUARDIAN_SIMA_RUNTIME_URL"
    ),
    "qualcomm-slot": SponsorRuntimeSlot(
        "qualcomm-slot", "Qualcomm", "assigned edge AI runtime", "GUARDIAN_QUALCOMM_RUNTIME_URL"
    ),
    "intel-slot": SponsorRuntimeSlot(
        "intel-slot", "Intel", "assigned edge AI runtime", "GUARDIAN_INTEL_RUNTIME_URL"
    ),
}


def runtime_catalog() -> list[dict[str, object]]:
    return [runtime.status() for runtime in RUNTIME_SLOTS.values()]


def runtime_result_to_dict(result: RuntimeResult) -> dict[str, object]:
    return asdict(result)
