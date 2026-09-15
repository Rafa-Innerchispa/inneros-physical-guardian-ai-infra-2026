# Demo Story - Judge Narrative

## The 30-Second Setup

A building already has cameras and recorders. Replacing them all with proprietary AI cameras is expensive, disruptive and creates lock-in.

InnerOS Physical Guardian connects to the infrastructure that is already there and adds a governed Physical AI layer.

SiMa gives the building efficient edge perception. Guardian turns that perception into policy, human approval, bounded physical action, verification and evidence.

## First Screen Message

The judge should understand this immediately:

`SEE -> PERCEIVE -> UNDERSTAND OVER TIME -> DECIDE UNDER POLICY -> HUMAN APPROVAL -> ACT -> VERIFY -> PROVE`

A detector alone does not close this loop. Guardian does.

## Judge Console V2 Flow

1. **See**
   - Show a camera/webcam preview or owned staged source.
   - Label preview truth separately from inference truth.
   - Never let a webcam preview imply verified SiMa inference.

2. **Perceive**
   - Send the bounded frame source through the SiMa runtime only when configured.
   - Draw bbox, class and confidence only from backend detections for the matching frame/source.
   - If hardware/runtime proof is missing, show `UNVERIFIED` or `BLOCKED` instead of pretending success.

3. **Understand over time**
   - Convert detections into temporary tracks, zones, repeated behavior or dwell-time context.
   - Explain that a single frame is not the product. The product is governed behavior over time.

4. **Decide under policy**
   - Show reason codes and the policy threshold.
   - Detections below the Guardian action threshold of 0.25 remain perception telemetry only.
   - Do not present low-confidence detections as security incidents.

5. **Human approval**
   - Make the approval boundary obvious.
   - Rejection must say: `DENIED - NOTHING EXECUTED`.
   - Voice cannot create approval or bypass policy.

6. **Act**
   - Execute only allowlisted, low-impact actions such as beacon, notification, reference light or safe relay action.
   - Door unlock, alarm disable, arbitrary shell and gate opening remain denied.

7. **Verify**
   - Require acknowledgement or readback before claiming the action happened.
   - If readback fails, show fail-closed state.

8. **Prove**
   - Show the Evidence Receipt in human-readable form first.
   - Keep raw JSON collapsible.
   - Include source/frame identity, inference truth, model/runtime truth, policy decision, approval state, action, verification and evidence seal when present.

## Live Truth Rule

Never call the full chain live unless the final strict hardware validation passes.

Current honest wording while Codex A final integration is pending:

> The Guardian composition and Judge Console are ready to demonstrate the governed loop. The current measured hardware proof is the September 15, 2026 warm-session SiMa Modalix perception path. The final webcam -> Guardian -> Modalix -> policy -> action -> verify -> Evidence Receipt chain remains pending until Codex A publishes the final candidate SHA and hardware validation passes.

If strict live passes later, replace the wording only with evidence from that exact run.

## Current SiMa Proof To Show

AntiGravity task `ops_b21694986b2d` passed on September 15, 2026:

- 20 distinct non-sensitive 640x640 JPEG frames processed through real warm-session Modalix MLA.
- Model loaded once for the session.
- Average host round trip: 84.96 ms.
- p50 host round trip: 81.42 ms.
- p95/worst host round trip: 149.27 ms.
- Sustained cadence: 11.77 fps.
- Average target preprocessing: 13.2 ms.
- Average target MLA inference: 27.96 ms.
- Average decode/postprocess: 37.18 ms.
- Corrupt JPEG failed closed with `IMAGE_DECODE_FAILED`.
- A valid frame immediately after the error recovered without restarting the session.

Truth limit:

> These frames had low-confidence detections below Guardian's policy-action threshold. They prove real warm SiMa perception telemetry and error recovery, not a successful security incident or physical action trigger.

## Core Lines For The Presentation

### Opening

> The building already had eyes. We gave it perception, judgment, controlled action, verification and memory.

### Product thesis

> InnerOS Physical Guardian turns existing cameras and building sensors into governed Physical AI without forcing customers to replace their security infrastructure.

### Local-first angle

> The architecture can run at the site edge, on shared local compute or in a hybrid topology. The customer is not forced into a cloud-only video pipeline.

### Real-world angle

> This project comes from actual building-security integration constraints in Ecuador and Latin America, where mixed camera generations, limited replacement budgets and local resilience are normal requirements.

### Evidence angle

> An alert is not enough. Guardian preserves what the system saw, why it escalated, who authorized action, what happened and how it was verified.

### Closing

> We did not build another smart camera. We built a Physical AI layer that can make existing buildings intelligent.

## Judge Proof Points

A strong demo should visibly prove:

- existing camera infrastructure remains useful;
- SiMa is materially used for efficient edge perception when strict runtime proof is available;
- measured latency and cadence are labeled by date and scope;
- preview truth, inference truth, policy truth, action truth and verification truth stay separate;
- temporal behavior beats single-frame classification;
- actions are bounded, auditable and interruptible;
- denied or unverified states are shown honestly;
- evidence is human-readable and replayable;
- the architecture remains portable above the accelerator.

## Avoid

- claiming criminal intent from visual behavior;
- using facial recognition as a requirement;
- hiding a cloud service behind an edge label;
- presenting low-confidence detections as incidents;
- presenting historical benchmark values as live telemetry;
- saying the full live chain passed before strict validation;
- adding unrelated sponsor APIs for logo count;
- spending demo time explaining every InnerOS subsystem;
- exposing private customer names, footage, credentials, LAN addresses or topology.
