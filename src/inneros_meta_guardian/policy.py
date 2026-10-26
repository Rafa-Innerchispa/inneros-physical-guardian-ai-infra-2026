"""Deterministic, fail-closed policy. The LLM never authorizes physical actions."""
from dataclasses import dataclass

ALLOWED_DEMO_ACTIONS = frozenset({"notify_operator", "activate_beacon"})
FORBIDDEN_ACTIONS = frozenset({"unlock_door", "disable_alarm", "open_gate", "reboot_device", "execute_shell", "change_firewall"})


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    action: str
    reason: str
    requires_approval: bool = True

    def as_dict(self) -> dict:
        return {"allowed": self.allowed, "action": self.action, "reason": self.reason, "requires_approval": self.requires_approval}


def evaluate(action: str, incident: dict) -> PolicyDecision:
    if action not in ALLOWED_DEMO_ACTIONS:
        return PolicyDecision(False, action, "Denied: action is outside demo allowlist.")
    if incident.get("truth") != "SIMULATED_FIXTURE":
        return PolicyDecision(False, action, "Denied: this sandbox only processes documented synthetic fixtures.")
    if incident.get("status") not in {"analyzed", "approved", "executed", "verified"}:
        return PolicyDecision(False, action, "Denied: incident must be analyzed before approval.")
    if action != incident.get("recommended_action"):
        return PolicyDecision(False, action, "Denied: action differs from deterministic recommendation.")
    return PolicyDecision(True, action, "Demo-only action, subject to human approval and independent readback.")
