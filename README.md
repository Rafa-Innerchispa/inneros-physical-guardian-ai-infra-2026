# InnerOS Physical Guardian — AI Infra Summit 2026

<!-- INNEROS-NARRATIVE:START -->
> **InnerOS role:** R&D / Hackathon Validation  
> **Lifecycle:** Submission snapshot  
> **Lineage:** AI Infra Summit 2026 validation track for the Physical Guardian / VigilOS product line.
>
> This repository demonstrates the physical-world perception, policy, approval, action, verification, and evidence loop that feeds the maintained Physical Guardian product.
>
> **InnerOS principle:** hackathons are validation environments. Reusable capabilities are extracted into maintained products and platform layers rather than treated as disconnected one-off projects.
<!-- INNEROS-NARRATIVE:END -->


**Live hackathon build. Functional judge demo.**

> **Continuity first:** a new chat/agent must read `docs/PROJECT_CONTINUITY.md` before changing code. It records the permanent-product vs hackathon boundary, canonical SHAs, sponsor strategy, on-site sequence and safety invariants.

> **Event freeze:** the team is officially confirmed for the **SiMa.ai onsite track**. Read `docs/EVENT_FREEZE_2026-09-14.md` before making any pre-judge change. Do not submit this project through the LabLab online Intel flow.

Speechmatics is an optional bonus lane. Guardian remains fully usable without Speechmatics, sponsor hardware or an external network.

InnerOS Physical Guardian turns existing cameras and building sensors into governed Physical AI without forcing customers to replace their security infrastructure.

> **SEE → UNDERSTAND OVER TIME → DECIDE UNDER POLICY → ACT → VERIFY → PROVE**

## Run the judge application

Requires Python 3.11+ and no third-party Python package for the demo runtime.

```bash
python3 scripts/run_demo.py
```

Open `http://127.0.0.1:8787`.

Before presenting, exercise the exact governed lifecycle with:

```bash
python3 scripts/judge_rehearsal.py
```

When real SiMa inference and Physical I/O readback are connected, the strict truth gate is:

```bash
python3 scripts/judge_rehearsal.py --runtime sima-slot --require-measured-sponsor --require-live-physical
```

The complete demo must not be described as live if that strict gate fails.

The single-screen WebUI includes:

- camera/sensor scenario visualization;
- normalized perception state;
- temporal/policy reasoning;
- explicit human action approval;
- bounded reference or permanent-product Physical I/O;
- verification/readback state;
- forensic evidence bundle with truth labels;
- replaceable SiMa.ai, Qualcomm and Intel runtime slots;
- measured composition timings clearly separated from simulated data.

## Zero-dependency acceptance check

A clean Python host can validate the application without installing pytest or any package:

```bash
python3 scripts/self_test.py
```

The acceptance script boots ephemeral loopback servers and verifies the offline runtime, human approval gate, safe reject path, dangerous-action fail-closed behavior, permanent-product Physical I/O contract/readback, WebUI delivery, HTTP demo flow, evidence production and optional hosted authentication.

The developer test suite remains available when pytest is installed:

```bash
python3 -m pytest -q
```

## Why this architecture matters

Most buildings do not need another camera platform. They need an intelligence and control layer that can work with the cameras, NVRs, DVRs and sensors they already own.

The permanent Physical Guardian product supplies reusable capabilities for camera ingestion, RTSP/ONVIF, event normalization, detection, tracking, zones, temporal behavior, low-cost edge transport, policy, physical I/O and evidence.

This hackathon repository does **not** copy that product. It implements the hackathon-specific composition, sponsor runtime boundary, judge experience, evidence presentation and deployment path.

Permanent product:

`Rafa-Innerchispa/inneros-physical-guardian`

Hackathon composition:

`Rafa-Innerchispa/inneros-physical-guardian-ai-infra-2026`

## Runtime portability

The judge app has one offline-safe deterministic runtime plus local-only sponsor SDK bridges.

| Runtime | Default state | On-site binding |
| --- | --- | --- |
| InnerOS deterministic fixture | Ready | none |
| SiMa.ai | Track confirmed; awaiting onsite DevKit/SDK binding | `GUARDIAN_SIMA_RUNTIME_URL` |
| Qualcomm | Awaiting hardware/SDK | `GUARDIAN_QUALCOMM_RUNTIME_URL` |
| Intel | Awaiting hardware/SDK | `GUARDIAN_INTEL_RUNTIME_URL` |

A sponsor sidecar exposes `POST /infer` on loopback. Once configured, the corresponding runtime becomes selectable in the WebUI without changing Guardian policy, approval, verification or evidence code.

See `docs/SPONSOR_RUNTIME_BRIDGE.md`.

## Permanent-product Physical I/O

The judge app can optionally use the permanent Physical Guardian HTTP I/O contract after human approval:

```bash
export GUARDIAN_PHYSICAL_IO_URL=http://127.0.0.1:8765
python3 scripts/run_demo.py
```

The bridge is loopback-only. For mapped low-impact actions it performs `/v1/action` followed by `/v1/verify`; a failed readback ends as `ACTION_FAILED_SAFE` rather than silently reverting to a simulated success.

Truth is explicit:

- `SIMULATED_REFERENCE_IO` — offline fallback;
- `PRODUCT_HTTP_READBACK` — permanent HTTP contract action + verified software readback;
- `REAL_LOW_VOLTAGE_HARDWARE` — reserved for an endpoint that explicitly verifies actual low-voltage hardware;
- `FAILED_CLOSED` — configured I/O could not be verified.

See `docs/PHYSICAL_IO_BRIDGE.md`.

## Truth and benchmark discipline

The default judge path intentionally labels:

- camera event: `SIMULATED_FIXTURE`;
- offline detections: `SIMULATED_FIXTURE`;
- policy/temporal logic: `DETERMINISTIC_RULE`;
- demo physical output: `SIMULATED_REFERENCE_IO` until the permanent I/O contract or safe electronics are attached;
- composition timings: measured live;
- sponsor benchmark: not claimed until real assigned hardware produces repeatable measurements.

The system will fail closed rather than fabricate sponsor or physical-output success.

## Safety boundary

Judge actions are low-impact and allowlisted: beacon warning, operator notification and reference attention light. Door unlock, alarm disable, arbitrary shell execution and gate opening are explicitly denied in the demo policy.

Human approval is required before the demo ACT stage can complete. After an interruption, resume is denied until the safe state has been explicitly re-verified.

## Hosted judge mode

Optional HTTP Basic access control is configured only through environment variables:

```bash
export GUARDIAN_DEMO_USER="judge"
export GUARDIAN_DEMO_PASSWORD="<secret-outside-git>"
python3 scripts/run_demo.py --host 0.0.0.0 --port 8787
```

Canonical container recipe: root `Dockerfile`.

Deployment details: `DEPLOYMENT.md` and `docs/HOSTED_JUDGE_DEPLOY.md`.

## Current hackathon build artifacts

- `app/` — single-screen judge WebUI;
- `src/guardian_demo/` — demo engine, sponsor runtime boundary, Physical I/O bridge, voice lane and HTTP server;
- `scripts/run_demo.py` — one-command application start;
- `scripts/judge_rehearsal.py` — lifecycle rehearsal + strict live truth gate;
- `scripts/event_preflight.py` — event readiness without exposing secrets;
- `scripts/sima_onsite_preflight.py` — SiMa host/device readiness;
- `scripts/sima_capture_evidence.py` — sponsor evidence/benchmark capture with truth gating;
- `scripts/speechmatics_voice_live.py` — official Speechmatics live microphone bridge;
- `scripts/self_test.py` — zero-dependency acceptance test;
- `scripts/mock_sponsor_sidecar.py` — contract-only sponsor sidecar harness;
- `tests/` — safety/runtime/server/Physical-I/O/voice/onsite developer checks;
- `docs/PROJECT_CONTINUITY.md` — canonical handoff for future chats/agents;
- `docs/EVENT_FREEZE_2026-09-14.md` — final scope freeze, SiMa bring-up order and judge truth gates;
- `docs/JUDGE_DEMO_RUNBOOK.md` — current 90-second SiMa + Speechmatics judge flow;
- `docs/SPONSOR_RUNTIME_BRIDGE.md` — on-site SDK integration contract;
- `docs/PHYSICAL_IO_BRIDGE.md` — permanent-product action/readback integration;
- `PREEXISTING_DISCLOSURE.md` and `BASELINE_PROVENANCE.json` — frozen provenance boundary.

## Pre-existing work disclosure

This project existed before the hackathon as the permanent InnerOS Physical Guardian product. The pre-kickoff baseline is explicitly disclosed instead of being passed off as work created during the competition.

See:

- `PREEXISTING_DISCLOSURE.md`
- `BASELINE_PROVENANCE.json`
- `HACKATHON_SCOPE.md`
- `docs/PROJECT_BRIEF.md`
- `docs/TRACK_STRATEGY.md`
- `docs/ONSITE_HARDWARE_PLAYBOOK.md`

## Team

**InnerOS Physical Guardian**

The team is intentionally kept small. Priority additions are a fluent English technical presenter and hands-on Edge AI / embedded optimization talent who can contribute directly to the existing build.
