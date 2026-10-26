"""Governed incident lifecycle: observe > reason > approve > act > verify > prove."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
import threading
from .evidence import Store
from .fixtures import SCENARIOS, get_fixture
from .models import ModelUnavailable, narrate
from .policy import evaluate


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LifecycleError(ValueError):
    pass


class Guardian:
    def __init__(self, db: str = ":memory:") -> None:
        self.store = Store(db)
        self.lock = threading.RLock()
        self.actuator: dict[str, bool] = {}
        self.scenarios = {k: v["title"] for k, v in SCENARIOS.items()}

    def ingest(self, scenario: str = "door_propped") -> dict:
        with self.lock:
            fixture = get_fixture(scenario)
            incident = {"id": str(uuid4()), "scenario": scenario, "truth": "SIMULATED_FIXTURE", "status": "observed", "created_at": now(), "updated_at": now(), "narration": None, **fixture}
            self.store.upsert(incident)
            self.store.append(incident["id"], "OBSERVE", {"scenario": scenario, "truth": incident["truth"], "signals": incident["signals"]})
            return incident

    def get(self, id: str) -> dict:
        incident = self.store.get(id)
        if incident is None:
            raise LifecycleError("Incident not found")
        return incident

    def _save(self, incident: dict, event: str, payload: dict) -> dict:
        incident["updated_at"] = now()
        self.store.upsert(incident)
        self.store.append(incident["id"], event, payload)
        return incident

    def analyze(self, id: str, mode: str = "deterministic") -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "observed":
                raise LifecycleError("Can only analyze an observed incident")
            if mode not in ("deterministic", "ollama", "meta"):
                raise LifecycleError("Unknown inference mode")
            try:
                narrative = narrate(mode, incident)
            except ModelUnavailable as exc:
                # Do not silently pretend this was a Meta or Ollama call.
                narrative = narrate("deterministic", incident)
                narrative["fallback_reason"] = str(exc)
                narrative["requested_provider"] = mode
            incident["narration"] = narrative
            incident["status"] = "analyzed"
            incident["policy"] = evaluate(incident["recommended_action"], incident).as_dict() if incident["status"] == "analyzed" else None
            return self._save(incident, "REASON", {"mode": mode, "provider": narrative["provider"], "truth": narrative["truth"], "model": narrative["model"], "policy": incident["policy"]})

    def approve(self, id: str, operator: str, action: str) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "analyzed":
                raise LifecycleError("Human approval requires an analyzed incident")
            if not isinstance(operator, str) or not (2 <= len(operator.strip()) <= 60):
                raise LifecycleError("Operator display name required (2-60 characters)")
            decision = evaluate(action, incident)
            if not decision.allowed:
                self.store.append(id, "DENY", {"action": action, "reason": decision.reason})
                raise LifecycleError(decision.reason)
            incident["approval"] = {"operator": operator.strip(), "action": action, "approved_at": now(), "truth": "DEMO_OPERATOR_ACK"}
            incident["status"] = "approved"
            return self._save(incident, "APPROVE", {"operator": operator.strip(), "action": action, "truth": "DEMO_OPERATOR_ACK"})

    def execute(self, id: str) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "approved":
                raise LifecycleError("Execution requires human approval")
            approval = incident.get("approval") or {}
            decision = evaluate(approval.get("action", ""), incident)
            if not decision.allowed or approval.get("action") != incident["recommended_action"]:
                raise LifecycleError("Policy blocked action")
            # Virtual actuator: NO real device API calls or network mutations.
            self.actuator[id] = True
            incident["execution"] = {"action": approval["action"], "issued_at": now(), "truth": "SIMULATED_REFERENCE_IO", "transport": "in-process virtual actuator"}
            incident["status"] = "executed"
            return self._save(incident, "ACT", incident["execution"])

    def verify(self, id: str) -> dict:
        with self.lock:
            incident = self.get(id)
            if incident["status"] != "executed":
                raise LifecycleError("Verification requires an executed action")
            # Readback from a separate virtual actuator state, not from command acknowledgment.
            verified = self.actuator.get(id) is True
            incident["verification"] = {"passed": verified, "verified_at": now(), "method": "virtual-state-readback", "truth": "SIMULATED_REFERENCE_IO"}
            incident["status"] = "verified" if verified else "failed_safe"
            return self._save(incident, "VERIFY", incident["verification"])

    def evidence(self, id: str) -> dict:
        incident = self.get(id)
        return {"schema": "inneros-guardian-evidence-v1", "incident": incident, "audit": self.store.audit(id), "global_chain_validation": self.store.verify(), "warning": "SIMULATION. Hash chain is tamper-evident within this local DB; not an external notarization or live hardware proof."}

    def reset_virtual_state(self, id: str) -> None:
        """Test hook: simulates failed actuator state before readback."""
        with self.lock:
            self.actuator[id] = False
