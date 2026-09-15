# English Pitch Practice - InnerOS Physical Guardian

## Core Product Thesis

InnerOS Physical Guardian turns existing cameras and building sensors into governed Physical AI without forcing customers to replace their security infrastructure.

The building already had eyes. We gave it perception, judgment, controlled action, verification and memory.

Core loop:

`SEE -> PERCEIVE -> UNDERSTAND OVER TIME -> DECIDE UNDER POLICY -> HUMAN APPROVAL -> ACT -> VERIFY -> PROVE`

## 15-Second Version

> Buildings already have cameras. InnerOS Physical Guardian turns that existing infrastructure into governed Physical AI. SiMa handles efficient edge perception. Guardian adds policy, human approval, bounded action, verification and evidence.

## 30-Second Version

> We do not sell another camera. We add intelligence and accountability to the cameras you already own. SiMa runs efficient local perception at the edge. Guardian turns that perception into a governed action loop: understand over time, decide under policy, require human approval, act only within limits, verify the result and preserve the evidence.

## 60-Second Judge Version

> Buildings already have eyes. The problem is that most of those eyes are passive. They record what happened after the fact. Replacing every camera with a new AI camera is expensive, disruptive and creates more lock-in. InnerOS Physical Guardian retrofits intelligence on top of the existing camera and sensor estate. For this SiMa track, Modalix provides the local perception runtime. Guardian receives normalized detections, reasons over time and zones, applies policy, asks for human approval before any physical action, executes only bounded actions, verifies the result through readback and stores an Evidence Receipt.

## 90-Second Judge Version

> Real buildings have mixed camera generations, DVRs, NVRs, access panels and low-voltage devices. A practical Physical AI system has to work with that reality. Physical Guardian keeps the infrastructure in place and separates the problem into proof layers.
>
> First, the system sees a camera or webcam source. Second, SiMa Modalix performs edge perception. Third, Guardian turns detections into temporal context: what has been happening, not just what appears in one frame. Fourth, policy decides whether this event is allowed, denied or needs escalation. Fifth, a human approves before any action. Sixth, Guardian executes only a bounded action such as a beacon, notification or reference relay. Seventh, independent readback verifies what happened. Finally, the Evidence Receipt preserves the source, inference, policy, approval, action and verification truth.
>
> The key is honesty. A preview is not inference. A detection is not an action. A historical benchmark is not a live frame. If proof is missing, Guardian fails closed.

## 3-Minute Technical And Commercial Version

> InnerOS Physical Guardian comes from a real commercial constraint: customers already own security infrastructure. They have analog cameras through DVRs, IP cameras through NVRs, access systems, alarms, lights and site-specific wiring. Replacing everything with a proprietary AI camera platform increases capital expense, interrupts operations and ties the customer to one vendor cycle.
>
> Guardian takes a different path. It creates a retrofit Physical AI layer above the existing estate. Camera and sensor sources are normalized. SiMa Modalix becomes the efficient edge perception engine for this track. The output is not treated as a final decision. It becomes one evidence input inside Guardian.
>
> Guardian adds temporal context, policy, human authority, bounded physical action, interruption, safe-state verification, resume control and Evidence Receipts. This is what an object detector does not provide. YOLO or another detector can answer what is visible in a frame. Guardian answers what has been happening over time, what policy applies, what action is permitted, who approved it, whether the physical action actually happened and whether we can prove it later.
>
> Commercially, this means a building owner or security integrator can preserve the existing camera investment, reduce cloud-video dependence, keep sensitive processing local where possible and upgrade intelligence independently from camera replacement. The same Guardian layer can move from one accelerator to another because the safety and accountability chain is above the inference hardware.
>
> For the hackathon, we disclose the permanent Guardian product as pre-existing. This repository contains the event-specific SiMa runtime boundary, judge console, evidence gates, demo orchestration, measured hardware proof and pitch package. We did not build another smart camera. We built a Physical AI layer that can make existing buildings intelligent.

## Strong Opener Options

> The building already had eyes. We gave it perception, judgment, controlled action, verification and memory.

> Buildings already have eyes. The problem is that most of those eyes are passive.

> The future of Physical AI in buildings should not require throwing away every camera already installed.

## Strong Closer Options

> SiMa gives the building efficient edge perception. InnerOS Guardian turns that perception into governed physical action with interruption, verification and evidence. The inference hardware can change. The safety and accountability chain stays intact.

> We did not build another smart camera. We built a Physical AI layer that can make existing buildings intelligent.

> We do not sell another camera. We add intelligence and accountability to the cameras you already own.

## What Exactly Did We Build During The Hackathon?

> The permanent Guardian product existed before the hackathon and is disclosed. For this event we built the challenge-specific SiMa runtime path, the judge console experience, the strict evidence and benchmark gates, the interrupt/reverify/resume demo lifecycle, the hardware proof package and the presentation materials. We keep the hackathon delta separate from the permanent product repository.

Use the provenance labels from `BASELINE_PROVENANCE.json`: `PRE-EXISTING`, `NEW DURING HACKATHON`, `ADAPTED DURING HACKATHON` and `THIRD-PARTY / SPONSOR TECHNOLOGY`.

## Current Measured Proof Line

> On September 15, 2026, AntiGravity measured 20 distinct 640x640 JPEG frames through a real warm-session SiMa Modalix MLA path with the model loaded once. Average host round trip was 84.96 ms, p50 was 81.42 ms, p95/worst was 149.27 ms and sustained cadence was 11.77 fps. The corrupt JPEG test failed closed with `IMAGE_DECODE_FAILED`, and the next valid frame recovered without restarting the session.

Truth limit to say immediately after:

> This proves the reusable warm Modalix perception path. It does not yet certify the final webcam-to-Guardian-to-Evidence-Receipt integration until Codex A's final candidate and hardware validation pass.

## Likely Judge Questions

### Why not just buy AI cameras?

> Because the camera lifecycle and the AI compute lifecycle should not be the same thing. Many buildings already have large CCTV estates. Guardian lets them upgrade intelligence without replacing working cameras or locking the whole system to one camera vendor.

### What exactly does SiMa do here?

> SiMa provides efficient local edge perception. Modalix runs the inference workload and gives Guardian normalized detections. Guardian then handles time, policy, approval, action, verification and evidence.

### What exactly does Guardian add beyond YOLO or another detector?

> Detection answers, "what is in this frame?" Guardian answers, "what has been happening over time, what policy applies, what action is allowed, who approved it, did it physically happen and can we prove it?"

### Does it use facial recognition?

> No. The demo uses object/person-style perception and temporary tracking IDs. It does not require biometric identity to show governed Physical AI.

### What happens if the AI is wrong?

> A detection is evidence for a decision, not an accusation. The system uses policy, bounded actions and human authority. High-impact actions are denied or require explicit authorization, and the evidence behind the event remains available for review.

### Can voice open a door?

> No. Voice can explain, interrupt, re-verify, resume after the canonical gate or cancel safely. Voice cannot approve a new physical action, unlock access or bypass policy.

### Is it cloud dependent?

> The architecture is local-first. SiMa perception can run at the edge, and Guardian is designed for local or hybrid deployment. Cloud services can help with management or reporting, but the safety model does not require cloud video streaming.

### Does it replace the NVR?

> Not by default. The point is to retrofit intelligence above existing cameras, DVRs and NVRs. Guardian can integrate with the existing estate instead of forcing replacement.

### What happens offline?

> Local-first paths can continue to apply policy and preserve evidence locally. Anything that cannot be proven or verified is labeled accordingly and fails closed instead of pretending success.

### Is this hackathon-only?

> No. The permanent Guardian product existed before the hackathon and is disclosed. The hackathon work is the sponsor-specific SiMa integration, judge demo, evidence gates and proof package around that product boundary.

### What is actually measured?

> The current measured hardware proof is the September 15, 2026 warm-session SiMa Modalix JPEG inference path. It measured 20 frames, model-loaded-once behavior, latency, cadence and fail-closed corrupt-image recovery. The final full webcam-to-action-to-evidence chain still needs the final backend SHA and hardware validation before we call it live.

### How can a security integrator deploy it?

> Start with the cameras and sensors already on site. Add a local Guardian node or edge appliance, connect a perception runtime such as SiMa where appropriate, map only bounded actions, require operator approval for physical effects and configure evidence retention around the customer's policy.

## Presentation Discipline

- Say the direct answer first, then one proof point.
- Keep sentences short; this is easier to remember under pressure.
- Do not claim autonomous security guard, criminal-intent detection, guaranteed prevention or production safety-critical actuation.
- Use governed, bounded, verifiable, portable and retrofit-first.
- Do not expose private customer names, credentials, footage, LAN addresses or topology.
