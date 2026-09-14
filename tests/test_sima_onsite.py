from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from guardian_demo import sima_onsite


def test_missing_sima_cli_is_warning_not_fake_success(monkeypatch) -> None:
    monkeypatch.setattr(sima_onsite, "find_sima_cli", lambda: None)
    checks = sima_onsite.collect_sima_readiness(probe_device=True, probe_modelzoo=True)
    assert len(checks) == 1
    assert checks[0].name == "sima_cli"
    assert checks[0].status == "WARN"


def test_readonly_probes_use_only_discovery_and_model_listing(monkeypatch) -> None:
    monkeypatch.setattr(sima_onsite, "find_sima_cli", lambda: "/opt/sima-cli")
    seen: list[list[str]] = []

    def runner(argv, **_kwargs):
        seen.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    checks = sima_onsite.collect_sima_readiness(
        probe_device=True,
        probe_modelzoo=True,
        runner=runner,
    )
    assert [item.status for item in checks] == ["PASS", "PASS", "PASS"]
    assert seen == [
        ["/opt/sima-cli", "device", "discover"],
        ["/opt/sima-cli", "modelzoo", "list"],
    ]


def test_bringup_plan_validates_devkit_ip_and_uses_official_boundary() -> None:
    plan = sima_onsite.build_bringup_plan("192.0.2.10")
    assert "ssh sima@192.0.2.10" in plan
    assert "sima-cli sdk setup --devkit 192.0.2.10" in plan
    assert "sima-cli modelzoo list" in plan
    assert "sima-cli modelzoo get yolo_v8s" in plan
    with pytest.raises(ValueError):
        sima_onsite.build_bringup_plan("not-an-ip")


def test_measured_truth_fails_closed_when_evidence_is_incomplete() -> None:
    record = sima_onsite.build_evidence_record(
        hardware="Modalix DevKit",
        platform_version="",
        neat_version="2.1.3",
        model="yolo_v8s",
        sample_count=1,
        latency_p50_ms=5.0,
        latency_p95_ms=7.0,
        measured_requested=True,
    )
    assert record["truth"] == sima_onsite.TRUTH_UNVERIFIED
    assert record["measured"] is False
    assert record["gate_reasons"]


def test_measured_truth_requires_hashed_source_benchmark(tmp_path: Path) -> None:
    source = tmp_path / "vendor-benchmark.json"
    source.write_text(json.dumps({"latency_ms": [4.0, 4.2, 5.8]}), encoding="utf-8")
    record = sima_onsite.build_evidence_record(
        hardware="Modalix MLSoC DevKit",
        platform_version="2.1.3",
        neat_version="2.1.3",
        model="yolo_v8s",
        sample_count=50,
        latency_p50_ms=4.2,
        latency_p95_ms=5.8,
        fps=120.0,
        source_json=source,
        measured_requested=True,
    )
    assert record["truth"] == sima_onsite.TRUTH_MEASURED
    assert record["measured"] is True
    assert record["gate_reasons"] == []
    assert len(record["source_json_sha256"]) == 64


def test_measured_truth_is_denied_without_source_even_with_good_numbers() -> None:
    record = sima_onsite.build_evidence_record(
        hardware="Modalix MLSoC DevKit",
        platform_version="2.1.3",
        neat_version="2.1.3",
        model="yolo_v8s",
        sample_count=50,
        latency_p50_ms=4.2,
        latency_p95_ms=5.8,
        fps=120.0,
        measured_requested=True,
    )
    assert record["truth"] == sima_onsite.TRUTH_UNVERIFIED
    assert record["measured"] is False
    assert "hashed source benchmark JSON" in " ".join(record["gate_reasons"])


def test_source_json_is_hashed_not_embedded(tmp_path: Path) -> None:
    source = tmp_path / "vendor-benchmark.json"
    source.write_text(json.dumps({"raw": "vendor output"}), encoding="utf-8")
    record = sima_onsite.build_evidence_record(
        hardware="Modalix MLSoC DevKit",
        platform_version="2.1.3",
        neat_version="2.1.3",
        model="yolo_v8s",
        sample_count=10,
        latency_p50_ms=4.0,
        latency_p95_ms=6.0,
        source_json=source,
        measured_requested=True,
    )
    assert record["source_json_name"] == "vendor-benchmark.json"
    assert len(record["source_json_sha256"]) == 64
    assert "vendor output" not in sima_onsite.dumps_record(record)
