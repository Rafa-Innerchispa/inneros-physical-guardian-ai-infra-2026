# Hackathon Scope — AI Infra Summit 2026

## Submission objective
Demonstrate that existing security camera infrastructure can become a governed Physical AI sensor/action fabric without forcing full camera replacement.

## Product story
Existing analog cameras through DVRs, IP cameras and NVRs feed a normalized local-first perception layer. The system reasons over time, zones and multiple cameras, detects anomalous behavior, routes decisions through InnerOS policy, triggers bounded actions, verifies outcomes and preserves forensic evidence.

## Target demo
1. Ingest real video from a Dahua DVR and at least one IP camera.
2. Detect a meaningful security event or anomalous behavior.
3. Correlate evidence across time or multiple views where available.
4. Produce an explainable risk/event assessment.
5. Trigger a governed action such as operator alert, lighting, Home Assistant or Cozmo physical response.
6. Record the complete evidence chain for replay.
7. Show a Windows edge-agent deployment path suitable for Bellini using existing hardware.

## Primary platform strategy
Choose one main sponsor track once official assignment/rules are confirmed. Additional sponsor technologies may be included only when they materially improve the system and remain compliant with the selected track.

Likely fit:
- SiMa.ai: strongest fit for real-world edge camera/video/sensor Physical AI.
- Speechmatics: complementary voice bonus layer.
- Intel/OpenVINO: optional optimization/inference path where relevant to final track.
- Qualcomm: optional on-device/edge path if track access and hardware/runtime fit.

## Repository responsibility
This repository holds only the hackathon-specific layer. Permanent camera ingestion, Windows edge agent, vendor abstraction, behavior engine and reusable Physical Guardian technology belong in `Rafa-Innerchispa/inneros-physical-guardian`.

## Security/privacy constraints
- Never commit customer camera credentials, public IPs, private Bellini topology or raw private resident footage.
- Demo datasets must be owned, consented, staged or appropriately sanitized.
- Remote deployment must use outbound/zero-trust style connectivity where practical rather than exposing camera/NVR ports directly to the Internet.
- Actions remain bounded and auditable.

## Pre-kickoff rule
Before the official build window, limit this repository to planning, architecture, disclosure, dependency inventory and reproducibility scaffolding unless official rules explicitly allow implementation. Preserve a clear baseline for judging provenance.
