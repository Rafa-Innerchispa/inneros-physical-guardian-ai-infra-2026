# SiMa.ai On-Site Integration Checklist — AI Infra Summit 2026

Status: **pre-hardware readiness**. Do not claim SiMa.ai execution or benchmark results until the assigned hardware and official SDK/runtime are physically available and measured.

## Architecture boundary

Physical Guardian stays vendor-neutral:

`camera / owned video -> sponsor runtime sidecar -> normalized detections -> Guardian temporal policy -> human-governed bounded action -> Physical I/O -> independent readback -> Evidence Receipt`

The permanent product owns reusable perception and Physical I/O contracts. This hackathon repository owns only sponsor adaptation, judge composition, evidence capture and event tooling.

## Current official SiMa.ai onboarding facts

Verified against current SiMa.ai public documentation on 2026-09-14:

- Developer Portal account approval is required before downloading SDK/software assets.
- `sima-cli` is the host-side control tool.
- Device discovery is `sima-cli device discover`.
- SSH access is `ssh sima@<devkit-ip>`.
- Current Neat SDK 2.1 channel is installed with `sima-cli neat install sdk@release-2.1`.
- Current documentation reports Neat SDK `2.1.3.0` compatible with DevKit software `2.1.3`; always record the actual onsite versions instead of assuming them.
- Pairing can be performed with `sima-cli sdk setup --devkit <DEVKIT_IP>`.
- A paired DevKit provisions the supported PyNeat environment under `~/pyneat`.
- Model Zoo can list, describe and download precompiled models; prefer a precompiled detector first to reduce event risk.
- The official benchmark example can emit latency, FPS, power and energy measurements to JSON for a compiled model package.

Official references:

- https://developer.sima.ai/agents
- https://developer.sima.ai/tools/qsg/index.html
- https://developer.sima.ai/software/tools/model-zoo/
- https://developer.sima.ai/software/getting-started/dev-environment/install-the-environment
- https://developer.sima.ai/examples/app/benchmarking/model-benchmark

## Repo tools prepared before hardware

Run the general event gate:

```bash
python3 scripts/event_preflight.py
```

Run the dedicated SiMa host check without touching hardware state:

```bash
python3 scripts/sima_onsite_preflight.py
```

After the DevKit is physically connected and `sima-cli` is available:

```bash
python3 scripts/sima_onsite_preflight.py --probe-device --probe-modelzoo
```

If the DevKit IP is already known, print a validated bring-up plan:

```bash
python3 scripts/sima_onsite_preflight.py --devkit-ip 192.0.2.10
```

The preflight intentionally does **not** login, install packages, update firmware or print credentials.

## Windows event laptop

The Windows event bootstrap now runs the SiMa preflight as an optional lane:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows_event_bootstrap.ps1
```

When the official `sima-cli` package is available through the approved SiMa Developer Portal account, the current SiMa quick-start documents the Windows host driver command as:

```text
sima-cli install drivers/windows
```

That driver installation can require administrator access and a host power cycle/restart. Do it before judge rehearsal, not three minutes before presenting because humans apparently enjoy suspense.

## First 30 minutes with the SiMa.ai kit

1. Record exact board/DevKit model, platform image/software version and serial/reference information allowed by the event.
2. Install/verify official host tooling only from SiMa.ai sources.
3. Run `sima-cli device discover`.
4. If mDNS is unreliable on Windows, use the discovered IP instead of depending on `modalix.local`.
5. Connect with `ssh sima@<devkit-ip>` and verify the device is healthy.
6. Run the official vendor hello-world/sample unchanged and preserve its output.
7. Record exact Neat SDK, Neat Library/PyNeat and DevKit software versions.
8. Prefer Model Zoo first:

```text
sima-cli modelzoo list
sima-cli modelzoo describe yolo_v8s
sima-cli modelzoo get yolo_v8s
```

Model identifiers vary by release, so `modelzoo list` is the source of truth.

9. If host-side Neat SDK is needed, use the current release channel:

```text
sima-cli neat install sdk@release-2.1
```

10. Pair the SDK to the DevKit when appropriate:

```text
sima-cli sdk setup --devkit <DEVKIT_IP>
```

11. On the DevKit, activate the supported PyNeat environment if needed:

```text
source ~/pyneat/bin/activate
```

12. Obtain one genuine inference outside Guardian before writing integration code.
13. Only then wrap the real inference call behind the existing loopback `/infer` contract in `docs/SPONSOR_RUNTIME_BRIDGE.md`.
14. Set `GUARDIAN_SIMA_RUNTIME_URL` to that loopback endpoint.
15. Confirm normalized `label`, `confidence`, `bbox`, `track_id` and `zone` fields reach Guardian without SiMa SDK objects leaking into product logic.

## Compile only if needed

Do not burn event time compiling a custom ONNX detector if a precompiled Model Zoo detector proves the architecture and meets the demo need.

If custom compilation is genuinely necessary, the current SiMa documentation provides a Model Compiler inside the Neat SDK and documents ONNX compilation. Record exact compiler/SDK compatibility first. Never force a model path based on an old tutorial when the assigned DevKit exposes a supported precompiled package.

## Truth-label gate

Use these labels exactly:

- `SIMULATED_SPONSOR_SDK`: contract/mock validation only.
- `SPONSOR_RUNTIME_UNVERIFIED`: real SiMa.ai path is connected but provenance or repeatability is not sufficient for a benchmark claim.
- `MEASURED_SPONSOR_RUNTIME`: only after repeatable runs on assigned SiMa.ai hardware with recorded hardware/runtime/model/version evidence.

The evidence capture helper enforces this gate:

```bash
python3 scripts/sima_capture_evidence.py \
  --hardware "Modalix MLSoC DevKit" \
  --platform-version "<actual>" \
  --neat-version "<actual>" \
  --model "<actual model>" \
  --sample-count 50 \
  --latency-p50-ms 4.2 \
  --latency-p95-ms 5.8 \
  --fps 120 \
  --source-json ./vendor-benchmark.json \
  --measured \
  --output ./evidence/sima-benchmark.json
```

If required provenance is incomplete, the helper refuses the measured claim and emits `SPONSOR_RUNTIME_UNVERIFIED` instead. The source JSON is hashed for provenance rather than copied into the normalized record.

## Closed-loop proof after first real inference

Do not optimize yet. First prove this complete path:

1. real/staged camera or owned video frame enters the SiMa.ai runtime;
2. normalized detection reaches Guardian;
3. tracking/zone/temporal policy produces an explainable event;
4. human operator authorizes one bounded low-voltage action;
5. Physical I/O executes and readback verifies it;
6. operator interrupts the action;
7. Guardian commands and verifies safe state;
8. resume remains blocked;
9. safe state is re-verified;
10. operator resumes or cancels;
11. the Evidence Receipt contains every transition and truth label.

Only after this works should the team tune latency, throughput, model conversion or UI polish.

## Measurements worth capturing

When genuinely available, record:

- exact hardware/DevKit identifier;
- platform software version;
- Neat SDK / Neat Library version;
- exact model artifact/name;
- sample count;
- inference latency p50/p95;
- throughput/FPS;
- end-to-end event-to-action latency;
- action and verification latency;
- memory use where reliably exposed;
- power and energy telemetry when the platform exposes them reliably;
- vendor benchmark JSON hash;
- Guardian Evidence Receipt correlation/evidence ID.

## Failover

If the SiMa.ai toolchain is unavailable or unstable, do not rewrite Guardian during the event. Return to:

`owned local video -> deterministic Guardian fixture -> local bounded actuator -> verification -> evidence`

The fallback must remain demonstrable with no Internet connection. Sponsor integration is an accelerator swap, not a new product architecture.

## Definition of ready for judges

- vendor sample PASS;
- one real SiMa.ai inference PASS;
- `/infer` sidecar PASS on loopback;
- normalized Guardian event PASS;
- bounded Physical I/O action PASS;
- readback verification PASS;
- interrupt -> verified safe state -> reverify -> resume/cancel PASS;
- Speechmatics live voice optional lane PASS if available;
- Evidence Receipt includes the full lifecycle;
- LIVE REAL vs SYNTHETIC status is visible in Judge UI;
- all benchmark numbers are traceable to real sponsor hardware runs.
