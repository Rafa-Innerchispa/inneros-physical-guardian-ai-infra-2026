# Physical Guardian AI Infra 2026 — Canonical Continuity

This file is the first project-specific document to read when work resumes in a new chat, IDE, agent session, or laptop.

## 1. Project identity

Hackathon: **AI Infra Summit 2026 / LabLab.ai**  
On-site event: **September 15–17, 2026, Santa Clara**  
Team/project: **InnerOS Physical Guardian**  
Current objective: arrive on-site with a stable, truthful Physical AI demo and adapt the inference backend to assigned sponsor hardware without destabilizing the permanent product.

Core loop:

`SEE → UNDERSTAND OVER TIME → DECIDE UNDER POLICY → ACT → VERIFY → PROVE`

Product thesis: upgrade infrastructure that already exists. Existing CCTV, sensors and low-voltage controls become governed Physical AI instead of being replaced by another closed camera platform.

## 2. Two repositories — never collapse this boundary

### Permanent InnerOS product

Repository: `Rafa-Innerchispa/inneros-physical-guardian`  
Canonical main observed during this readiness cycle: `12e1720ddd439ba796daba3d31029d2151f6a544`

This is the reusable InnerOS product. It owns reusable camera ingestion, RTSP/ONVIF, detection/tracking, zones, temporal behavior, policy, Physical I/O, verification, evidence, replay, audit and reusable edge/device contracts.

**Do not modify this repository to experiment during the event.** It must remain operational. Any reusable discovery from the hackathon returns later through an explicit, reviewed product PR.

### AI Infra Summit hackathon composition

Repository: `Rafa-Innerchispa/inneros-physical-guardian-ai-infra-2026`  
Baseline immediately before Speechmatics readiness: `37b5a722fd838637cf2f27916364fec685146329`  
Canonical main after event-preflight PR #12: `288047eca85c2f17f11f3a2aa914eeb355de440b`

This repository owns only the competition delta: Judge UI, sponsor runtime adapters, on-site integration, benchmark collection, demo orchestration, Speechmatics bonus integration, deployment, evidence presentation, pitch and pre-existing-work disclosure.

The hackathon repo may consume stable product contracts. It must not silently copy or mutate the permanent product.

## 3. Current sponsor strategy

Primary on-site target: **SiMa.ai Physical AI**.

Expected SiMa path:

`camera/video → Modalix MLSoC DevKit → normalized detections → Guardian policy → human authorization → bounded Physical I/O → independent readback → Evidence Receipt`

On-site SiMa hardware/software expected from event communications:

- Modalix MLSoC DevKit per team;
- Palette Neat / official SiMa tooling;
- SiMa mentors on site.

Do not claim real SiMa inference, benchmark numbers or hardware verification until the physical DevKit and official tooling are actually used.

Fallback sponsor targets: Qualcomm and Intel through the same normalized inference boundary.

Important track distinction: the **SO-101 robotic arm belongs to the on-site Intel Physical AI track**, not the SiMa track. Do not make the SiMa demo depend on that arm.

Latest organizer evidence still says track allocation may be completed onsite and there should be no issue joining SiMa; no later formal assignment email has superseded that state.

## 4. Speechmatics bonus

Speechmatics is a stackable bonus across tracks. It is an optional speech-to-text input adapter, never a required dependency of Guardian.

Existing internal resource truth as of September 14, 2026:

- Speechmatics API credential exists server-side at the logical vault reference `owner_vault:speechmatics/api_key`;
- registered Speechmatics credit balance: USD 475;
- no dedicated ChatGPT Speechmatics plugin is currently part of this project;
- use the official Speechmatics API/SDK and server-side secret binding;
- never copy the raw API key into Git, coordination, logs, screenshots or chat.

Runtime readiness after PR #12:

- primary `.4` hackathon runtime is synchronized exactly to `288047eca85c2f17f11f3a2aa914eeb355de440b`;
- isolated project `.venv` exists on `.4`;
- official `speechmatics-rt==1.1.1` is installed successfully in that venv;
- `scripts/self_test.py` passes from the merged runtime;
- `scripts/event_preflight.py` is the canonical event readiness gate and separates required Guardian core checks from optional Speechmatics, microphone, SiMa and Physical I/O lanes;
- event-preflight feature validation reached 36/36 pytest PASS and GitHub CI PASS before merge;
- runtime event preflight on `.4` reports Guardian core PASS and `speechmatics-rt 1.1.1` PASS;
- optional PyAudio microphone install on `.4` is blocked because `portaudio.h` is absent and `portaudio19-dev` is not on the bounded peer-package allowlist;
- this PortAudio limitation is **not a blocker for the event architecture** because `.4` is not the required on-site microphone host. The live mic bridge is intended to run on the event laptop, where the audio dependency can be installed against the actual OS/audio device;
- the raw Speechmatics key remains vault-only. Current ChatGPT tool surface does not expose a generic secret binder for injecting its value into this project runtime, so do not work around that by copying the secret.

Voice safety invariant:

- voice may explain an incident;
- voice may request camera navigation;
- voice may acknowledge an incident;
- voice may interrupt an already authorized action;
- voice may request safe-state re-verification;
- voice may request resume only after the canonical re-verification gate passes;
- voice may cancel safely;
- **voice must never approve, authorize, execute, unlock/open access, disable an alarm, or bypass policy.**

Raw microphone audio is not written to project storage by the hackathon bridge. The Guardian voice adapter stores/returns a transcript SHA-256 for traceability rather than persisting raw transcript content in evidence.

## 5. Current interruptible action lifecycle

Current hackathon main implements:

`PROPOSED → AUTHORIZED → EXECUTING → EXECUTION_VERIFIED → INTERRUPTED → SAFE_STATE_VERIFIED → REVERIFIED → RESUMING → RESUMED_VERIFIED`

or a safe terminal cancellation.

Resume is fail-closed until safe state has been explicitly re-verified. Mapped low-voltage safe state uses an OFF command followed by independent readback. Resume uses a new action/idempotency identity so cached execution cannot masquerade as a physical resume.

## 6. Truth-label discipline

Never blur simulated and real evidence.

Examples:

- synthetic camera fixture → `SIMULATED_FIXTURE`;
- sponsor mock/contract harness → simulated sponsor truth label;
- real sponsor runtime only after actual SDK/hardware inference → measured sponsor truth label;
- manual/browser transcript → `CLIENT_REPORTED_TRANSCRIPT`;
- live Speechmatics bridge may use `SPEECHMATICS_LIVE_TRANSCRIPT` only when the server-side bridge authentication is configured and the transcript came from the official SDK;
- permanent Physical I/O software readback → `PRODUCT_HTTP_READBACK`;
- real low-voltage hardware only after actual readback → `REAL_LOW_VOLTAGE_HARDWARE`.

If verification fails, fail closed. Never downgrade silently to a simulated success.

## 7. On-site sequence

Do not spend the first event hours rewriting Guardian. Use this order:

1. confirm assigned track and exact DevKit revision;
2. connect laptop and DevKit on a local network/Ethernet path;
3. run vendor hello-world first;
4. record exact SDK/Palette/firmware/tool versions;
5. obtain one genuine model inference outside Guardian;
6. wrap that runtime behind the existing loopback `/infer` contract;
7. confirm normalized detections in Judge UI;
8. connect bounded low-voltage output/readback;
9. run full loop: detect → decide → authorize → act → verify → interrupt → safe state → reverify → resume/cancel → evidence;
10. install/verify the laptop microphone dependency and bind `SPEECHMATICS_API_KEY` through a safe environment/secret mechanism;
11. validate Speechmatics live voice path;
12. only after the full loop works, collect repeatable latency/FPS/power metrics.

Fallback if sponsor hardware is delayed: deterministic owned fixture + local Guardian + local safe actuator. Remote Ecuador CCTV is a bonus proof of retrofit capability, never an on-site dependency.

### Windows event-laptop kit

The on-site Windows path is documented in `docs/WINDOWS_EVENT_LAPTOP.md` and consists of:

- `scripts/windows_event_bootstrap.ps1`: locate Python 3.11+, create isolated `.venv`, install the pinned Speechmatics/live-audio extras and run strict readiness checks;
- `scripts/audio_devices.py`: inventory microphone/input devices without recording audio;
- `scripts/windows_event_start.ps1`: launch Guardian, verify health, generate an ephemeral in-memory voice-bridge token and optionally start live Speechmatics after strict gates pass.

These scripts must never prompt for, print, or persist the Speechmatics API key. Actual Windows microphone verification remains a physical event-laptop step.

## 8. Resume protocol for a new chat/agent

Before writing code:

1. read this file;
2. inspect GitHub `main` for both repositories and record exact SHAs;
3. read the current coordination task `ops_3eaabe14cdf0` and latest project handoff/coordination messages;
4. verify the permanent product repo is clean and untouched;
5. verify the hackathon runtime/repo is clean;
6. compare planned work against existing sponsor/voice adapters before creating anything new;
7. run `scripts/event_preflight.py` before adding features and treat optional physical/provider warnings as physical integration work, not justification to rewrite the core.

Never infer that an agent failed to deliver from one inbox surface alone. Cross-check coordination messages, ops task state, GitHub branch/commit/PR and handoff documentation.

## 9. Git lifecycle

For hackathon changes:

`clean main → exact remote SHA → isolated worktree/branch → code → tests → PR → CI → merge → verify remote main → sync runtime → acceptance smoke → cleanup`

Rules:

- no direct protected-main edits;
- no force push;
- no blind merge of historical agent branches;
- no useful work left only in an IDE, worktree or runtime;
- no runtime checkout used as a development workspace;
- no product-repo mutation during event prep unless a separate product task explicitly authorizes it.

## 10. Pre-event definition of ready

Before Tuesday/on-site work begins, the repository should provide:

- offline deterministic Judge demo PASS;
- interrupt/reverify/resume/cancel PASS;
- optional sponsor `/infer` boundary PASS;
- SiMa on-site checklist and version capture ready;
- Speechmatics bounded voice adapter PASS without external dependency;
- official Speechmatics SDK installed in a project-specific environment where possible;
- live microphone bridge ready to consume `SPEECHMATICS_API_KEY` from a safe runtime environment;
- Windows laptop bootstrap/start scripts ready and CI/static tested; actual microphone/device verification remains a physical laptop step;
- clear LIVE REAL vs SYNTHETIC truth labels;
- no raw secrets in Git;
- no regression or mutation of permanent `inneros-physical-guardian`.

Update this file whenever a new canonical main SHA, sponsor assignment, hardware fact, runtime contract or critical safety invariant changes.
