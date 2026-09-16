# CURRENT HANDOFF — InnerOS Physical Guardian / AI Infra Summit 2026

Last updated: 2026-09-16
Canonical hackathon repo: `Rafa-Innerchispa/inneros-physical-guardian-ai-infra-2026`
Canonical permanent product repo: `Rafa-Innerchispa/inneros-physical-guardian`
Hackathon `main` at handoff creation: `dd2bb4837921f4c782380b725685133ba6f7eb02`

## Purpose

This file is the cross-chat continuation point. A new ChatGPT/AntiGravity/Codex session should read this file first before changing the project. It captures the current operational truth, open problems, ownership, and non-negotiable safety/provenance rules from the current working session.

## Immediate user priority

1. Recover reliable `Ralphi IA MCP` access in ChatGPT desktop/web/mobile. ChatGPT currently recognizes the app and its permissions, but the Ralphi MCP tool surface is not exposed in the current chat and the user also reports failure on mobile. Treat this as a connection/server/session issue until proven otherwise. Do not uninstall the private app unless reinstallability is confirmed first.
2. Continue Physical Guardian work in parallel without waiting for SiMa hardware.
3. Do not lose context again. Important state must be persisted in GitHub docs, not only chat memory.

## MCP recovery task already defined

AntiGravity should diagnose, without destructive reinstallation:
- MCP service health
- public/private endpoint expected by ChatGPT
- HTTPS/TLS/DNS
- authentication/session backend
- MCP initialize
- `tools/list`
- one read-only `tools/call`
- manifest/app configuration
- logs around recent restart/reboot
- .4/.5 MCP profiles if applicable

Expected recovery report fields:
`server`, `TLS`, `auth`, `initialize`, `tools/list`, `read-only tool call`, `root cause`, `restart persistence`, `ChatGPT reconnect required`.

## SiMa current physical status

The SiMa Modalix EV74 hardware is CURRENTLY PHYSICALLY DISCONNECTED from the user's working setup.

Therefore the correct current judge UI truth is:
- Camera source may be READY independently.
- SiMa inference must be `OFFLINE` / `UNVERIFIED` while disconnected.
- No current latency, detections, tensor proof, or `MEASURED` state may be shown unless a fresh current-frame proof returns.
- Configured target information may be displayed separately, but must not be labeled as current hardware proof.
- No deterministic/fixture fallback may masquerade as live SiMa.

When SiMa is reconnected, live proof must require current-frame evidence including `MEASURED_SPONSOR_RUNTIME`, exact frame/source/SHA match, and the strong Modalix attestation already implemented by the backend.

## What SiMa actually does

The hackathon worker uses YOLO26 with COCO80 labels. It can decode classes including `person`, `cat`, `dog`, `car`, and other COCO objects. The UI should expose a simple `WHAT SiMa SAW` panel containing current backend detections and confidence values. Bounding boxes must only be drawn for the exact matched processed frame.

Do not confuse object detection with identity recognition.

Correct architecture:
`Camera -> SiMa Modalix object detection -> optional local enrichment -> Guardian policy -> human approval/action -> evidence`.

## Identity/enrichment truth

SiMa does not identify a real-world person by name. A separate local enrichment layer may classify a detected object as:
- `person` -> known enrolled local profile / unknown person / identity module offline
- `dog` -> known enrolled pet / unknown dog
- `cat` -> known enrolled pet / unknown cat

Human identity is separate from SiMa proof and must never be presented as proof that SiMa inference occurred.

The permanent product continuity document records that nominal human recognition was requested and handed to AntiGravity for independent evaluation/integration. Do not claim it is in hackathon `main` unless verified.

## Permanent product capabilities already confirmed

Repository: `Rafa-Innerchispa/inneros-physical-guardian`

Canonical permanent-product continuity source: `docs/PROJECT_CONTINUITY.md`.

Known product facts already documented there:
- real Dahua home-lab channels 2/3 validated
- Visual Watch supports `person`, `dog`, `cat`
- RT-DETR local detector
- class-specific thresholds
- WhatsApp snapshot/event path
- secure PyAV continuous watcher
- Door Guard / ROI / dwell work
- multi-tenant product architecture

A development branch exists:
`chatgpt/guardian-pet-reid-watcher-20260913`

It contains:
- `src/physical_guardian/perception/pet_recognition.py`
- `tests/test_pet_recognition.py`
- `tests/test_pet_watcher_integration.py`

That branch implements dog/cat enrollment and matching. It must be reviewed/tested before reuse; do not blindly merge it into the hackathon repo.

## Guayaquil camera state

Required sources:
- `gye-dahua-ch2`
- `gye-dahua-ch3`

Historically validated judge path:
`Dahua cameras -> AMD .5 -> bounded private snapshot bridge -> Tailscale -> SF host -> SiMa when connected`.

The user states the home Dahua recorder LAN address is `192.168.1.100` and the current team is now working on private Tailscale reachability to that recorder. IMPORTANT: direct SF -> Tailscale -> `192.168.1.100` access was NOT previously established as canonical truth. Treat it as currently being tested/implemented, not already proven.

Never expose DVR/NVR ports publicly. No camera credentials, RTSP URLs, tokens, or private secrets in frontend, GitHub, logs, or evidence.

Even with SiMa disconnected, GYE Ch2/Ch3 should be independently testable as real image sources. If a source is unavailable it must remain visible as `BLOCKED`/`OFFLINE`, not silently disappear.

## Known judge UI problem history

The previous UI became visually simpler but several functional/provenance issues were identified:
- live SiMa button returned HTTP 400 after a reboot
- SiMa current proof remained `UNVERIFIED`
- GYE buttons existed but real GYE images were not visible
- frontend/backend camera catalog contract had a `source_id` vs `id` mismatch
- `/api/inference/source` needed an ephemeral exact-frame `source_preview` so the browser can render the same GYE snapshot that was processed
- UI must not hardcode `READY`, `MEASURED`, latency, model, tensors, or device proof
- synthetic webcam placeholders are forbidden

Current hackathon `main` is the truth-correctness UI commit `dd2bb483...`; do not assume later recovery work has been merged until verified.

## Reboot lesson

A Windows reboot likely killed local runtime processes and lost environment variables. The canonical strict-live stack depends on:
- local SiMa sidecar on loopback
- Guardian demo server
- `GUARDIAN_SIMA_RUNTIME_URL`
- runtime camera-source configuration
- GYE bridge token/env

A durable one-click Windows launcher is required so future reboot recovery is deterministic. Expected behavior after reboot:
- restore/load safe local runtime config
- restore GYE source configuration without committing secrets
- start/check SiMa sidecar if hardware is available
- set `GUARDIAN_SIMA_RUNTIME_URL`
- start Guardian UI
- perform health checks
- report Camera / SiMa / GYE states truthfully
- fail closed when SiMa hardware is absent

## Parallel agent ownership currently assigned

Two Codex lanes were defined specifically to avoid overlapping edits. Do NOT merge either into `main` automatically.

### Codex 1 — GYE camera transport / recorder / reboot recovery

Suggested branch:
`codex/gye-recorder-recovery-20260916`

Owns:
- local Tailscale diagnostics
- private reachability to `192.168.1.100`
- bounded tests of expected DVR services only
- primary AMD .5 snapshot bridge path
- GYE Ch2/Ch3 snapshot recovery
- durable camera catalog/runtime config
- reboot recovery for GYE side

Must NOT own:
- UI redesign
- SiMa model/adapter changes
- identity implementation

### Codex 2 — perception/truth UI separation

Suggested branch:
`codex/perception-ui-separation-20260916`

Owns:
- clear separation of Camera Source / SiMa Inference / Identity-Enrichment / Guardian
- truthful SiMa offline state
- `WHAT SiMa SAW` detection panel
- optional enrichment contract
- no fake measured/detection state
- reconnect behavior requiring no code change when hardware returns

Must NOT own:
- Tailscale/DVR/network work
- human facial identity implementation
- SiMa hardware configuration

## Merge discipline

`merge` means integrating a feature branch into canonical `main`.

Current rule:
- Codex 1 works only on its branch.
- Codex 2 works only on its branch.
- Neither merges to `main`.
- Each returns SHA + tests + report.
- AntiGravity performs controlled integration after both are reviewed.
- User should not have to resolve Git conflicts manually.

If Codex asks whether to merge, response is:
`NO MERGE. Keep changes on your branch. Deliver SHA, tests, and final report. AntiGravity will integrate after review.`

## UI target for final demo

Default judge screen should remain simple. Main truth areas:
1. SOURCE: Laptop / GYE Ch2 / GYE Ch3
2. CAMERA: READY / OFFLINE
3. SiMa: MEASURED / OFFLINE / UNVERIFIED
4. WHAT SiMa SAW: current object detections + confidence
5. IDENTITY/ENRICHMENT: MATCHED / UNKNOWN / OFFLINE / NOT CONFIGURED
6. GUARDIAN: policy/action gate
7. EVIDENCE: compact proof summary

Advanced technical proof may hold hashes, tensors, worker IDs, raw JSON, lifecycle details, etc.

## Reference governed flow vs live SiMa

The governed reference flow is a deterministic/reference policy path used to demonstrate approval/action/evidence. It is not proof of live SiMa perception.

`Run Live SiMa Demo` must represent the real camera -> SiMa path and fail closed if SiMa is unavailable.

Approval buttons must appear only when Guardian returns `AWAITING_APPROVAL`. A live frame that does not trigger policy must truthfully show no action required. Do not force approval for every live frame.

## Security / truth invariants

Never violate:
- no fake live
- unavailable hardware => BLOCKED/OFFLINE/UNVERIFIED
- no invented MEASURED state
- no invented latency/tensors/model/device proof
- exact frame/source/SHA provenance for overlays
- DENY => nothing executed
- missing physical readback cannot become VERIFIED
- no public camera/NVR exposure
- no secrets in repo/frontend/evidence
- no internet dependency for golden local demo where avoidable
- no firmware/SDK/compiler reinstall unless absolutely proven necessary
- do not reconfigure event network casually

## What the next chat should do first

1. Read this file.
2. Read `docs/FINAL_INTEGRATED_ACCEPTANCE_2026-09-16.md` for the last integrated real-hardware acceptance history.
3. Read permanent product `docs/PROJECT_CONTINUITY.md` only when touching product/GYE/identity/pet work.
4. Check current GitHub `main` SHA before asserting state.
5. Ask for or inspect the latest AntiGravity/Codex completion reports if they have finished since this handoff.
6. Prioritize MCP recovery first if Ralphi IA MCP is still unavailable.
7. Do not make the user repeat the project story.

## Current unresolved items

- Ralphi IA MCP not reliably usable from ChatGPT web/mobile in current session.
- SiMa hardware physically disconnected at present.
- post-reboot HTTP 400 root cause not yet proven in this handoff.
- GYE Ch2/Ch3 real images not yet confirmed visible in current judge UI.
- direct private Tailscale access to recorder `192.168.1.100` is being worked on, not yet accepted as canonical.
- human identity module needs AntiGravity inspection/integration status.
- pet recognition branch requires review/tests before reuse.
- two Codex lanes must finish and be reviewed before any merge.

## No-secrets rule

This file intentionally contains no camera credentials, bearer tokens, passwords, authenticated RTSP URLs, or biometric artifacts.
