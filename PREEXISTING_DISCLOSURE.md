# Pre-existing Components Disclosure

This submission builds on technology that existed before the AI Infra Summit Hackathon 2026 build window. The hackathon work must be evaluated as the **new sponsor integration, hardware/runtime optimization, challenge-specific composition, benchmarks, judge demo and evidence** produced during the official build window.

## Frozen product baseline

Canonical permanent product repository:

`Rafa-Innerchispa/inneros-physical-guardian`

Pre-kickoff product baseline commit:

`27e3e65bff070716c66a612c9f0c7e790438909c`

The hackathon repository depends on that product baseline by repository/commit reference. Product source is not copied into this repository.

## Pre-existing Physical Guardian capabilities

The following were implemented before the hackathon build window and must not be presented as hackathon-created work:

- provider-neutral camera/source contracts and RTSP resolution;
- optional ONVIF discovery/media integration;
- Dahua local RTSP/event/snapshot integration and real XVR lab validation;
- EZVIZ cloud adapter and generic cloud/network media bridge;
- RT-DETRv2 lab detector backend;
- provider-neutral IoU tracking with temporary camera-local track IDs;
- polygon/rectangle zones and spatial enter/exit events;
- temporal anomaly/behavior engine and composed frame pipeline;
- FFmpeg RTSP/network frame sampling with redacted operational surfaces;
- event-driven low-cost edge gateway design/runtime for recorder estates;
- Bellini outbound tunnel-only Windows edge path with no mandatory local AI/GPU;
- existing `ActionContract` / evidence foundations and Forensic Replay integration direction;
- sponsor-neutral `EdgeRuntimeAdapter` contract for replaceable CPU/GPU/NPU/accelerator runtimes;
- sponsor-neutral `PhysicalIOAdapter` plus bounded physical action controller with allowlists, timeout, idempotency, dry-run, verification and secret-minimized action evidence;
- Raspberry Pi / GPIO / relay / MQTT / HTTP / Home Assistant reference topology for physical I/O experiments.

The final hardware abstraction item above was completed and merged into the permanent product before kickoff specifically so on-site hardware can be integrated through an adapter rather than by changing the product core.

## Pre-existing broader InnerOS ecosystem components

- InnerOS control plane and local-first/hybrid orchestration foundations.
- VigilOS security/access and camera-oriented operational experience.
- InnerOS Forensic Replay evidence/replay foundations.
- InnerOS VoiceOps architecture and governed voice workflows.
- Existing Cozmo physical control experiments/integration.
- Existing AMD/NVIDIA local compute infrastructure and model routing.
- Existing Home Assistant / DMX / electronics / physical-world integration knowledge where reused.

## Intended new work during the hackathon

Subject to final assigned track, official rules and sponsor starter kits:

- challenge-specific adapter for the assigned on-site accelerator/runtime;
- model conversion/optimization required by that runtime;
- measured sponsor-hardware inference path and benchmark evidence;
- challenge-specific composition of the pre-existing Guardian product with the sponsor runtime;
- physical closed-loop demo binding perception -> Guardian policy -> bounded action -> verification;
- any challenge-specific multi-camera/behavior composition not already in the baseline;
- hackathon evidence/benchmark adapter and judge-facing console;
- on-site hardware integration and reproducibility instructions;
- submission documentation, pitch and video assets.

## What is explicitly not implemented pre-kickoff

As of this baseline there is **no challenge-specific SiMa.ai, Qualcomm, Intel or other sponsor SDK/runtime adapter in this repository or in the permanent product core**. No benchmark claim is made for sponsor hardware that has not yet been provided/tested.

## Provenance rule

Every material feature in the final submission should be classified as one of:

- `PRE-EXISTING`
- `NEW DURING HACKATHON`
- `ADAPTED DURING HACKATHON`
- `THIRD-PARTY / SPONSOR TECHNOLOGY`

The final README, demo and submission description must preserve this distinction. See `BASELINE_PROVENANCE.json` for the machine-readable baseline.
