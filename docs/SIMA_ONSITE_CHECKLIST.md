# SiMa.ai On-Site Integration Checklist — AI Infra Summit 2026

Status: **pre-hardware readiness**. Do not claim SiMa.ai execution or benchmark results until the assigned hardware and official SDK/runtime are physically available and measured.

## Architecture boundary

Physical Guardian stays vendor-neutral:

`camera / owned video -> sponsor runtime sidecar -> normalized detections -> Guardian temporal policy -> human-governed bounded action -> Physical I/O -> independent readback -> Evidence Receipt`

The permanent product already defines provider-neutral detection and Physical I/O contracts. The hackathon layer only adapts the assigned SiMa.ai runtime to the existing normalized detection contract.

## Before hardware is available

- Keep `GUARDIAN_SIMA_RUNTIME_URL` unset.
- Judge UI must show the SiMa slot as `AWAITING_ASSIGNED_HARDWARE_OR_SDK` / not benchmarked.
- Use the deterministic offline fixture for rehearsal.
- Use `scripts/mock_sponsor_sidecar.py` only for contract validation. Never present it as a SiMa.ai benchmark.
- Keep the fully local Physical I/O fallback working without conference Wi-Fi.

## First 30 minutes with the SiMa.ai kit

1. Record exact board/devkit model, image, SDK and Palette Neat versions.
2. Run the official vendor hello-world/sample unchanged and preserve its output.
3. Confirm which model formats and operators are actually supported before converting anything.
4. Choose the smallest useful Guardian perception workload that can be deployed reliably.
5. If ONNX is supported by the provided workflow, export the chosen detector with fixed input shape and record the source model/hash, preprocessing and postprocessing assumptions. Do not force an ONNX path if the official workflow says otherwise.
6. Compile/optimize through the official SiMa.ai / Palette Neat path.
7. Run one real inference outside Guardian and preserve raw output plus timing.
8. Wrap only the inference call behind the loopback `/infer` contract documented in `docs/SPONSOR_RUNTIME_BRIDGE.md`.
9. Set `GUARDIAN_SIMA_RUNTIME_URL` to that loopback sidecar. Never expose the sponsor runtime directly to the public network.
10. Confirm Guardian receives normalized `label`, `confidence`, `bbox`, `track_id` and `zone` fields without sponsor SDK objects leaking into product logic.

## Truth-label gate

Use these labels exactly:

- `SIMULATED_SPONSOR_SDK`: contract/mock validation only.
- `SPONSOR_RUNTIME_UNVERIFIED`: real SiMa.ai path is connected but provenance or repeatability is not sufficient for a benchmark claim.
- `MEASURED_SPONSOR_RUNTIME`: only after repeatable runs on the assigned SiMa.ai hardware with recorded runtime/model/version evidence.

The Judge UI must make synthetic versus real execution obvious. No inferred or estimated value may be labeled measured.

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

- model and runtime version;
- inference latency p50/p95 with sample count;
- throughput/FPS;
- end-to-end event-to-action latency;
- action and verification latency;
- memory use;
- power/energy telemetry if the platform exposes it reliably;
- Evidence Receipt correlation/evidence ID.

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
- Evidence Receipt includes the full lifecycle;
- LIVE REAL vs SYNTHETIC status is visible in Judge UI;
- all benchmark numbers are traceable to real sponsor hardware runs.
