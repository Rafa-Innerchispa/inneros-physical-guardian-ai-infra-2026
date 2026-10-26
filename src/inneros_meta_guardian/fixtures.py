"""Public, synthetic-only incident fixtures for a reproducible judge demo."""
from copy import deepcopy

SCENARIOS = {
    "door_propped": {
        "title": "Pedestrian door held open",
        "site": "DEMO-LAB / Lobby A",
        "severity": "high",
        "signals": [
            {"source": "sensor:door-contact-01", "metric": "door_open_seconds", "value": 96, "truth": "SIMULATED_FIXTURE"},
            {"source": "camera:entry-01", "metric": "person_in_zone", "value": True, "truth": "SIMULATED_FIXTURE"},
            {"source": "network:edge-01", "metric": "network_healthy", "value": True, "truth": "SIMULATED_FIXTURE"},
        ],
        "recommended_action": "activate_beacon",
        "explanation": "A door has been open for 96 seconds while the entry zone is occupied. An operator warning is appropriate; unlocking doors is not allowed.",
    },
    "camera_offline": {
        "title": "Entry camera connectivity loss",
        "site": "DEMO-LAB / Lobby A",
        "severity": "medium",
        "signals": [
            {"source": "network:poe-switch-01", "metric": "poe_port_up", "value": False, "truth": "SIMULATED_FIXTURE"},
            {"source": "camera:entry-01", "metric": "rtsp_reachable", "value": False, "truth": "SIMULATED_FIXTURE"},
            {"source": "network:uplink-01", "metric": "uplink_healthy", "value": True, "truth": "SIMULATED_FIXTURE"},
        ],
        "recommended_action": "notify_operator",
        "explanation": "A camera stream is unreachable while the upstream network is healthy. Check the PoE port locally before changing any device configuration.",
    },
    "unverified_alert": {
        "title": "Unverified access-control event",
        "site": "DEMO-LAB / Parking gate",
        "severity": "low",
        "signals": [
            {"source": "reader:visitor-01", "metric": "badge_read", "value": "unknown", "truth": "SIMULATED_FIXTURE"},
            {"source": "sensor:gate-01", "metric": "gate_closed", "value": True, "truth": "SIMULATED_FIXTURE"},
        ],
        "recommended_action": "notify_operator",
        "explanation": "A visitor credential could not be validated. Notify a human; never open the gate based on this incident.",
    },
}


def get_fixture(name: str) -> dict:
    if name not in SCENARIOS:
        raise ValueError("Unknown scenario")
    return deepcopy(SCENARIOS[name])
