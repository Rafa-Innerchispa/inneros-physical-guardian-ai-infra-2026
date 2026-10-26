"""Exercise every incident stage against a running local Guardian server."""
import json
import os
import urllib.request

BASE = os.getenv("GUARDIAN_BASE", "http://127.0.0.1:8787")


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=4) as response:
        return json.load(response)


def post(path, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=4) as response:
        return json.load(response)


def main():
    assert get("/api/health")["ok"]
    row = post("/api/incidents", {"scenario": "door_propped"})
    assert row["status"] == "observed"
    row = post(f"/api/incidents/{row['id']}/analyze", {"mode": "deterministic"})
    assert row["status"] == "analyzed"
    assert row["policy"]["allowed"]
    row = post(f"/api/incidents/{row['id']}/approve", {"operator": "Judge demo", "action": row["recommended_action"]})
    assert row["status"] == "approved"
    row = post(f"/api/incidents/{row['id']}/execute", {})
    assert row["status"] == "executed"
    row = post(f"/api/incidents/{row['id']}/verify", {})
    assert row["status"] == "verified"
    proof = get(f"/api/incidents/{row['id']}/evidence")
    assert proof["global_chain_validation"]["valid"]
    print("PASS: OBSERVE -> REASON -> APPROVE -> ACT -> VERIFY -> PROVE")
    print("Audit entries:", proof["global_chain_validation"]["entries"])
    print("TRUTH: SIMULATED_FIXTURE + SIMULATED_REFERENCE_IO, not live hardware")


if __name__ == "__main__":
    main()
