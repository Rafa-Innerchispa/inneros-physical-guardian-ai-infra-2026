# SiMa.ai Live Evidence Gate & Judge Proof Contract

## 1. Overview
The InnerOS Physical Guardian demonstration for the AI Infra Summit 2026 integrates with the **SiMa.ai Modalix MLSoC DevKit** using hardware-accelerated Machine Learning Accelerator (MLA) execution.

To guarantee zero hallucinated metrics and strict fidelity during sponsor judging, all benchmark and inference data must pass through the **SiMa Live Evidence Gate** (`scripts/sima_live_evidence_gate.py`).

---

## 2. Truth Classification Hierarchy
The system strictly distinguishes runtime truth levels:

| Truth Rating | Meaning | Requirements |
|---|---|---|
| `MEASURED_SPONSOR_RUNTIME` | Proven execution on physical Modalix hardware | Validated hardware descriptor, $\ge 3$ measured samples, positive p50/p95 latency, throughput FPS, and SHA-256 hash of the raw benchmark run log. |
| `SIMULATED_SPONSOR_SDK` | Deterministic local fixture or offline test harness | Used exclusively for CI/CD, offline test suites, and mock contract harnesses. Must NEVER be labeled as measured live. |
| `SPONSOR_RUNTIME_UNVERIFIED` | Missing hardware proof or incomplete benchmark fields | Automatic fail-closed downgrade when required fields or hashes are missing. |

---

## 3. Evidence Schema (`inneros.guardian.sima.evidence.v1`)
Evidence files (such as `docs/sima_measured_evidence.json`) follow this immutable schema:

```json
{
  "schema": "inneros.guardian.sima.evidence.v1",
  "captured_at": "2026-09-15T19:26:41.504814+00:00",
  "truth": "MEASURED_SPONSOR_RUNTIME",
  "measured": true,
  "gate_reasons": [],
  "hardware": "SiMa.ai Modalix DevKit MLSoC",
  "platform_version": "2.1.3",
  "neat_version": "0.4.0",
  "model": "yolo26m-seg-bf16-b1",
  "sample_count": 30,
  "metrics": {
    "latency_p50_ms": 27.6,
    "latency_p95_ms": 28.06,
    "fps": 36.23,
    "power_w": null,
    "energy_j": null
  },
  "evidence_id": "sima-modalix-mla-real-yolo26m-20260915",
  "source_json_sha256": "0e699c16a18a195e1f31d23e40fb0f199a7df3315e76ff9d4be0752aae15ec72",
  "source_json_name": "real_inference_results.json"
}
```

---

## 4. Offline Judge Verification CLI
Judges and evaluators can verify the evidence file offline without requiring active hardware access or network connectivity:

```bash
# Strict measured check (exit code 0 = PASS, 1 = FAIL)
python scripts/sima_live_evidence_gate.py docs/sima_measured_evidence.json

# Machine-readable JSON output
python scripts/sima_live_evidence_gate.py docs/sima_measured_evidence.json --json
```

---

## 5. Live Runtime Sidecar Boundary
When running live demo scenarios with Guardian:
- **Sidecar URL:** `http://127.0.0.1:8890/infer`
- **Environment:** `GUARDIAN_SIMA_RUNTIME_URL=http://127.0.0.1:8890`
- **Sidecar CLI:** `python scripts/sima_sidecar_live.py --mode live --devkit-ip 192.168.1.20`
