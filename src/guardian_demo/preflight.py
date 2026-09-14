from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from importlib import metadata
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
EXPECTED_SPEECHMATICS_VERSION = "1.1.1"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    required: bool
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


def _check(name: str, ok: bool, *, required: bool, detail_ok: str, detail_fail: str) -> Check:
    return Check(
        name=name,
        status="PASS" if ok else ("FAIL" if required else "WARN"),
        required=required,
        detail=detail_ok if ok else detail_fail,
    )


def _python_check() -> Check:
    version = sys.version_info
    ok = version >= (3, 11)
    return _check(
        "python",
        ok,
        required=True,
        detail_ok=f"Python {version.major}.{version.minor}.{version.micro}",
        detail_fail=f"Python {version.major}.{version.minor}.{version.micro}; Guardian requires Python 3.11+",
    )


def _repo_files_check() -> Check:
    required_files = (
        "app/index.html",
        "scripts/run_demo.py",
        "scripts/self_test.py",
        "src/guardian_demo/server.py",
    )
    missing = [path for path in required_files if not (REPO_ROOT / path).is_file()]
    return _check(
        "core_files",
        not missing,
        required=True,
        detail_ok="Core judge application files are present",
        detail_fail="Missing core files: " + ", ".join(missing),
    )


def _git_head() -> Check:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        sha = proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return Check("git_head", "WARN", False, "Git HEAD unavailable")
    return Check("git_head", "PASS", False, sha)


def _package_version(distribution: str) -> str | None:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return None


def _speechmatics_sdk_check(required: bool) -> Check:
    version = _package_version("speechmatics-rt")
    ok = version == EXPECTED_SPEECHMATICS_VERSION
    if version is None:
        detail_fail = "speechmatics-rt is not installed in this Python environment"
    else:
        detail_fail = (
            f"speechmatics-rt {version} installed; expected {EXPECTED_SPEECHMATICS_VERSION} for the event baseline"
        )
    return _check(
        "speechmatics_sdk",
        ok,
        required=required,
        detail_ok=f"speechmatics-rt {version}",
        detail_fail=detail_fail,
    )


def _secret_presence_check(env_name: str, name: str, required: bool) -> Check:
    present = bool(os.environ.get(env_name, "").strip())
    return _check(
        name,
        present,
        required=required,
        detail_ok=f"{env_name} is bound server-side/environment-side (value hidden)",
        detail_fail=f"{env_name} is not bound; value is never printed by preflight",
    )


def _pyaudio_check(required: bool) -> Check:
    available = importlib.util.find_spec("pyaudio") is not None
    return _check(
        "microphone_driver",
        available,
        required=required,
        detail_ok="PyAudio import is available for live microphone capture",
        detail_fail="PyAudio is unavailable; typed transcript fallback remains usable",
    )


def _loopback_url_check(env_name: str, name: str, required: bool) -> Check:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return _check(
            name,
            False,
            required=required,
            detail_ok="",
            detail_fail=f"{env_name} is not configured",
        )
    parsed = urlparse(raw)
    safe = (
        parsed.scheme in {"http", "https"}
        and parsed.hostname in LOOPBACK_HOSTS
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
    )
    return _check(
        name,
        safe,
        required=required,
        detail_ok=f"{env_name} is configured to a loopback-only endpoint (address hidden)",
        detail_fail=f"{env_name} is configured but violates the loopback/no-credential boundary",
    )


def _guardian_health_check(base_url: str, required: bool) -> Check:
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in LOOPBACK_HOSTS:
        return Check(
            "guardian_health",
            "FAIL" if required else "WARN",
            required,
            "Guardian health URL must remain loopback-only",
        )
    try:
        with urlopen(base_url.rstrip("/") + "/api/health", timeout=1.5) as response:  # nosec B310
            body = json.loads(response.read().decode("utf-8"))
        healthy = response.status == 200 and body.get("ok") is True
    except Exception:
        healthy = False
    return _check(
        "guardian_health",
        healthy,
        required=required,
        detail_ok="Guardian /api/health is reachable on loopback",
        detail_fail="Guardian is not currently reachable on loopback; start scripts/run_demo.py",
    )


def collect_checks(
    *,
    require_speechmatics: bool = False,
    require_mic: bool = False,
    require_sima: bool = False,
    require_physical_io: bool = False,
    require_guardian: bool = False,
    guardian_url: str = "http://127.0.0.1:8787",
) -> list[Check]:
    checks = [
        _python_check(),
        _repo_files_check(),
        _git_head(),
        _speechmatics_sdk_check(require_speechmatics),
        _secret_presence_check("SPEECHMATICS_API_KEY", "speechmatics_api_key", require_speechmatics),
        _secret_presence_check("GUARDIAN_VOICE_BRIDGE_TOKEN", "voice_bridge_token", False),
        _pyaudio_check(require_mic),
        _loopback_url_check("GUARDIAN_SIMA_RUNTIME_URL", "sima_sidecar", require_sima),
        _loopback_url_check("GUARDIAN_PHYSICAL_IO_URL", "physical_io_sidecar", require_physical_io),
        _guardian_health_check(guardian_url, require_guardian),
    ]
    return checks


def summarize(checks: Iterable[Check]) -> dict[str, object]:
    items = list(checks)
    required_failures = [item.name for item in items if item.required and not item.ok]
    warnings = [item.name for item in items if item.status == "WARN"]
    return {
        "ok": not required_failures,
        "required_failures": required_failures,
        "warnings": warnings,
        "checks": [asdict(item) for item in items],
    }


def _render_human(report: dict[str, object]) -> str:
    lines = ["InnerOS Physical Guardian - event preflight", ""]
    for item in report["checks"]:  # type: ignore[index]
        marker = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL"}[item["status"]]  # type: ignore[index]
        required = " required" if item["required"] else " optional"  # type: ignore[index]
        lines.append(f"{marker:4} {item['name']}{required}: {item['detail']}")  # type: ignore[index]
    lines.append("")
    if report["ok"]:
        lines.append("READY: all required preflight checks passed.")
    else:
        failures = ", ".join(report["required_failures"])  # type: ignore[arg-type]
        lines.append(f"BLOCKED: required checks failed: {failures}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fail-closed preflight for the AI Infra Summit judge demo")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--require-speechmatics", action="store_true")
    parser.add_argument("--require-mic", action="store_true")
    parser.add_argument("--require-sima", action="store_true")
    parser.add_argument("--require-physical-io", action="store_true")
    parser.add_argument("--require-guardian", action="store_true")
    parser.add_argument("--guardian-url", default="http://127.0.0.1:8787")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = summarize(
        collect_checks(
            require_speechmatics=args.require_speechmatics,
            require_mic=args.require_mic,
            require_sima=args.require_sima,
            require_physical_io=args.require_physical_io,
            require_guardian=args.require_guardian,
            guardian_url=args.guardian_url,
        )
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        print(_render_human(report))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
