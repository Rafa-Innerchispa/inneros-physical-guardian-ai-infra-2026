from __future__ import annotations

import hashlib
import ipaddress
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

SIMA_DOCS = {
    "agents": "https://developer.sima.ai/agents",
    "quickstart": "https://developer.sima.ai/tools/qsg/index.html",
    "model_zoo": "https://developer.sima.ai/software/tools/model-zoo/",
    "benchmark": "https://developer.sima.ai/examples/app/benchmarking/model-benchmark",
}

TRUTH_SIMULATED = "SIMULATED_SPONSOR_SDK"
TRUTH_UNVERIFIED = "SPONSOR_RUNTIME_UNVERIFIED"
TRUTH_MEASURED = "MEASURED_SPONSOR_RUNTIME"


@dataclass(frozen=True)
class ProbeResult:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class EvidenceGate:
    truth: str
    measured: bool
    reasons: tuple[str, ...]


def find_sima_cli() -> str | None:
    return shutil.which("sima-cli")


def _run_readonly(
    argv: Sequence[str],
    *,
    timeout: float = 20.0,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> ProbeResult:
    try:
        proc = runner(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ProbeResult(argv[-1], "WARN", f"read-only probe unavailable: {type(exc).__name__}")
    if proc.returncode != 0:
        return ProbeResult(argv[-1], "WARN", f"read-only probe returned code {proc.returncode}")
    return ProbeResult(argv[-1], "PASS", "read-only probe completed")


def collect_sima_readiness(
    *,
    probe_device: bool = False,
    probe_modelzoo: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[ProbeResult]:
    cli = find_sima_cli()
    results = [
        ProbeResult(
            "sima_cli",
            "PASS" if cli else "WARN",
            "sima-cli available on PATH (path hidden)" if cli else "sima-cli not installed or not on PATH",
        )
    ]
    if not cli:
        return results
    if probe_device:
        results.append(_run_readonly([cli, "device", "discover"], runner=runner))
    if probe_modelzoo:
        results.append(_run_readonly([cli, "modelzoo", "list"], runner=runner))
    return results


def validate_devkit_ip(value: str) -> str:
    return str(ipaddress.ip_address(value.strip()))


def build_bringup_plan(devkit_ip: str | None = None) -> list[str]:
    plan = [
        "sima-cli device discover",
        "sima-cli modelzoo list",
        "sima-cli modelzoo describe yolo_v8s",
        "sima-cli modelzoo get yolo_v8s",
        "sima-cli neat install apps",
    ]
    if devkit_ip:
        ip = validate_devkit_ip(devkit_ip)
        plan.insert(1, f"ssh sima@{ip}")
        plan.insert(2, f"sima-cli sdk setup --devkit {ip}")
    return plan


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate_measured_gate(
    *,
    hardware: str,
    platform_version: str,
    neat_version: str,
    model: str,
    sample_count: int,
    latency_p50_ms: float | None,
    latency_p95_ms: float | None,
    source_json_sha256: str | None,
    measured_requested: bool,
) -> EvidenceGate:
    reasons: list[str] = []
    if not measured_requested:
        reasons.append("measured flag not requested")
    for label, value in (
        ("hardware", hardware),
        ("platform_version", platform_version),
        ("neat_version", neat_version),
        ("model", model),
    ):
        if not value.strip():
            reasons.append(f"missing {label}")
    if sample_count < 3:
        reasons.append("sample_count must be at least 3")
    if latency_p50_ms is None or latency_p50_ms <= 0:
        reasons.append("latency_p50_ms must be positive")
    if latency_p95_ms is None or latency_p95_ms <= 0:
        reasons.append("latency_p95_ms must be positive")
    if not source_json_sha256:
        reasons.append("measured evidence requires a hashed source benchmark JSON")
    measured = measured_requested and not reasons
    return EvidenceGate(
        truth=TRUTH_MEASURED if measured else TRUTH_UNVERIFIED,
        measured=measured,
        reasons=tuple(reasons),
    )


def build_evidence_record(
    *,
    hardware: str,
    platform_version: str,
    neat_version: str,
    model: str,
    sample_count: int,
    latency_p50_ms: float | None,
    latency_p95_ms: float | None,
    fps: float | None = None,
    power_w: float | None = None,
    energy_j: float | None = None,
    evidence_id: str = "",
    source_json: Path | None = None,
    measured_requested: bool = False,
) -> dict[str, object]:
    source_sha256 = sha256_file(source_json) if source_json else None
    gate = evaluate_measured_gate(
        hardware=hardware,
        platform_version=platform_version,
        neat_version=neat_version,
        model=model,
        sample_count=sample_count,
        latency_p50_ms=latency_p50_ms,
        latency_p95_ms=latency_p95_ms,
        source_json_sha256=source_sha256,
        measured_requested=measured_requested,
    )
    return {
        "schema": "inneros.guardian.sima.evidence.v1",
        "evidence_kind": "HISTORICAL_BENCHMARK",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "truth": gate.truth,
        "measured": gate.measured,
        "gate_reasons": list(gate.reasons),
        "hardware": hardware,
        "platform_version": platform_version,
        "neat_version": neat_version,
        "model": model,
        "sample_count": sample_count,
        "metrics": {
            "latency_p50_ms": latency_p50_ms,
            "latency_p95_ms": latency_p95_ms,
            "fps": fps,
            "power_w": power_w,
            "energy_j": energy_j,
        },
        "evidence_id": evidence_id or None,
        "source_json_sha256": source_sha256,
        "source_json_name": source_json.name if source_json else None,
        "official_docs": SIMA_DOCS,
    }


def dumps_record(record: dict[str, object]) -> str:
    return json.dumps(record, indent=2, sort_keys=False) + "\n"
