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
Canonical main after Windows event-laptop PR #13: `f9be26cde421711e954d94a1d843c12194513321`

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

Runtime readiness after PR #13:

- primary `.4` hackathon runtime is synchronized exactly to `f9be26cde421711e954d94a1d843c12194513321`;
- isolated project `.venv` exists on `.4`;
- official `speechmatics-rt==1.1.1` is installed successfully in that venv;
- `scripts/self_test.py` passes from the merged runtime;
- `scripts/event_preflight.py` is the canonical event readiness gate and separates required Guardian core checks from optional Speechmatics, microphone, SiMa and Physical I/O lanes;
- event-preflight feature validation reached 36/36 pytest PASS and PR #12 GitHub CI PASS;
- Windows event-laptop feature validation reached 40/40 pytest PASS, compileall PASS, diff check PASS and PR #13 GitHub CI PASS;
- runtime event preflight on `.4` at `f9be26c...` reports Guardian core PASS and `speechmatics-rt 1.1.1` PASS;
- merged runtime `scripts/self_test.py` at `f9be26c...` reports ALL ACCEPTANCE CHECKS PASSED;
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


## 11. September 14 SiMa + provider readiness delta

Functional base for this readiness increment: hackathon `main` `55dbd0a7fcf5d934c43c02e4a330a49b34fa2259`. Development branch: `chatgpt/guardian-sima-onsite-kit-20260914`. Re-verify GitHub main after merge; never treat a temporary branch SHA as canonical product truth.

### Speechmatics platform registration

Speechmatics is no longer only an adapter buried in this hackathon repository:

- provider manifest `speechmatics` is registered through Provider Onboarding;
- auth mode is `owner_vault`; raw API key remains outside repositories and coordination;
- provider preflight PASS;
- project `inneros-physical-guardian-ai-infra-2026` is durably linked to provider `speechmatics` capability `realtime_stt` under task `ops_3eaabe14cdf0`;
- the hackathon repository remains a consumer of that capability/SDK boundary, not the owner of the secret.

### SiMa onsite tooling

Pre-hardware tooling now includes:

- `src/guardian_demo/sima_onsite.py` — read-only SiMa readiness helpers, validated DevKit IP planning and truth-gated evidence packaging;
- `scripts/sima_onsite_preflight.py` — checks `sima-cli`, optional `device discover` and Model Zoo listing without login/install/update side effects;
- `scripts/sima_capture_evidence.py` — packages sponsor benchmark evidence and refuses `MEASURED_SPONSOR_RUNTIME` unless hardware/runtime/model versions, sample count, positive p50/p95 latency and a hashed source benchmark JSON are present;
- `docs/SIMA_ONSITE_CHECKLIST.md` — current official bring-up path: Developer Portal approval -> `sima-cli` -> device discovery/SSH -> Neat SDK/Model Zoo -> one genuine inference -> loopback `/infer` -> Guardian closed loop -> benchmark;
- `scripts/windows_event_bootstrap.ps1` now runs the SiMa preflight as an optional lane without making sponsor hardware a dependency of the offline demo.

Validation on the feature tree reached 47/47 pytest PASS, compileall PASS, diff hygiene PASS and `scripts/self_test.py` ALL ACCEPTANCE CHECKS PASSED before PR. Read-only SiMa preflight on `.4` truthfully reports `sima-cli` missing; this is expected before approved SiMa software/hardware access and does not block Guardian.


## 12. Post-merge canonical checkpoint — 2026-09-14

Canonical hackathon `main` after PR #15 is `96bf5791a6eb2712c5369200adfd817eceb6c46a` (`Add SiMa onsite bring-up and evidence kit`). Primary `.4` runtime is synchronized exactly to that SHA and clean.

Post-merge runtime verification at `96bf5791...`:

- `scripts/event_preflight.py` => READY; Python/core/Git/Speechmatics SDK PASS;
- `speechmatics-rt==1.1.1` remains installed in the project `.venv`;
- `scripts/self_test.py` => ALL ACCEPTANCE CHECKS PASSED;
- `scripts/sima_onsite_preflight.py` => expected WARN only because `sima-cli` is not installed/on PATH before approved SiMa software access; no hardware success is fabricated;
- SiMa feature tree validation before merge: 47/47 pytest PASS, compileall PASS, diff hygiene PASS, GitHub CI SUCCESS;
- permanent product repository remains untouched at `12e1720ddd439ba796daba3d31029d2151f6a544`.

Speechmatics platform state at this checkpoint:

- Provider Onboarding manifest `speechmatics` registered and preflight PASS;
- project capability link exists: `inneros-physical-guardian-ai-infra-2026` -> `speechmatics/realtime_stt` under `ops_3eaabe14cdf0`;
- Resource Fabric projection gap discovered: registered Speechmatics manifest/link is not yet displayed in the global providers projection; repair task `ops_029e98c0b3f5` was created and launched in `Rafa-Innerchispa/innerops-agentic-platform` on branch `chatgpt/resource-fabric-speechmatics-projection-20260914`.

Remaining Guardian blockers are physical/environmental only: actual event-laptop microphone + safe Speechmatics secret binding, SiMa Modalix DevKit/approved `sima-cli`/Neat access onsite, and a verified real low-voltage/DMX Physical I/O sidecar. Do not reopen core architecture to compensate for missing physical hardware.


## 13. Speechmatics Resource Fabric repair completed — 2026-09-14

The platform repair previously recorded as pending is now **completed**.

Canonical platform repository: `Rafa-Innerchispa/innerops-agentic-platform`.

- PR #45 merged: registered Provider Onboarding manifests are projected into Resource Fabric without duplicating richer native providers; merge SHA `a7300a42fd77dbbb19568300b71ba3fcc53fc6bc`.
- PR #46 merged: external-provider routing audit truth corrected; final platform main SHA `d2d8e66c9cce9df11a45f05f25a02422d8b09afb`.
- platform repair task `ops_029e98c0b3f5` is completed with evidence.
- live Resource Fabric contains both `speechmatics` and `assemblyai`.
- Physical Guardian project capability link `realtime_stt -> speechmatics` is active and has priority over unlinked AssemblyAI for this project.
- live routing acceptance selected `speechmatics` with `explicit_project_link=true`.
- audit evidence now truthfully records `provider_kind=external_voice_provider`, `local_cloud=cloud`, and `reason_codes=[explicit_project_link]`.
- live audit event `evt_26fc7498a34d8fc20d1968ed` was stored in Mongo, published to NATS JetStream, and exported through OpenTelemetry.
- no raw Speechmatics secret was placed in Git, coordination, Resource Fabric documents, or logs.

A live deployment drift was also corrected: the MCP runtime directory was missing tracked `audit_fabric.py` and had an older `durable_coordination_spine.py`. Both were aligned to tracked platform main content and the MCP restarted healthy before the final route acceptance.

This means a new chat must **not** recreate a Speechmatics integration, manifest, or project link. Treat Speechmatics as an existing reusable InnerOS provider and use the Resource Fabric capability link already present. Remaining Physical Guardian work is still physical/event-specific: event-laptop microphone + secure key binding, SiMa Modalix/Neat live bring-up, and verified real low-voltage/DMX Physical I/O.

## 2026-09-14 — SiMa onsite assignment confirmed

Official LabLab coordination email received 2026-09-14 from `coordination@lablab.ai` confirms the team is assigned to the **SiMa track** at the AI Infra Summit Hackathon, matching the team's first choice.

Operational truth now:
- On-site participation is guaranteed.
- Assigned track: **SiMa — Building Physical AI That Sees, Understands, and Acts**.
- Do **not** submit this project through the LabLab online hackathon flow; LabLab coordination explicitly stated that the online flow is for the Intel online challenge and a project can only be added to one track.
- No additional Discord ticket/action is required for track assignment.
- Previous blocker `formal SiMa assignment pending` is RESOLVED.
- Sponsor hardware remains onsite: Modalix MLSoC DevKit + Palette Neat, with SiMa mentors onsite. LabLab sponsor communication states one DevKit per team and that teams keep the hardware.
- Speechmatics remains an additive bonus path and is already routed through InnerOS Resource Fabric as the explicit `realtime_stt` provider for this project.
- Conference access previously confirmed by LabLab coordination: hackathon participants receive an Expo Pass for Days 1 and 2, with special content-track access on Thursday.

Remaining real gate:
- Physical Modalix hardware is not yet in hand. Final sponsor-runtime truth, device firmware/Neat compatibility, real inference, measured benchmark and end-to-end physical action verification must be completed onsite.

Onsite sequence remains:
1. Receive/identify exact Modalix DevKit revision.
2. Confirm DevKit software with `/etc/buildinfo` and compatible Palette Neat version.
3. Run vendor hello-world / Model Zoo path first.
4. Produce one real inference outside Guardian.
5. Expose normalized loopback `/infer` sidecar and set `GUARDIAN_SIMA_RUNTIME_URL`.
6. Run Guardian perception -> temporal reasoning -> bounded action -> readback -> interrupt -> safe state -> reverify -> resume/cancel -> Evidence Receipt.
7. Capture source benchmark artifact and only then allow `MEASURED_SPONSOR_RUNTIME` truth label.
8. Exercise Speechmatics bounded voice intents without bypassing approval/reverification gates.
