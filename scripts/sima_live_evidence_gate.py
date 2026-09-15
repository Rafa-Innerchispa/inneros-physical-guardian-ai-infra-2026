#!/usr/bin/env python3
"""Deterministic offline gate for SiMa live inference evidence JSON."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "inneros.guardian.sima.live_evidence.v1"
LIVE_TRUTHS = frozenset({"MEASURED_SPONSOR_RUNTIME", "LIVE_SPONSOR_RUNTIME"})
SIMULATED_TRUTHS = frozenset(
    {
        "SIMULATED_SPONSOR_SDK",
        "SIMULATED_FIXTURE",
        "SPONSOR_RUNTIME_UNVERIFIED",
    }
)
SIMA_SPONSORS = frozenset({"sima", "sima.ai", "sima_ai"})


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    observed: str


@dataclass(frozen=True)
class GateResult:
    ok: bool
    checks: tuple[Check, ...]
    summary: str

    def exit_code(self) -> int:
        return 0 if self.ok else 2


def _parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _bbox_ok(bbox: Any) -> bool:
    if not isinstance(bbox, Sequence) or isinstance(bbox, (str, bytes)):
        return False
    if len(bbox) != 4:
        return False
    try:
        coords = [float(item) for item in bbox]
    except (TypeError, ValueError):
        return False
    return all(0.0 <= coord <= 1.0 for coord in coords) and coords[2] > coords[0] and coords[3] > coords[1]


def _detection_ok(detection: Any) -> tuple[bool, str]:
    if not isinstance(detection, Mapping):
        return False, "detection is not an object"
    label = detection.get("class") or detection.get("label")
    if not isinstance(label, str) or not label.strip():
        return False, "missing class/label"
    confidence = detection.get("confidence")
    try:
        confidence_value = float(confidence)
    except (TypeError, ValueError):
        return False, "confidence is not numeric"
    if not 0.0 <= confidence_value <= 1.0:
        return False, f"confidence out of range: {confidence_value}"
    if not _bbox_ok(detection.get("bbox")):
        return False, "bbox malformed or out of normalized range"
    return True, label.strip()


def validate_live_evidence(
    payload: Mapping[str, Any],
    *,
    now: datetime | None = None,
    require_live: bool = True,
) -> GateResult:
    checks: list[Check] = []
    now = now or datetime.now(timezone.utc)

    schema = payload.get("schema")
    checks.append(
        Check(
            "schema_version",
            schema == SCHEMA,
            str(schema),
        )
    )

    truth = str(payload.get("truth", "")).strip()
    live_flag = payload.get("live")
    is_live_truth = truth in LIVE_TRUTHS or live_flag is True
    is_simulated = truth in SIMULATED_TRUTHS or live_flag is False
    if require_live:
        checks.append(
            Check(
                "truth_is_live",
                is_live_truth and not is_simulated,
                truth or str(live_flag),
            )
        )
    else:
        checks.append(Check("truth_present", bool(truth or live_flag is not None), truth or str(live_flag)))

    sponsor = str(payload.get("sponsor_runtime", "")).strip().lower()
    checks.append(
        Check(
            "sponsor_is_sima",
            sponsor in SIMA_SPONSORS,
            sponsor or "missing",
        )
    )

    device = payload.get("device")
    device_ok = isinstance(device, Mapping) and bool(str(device.get("identifier", "")).strip())
    checks.append(
        Check(
            "device_identified",
            device_ok,
            str(device.get("identifier", device)) if isinstance(device, Mapping) else str(device),
        )
    )

    model = str(payload.get("model", "")).strip()
    checks.append(Check("model_present", bool(model), model or "missing"))

    input_source = str(payload.get("input_source", "")).strip()
    checks.append(Check("input_source_present", bool(input_source), input_source or "missing"))

    captured_at = _parse_timestamp(str(payload.get("captured_at", "")))
    frame_at = _parse_timestamp(str(payload.get("frame_timestamp", "")))
    checks.append(
        Check(
            "timestamps_parseable",
            captured_at is not None and frame_at is not None,
            f"captured_at={payload.get('captured_at')} frame_timestamp={payload.get('frame_timestamp')}",
        )
    )

    max_staleness_ms = payload.get("max_staleness_ms", 5000)
    stale = False
    if captured_at and frame_at:
        try:
            staleness_ms = abs((captured_at - frame_at).total_seconds()) * 1000.0
            stale = staleness_ms > float(max_staleness_ms)
            checks.append(
                Check(
                    "frame_is_fresh",
                    not stale,
                    f"staleness_ms={staleness_ms:.1f} max={max_staleness_ms}",
                )
            )
        except (TypeError, ValueError):
            checks.append(Check("frame_is_fresh", False, "invalid max_staleness_ms"))

    detections = payload.get("detections")
    detections_ok = isinstance(detections, list) and len(detections) > 0
    checks.append(
        Check(
            "detections_present",
            detections_ok,
            f"count={len(detections) if isinstance(detections, list) else 'invalid'}",
        )
    )

    valid_detection = False
    if isinstance(detections, list):
        for index, detection in enumerate(detections):
            ok, detail = _detection_ok(detection)
            if ok:
                valid_detection = True
                break
            if index == 0:
                checks.append(Check("detection_shape", False, detail))
        if valid_detection:
            checks.append(Check("detection_shape", True, "at least one valid detection"))

    provenance = payload.get("provenance")
    checks.append(
        Check(
            "provenance_present",
            isinstance(provenance, Mapping) and bool(str(provenance.get("adapter", "")).strip()),
            str(provenance.get("adapter", provenance)) if isinstance(provenance, Mapping) else "missing",
        )
    )

    metrics = payload.get("metrics")
    if isinstance(metrics, Mapping) and metrics:
        metrics_provenance = str(payload.get("metrics_provenance", "")).strip()
        checks.append(
            Check(
                "measured_metrics_have_provenance",
                bool(metrics_provenance),
                metrics_provenance or "missing metrics_provenance",
            )
        )

    ok = all(check.ok for check in checks)
    if ok:
        summary = "PASS live SiMa evidence gate"
    else:
        failed = ", ".join(check.name for check in checks if not check.ok)
        summary = f"FAIL live SiMa evidence gate: {failed}"
    return GateResult(ok=ok, checks=tuple(checks), summary=summary)


def load_payload(path: Path) -> Mapping[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ValueError("evidence root must be a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate SiMa live inference evidence JSON for judge rehearsal."
    )
    parser.add_argument("evidence", type=Path, help="Path to live evidence JSON")
    parser.add_argument(
        "--allow-simulated",
        action="store_true",
        help="Do not require live truth labels (for contract inspection only)",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.evidence.is_file():
        print(f"evidence file not found: {args.evidence}", file=sys.stderr)
        return 1

    try:
        payload = load_payload(args.evidence)
        result = validate_live_evidence(payload, require_live=not args.allow_simulated)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL live SiMa evidence gate: {exc}", file=sys.stderr)
        return 1

    if args.as_json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "summary": result.summary,
                    "checks": [
                        {"name": check.name, "ok": check.ok, "observed": check.observed}
                        for check in result.checks
                    ],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(result.summary)
        for check in result.checks:
            marker = "PASS" if check.ok else "FAIL"
            print(f"[{marker}] {check.name}: {check.observed}")

    return result.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
