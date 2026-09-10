# Submission Draft — Live Build

## Title

**InnerOS Physical Guardian — Governed Physical AI for Existing Buildings**

## Short description

Physical Guardian adds a local-first Physical AI control plane to existing cameras and sensors: perceive events, understand behavior over time, decide under policy, propose bounded physical actions, verify outcomes and preserve forensic evidence.

## Long description

Buildings already contain huge camera and sensor estates. Replacing those systems just to adopt AI is expensive, disruptive and often unnecessary.

InnerOS Physical Guardian sits above the existing estate. The permanent product already connects to common camera/recorder paths and normalizes perception, tracking, zones and events. During the AI Infra Summit Hackathon we built a sponsor-neutral judge composition layer that makes the inference runtime replaceable while keeping governance, verification and evidence stable.

The demo follows one visible loop:

**SEE → UNDERSTAND → DECIDE → ACT → VERIFY → PROVE**

A camera/sensor event becomes normalized perception. Temporal rules and policy explain why the event matters. Guardian proposes only a bounded low-impact action and stops at an explicit human approval gate. After approval, the reference physical output is verified and the system seals an evidence bundle that records the decision, truth labels and measured composition timing.

The inference layer can be connected to assigned SiMa.ai, Qualcomm or Intel hardware through a local-only sidecar contract. The same WebUI and Guardian control path therefore survive a hardware/runtime swap.

The offline fallback is intentionally complete so judges can inspect the full product behavior even without WAN access or sponsor hardware availability. Simulated fixture output is labeled as simulated and is never presented as sponsor benchmark evidence.

## What was built during this hackathon

- single-screen judge WebUI;
- hackathon composition engine and HTTP API;
- deterministic offline fallback scenarios;
- explicit human approval/rejection gate;
- bounded demo action policy with dangerous-action deny list;
- evidence sealing and truthful measurement labels;
- sponsor-neutral runtime protocol;
- loopback-only SiMa.ai / Qualcomm / Intel sidecar integration slots;
- sponsor sidecar contract harness;
- container/hosted demo path with optional access control;
- automated runtime, safety and end-to-end tests.

## Pre-existing product disclosure

InnerOS Physical Guardian existed before the hackathon. Pre-existing camera ingestion, RTSP/ONVIF, tracking, zones, temporal logic, edge transport, policy, physical-I/O and evidence work is disclosed in `PREEXISTING_DISCLOSURE.md` and `BASELINE_PROVENANCE.json`.

The hackathon repository contains the competition-specific composition and does not claim the full permanent product was created during the build window.

## Judge demo sentence

**We are not selling another camera. We are building the governed control plane between perception and physical action.**

## Technical tags

Physical AI, Edge AI, Computer Vision, Local-first AI, CCTV, RTSP, ONVIF, Temporal Reasoning, Human-in-the-loop, Safety Policy, Forensic Evidence, SiMa.ai, Qualcomm, Intel, Python, WebUI.

## Claims requiring final on-site evidence

Do not insert numbers here until real assigned sponsor hardware has been measured. Final submission should add exact hardware, model/runtime version, inference latency/throughput and reproducible benchmark method after on-site validation.
