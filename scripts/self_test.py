#!/usr/bin/env python3
"""Zero-dependency acceptance test for the hackathon judge application."""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardian_demo.engine import GuardianDemoEngine  # noqa: E402
from guardian_demo.models import ProposedAction  # noqa: E402
from guardian_demo.server import ENGINE, build_server  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS  {message}")


def request(base: str, path: str, *, method: str = "GET", payload: dict | None = None, auth: str | None = None) -> tuple[int, str, str]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = auth
    req = Request(base + path, data=data, method=method, headers=headers)
    with urlopen(req, timeout=3) as response:  # nosec B310 - ephemeral loopback server only
        return response.status, response.headers.get("Content-Type", ""), response.read().decode("utf-8")


def engine_checks() -> None:
    engine = GuardianDemoEngine()
    catalog = engine.catalog()
    runtimes = {row["runtime_id"]: row for row in catalog["runtimes"]}
    check(runtimes["local-deterministic"]["status"] == "READY", "offline deterministic runtime is ready")
    check(runtimes["sima-slot"]["truth"] == "NOT_BENCHMARKED", "SiMa slot does not fabricate a benchmark")
    check("unlock_door" in catalog["safety"]["denied_actions"], "high-impact door unlock is explicitly denied")

    state = engine.run("loitering_after_hours")
    check(state["current"]["status"] == "AWAITING_APPROVAL", "demo stops at explicit human approval gate")
    check(state["current"]["truth"]["detections"] == "SIMULATED_FIXTURE", "fixture inference is truth-labeled")

    approved = engine.approve()
    check(approved["current"]["status"] == "VERIFIED", "approved bounded action reaches verified state")
    check(approved["latest_evidence"]["evidence_id"].startswith("ev-"), "verified flow produces sealed evidence id")

    engine.reset()
    engine.run("restricted_zone_entry")
    rejected = engine.reject()
    check(rejected["current"]["status"] == "REJECTED_SAFE", "rejected action becomes a safe no-op")

    engine.reset()
    engine.run("loitering_after_hours")
    if engine.current is None:
        raise AssertionError("expected active trace")
    engine.current.proposed_action = ProposedAction(
        action_id="self-test-denied",
        action_type="unlock_door",
        target="door-controller",
        reason="self-test must fail closed",
    )
    try:
        engine.approve()
    except PermissionError:
        print("PASS  dangerous action fails closed at approval gate")
    else:
        raise AssertionError("dangerous action unexpectedly passed approval gate")


def http_checks() -> None:
    previous_user = os.environ.pop("GUARDIAN_DEMO_USER", None)
    previous_password = os.environ.pop("GUARDIAN_DEMO_PASSWORD", None)
    ENGINE.reset()
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"

    try:
        status, content_type, body = request(base, "/api/health")
        check(status == 200 and "application/json" in content_type, "health endpoint is reachable")
        check(json.loads(body)["ok"] is True, "health endpoint reports healthy")

        status, content_type, body = request(base, "/")
        check(status == 200 and "text/html" in content_type, "single-screen WebUI is served")
        required_ui_markers = (
            "Physical Guardian",
            "See. Understand. Decide. Act. Verify. Prove.",
            'id="runBtn"',
            'id="approveBtn"',
            'id="evidencePreview"',
        )
        check(all(marker in body for marker in required_ui_markers), "judge WebUI contains critical controls and evidence panel")

        state = json.loads(
            request(
                base,
                "/api/demo/run",
                method="POST",
                payload={"scenario": "repeated_access_attempt", "runtime_id": "local-deterministic"},
            )[2]
        )
        check(state["current"]["status"] == "AWAITING_APPROVAL", "HTTP demo API reaches approval gate")
        state = json.loads(request(base, "/api/action/approve", method="POST", payload={})[2])
        check(state["current"]["verified"] is True, "HTTP approval API reaches verified evidence state")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        ENGINE.reset()
        if previous_user is not None:
            os.environ["GUARDIAN_DEMO_USER"] = previous_user
        if previous_password is not None:
            os.environ["GUARDIAN_DEMO_PASSWORD"] = previous_password


def auth_checks() -> None:
    previous_user = os.environ.get("GUARDIAN_DEMO_USER")
    previous_password = os.environ.get("GUARDIAN_DEMO_PASSWORD")
    os.environ["GUARDIAN_DEMO_USER"] = "judge"
    os.environ["GUARDIAN_DEMO_PASSWORD"] = "self-test-secret"
    server = build_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"

    try:
        check(request(base, "/api/health")[0] == 200, "health remains available for readiness probes with auth enabled")
        try:
            request(base, "/")
        except HTTPError as exc:
            check(exc.code == 401, "judge UI is protected when hosted auth is enabled")
        else:
            raise AssertionError("judge UI unexpectedly accessible without credentials")

        token = base64.b64encode(b"judge:self-test-secret").decode("ascii")
        status, content_type, _ = request(base, "/", auth=f"Basic {token}")
        check(status == 200 and "text/html" in content_type, "valid hosted demo credentials unlock WebUI")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        if previous_user is None:
            os.environ.pop("GUARDIAN_DEMO_USER", None)
        else:
            os.environ["GUARDIAN_DEMO_USER"] = previous_user
        if previous_password is None:
            os.environ.pop("GUARDIAN_DEMO_PASSWORD", None)
        else:
            os.environ["GUARDIAN_DEMO_PASSWORD"] = previous_password


def main() -> int:
    print("InnerOS Physical Guardian — zero-dependency acceptance test\n")
    engine_checks()
    http_checks()
    auth_checks()
    print("\nALL ACCEPTANCE CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
