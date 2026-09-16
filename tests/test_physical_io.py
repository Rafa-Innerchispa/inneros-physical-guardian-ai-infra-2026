from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from guardian_demo.engine import GuardianDemoEngine
from guardian_demo.models import ProposedAction
from guardian_demo.physical_io import ENV_VAR, PhysicalIOBridge


class ContractHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _read(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        payload = self._read()
        self.server.requests.append((self.path, payload, self.headers.get("Idempotency-Key")))  # type: ignore[attr-defined]
        identity = {
            key: payload[key]
            for key in ("action_id", "idempotency_key", "action_type", "target_id")
        }
        if self.path == "/v1/action":
            self._send({**identity, "ok": True, "accepted": True})
            return
        if self.path == "/v1/verify":
            self._send(
                {
                    **identity,
                    "ok": True,
                    "verified": self.server.verify_success,  # type: ignore[attr-defined]
                    "truth": self.server.truth,  # type: ignore[attr-defined]
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)


def start_contract_server(*, verify_success: bool = True, truth: str | None = "PRODUCT_HTTP_READBACK"):
    server = ThreadingHTTPServer(("127.0.0.1", 0), ContractHandler)
    server.requests = []  # type: ignore[attr-defined]
    server.verify_success = verify_success  # type: ignore[attr-defined]
    server.truth = truth  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def stop_contract_server(server: ThreadingHTTPServer, thread: threading.Thread) -> None:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def test_bridge_is_optional_and_fallback_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_VAR, raising=False)
    status = PhysicalIOBridge().status()
    assert status["status"] == "FALLBACK_ONLY"
    assert status["truth"] == "SIMULATED_REFERENCE_IO"


def test_bridge_rejects_non_loopback_destination(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_VAR, "https://example.com")
    bridge = PhysicalIOBridge()
    assert bridge.status()["status"] == "INVALID_LOCAL_BRIDGE_CONFIG"
    with pytest.raises(RuntimeError, match="loopback-only"):
        bridge.execute(
            ProposedAction(
                action_id="action-external",
                action_type="beacon_warning",
                target="reference-low-voltage-beacon",
                reason="must stay local",
            )
        )


def test_bridge_maps_action_and_requires_verified_readback(monkeypatch: pytest.MonkeyPatch) -> None:
    server, thread = start_contract_server()
    try:
        host, port = server.server_address
        monkeypatch.setenv(ENV_VAR, f"http://{host}:{port}")
        result = PhysicalIOBridge().execute(
            ProposedAction(
                action_id="action-bridge-test",
                action_type="beacon_warning",
                target="reference-low-voltage-beacon",
                reason="contract test",
            )
        )
        assert result["verified"] is True
        assert result["truth"] == "PRODUCT_HTTP_READBACK"
        assert result["contract_action"] == "beacon.set"
        assert result["contract_target"] == "demo-beacon"
        assert result["total_round_trip_ms"] >= 0
        requests = server.requests  # type: ignore[attr-defined]
        assert [row[0] for row in requests] == ["/v1/action", "/v1/verify"]
        assert requests[0][1]["parameters"] == {"state": "on"}
        assert requests[0][2] == "guardian-action-bridge-test"
    finally:
        stop_contract_server(server, thread)


@pytest.mark.parametrize("truth", [None, "", "UNKNOWN_PHYSICAL_TRUTH"])
def test_bridge_rejects_missing_or_unknown_physical_truth(
    monkeypatch: pytest.MonkeyPatch,
    truth: str | None,
) -> None:
    server, thread = start_contract_server(truth=truth)
    try:
        host, port = server.server_address
        monkeypatch.setenv(ENV_VAR, f"http://{host}:{port}")
        with pytest.raises(RuntimeError, match="truth is missing or unrecognized"):
            PhysicalIOBridge().execute(
                ProposedAction(
                    action_id="action-unknown-truth",
                    action_type="beacon_warning",
                    target="reference-low-voltage-beacon",
                    reason="must fail closed",
                )
            )
    finally:
        stop_contract_server(server, thread)


def test_engine_approval_uses_permanent_contract_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    server, thread = start_contract_server()
    try:
        host, port = server.server_address
        monkeypatch.setenv(ENV_VAR, f"http://{host}:{port}")
        engine = GuardianDemoEngine()
        assert engine.catalog()["physical_io"]["status"] == "READY_CONFIGURED"
        engine.run("loitering_after_hours")
        approved = engine.approve()
        trace = approved["current"]
        evidence = approved["latest_evidence"]
        assert trace["status"] == "VERIFIED"
        assert trace["verified"] is True
        assert trace["truth"]["physical_io"] == "PRODUCT_HTTP_READBACK"
        assert trace["metrics"]["physical_io_round_trip_ms"] >= 0
        verify = next(stage for stage in trace["stages"] if stage["stage"] == "VERIFY")
        assert verify["truth"] == "PRODUCT_HTTP_READBACK"
        assert evidence["physical_io_bridge"]["status"] == "READY_CONFIGURED"
        assert ENV_VAR not in json.dumps(evidence)
        assert f"{host}:{port}" not in json.dumps(evidence)
    finally:
        stop_contract_server(server, thread)


def test_engine_fails_closed_when_readback_is_not_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    server, thread = start_contract_server(verify_success=False)
    try:
        host, port = server.server_address
        monkeypatch.setenv(ENV_VAR, f"http://{host}:{port}")
        engine = GuardianDemoEngine()
        engine.run("restricted_zone_entry")
        state = engine.approve()
        trace = state["current"]
        assert trace["status"] == "ACTION_FAILED_SAFE"
        assert trace["verified"] is False
        assert trace["truth"]["physical_io"] == "FAILED_CLOSED"
        verify = next(stage for stage in trace["stages"] if stage["stage"] == "VERIFY")
        assert verify["status"] == "failed_closed"
        assert state["latest_evidence"]["final"] is True
        assert "readback verification failed" in state["latest_evidence"]["physical_io_failure"]
    finally:
        stop_contract_server(server, thread)


def test_unmapped_operator_notification_remains_local_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    server, thread = start_contract_server()
    try:
        host, port = server.server_address
        monkeypatch.setenv(ENV_VAR, f"http://{host}:{port}")
        engine = GuardianDemoEngine()
        engine.run("repeated_access_attempt")
        state = engine.approve()
        assert state["current"]["status"] == "VERIFIED"
        assert state["current"]["truth"]["physical_io"] == "SIMULATED_REFERENCE_IO"
        assert server.requests == []  # type: ignore[attr-defined]
    finally:
        stop_contract_server(server, thread)
