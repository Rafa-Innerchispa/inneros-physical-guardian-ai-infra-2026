# Hackathon Scope — AI Infra Summit 2026

## Submission objective
Demonstrate that existing security camera infrastructure can become a governed Physical AI sensor/action fabric without forcing full camera replacement.

## Product story
Existing analog cameras through DVRs, IP cameras and NVRs feed a normalized local-first perception layer. The system reasons over time, zones and multiple cameras, detects anomalous behavior, routes decisions through InnerOS policy, triggers bounded actions, verifies outcomes and preserves forensic evidence.

The on-site version should go beyond a video analytics dashboard: the assigned sponsor hardware becomes a replaceable edge-inference runtime and Guardian closes the loop into a safe physical output or actuator with verification.

## Target demo
1. Ingest real or owned/staged video through the same camera contracts used by the permanent product.
2. Run the selected perception workload on the assigned sponsor hardware through a challenge-specific runtime adapter.
3. Detect a meaningful security event or anomalous behavior and reason across time/zones or multiple views where useful.
4. Produce an explainable risk/event assessment.
5. Route the result through Guardian policy rather than letting the perception model directly control hardware.
6. Trigger a bounded physical action such as a low-voltage beacon/LED/relay, Home Assistant device or another safe actuator available on-site.
7. Verify the action through acknowledgment/readback where the hardware supports it.
8. Record the complete evidence chain for replay: what was seen, the normalized event, policy outcome, requested action, execution and verification result.
9. Show that the same permanent architecture can support the Bellini/real-building path without replacing the existing DVR/NVR/camera estate.

## On-site hardware strategy
The permanent product already exposes a sponsor-neutral `EdgeRuntimeAdapter` and `PhysicalIOAdapter` boundary before kickoff. During the official build window we will implement only the assigned challenge runtime/board adapter and the benchmark/demo glue in this repository.

This means access to real sponsor hardware changes the **implementation and benchmark**, not the product thesis:

`existing camera/sensor -> sponsor edge runtime -> Guardian temporal policy -> bounded physical action -> verification -> evidence`

A Raspberry Pi, microcontroller, relay, LED/beacon, sensor, Home Assistant device or available robotic platform can serve as the physical demo endpoint. No specific actuator is mandatory, and the team will not distort the product into a robot-arm use case merely because a robot is available.

## Primary platform strategy
Choose one main sponsor track once official assignment/rules are confirmed. Additional sponsor technologies may be included only when they materially improve the system and remain compliant with the selected track.

Current preference:
- **SiMa.ai**: strongest fit for real-world edge camera/video/sensor Physical AI.
- **Qualcomm**: strong fit for model-to-device and portable on-device inference.
- **Intel Physical AI**: useful edge/VLA/Physical AI path when the assigned hardware and challenge allow a natural integration.
- **Speechmatics**: complementary bonus layer only if voice materially improves the operator workflow.

## Repository responsibility
This repository holds only the hackathon-specific layer. Permanent camera ingestion, Windows edge agent, vendor abstraction, behavior engine, hardware abstraction and reusable Physical Guardian technology belong in `Rafa-Innerchispa/inneros-physical-guardian`.

The frozen product dependency is recorded in `BASELINE_PROVENANCE.json`. Product source is not copied into this repository.

## Security/privacy constraints
- Never commit customer camera credentials, public IPs, private Bellini topology or raw private resident footage.
- Demo datasets must be owned, consented, staged or appropriately sanitized.
- Remote deployment must use outbound/zero-trust style connectivity where practical rather than exposing camera/NVR ports directly to the Internet.
- Actions remain bounded and auditable.
- High-impact access actions require policy/approval and are not appropriate as casual demo side effects.

## Pre-kickoff rule
Before the official build window, limit this repository to planning, architecture, disclosure, dependency inventory and reproducibility scaffolding unless official rules explicitly allow implementation. Preserve a clear baseline for judging provenance.

As of the pre-kickoff baseline there is no sponsor-specific SiMa.ai, Qualcomm or Intel challenge implementation and no unmeasured sponsor-hardware performance claim.
