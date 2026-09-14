# Event Freeze — 2026-09-14

## Status

- Event: AI Infra Summit Hackathon, Santa Clara Convention Center, September 15–17, 2026.
- Project: InnerOS Physical Guardian.
- Onsite track: **SiMa.ai confirmed by LabLab on 2026-09-14**, matching first choice.
- Onsite spot: previously confirmed guaranteed by LabLab.
- Do **not** submit this project through the LabLab online flow. LabLab explicitly stated that the online challenge is Intel-only and one project can only occupy one track.
- Speechmatics remains a stackable bonus integration and is already wired into Guardian with bounded voice authority.

## Freeze boundary

This document starts from hackathon `main` at `0c8f9d1f317c6f2c0a5e832721b159a1ccdb78bc`. The final pre-event hardening merge may advance the SHA, but the architectural scope freezes here.

After the hardening merge, no new product features should be added before judging unless a real P0 onsite blocker requires a change.

### Allowed after freeze

- SiMa DevKit/Palette Neat installation or adapter work required by the hardware actually handed to the team.
- Binding the existing `sima-slot` to a real loopback `/infer` sidecar.
- Physical I/O sidecar/readback work required by the actual safe low-voltage actuator.
- Windows microphone/PyAudio/driver fixes required for live Speechmatics.
- Bug fixes that block the demonstrated closed loop.
- Evidence capture, benchmark capture and truth-label corrections.

### Not allowed after freeze

- new unrelated features;
- UI redesigns;
- cross-hackathon feature merges from FieldOps, VoiceOps or other repos;
- experiments directly against the permanent Guardian product `main`;
- claims of sponsor performance without measured evidence;
- remote Ecuador infrastructure as a required dependency for the judge path.

## Onsite bring-up order

### 1. Check-in

Carry/keep immediately accessible:

- LabLab SiMa track confirmation email;
- government photo ID;
- conference/hackathon registration email or Expo Pass instructions when received;
- laptop and charger;
- Ethernet/USB adapters;
- local fallback assets.

If the badge email is still missing, use the confirmed LabLab onsite allocation as the escalation evidence at check-in. Do not create an online Intel submission as a workaround.

### 2. Modalix identity before installation

Record the actual unit before changing anything:

- hardware/DevKit revision;
- `/etc/buildinfo` or vendor-equivalent build information;
- firmware/software image version;
- network address assigned onsite;
- mentor-confirmed Palette Neat version compatible with that DevKit.

Do not assume the exact hardware revision from marketing material.

### 3. Minimal SiMa path first

Preferred order:

1. install/verify current vendor-supported `sima-cli` on the event laptop;
2. `sima-cli device discover`;
3. verify SSH access to the DevKit;
4. use a compatible **precompiled Model Zoo model first**;
5. prove one real inference independently of Guardian;
6. wrap that result behind the existing loopback `/infer` contract;
7. set `GUARDIAN_SIMA_RUNTIME_URL`;
8. run Guardian strict rehearsal;
9. only then consider model compilation/optimization if it materially improves the result.

Do not spend the first hours compiling an ONNX model if a Model Zoo artifact proves the integration path.

## SiMa mentor questions

Ask these early and write the answers into the evidence notes:

1. What exact DevKit/hardware revision did this team receive?
2. What Palette Neat version is recommended for this revision today?
3. Is a firmware/image update required before Neat use?
4. Which Model Zoo object-detection model is the fastest reliable starting point for a person/zone demo?
5. What is the recommended live camera/input path for this DevKit?
6. What benchmark command or method should we use for latency/power claims?
7. Which measurements are produced by vendor tooling versus measurements we must capture ourselves?

## Pre-judge gates

Offline confidence check:

```bash
python3 scripts/event_preflight.py
python3 scripts/judge_rehearsal.py
```

Strict live gate after SiMa + Physical I/O are connected:

```bash
python3 scripts/judge_rehearsal.py \
  --runtime sima-slot \
  --require-measured-sponsor \
  --require-live-physical
```

The strict command must PASS before saying the complete SiMa-to-actuator loop is live.

## Required proof bundle

Before judging, preserve:

- SiMa device/build/version identity;
- model name/version;
- source evidence for measured inference results;
- benchmark file hash via the existing evidence capture tool;
- Guardian trace/evidence ID;
- Physical I/O execution and independent readback truth;
- interrupt → safe state → reverify → resume/cancel lifecycle;
- Speechmatics live provenance if voice is demonstrated live;
- final repo SHA.

## Judge-path fallback policy

Never wait for remote connectivity to rescue the demo.

1. real SiMa + real local actuator + live voice;
2. real SiMa + real local actuator + typed voice fallback;
3. real SiMa + simulated safe actuator;
4. deterministic local inference + real local actuator;
5. fully deterministic offline demo.

Whichever fallback is used, the UI truth labels must match reality.

## Definition of done for the onsite task

The hackathon ops task is complete only when there is evidence of:

1. real SiMa inference reaching Guardian through `sima-slot`;
2. bounded action executed through the Physical I/O contract;
3. independent readback verified;
4. interruption reaches verified safe state;
5. resume is denied until re-verification;
6. final evidence receipt is sealed;
7. live Speechmatics path proven if claiming the bonus demo live.
