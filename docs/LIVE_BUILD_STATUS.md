# Live Build Status — 2026-09-10

## Status

**LIVE BUILD / FUNCTIONAL JUDGE DEMO**

The official AI Infra Summit Hackathon build window is active. This repository has now moved beyond pre-kickoff planning into hackathon-specific implementation while preserving the frozen pre-existing product disclosure.

## Implemented during the hackathon build window

- dependency-light Python HTTP application server;
- polished single-screen judge WebUI;
- deterministic offline demo runtime and three judge scenarios;
- six-stage Physical Guardian presentation loop: SEE → UNDERSTAND → DECIDE → ACT → VERIFY → PROVE;
- explicit human approval/rejection gate;
- allowlisted low-impact demo actions and explicit dangerous-action deny list;
- measured composition timing separated from simulated inference truth;
- SHA-256 identified forensic evidence bundle;
- sponsor-neutral runtime protocol;
- local-only SiMa.ai / Qualcomm / Intel SDK sidecar slots;
- local sponsor sidecar contract harness;
- optional HTTP Basic access control for a hosted judge demo;
- container deployment recipe;
- API/server/safety/runtime tests.

## Pre-existing boundary

The permanent product remains `Rafa-Innerchispa/inneros-physical-guardian`. Existing camera ingestion, RTSP/ONVIF, tracking, zones, temporal analysis, edge transport, policy and physical-I/O capabilities are disclosed as pre-existing work in `PREEXISTING_DISCLOSURE.md` and `BASELINE_PROVENANCE.json`.

No permanent product source has been copied into this repository.

## Truth boundary

Current offline judge path:

- camera/sensor event: `SIMULATED_FIXTURE`;
- detections: `SIMULATED_FIXTURE` unless a configured sponsor sidecar explicitly reports another allowed truth class;
- temporal reasoning: deterministic demo rule;
- policy: deterministic demo rule;
- physical I/O: simulated reference low-voltage output until real safe demo electronics are connected;
- composition timings: measured live by this application;
- sponsor hardware benchmarks: **NOT YET CLAIMED**.

## What remains hardware/track dependent

Only the final sponsor-specific sidecar implementation, exact model conversion/optimization and real sponsor-hardware benchmark are intentionally left open until official track allocation and hardware/SDK access are known.

That work does not require redesigning the WebUI or Guardian judge flow.
