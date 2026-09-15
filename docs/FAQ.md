# FAQ - InnerOS Physical Guardian

## Why not buy AI cameras?

Because the camera lifecycle and the AI compute lifecycle should not be forced into the same purchase. Many buildings already have working cameras, DVRs and NVRs. Guardian adds intelligence above that estate instead of requiring a full replacement.

## What does SiMa do?

SiMa Modalix provides efficient local edge perception for the onsite track. It runs the inference workload and returns detections that Guardian can normalize and reason about.

## What does Guardian add beyond YOLO?

YOLO or another detector answers what is visible in a frame. Guardian answers what has been happening over time, what policy applies, what action is allowed, who approved it, whether the physical action happened and whether the chain can be proven later.

## Does it use facial recognition?

No. The demo does not require facial recognition or biometric identity. It uses object/person-style perception, temporary tracking IDs, zones and temporal behavior.

## What if the AI is wrong?

A detection is evidence for a decision, not an accusation. Guardian uses policy, bounded actions, human authority, verification and evidence review so one model output cannot silently become an unsafe physical action.

## Can voice open a door?

No. Voice can explain, interrupt, re-verify, resume after the canonical safety gate or cancel safely. Voice cannot approve a new physical action, unlock/open access, disable an alarm or bypass policy.

## Is it cloud dependent?

No. The architecture is local-first. Perception can run at the site edge and Guardian can preserve policy/evidence locally. Cloud or hybrid services can be added for management, but the safety model does not require a cloud-only video pipeline.

## Does it replace the NVR?

Not by default. Physical Guardian is designed to work above existing cameras, DVRs and NVRs. The point is to retrofit intelligence without forcing customers to throw away functioning infrastructure.

## What happens offline?

Local-first paths can continue when configured locally. If an external service or hardware path is unavailable, Guardian labels that truth honestly and fails closed instead of pretending that inference, action or verification succeeded.

## Is this hackathon-only?

No. The permanent InnerOS Physical Guardian product existed before the hackathon and is disclosed. This hackathon repository contains the event-specific SiMa runtime boundary, judge experience, evidence gates, measured proof package and pitch materials.

## What was pre-existing?

The permanent product already included reusable camera/source contracts, RTSP/ONVIF direction, tracking, zones, temporal behavior, policy, Physical I/O abstractions and evidence foundations. See `PREEXISTING_DISCLOSURE.md` and `BASELINE_PROVENANCE.json`.

## What was built or adapted during the hackathon?

The hackathon work is the competition composition: sponsor runtime boundary, SiMa onsite integration tooling, judge console, strict evidence gates, interrupt/reverify/resume flow, Speechmatics bonus lane, measured hardware proof and public story package.

## What is actually measured?

The current measured hardware proof, dated September 15, 2026, is a warm-session SiMa Modalix JPEG inference path over 20 distinct 640x640 non-sensitive test frames. Average host round trip was 84.96 ms, p50 was 81.42 ms, p95/worst was 149.27 ms and sustained cadence was 11.77 fps. A corrupt JPEG failed closed with `IMAGE_DECODE_FAILED`, and the next valid frame recovered without restarting the session.

## Does that prove the full live demo?

Not yet. It proves real warm Modalix perception telemetry and error recovery. The final webcam -> Guardian -> Modalix -> policy -> action -> verify -> Evidence Receipt chain still requires Codex A's final pushed SHA and hardware validation before being described as live.

## What happens if hardware is unavailable?

The deterministic demo can still show the governed Guardian lifecycle, but it must be labeled as fixture or unverified where appropriate. Strict live mode must fail without target proof.

## How can a security integrator deploy it?

Start with one existing camera group, one local Guardian node, one perception runtime where appropriate, and one bounded action such as a notification, beacon or safe relay. Map policy, require human approval for physical effects, verify through readback and preserve Evidence Receipts.

## What actions are allowed?

The demo allows low-impact actions such as beacon warning, operator notification and reference attention light. Dangerous actions such as door unlock, alarm disable, gate opening or arbitrary shell execution are denied.

## What makes this commercial?

It lets buyers preserve camera investment, avoid disruptive rip-and-replace projects, reduce cloud-video dependence, keep private processing local where possible and add recurring managed-service value around policy, verification and evidence.

## What should we avoid claiming?

Do not claim autonomous security guard behavior, criminal-intent detection, guaranteed incident prevention, production-ready safety-critical actuation, deployment at scale or live end-to-end SiMa success before strict validation.
