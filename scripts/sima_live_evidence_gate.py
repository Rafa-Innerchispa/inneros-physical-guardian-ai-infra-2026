#!/usr/bin/env python3
"""SiMa.ai Live Evidence Gate & Judge Validation CLI for InnerOS Physical Guardian.

Validates truth-gated SiMa benchmark evidence files deterministically offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "inneros.guardian.sima.evidence.v1"
TRUTH_MEASURED = "MEASURED_SPONSOR_RUNTIME"
TRUTH_SIMULATED = "SIMULATED_SPONSOR_SDK"
TRUTH_UNVERIFIED = "SPONSOR_RUNTIME_UNVERIFIED"


def validate_evidence(
    data: dict[str, Any],
    *,
    strict_measured: bool = True,
    source_file_to_check: Path | None = None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # 1. Schema check
    schema = data.get("schema")
    if schema != EXPECTED_SCHEMA:
        errors.append(f"Invalid schema: expected '{EXPECTED_SCHEMA}', got '{schema}'")

    # 2. Truth rating
    truth = data.get("truth")
    measured = data.get("measured", False)
    if strict_measured:
        if truth != TRUTH_MEASURED:
            errors.append(f"Strict measured mode requires truth='{TRUTH_MEASURED}', got '{truth}'")
        if not measured:
            errors.append("Strict measured mode requires measured=true")
    else:
        if truth not in {TRUTH_MEASURED, TRUTH_SIMULATED, TRUTH_UNVERIFIED}:
            errors.append(f"Unknown truth rating: '{truth}'")

    # 3. Hardware & Platform
    hardware = str(data.get("hardware", "")).strip()
    if not hardware:
        errors.append("Missing 'hardware' descriptor (e.g. 'SiMa.ai Modalix DevKit MLSoC')")
    elif "modalix" not in hardware.lower() and "sima" not in hardware.lower():
        errors.append(f"Hardware descriptor must reference SiMa/Modalix: '{hardware}'")

    model = str(data.get("model", "")).strip()
    if not model:
        errors.append("Missing 'model' descriptor")

    # 4. Sample count & Metrics
    sample_count = data.get("sample_count", 0)
    if not isinstance(sample_count, int) or sample_count < 3:
        errors.append(f"sample_count must be an integer >= 3, got {sample_count}")

    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("Missing 'metrics' object")
    else:
        p50 = metrics.get("latency_p50_ms")
        p95 = metrics.get("latency_p95_ms")
        fps = metrics.get("fps")

        if p50 is None or not isinstance(p50, (int, float)) or p50 <= 0:
            errors.append(f"Invalid latency_p50_ms: {p50} (must be positive number)")
        if p95 is None or not isinstance(p95, (int, float)) or p95 <= 0:
            errors.append(f"Invalid latency_p95_ms: {p95} (must be positive number)")
        if p50 is not None and p95 is not None and p50 > p95:
            errors.append(f"latency_p50_ms ({p50}) cannot be greater than latency_p95_ms ({p95})")
        if fps is not None and (not isinstance(fps, (int, float)) or fps <= 0):
            errors.append(f"Invalid fps: {fps} (must be positive number)")

    # 5. Provenance Hash
    sha256 = data.get("source_json_sha256")
    if strict_measured:
        if not sha256 or not isinstance(sha256, str) or len(sha256) != 64:
            errors.append(f"Invalid source_json_sha256: expected 64-char hex hash, got '{sha256}'")
        elif source_file_to_check and source_file_to_check.is_file():
            hasher = hashlib.sha256()
            with source_file_to_check.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
            actual_sha = hasher.hexdigest()
            if actual_sha != sha256:
                errors.append(f"source_json_sha256 mismatch: recorded={sha256}, actual_file={actual_sha}")

    # 6. Detections check (if embedded or provided in source)
    detections = data.get("detections", [])
    if detections:
        for idx, det in enumerate(detections):
            if not isinstance(det, dict):
                errors.append(f"Detection {idx} must be an object")
                continue
            conf = det.get("confidence")
            if conf is None or not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                errors.append(f"Detection {idx} has invalid confidence: {conf} (must be 0.0 .. 1.0)")
            bbox = det.get("bbox")
            if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                errors.append(f"Detection {idx} bbox must have 4 numeric coordinates: {bbox}")
            else:
                if any(not isinstance(coord, (int, float)) or coord < 0 for coord in bbox):
                    errors.append(f"Detection {idx} bbox has invalid coordinate values: {bbox}")

    return len(errors) == 0, errors


def format_report(data: dict[str, Any], is_valid: bool, errors: list[str]) -> str:
    lines = [
        "============================================================",
        "  SiMa.ai Modalix Evidence Gate Report — InnerOS Guardian",
        "============================================================",
        f"  Overall Status:  {'[PASS] VALID' if is_valid else '[FAIL] REJECTED'}",
        f"  Schema:          {data.get('schema', 'N/A')}",
        f"  Truth:           {data.get('truth', 'N/A')}",
        f"  Measured:        {data.get('measured', 'N/A')}",
        f"  Hardware:        {data.get('hardware', 'N/A')}",
        f"  Model:           {data.get('model', 'N/A')}",
        f"  Sample Count:    {data.get('sample_count', 'N/A')}",
    ]
    metrics = data.get("metrics", {})
    if isinstance(metrics, dict):
        lines.extend([
            f"  Latency (p50):   {metrics.get('latency_p50_ms', 'N/A')} ms",
            f"  Latency (p95):   {metrics.get('latency_p95_ms', 'N/A')} ms",
            f"  Throughput:      {metrics.get('fps', 'N/A')} FPS",
        ])
    lines.append(f"  Source Hash:     {data.get('source_json_sha256', 'N/A')}")
    lines.append("------------------------------------------------------------")
    if is_valid:
        lines.append("  Result: All proof requirements satisfied for sponsor judging.")
    else:
        lines.append(f"  Gate Violations ({len(errors)}):")
        for err in errors:
            lines.append(f"    - [ERROR] {err}")
    lines.append("============================================================")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SiMa.ai Live Evidence Gate & Judge Validation CLI")
    parser.add_argument("evidence_file", type=Path, help="Path to evidence JSON file (e.g. docs/sima_measured_evidence.json)")
    parser.add_argument("--source-file", type=Path, help="Optional path to source benchmark JSON to verify SHA256")
    parser.add_argument("--allow-simulated", action="store_true", help="Allow SIMULATED_SPONSOR_SDK fixtures (default enforces strict measured)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON report")
    args = parser.parse_args(argv)

    if not args.evidence_file.is_file():
        print(f"Error: Evidence file not found at {args.evidence_file}", file=sys.stderr)
        return 2

    try:
        data = json.loads(args.evidence_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error: Failed to parse JSON from {args.evidence_file}: {exc}", file=sys.stderr)
        return 1

    strict_measured = not args.allow_simulated
    is_valid, errors = validate_evidence(
        data,
        strict_measured=strict_measured,
        source_file_to_check=args.source_file,
    )

    if args.json:
        report = {
            "valid": is_valid,
            "errors": errors,
            "truth": data.get("truth"),
            "measured": data.get("measured"),
            "hardware": data.get("hardware"),
            "model": data.get("model"),
            "metrics": data.get("metrics"),
        }
        print(json.dumps(report, indent=2))
    else:
        print(format_report(data, is_valid, errors))

    return 0 if is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
