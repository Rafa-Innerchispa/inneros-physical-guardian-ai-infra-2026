from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from typing import Any

LIVE_EVIDENCE_SCHEMA = "inneros.guardian.sima.frame-evidence.v2"
LIVE_EVIDENCE_KIND = "LIVE_FRAME_INFERENCE"
HISTORICAL_EVIDENCE_KIND = "HISTORICAL_BENCHMARK"
TRUTH_MEASURED = "MEASURED_SPONSOR_RUNTIME"
TRUTH_SIMULATED = "SIMULATED_SPONSOR_SDK"
TRUTH_UNVERIFIED = "SPONSOR_RUNTIME_UNVERIFIED"
ATTESTATION_KIND = "SIMA_MODALIX_RUNTIME"
TELEMETRY_SOURCE = "MODALIX_RUNTIME"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc_timestamp(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing {field_name}")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid {field_name}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone")
    return parsed.astimezone(timezone.utc)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def normalize_detection(item: object, index: int = 0) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"detection {index} must be an object")
    label = item.get("label")
    if not isinstance(label, str) or not label.strip() or len(label.strip()) > 80:
        raise ValueError(f"detection {index} requires a bounded label")

    confidence = item.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError(f"detection {index} confidence must be numeric")
    confidence_value = float(confidence)
    if not math.isfinite(confidence_value) or not 0.0 <= confidence_value <= 1.0:
        raise ValueError(f"detection {index} confidence must be between 0 and 1")

    bbox = item.get("bbox")
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError(f"detection {index} bbox must contain four coordinates")
    coordinates: list[float] = []
    for value in bbox:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"detection {index} bbox coordinates must be numeric")
        coordinate = float(value)
        if not math.isfinite(coordinate) or not 0.0 <= coordinate <= 1.0:
            raise ValueError(f"detection {index} bbox coordinates must be normalized")
        coordinates.append(coordinate)
    if coordinates[0] >= coordinates[2] or coordinates[1] >= coordinates[3]:
        raise ValueError(f"detection {index} bbox must have positive area")

    normalized: dict[str, Any] = {
        "label": label.strip(),
        "confidence": round(confidence_value, 6),
        "bbox": coordinates,
    }
    class_id = item.get("class_id")
    if class_id is not None:
        if isinstance(class_id, bool) or not isinstance(class_id, int) or not 0 <= class_id <= 999:
            raise ValueError(f"detection {index} class_id must be a bounded integer")
        normalized["class_id"] = class_id
    for optional in ("track_id", "zone"):
        value = item.get(optional)
        if value is not None:
            if not isinstance(value, str) or len(value) > 120:
                raise ValueError(f"detection {index} {optional} must be a bounded string")
            normalized[optional] = value
    return normalized


def validate_live_evidence(
    data: object,
    *,
    source_bytes: bytes | None,
    now: datetime | None = None,
    max_age_seconds: float = 15.0,
    expected_frame_id: str | None = None,
    expected_source_id: str | None = None,
    expected_model: str | None = None,
    expected_media_type: str | None = None,
    expected_dimensions: tuple[int, int] | None = None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return False, ["evidence must be a JSON object"]

    if data.get("schema") != LIVE_EVIDENCE_SCHEMA:
        errors.append(f"strict live evidence requires schema={LIVE_EVIDENCE_SCHEMA}")
    if data.get("evidence_kind") != LIVE_EVIDENCE_KIND:
        errors.append(f"strict live evidence requires evidence_kind={LIVE_EVIDENCE_KIND}")
    if data.get("truth") != TRUTH_MEASURED or data.get("measured") is not True:
        errors.append("strict live evidence requires measured sponsor-runtime truth")

    current = (now or utc_now()).astimezone(timezone.utc)
    captured: datetime | None = None
    inferred: datetime | None = None
    for field_name in ("captured_at", "inferred_at"):
        try:
            parsed = parse_utc_timestamp(data.get(field_name), field_name)
            age = (current - parsed).total_seconds()
            if age > max_age_seconds:
                errors.append(f"{field_name} is stale ({age:.3f}s old)")
            if age < -2.0:
                errors.append(f"{field_name} is in the future")
            if field_name == "captured_at":
                captured = parsed
            else:
                inferred = parsed
        except ValueError as exc:
            errors.append(str(exc))
    if captured and inferred and inferred < captured:
        errors.append("inferred_at cannot precede captured_at")

    model = data.get("model")
    runtime = data.get("runtime")
    device = data.get("device")
    if not isinstance(model, str) or not model.strip():
        errors.append("missing exact model")
    elif expected_model and model != expected_model:
        errors.append(f"model mismatch: expected {expected_model}")
    if not isinstance(runtime, str) or not runtime.strip():
        errors.append("missing SiMa runtime identity")
    elif not any(token in runtime.lower() for token in ("sima", "mla", "neat")):
        errors.append("runtime identity does not identify SiMa/MLA/NEAT")
    if not isinstance(device, str) or not device.strip():
        errors.append("missing Modalix device identity")
    elif "modalix" not in device.lower() and "sima" not in device.lower():
        errors.append("device identity does not identify SiMa/Modalix")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("missing frame source provenance")
    else:
        frame_id = source.get("frame_id")
        source_id = source.get("source_id")
        source_hash = source.get("sha256")
        media_type = source.get("media_type")
        width = source.get("width")
        height = source.get("height")
        if not isinstance(frame_id, str) or not frame_id:
            errors.append("missing source frame_id")
        elif expected_frame_id and frame_id != expected_frame_id:
            errors.append("frame_id does not match the requested frame")
        if not isinstance(source_id, str) or not source_id:
            errors.append("missing source source_id")
        elif expected_source_id and source_id != expected_source_id:
            errors.append("source_id does not match the requested source")
        if not isinstance(source_hash, str) or not _SHA256_RE.fullmatch(source_hash):
            errors.append("missing or malformed source sha256")
        if source_bytes is None:
            errors.append("strict live validation requires the source frame bytes")
        elif isinstance(source_hash, str) and source_hash != sha256_bytes(source_bytes):
            errors.append("source sha256 does not match the frame bytes")
        if media_type not in {"image/jpeg", "image/png"}:
            errors.append("source media_type must be image/jpeg or image/png")
        elif expected_media_type and media_type != expected_media_type:
            errors.append("source media_type mismatch")
        if (
            isinstance(width, bool)
            or isinstance(height, bool)
            or not isinstance(width, int)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            errors.append("source dimensions must be positive integers")
        elif expected_dimensions and (width, height) != expected_dimensions:
            errors.append("source dimensions mismatch")

    detections = data.get("detections")
    if not isinstance(detections, list):
        errors.append("missing detections list")
    elif not detections:
        errors.append("strict live evidence requires at least one decoded detection")
    else:
        for index, detection in enumerate(detections):
            try:
                normalize_detection(detection, index)
            except ValueError as exc:
                errors.append(str(exc))

    telemetry = data.get("telemetry")
    if telemetry is not None:
        if not isinstance(telemetry, dict):
            errors.append("telemetry must be an object")
        else:
            measured_values = [name for name in ("latency_ms", "fps") if telemetry.get(name) is not None]
            if measured_values and telemetry.get("source") != TELEMETRY_SOURCE:
                errors.append("live timing requires source=MODALIX_RUNTIME")
            for name in measured_values:
                value = telemetry.get(name)
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    errors.append(f"telemetry {name} must be numeric")
                elif not math.isfinite(float(value)) or float(value) <= 0:
                    errors.append(f"telemetry {name} must be positive")

    attestation = data.get("attestation")
    if not isinstance(attestation, dict):
        errors.append("missing Modalix runtime attestation")
    else:
        if attestation.get("kind") != ATTESTATION_KIND:
            errors.append(f"attestation kind must be {ATTESTATION_KIND}")
        if attestation.get("runtime_verified") is not True:
            errors.append("runtime attestation is not verified")
        if attestation.get("device_verified") is not True:
            errors.append("device attestation is not verified")
        evidence_id = attestation.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip() or len(evidence_id) > 160:
            errors.append("attestation requires an evidence_id")

    return not errors, errors
