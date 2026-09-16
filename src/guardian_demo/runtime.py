from __future__ import annotations

import json
import os
from dataclasses import asdict
from time import perf_counter
from typing import Any, Protocol
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .frame_input import FramePayload
from .models import Detection, RuntimeResult
from .sima_contract import TRUTH_MEASURED, TRUTH_UNVERIFIED, normalize_detection, validate_live_evidence


MAX_SIDECAR_RESPONSE_BYTES = 256_000
SIDECAR_INFERENCE_TIMEOUT_SECONDS = 45.0


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
        if parsed.username or parsed.password:
            raise RuntimeError(f"{self.env_var} must not embed credentials")
        if parsed.query or parsed.fragment:
            raise RuntimeError(f"{self.env_var} must not contain query or fragment data")
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
        if not configured:
            return {
                "runtime_id": self.runtime_id,
                "provider": self.provider,
                "target": self.target,
                "status": "OFFLINE",
                "truth": TRUTH_UNVERIFIED,
            }
        try:
            request = Request(self._configured_url() + "/health", method="GET")  # type: ignore[operator]
            with urlopen(request, timeout=0.75) as response:  # nosec B310 - loopback URL validated above
                raw = json.loads(response.read(32_001).decode("utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("invalid health response")
            reported = str(raw.get("status", "BLOCKED")).upper()
            status = "READY" if reported == "READY" else "BLOCKED"
        except Exception:
            status = "BLOCKED"
        return {
            "runtime_id": self.runtime_id,
            "provider": self.provider,
            "target": self.target,
            "status": status,
            # Health/configuration is never proof for a particular frame.
            "truth": TRUTH_UNVERIFIED,
        }

    @staticmethod
    def _parse_detection(item: dict[str, Any]) -> Detection:
        try:
            normalized = normalize_detection(item)
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        return Detection(
            label=str(normalized["label"]),
            confidence=float(normalized["confidence"]),
            bbox=tuple(float(value) for value in normalized["bbox"]),
            track_id=normalized.get("track_id"),
            zone=normalized.get("zone"),
            class_id=normalized.get("class_id"),
        )

    def infer(self, *, scenario: str, frame_ref: str) -> RuntimeResult:
        base_url = self._configured_url()
        if self.runtime_id == "sima-slot":
            raise RuntimeError(
                "SiMa live inference requires submitted frame bytes; use the per-frame inference route."
            )
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

    def infer_frame(self, *, scenario: str, frame: FramePayload) -> RuntimeResult:
        """Submit one bounded frame and accept only matching live Modalix proof."""

        base_url = self._configured_url()
        if not base_url:
            raise RuntimeError(
                f"{self.provider} per-frame runtime is unavailable until its loopback sidecar is configured."
            )
        payload = json.dumps(
            {"scenario": scenario, **frame.to_transport()},
            separators=(",", ":"),
        ).encode("utf-8")
        request = Request(
            base_url + "/infer",
            data=payload,
            method="POST",
            headers={
                "Accept": "application/json",
                "Cache-Control": "no-store",
                "Content-Type": "application/json",
            },
        )
        started = perf_counter()
        try:
            with urlopen(request, timeout=SIDECAR_INFERENCE_TIMEOUT_SECONDS) as response:  # nosec B310 - loopback URL validated above
                if response.headers.get_content_type().lower() != "application/json":
                    raise RuntimeError("sponsor sidecar response is not JSON")
                encoded = response.read(MAX_SIDECAR_RESPONSE_BYTES + 1)
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"{self.provider} per-frame bridge failed: {type(exc).__name__}") from exc
        if len(encoded) > MAX_SIDECAR_RESPONSE_BYTES:
            raise RuntimeError("sponsor sidecar response exceeds the bounded contract")
        try:
            raw = json.loads(encoded.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("sponsor sidecar returned malformed JSON") from exc

        valid, errors = validate_live_evidence(
            raw,
            source_bytes=frame.image_bytes,
            expected_frame_id=frame.frame_id,
            expected_source_id=frame.source_id,
            expected_media_type=frame.image_type,
            expected_dimensions=(frame.width, frame.height),
        )
        if not valid:
            raise RuntimeError("per-frame sponsor evidence rejected: " + "; ".join(errors))
        if not isinstance(raw, dict):  # validate_live_evidence already rejects this; narrows the type.
            raise RuntimeError("sponsor sidecar response must be a JSON object")

        detections_raw = raw.get("detections", [])
        detections = tuple(self._parse_detection(item) for item in detections_raw)
        telemetry = raw.get("telemetry") if isinstance(raw.get("telemetry"), dict) else {}
        attestation = raw.get("attestation") if isinstance(raw.get("attestation"), dict) else {}
        source = raw.get("source") if isinstance(raw.get("source"), dict) else {}
        return RuntimeResult(
            runtime_id=self.runtime_id,
            provider=self.provider,
            model=str(raw["model"]),
            detections=detections,
            runtime_overhead_ms=round((perf_counter() - started) * 1000.0, 4),
            inference_truth=TRUTH_MEASURED,
            notes=str(raw.get("notes", "Per-frame result supplied by the configured SiMa sidecar.")),
            runtime=str(raw["runtime"]),
            device=str(raw["device"]),
            captured_at=str(raw["captured_at"]),
            inferred_at=str(raw["inferred_at"]),
            source=dict(source),
            telemetry=dict(telemetry),
            attestation=dict(attestation),
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
