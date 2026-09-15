#!/usr/bin/env python3
"""One-Click Judge Live Launcher and Runtime Hardening for InnerOS Physical Guardian.

Orchestrates, health-checks, and manages the SiMa live sidecar, Guardian demo server,
and Physical I/O bridge with scoped PID tracking and zero simulated fallback in strict mode.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = REPO_ROOT / ".guardian_live_pids.json"
EVIDENCE_FILE = REPO_ROOT / "docs" / "sima_measured_evidence.json"
GATE_SCRIPT = REPO_ROOT / "scripts" / "sima_live_evidence_gate.py"
SIDECAR_SCRIPT = REPO_ROOT / "scripts" / "sima_sidecar_live.py"
DEMO_SERVER_SCRIPT = REPO_ROOT / "scripts" / "run_demo.py"

DEFAULT_SIDECAR_PORT = 8890
DEFAULT_DEMO_PORT = 8000


def is_port_healthy(url: str, timeout: float = 1.0) -> bool:
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (URLError, OSError, TimeoutError):
        return False


def get_sidecar_status(url: str, timeout: float = 1.0) -> dict[str, Any] | None:
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass
    return None


def read_pids() -> dict[str, int]:
    if STATE_FILE.is_file():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def write_pids(pids: dict[str, int]) -> None:
    STATE_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")


def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop_scoped_services() -> dict[str, str]:
    pids = read_pids()
    results: dict[str, str] = {}
    for name, pid in pids.items():
        if is_pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)
                if is_pid_alive(pid):
                    os.kill(pid, signal.SIGKILL)
                results[name] = f"stopped (PID {pid})"
            except Exception as e:
                results[name] = f"error stopping PID {pid}: {e}"
        else:
            results[name] = f"already terminated (PID {pid})"
    if STATE_FILE.is_file():
        STATE_FILE.unlink(missing_ok=True)
    return results


def validate_prerequisites(strict_live: bool = True) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not EVIDENCE_FILE.is_file():
        errors.append(f"Evidence file missing: {EVIDENCE_FILE}")
    elif strict_live and GATE_SCRIPT.is_file():
        # Validate through offline gate
        proc = subprocess.run(
            [sys.executable, str(GATE_SCRIPT), str(EVIDENCE_FILE)],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            errors.append(f"SiMa live evidence gate rejected evidence (code {proc.returncode}): {proc.stderr or proc.stdout}")

    if not SIDECAR_SCRIPT.is_file():
        errors.append(f"SiMa sidecar script missing: {SIDECAR_SCRIPT}")

    return len(errors) == 0, errors


def launch_live_stack(
    *,
    sidecar_port: int = DEFAULT_SIDECAR_PORT,
    demo_port: int = DEFAULT_DEMO_PORT,
    devkit_ip: str = "192.168.1.20",
    strict_live: bool = True,
    max_wait_sec: float = 6.0,
) -> dict[str, Any]:
    valid_prereqs, prereq_errors = validate_prerequisites(strict_live=strict_live)
    if not valid_prereqs:
        return {
            "status": "BLOCKED",
            "reason": "Prerequisite validation failed",
            "errors": prereq_errors,
        }

    pids = read_pids()
    active_pids: dict[str, int] = {}

    sidecar_url = f"http://127.0.0.1:{sidecar_port}/health"
    demo_url = f"http://127.0.0.1:{demo_port}/api/health"

    # 1. Start or reuse SiMa Sidecar
    sidecar_healthy = is_port_healthy(sidecar_url)
    sidecar_pid = pids.get("sima_sidecar")
    if sidecar_healthy:
        if sidecar_pid and is_pid_alive(sidecar_pid):
            active_pids["sima_sidecar"] = sidecar_pid
        sidecar_state = "reused (healthy)"
    else:
        # Clean stale PID if recorded
        if sidecar_pid and is_pid_alive(sidecar_pid):
            try:
                os.kill(sidecar_pid, signal.SIGTERM)
            except OSError:
                pass

        env = os.environ.copy()
        proc = subprocess.Popen(
            [
                sys.executable,
                str(SIDECAR_SCRIPT),
                "--port", str(sidecar_port),
                "--mode", "live",
                "--devkit-ip", devkit_ip,
                "--evidence", str(EVIDENCE_FILE),
            ],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        active_pids["sima_sidecar"] = proc.pid
        sidecar_state = f"spawned (PID {proc.pid})"

    # 2. Start or reuse Guardian Demo Server
    demo_healthy = is_port_healthy(demo_url)
    demo_pid = pids.get("guardian_demo")
    if demo_healthy:
        if demo_pid and is_pid_alive(demo_pid):
            active_pids["guardian_demo"] = demo_pid
        demo_state = "reused (healthy)"
    else:
        if demo_pid and is_pid_alive(demo_pid):
            try:
                os.kill(demo_pid, signal.SIGTERM)
            except OSError:
                pass

        env = os.environ.copy()
        env["GUARDIAN_SIMA_RUNTIME_URL"] = f"http://127.0.0.1:{sidecar_port}"
        proc_demo = subprocess.Popen(
            [
                sys.executable,
                "-m", "guardian_demo.server",
                "--port", str(demo_port),
            ],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        active_pids["guardian_demo"] = proc_demo.pid
        demo_state = f"spawned (PID {proc_demo.pid})"

    write_pids(active_pids)

    # 3. Wait for readiness
    t0 = time.time()
    sima_ready = False
    demo_ready = False
    while time.time() - t0 < max_wait_sec:
        if not sima_ready:
            sima_ready = is_port_healthy(sidecar_url)
        if not demo_ready:
            demo_ready = is_port_healthy(demo_url)
        if sima_ready and demo_ready:
            break
        time.sleep(0.3)

    if not sima_ready or not demo_ready:
        return {
            "status": "BLOCKED",
            "reason": "Services failed to become healthy within timeout",
            "sima_sidecar_ready": sima_ready,
            "guardian_demo_ready": demo_ready,
            "sidecar_url": f"http://127.0.0.1:{sidecar_port}",
            "demo_url": f"http://127.0.0.1:{demo_port}",
            "pids": active_pids,
        }

    # 4. Strict Live Verification Check
    if strict_live:
        sidecar_info = get_sidecar_status(sidecar_url) or {}
        if sidecar_info.get("status") != "OK":
            return {
                "status": "BLOCKED",
                "reason": f"SiMa sidecar reported unhealthy status: {sidecar_info}",
            }

    return {
        "status": "READY",
        "sidecar_url": f"http://127.0.0.1:{sidecar_port}",
        "demo_ui_url": f"http://127.0.0.1:{demo_port}",
        "sidecar_state": sidecar_state,
        "demo_state": demo_state,
        "mode": "MEASURED_LIVE" if strict_live else "DEMO",
        "evidence_file": str(EVIDENCE_FILE),
        "rehearsal_cmd": f"GUARDIAN_SIMA_RUNTIME_URL=http://127.0.0.1:{sidecar_port} python scripts/judge_rehearsal.py --runtime sima-slot --require-measured-sponsor",
        "pids": active_pids,
    }


def print_summary(res: dict[str, Any]) -> None:
    print("============================================================")
    print("  InnerOS Physical Guardian — Judge Live Launch Summary")
    print("============================================================")
    status = res.get("status", "UNKNOWN")
    print(f"  Status:         [{status}]")
    if status == "READY":
        print(f"  Guardian WebUI: {res.get('demo_ui_url')}")
        print(f"  SiMa Sidecar:   {res.get('sidecar_url')}")
        print(f"  Sidecar State:  {res.get('sidecar_state')}")
        print(f"  Demo State:     {res.get('demo_state')}")
        print(f"  Evidence Path:  {res.get('evidence_file')}")
        print("------------------------------------------------------------")
        print("  Judge Demonstration Ready. Run rehearsal:")
        print(f"    {res.get('rehearsal_cmd')}")
    else:
        print(f"  Failure Reason: {res.get('reason')}")
        for err in res.get("errors", []):
            print(f"    - [ERROR] {err}")
    print("============================================================")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="One-Click Judge Live Launcher for Physical Guardian")
    parser.add_argument("--stop", action="store_true", help="Stop all scoped launcher services")
    parser.add_argument("--status", action="store_true", help="Check status of running services")
    parser.add_argument("--sidecar-port", type=int, default=DEFAULT_SIDECAR_PORT)
    parser.add_argument("--demo-port", type=int, default=DEFAULT_DEMO_PORT)
    parser.add_argument("--devkit-ip", default="192.168.1.20")
    parser.add_argument("--allow-simulated", action="store_true", help="Allow simulated fixtures (default enforces strict live)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    if args.stop:
        results = stop_scoped_services()
        if args.json:
            print(json.dumps({"action": "stop", "results": results}, indent=2))
        else:
            print("Scoped services stopped:")
            for k, v in results.items():
                print(f"  - {k}: {v}")
        return 0

    if args.status:
        sidecar_healthy = is_port_healthy(f"http://127.0.0.1:{args.sidecar_port}/health")
        demo_healthy = is_port_healthy(f"http://127.0.0.1:{args.demo_port}/api/health")
        pids = read_pids()
        alive_pids = {k: pid for k, pid in pids.items() if is_pid_alive(pid)}
        is_ready = sidecar_healthy and demo_healthy
        report = {
            "status": "READY" if is_ready else "BLOCKED",
            "sidecar_healthy": sidecar_healthy,
            "demo_healthy": demo_healthy,
            "pids": alive_pids,
        }
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Status: [{'READY' if is_ready else 'BLOCKED'}]")
            print(f"  SiMa Sidecar (port {args.sidecar_port}): {'HEALTHY' if sidecar_healthy else 'OFFLINE'}")
            print(f"  Guardian Demo (port {args.demo_port}):   {'HEALTHY' if demo_healthy else 'OFFLINE'}")
            print(f"  Tracked PIDs: {alive_pids}")
        return 0 if is_ready else 1

    strict_live = not args.allow_simulated
    res = launch_live_stack(
        sidecar_port=args.sidecar_port,
        demo_port=args.demo_port,
        devkit_ip=args.devkit_ip,
        strict_live=strict_live,
    )

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print_summary(res)

    return 0 if res.get("status") == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
