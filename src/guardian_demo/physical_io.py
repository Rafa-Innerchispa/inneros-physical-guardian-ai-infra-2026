from __future__ import annotations

import json
import os
from time import perf_counter
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .models import ProposedAction


ENV_VAR = "GUARDIAN_PHYSICAL_IO_URL"
TIMEOUT_SECONDS = 3.0
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOWED_TRUTH = {"PRODUCT_HTTP_READBACK", "REAL_LOW_VOLTAGE_HARDWARE"}

# Hackathon-facing actions remain descriptive and policy-oriented. Only this
# adapter knows how they map to the permanent product's generic Physical I/O
# HTTP contract.
ACTION_MAP: dict[str, tuple[str, str, dict[str, object]]] = {
    "beacon_warning": ("beacon.set", "demo-beacon", {"state": "on"}),
    "dmx_attention": ("light.set", "demo-light", {"state": "on"}),
}


class PhysicalIOBridge:
    """Loopback-only bridge to the permanent Physical Guardian HTTP I/O contract.

    The URL is deployment configuration, never event/model input. The bridge is
    optional so the judge application remains fully usable offline. When it is
    configured, mapped physical actions fail closed on any transport, identity,
    or readback verification error.
    """

    def _configured_url(self) -> str | None:
        raw = os.environ.get(ENV_VAR, "").strip()
        if not raw:
            return None

        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            raise RuntimeError(f"{ENV_VAR} must use http or https")
        if parsed.hostname not in LOOPBACK_HOSTS:
            raise RuntimeError(f"{ENV_VAR} must point to a loopback-only Physical I/O sidecar")
        if parsed.username or parsed.password:
            raise RuntimeError(f"{ENV_VAR} must not embed credentials")
        if parsed.query or parsed.fragment:
            raise RuntimeError(f"{ENV_VAR} must not contain a query string or fragment")
        return raw.rstrip("/")

    def status(self) -> dict[str, object]:
        try:
            configured = bool(self._configured_url())
        except RuntimeError:
            return {
                "status": "INVALID_LOCAL_BRIDGE_CONFIG",
                "truth": "NOT_EXECUTED",
                "mapped_actions": sorted(ACTION_MAP),
            }
        return {
            "status": "READY_CONFIGURED" if configured else "FALLBACK_ONLY",
            "truth": "PRODUCT_HTTP_CONTRACT" if configured else "SIMULATED_REFERENCE_IO",
            "mapped_actions": sorted(ACTION_MAP),
        }

    @staticmethod
    def can_execute(action_type: str) -> bool:
        return action_type in ACTION_MAP

    @staticmethod
    def _validate_identity(payload: dict[str, Any], expected: dict[str, str]) -> None:
        for field_name, expected_value in expected.items():
            supplied = payload.get(field_name)
            if supplied is not None and supplied != expected_value:
                raise RuntimeError(f"Physical I/O response identity mismatch: {field_name}")

    @staticmethod
    def _post_json(url: str, payload: dict[str, object]) -> tuple[dict[str, Any], float]:
        data = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        request = Request(
            url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Idempotency-Key": str(payload["idempotency_key"]),
            },
        )
        started = perf_counter()
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # nosec B310 - loopback URL validated by caller
                raw = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            # Do not leak a configured endpoint or credentials through error text.
            raise RuntimeError(f"Physical I/O local bridge failed: {type(exc).__name__}") from exc
        elapsed_ms = (perf_counter() - started) * 1000.0
        if not isinstance(raw, dict):
            raise RuntimeError("Physical I/O response must be a JSON object")
        return raw, elapsed_ms

    def execute(self, action: ProposedAction) -> dict[str, object]:
        base_url = self._configured_url()
        if not base_url:
            raise RuntimeError("Physical I/O bridge is not configured")
        mapped = ACTION_MAP.get(action.action_type)
        if mapped is None:
            raise RuntimeError(f"No permanent Physical I/O mapping exists for action: {action.action_type}")

        product_action, product_target, parameters = mapped
        identity = {
            "action_id": action.action_id,
            "idempotency_key": f"guardian-{action.action_id}",
            "action_type": product_action,
            "target_id": product_target,
        }
        action_payload: dict[str, object] = {**identity, "parameters": parameters}

        total_started = perf_counter()
        accepted, action_ms = self._post_json(base_url + "/v1/action", action_payload)
        self._validate_identity(accepted, identity)
        if accepted.get("ok") is not True or accepted.get("accepted") is False:
            raise RuntimeError("Physical I/O action was not accepted")

        verified, verify_ms = self._post_json(base_url + "/v1/verify", identity)
        self._validate_identity(verified, identity)
        if verified.get("ok") is not True or verified.get("verified") is not True:
            raise RuntimeError("Physical I/O readback verification failed")

        truth = str(verified.get("truth") or accepted.get("truth") or "PRODUCT_HTTP_READBACK")
        if truth not in ALLOWED_TRUTH:
            truth = "PRODUCT_HTTP_READBACK"

        return {
            "ok": True,
            "verified": True,
            "truth": truth,
            "contract_action": product_action,
            "contract_target": product_target,
            "action_round_trip_ms": round(action_ms, 3),
            "verify_round_trip_ms": round(verify_ms, 3),
            "total_round_trip_ms": round((perf_counter() - total_started) * 1000.0, 3),
        }


PHYSICAL_IO = PhysicalIOBridge()
