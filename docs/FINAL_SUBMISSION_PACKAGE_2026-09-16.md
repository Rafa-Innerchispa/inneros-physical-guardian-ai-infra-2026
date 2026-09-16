# InnerOS Physical Guardian — Final Submission Package

Status: `FINAL_SUBMISSION_PACKAGE_READY`

Backend SHA: `d69f9af7865cc22a9c0a51bc6002bac631cb9d63`

UI SHA: `e8b0c0ba877941fabea92d5f70a8861c4633fe69`

Hardware validation: `HARDWARE_PASS`

> Update this document if AntiGravity later produces `GYE_TWO_CAMERA_E2E_PASS`. Until then, do not claim GYE camera E2E completion.

## 1. 90-second judge demo script

Physical Guardian starts with a simple premise: Latin America already has cameras everywhere. We are not asking customers to replace that infrastructure to adopt AI. We bring AI to the infrastructure they already have.

First, we ingest from an existing camera source. In the validated build, a real laptop webcam frame is submitted with exact source and frame provenance.

Second, perception runs on real SiMa.ai Modalix hardware through PyNeat 0.4.0 and MLA. The Modalix worker stays persistent, the model loads once, and multiple frames run in the same session. A corrupt frame fails closed and the same worker recovers on the next valid input.

Third, Guardian receives only detections tied to the current frame and source. It evaluates the scenario and policy before proposing any bounded action.

Fourth, the human approval gate is mandatory. Camera preview or inference alone cannot bypass it. DENY means nothing executed.

Finally, Guardian produces an Evidence Receipt containing source, frame, inference, policy decision, approval state, action state, and verification status.

For this submission, Physical I/O remains blocked because no physical relay/readback hardware is connected. We do not claim real relay execution.

## 2. 30-second pitch

Latin America already has cameras, access systems, alarms, and buildings full of existing infrastructure. InnerOS Physical Guardian brings AI to what already exists instead of requiring replacement.

It ingests camera frames locally, runs perception on SiMa.ai Modalix, applies Guardian policy reasoning, requires human approval before bounded action, and produces an Evidence Receipt showing what happened, what was verified, and what was not.

## 3. 60-second pitch

InnerOS Physical Guardian turns existing cameras into governed physical AI infrastructure.

The system captures frames from current camera sources, sends them through real SiMa.ai Modalix perception, and gives Guardian detections with exact frame and source provenance. Guardian then reasons over the scenario, applies policy, and proposes only bounded actions.

The important part is governance. Nothing physical executes from a camera preview or raw detection alone. Human approval is required, DENY means nothing executed, and every run produces an Evidence Receipt covering source, frame, inference, decision, approval, action state, and verification.

Our commercial thesis is simple: we are not asking Latin America to replace its infrastructure to adopt AI. We are bringing AI to the infrastructure Latin America already has.

## 4. Devpost / LabLab project description

InnerOS Physical Guardian is a governed physical AI layer for existing camera and building infrastructure.

Instead of replacing cameras, sensors, alarms, and access systems, Guardian connects to what customers already have. It ingests camera frames locally, runs real perception on SiMa.ai Modalix, reasons over events and policy, requires human approval for bounded action, verifies outcomes when physical I/O is available, and produces a forensic Evidence Receipt.

For this submission, we validated laptop webcam capture into real Modalix inference using PyNeat 0.4.0 / MLA with a persistent worker, model loaded once, multiple frames in one session, corrupt-frame fail-closed behavior, recovery in the same worker, Guardian policy governance, DENY equals nothing executed, and Evidence Receipt generation.

Physical relay execution is not claimed because no physical relay/readback hardware is connected. GYE camera E2E is not claimed until AntiGravity validation explicitly passes it.

## 5. What we built

Existing cameras -> local-first ingestion -> SiMa Modalix perception -> Guardian reasoning -> policy gate -> human approval -> bounded action governance -> verification boundary -> Evidence Receipt.

The validated submission demonstrates real camera capture, real Modalix inference, provenance-bound detections, policy evaluation, human approval governance, denial safety, and evidence generation.

## 6. How SiMa.ai is used

SiMa.ai Modalix is the real perception engine.

Validated usage:

- Real webcam frames are sent to Modalix.
- PyNeat 0.4.0 / MLA executes inference.
- A persistent worker keeps the model loaded once.
- Multiple frames run in the same session.
- Detections include provenance tied to `frame_id` and `source_id`.
- Corrupt frames fail closed.
- The worker recovers after corrupt input.
- Guardian only advances policy when inference evidence is valid for the current frame/source.

## 7. Architecture

1. **Camera ingestion**: existing camera sources provide frames. Laptop webcam capture is already proven in the validated package.
2. **Perception**: frames are processed by real SiMa Modalix through PyNeat / MLA.
3. **Guardian reasoning**: Guardian checks provenance, evaluates the scenario and applies policy.
4. **Human governance**: a bounded action can only appear after a valid trigger; human approval is required; DENY means nothing executed.
5. **Evidence**: the system records source, frame, inference, policy decision, approval state, action state, and verification status in an Evidence Receipt.

## 8. Three strongest technical proof points

1. **Real Modalix inference path**: webcam frame -> PyNeat 0.4.0 / MLA -> real detections with provenance.
2. **Persistent worker robustness**: model loads once, multiple frames run in the same session, corrupt input fails closed, and the same worker recovers.
3. **Strict provenance and stale-state control**: detections are only accepted for the exact current `frame_id` and `source_id`; stale overlays and previous decisions are cleared.

## 9. Three strongest commercial/product proof points

1. **No infrastructure replacement required**: the product brings AI to existing cameras and building systems.
2. **Governed automation, not blind automation**: human approval, bounded actions, denial safety, and evidence make deployments auditable.
3. **Strong fit for Latin America**: existing camera estates can be upgraded without forcing replacement of the installed base.

## 10. Exact claims we can make now

- Real laptop webcam capture was validated.
- Webcam frame ingestion into real Modalix was validated.
- PyNeat 0.4.0 / MLA inference was validated.
- Persistent Modalix worker was validated.
- Model load once / multiple frames same session was validated.
- Real detections with provenance were validated.
- Corrupt frame fail-closed behavior was validated.
- Recovery in the same worker was validated.
- Guardian policy governance was validated.
- Human approval gating was validated.
- DENY = NOTHING EXECUTED was validated.
- Evidence Receipt generation was validated.
- Backend SHA: `d69f9af7865cc22a9c0a51bc6002bac631cb9d63`.
- UI SHA: `e8b0c0ba877941fabea92d5f70a8861c4633fe69`.

## 11. Exact claims we must not make yet

- Do not claim real physical relay execution.
- Do not claim Physical I/O E2E PASS.
- Do not claim GYE camera E2E PASS until AntiGravity explicitly passes it.
- Do not claim arbitrary remote camera support.
- Do not claim camera preview is inference truth.
- Do not claim historical benchmark is current/live telemetry.
- Do not claim approval proves physical execution.
- Do not claim verification without connected physical readback.

## 12. Screenshot / video shot list

1. UI opening screen showing Physical Guardian console.
2. Source selector showing laptop webcam.
3. Webcam local preview active.
4. Captured frame with frame ID visible.
5. Request frame inference.
6. Modalix/SiMa telemetry showing verified inference state.
7. Detection overlay shown only after matched frame/source.
8. Policy stage leading to human approval.
9. Approval panel showing bounded proposed action.
10. DENY showing `DENIED - NOTHING EXECUTED`.
11. Evidence Receipt showing source/frame/inference/decision.
12. Physical I/O shown as BLOCKED/UNVERIFIED because no relay/readback hardware is connected.
13. Historical benchmark clearly labeled as non-live telemetry.
14. Reset/new frame clearing previous overlay/state.

## 13. Final submission checklist

- Backend SHA confirmed.
- UI SHA confirmed.
- Hardware validation status: HARDWARE_PASS.
- Real Modalix perception claims included.
- Physical relay execution claims excluded.
- GYE E2E claims excluded until AntiGravity pass.
- Commercial thesis included.
- Judge demo script ready.
- 30-second pitch ready.
- 60-second pitch ready.
- Devpost/LabLab description ready.
- Screenshot/video list ready.
- Judge Q&A ready.
- Final combined backend+UI integration SHA still to be created and validated.
- Final golden rehearsal still to be run after B and AntiGravity finish their current lanes.

## 14. Judge Q&A

**1. Are you replacing existing cameras?**
No. The product is designed to add AI to existing camera infrastructure.

**2. What role does SiMa.ai play?**
SiMa Modalix is the real perception engine. It runs frame inference and returns provenance-bound detections.

**3. Is this just a camera demo?**
No. The camera is the input. The core is governed physical AI: perception, policy, approval, verification boundary, and evidence.

**4. Can the system act automatically?**
Not blindly. Guardian requires a valid policy trigger and human approval before bounded action.

**5. What happens if the operator denies?**
DENY means nothing executed, and that state is recorded.

**6. Did you validate real hardware inference?**
Yes. Hardware validation passed for laptop webcam capture into real Modalix using PyNeat 0.4.0 / MLA.

**7. Did you validate real physical relay execution?**
No. Physical I/O remains blocked because no physical relay/readback hardware is connected, so real relay execution is not claimed.

**8. Are GYE cameras validated end to end?**
Not yet unless AntiGravity has subsequently produced `GYE_TWO_CAMERA_E2E_PASS`. Until that explicit verdict exists, do not claim it.

**9. How do you prevent stale detections?**
The UI and backend bind detections to the exact `frame_id` and `source_id`. If they do not match the current frame/source, detections are not accepted/displayed as current proof.

**10. Why is this commercially relevant?**
Customers in Latin America already have infrastructure. Guardian provides an AI upgrade path without forcing replacement of cameras and building systems.
