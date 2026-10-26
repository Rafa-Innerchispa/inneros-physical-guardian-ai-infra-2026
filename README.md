# InnerOS Autonomous Infrastructure Guardian | Meta Global AI Developer Hackathon 2026

**From AI that answers to AI that safely operates the physical world.**

![Build status](https://img.shields.io/badge/runtime-Python%203.10%2B-blue) ![Operational truth](https://img.shields.io/badge/demo-synthetic%20only-yellow) ![External spend](https://img.shields.io/badge/Meta%20API-opt--in-green)

> **Hackathon entry, Oct 26 – Nov 4, 2026.** Independent local-first demo for the Meta Global AI Developer Hackathon, built by InnerChispa. This is a new hackathon-specific composition, **not** a claim that InnerOS's earlier work was created during this event. See [PROVENANCE](docs/PROVENANCE.md).

The system turns synthetic observations from cameras, access controls and networks into a governed operational flow:

`OBSERVE → REASON → APPROVE → ACT → VERIFY → PROVE`

The same policy gate is used regardless of which inference provider generates the explanation. The demo **never** operates a real door, camera or building network.

## Live demo locally (zero dependencies)

```bash
cd inneros-meta-guardian-2026
PYTHONPATH=src python -m inneros_meta_guardian.web
```

Open **http://127.0.0.1:8787**. Select a scenario, create an incident, analyze using the deterministic local engine, approve the safe recommended action, execute the virtual actuator, independently verify it, and export a JSON evidence bundle.

Supported scenarios:

1. Pedestrian door propped open, with camera zone occupancy.
2. PoE camera offline, but uplink healthy.
3. Unverified visitor badge event (explicitly **does not open gate**).

## Test without paid APIs

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
# In another terminal after starting the server:
PYTHONPATH=src python scripts/e2e_smoke.py
```

## Optional local Ollama inference

```bash
# Use any locally downloaded Ollama model, e.g. qwen2.5:7b.
export OLLAMA_MODEL=qwen2.5:7b
PYTHONPATH=src python -m inneros_meta_guardian.web
```

Select **Ollama local** in the web UI. Unavailable models fail over to deterministic reasoning with an explicit fallback label. This does not authorize additional operations.

## Optional Meta Model API inference

**Do not configure this until credits appear in Billing and you have explicitly approved API consumption.**

```bash
export MODEL_API_KEY='[put key here, NEVER in a Git commit]'
export ALLOW_EXTERNAL_META=true
export META_MODEL=muse-spark-1.3
PYTHONPATH=src python -m inneros_meta_guardian.web
```

Select **Meta Muse Spark** in the web UI. The adapter uses Meta's official Responses API at `https://api.meta.ai/v1/responses`. It sends only the synthetic fixture, never device passwords, identifiable people, or real customer streams. API calls require an account and payment method. The SDK is not required: Python `urllib` is used to avoid extra dependencies. The `MODEL_API_KEY` remains server-side in the environment.

* Official Meta Model API overview: https://dev.meta.ai/docs
* Official API quickstart: https://dev.meta.ai/docs/quickstart
* Event page: https://cerebralvalley.ai/e/meta-ai-developer-hackathon

## Container demo (local loopback only)

```bash
docker compose up --build
```

WebUI is bound to `127.0.0.1:8787` on the host. **Never publish the demo directly to the public Internet**: it intentionally has no login, only synthetic input and in-process virtual actuators. Add authentication and rate limiting before any public judge link. Never enable `GUARDIAN_UNSAFE_BIND` outside an isolated demonstration container or secure reverse proxy.

## Architecture

```
Synthetic incident fixture / future scoped MCP reader
      │
      ▼
Stateful Guardian lifecycle engine ────────→ SQLite incident state
      │                                            │
      ▼                                            ▼
Local deterministic reasoning                SHA-256 audit chain
  ├── optional Ollama local model                  │
  └── optional Meta Muse Spark 1.3                 └── JSON evidence bundle
      │
      ▼
Fixed allowlist + human approval
      │
      ▼
Virtual actuator (NO real I/O)
      │
      ▼
Independent virtual-state readback
```

### What is proven today vs. not yet built

| Capability | Status | Truth label |
|---|---|---|
| Full six-stage demo | Implemented and locally testable | `SIMULATED_FIXTURE` |
| Persistent SQLite incident/audit log | Implemented | `DEMO_HASH_CHAIN_NOT_PRODUCTION_ATTESTATION` |
| Approval/forbidden action policy | Implemented | `DETERMINISTIC_RULE` |
| Virtual actuator and independent in-process readback | Implemented | `SIMULATED_REFERENCE_IO` |
| Ollama local reasoning | Adapter implemented; endpoint not exercised on physical AMD host yet | `LOCAL_MODEL_FROM_SIMULATED_SIGNALS` only when real call succeeds |
| Meta Model API reasoning | Adapter implemented; live key/credits not tested | `MODEL_GENERATED_FROM_SIMULATED_SIGNALS` only when real call succeeds |
| SAM 3.1 camera segmentation | **Planned, not integrated** | Not claimed |
| Live MCP device read and real hardware readback | **Planned, not integrated** | Not claimed |
| Published external judge URL | **Not deployed** | Not claimed |

## Security and scope

* Fail closed: no gate opening, door unlocking, firewall changes, reboots or shell commands.
* A model's text can never bypass deterministic policy or human approval.
* All incidents are clearly labeled synthetic. Meta and Ollama providers have distinguishable truth labels; fallback is explicitly recorded.
* No biometrics, customer images, credentials or internal network topology in the repository.
* Tests and API use need no external spend by default.

See [architecture](docs/ARCHITECTURE.md), [provenance](docs/PROVENANCE.md), and [submission checklist](docs/SUBMISSION.md).
