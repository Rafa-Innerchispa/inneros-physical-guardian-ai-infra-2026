# English Pitch Practice — InnerOS Physical Guardian

## 15-second version

> Buildings already have cameras. InnerOS Physical Guardian turns that existing infrastructure into governed Physical AI. SiMa handles efficient edge perception, while Guardian decides what actions are allowed, verifies the physical result, and preserves evidence.

## 30-second version

> InnerOS Physical Guardian upgrades existing CCTV instead of forcing customers to replace it. We use SiMa edge inference to understand what is happening locally, then Guardian applies temporal rules and policy before any physical action. Actions are bounded, interruptible and independently verified, and every step is preserved as evidence. Speechmatics adds voice control, but voice cannot bypass approval or safety gates.

## 60-second version

> We build real security and automation systems in Ecuador, and we constantly see buildings with dozens of perfectly usable cameras that mostly record evidence after something has already happened. Replacing the whole estate with new AI cameras is expensive and creates more vendor lock-in. InnerOS Physical Guardian adds intelligence on top of the infrastructure customers already own. For the SiMa track, the Modalix edge platform becomes our perception engine: it detects what is happening locally and feeds normalized events into Guardian. Guardian then reasons over time, applies policy, proposes a bounded physical action, requires the right authorization, verifies the result through independent readback, and preserves a forensic evidence receipt. The action can also be interrupted, forced into a verified safe state, re-verified, and only then resumed. Speechmatics gives us a natural voice interface for explanation and interruption without allowing voice to bypass the safety model.

## 90-second judge narrative

### 1. Problem

> Buildings already have eyes, but most of those eyes are passive. They record what happened instead of helping the building respond safely while it is happening.

### 2. Retrofit constraint

> Real customers cannot replace sixty-four cameras and multiple recorders every time a better AI accelerator appears.

### 3. SiMa perception

> We keep the camera infrastructure and move perception to SiMa at the edge. The inference adapter normalizes detections so Guardian is not locked to one accelerator.

### 4. Guardian control plane

> Guardian adds the part an object detector does not provide: temporal context, policy, human authority, bounded action, interruption, safe state, readback verification and evidence.

### 5. Live proof

> A person remains in or enters a restricted zone. SiMa produces the edge inference. Guardian explains the reason codes and proposes a safe action. The action cannot execute until authorized. After execution, Guardian independently verifies the physical state.

### 6. Safety proof

> We interrupt the action. Guardian enters a verified safe state. A premature resume is rejected. Only after re-verification can the action resume or be cancelled.

### 7. Voice bonus

> Speechmatics lets the operator ask why the incident triggered, interrupt, re-verify, resume or cancel. Voice never grants a new physical approval.

### 8. Evidence

> The final receipt shows what the system saw, why it decided, who authorized it, what physically happened and how that result was verified.

## Strong closer

> SiMa gives the building perception. InnerOS Guardian gives that perception judgment, controlled action and accountability. The accelerator can change. The safety and evidence chain stays intact.

## What we built for this hackathon

Use this answer exactly when provenance matters:

> The permanent Guardian product existed before the hackathon and is disclosed. For this event we built the sponsor-runtime adapter path, the SiMa onsite integration tooling, the interrupt/reverify/resume judge lifecycle, the evidence and benchmark gates, the judge console, and the bounded Speechmatics voice lane. We keep the hackathon delta separate from the permanent product repository.

## Technical Q&A anchors

- “The permanent product core is vendor-neutral.”
- “SiMa is the assigned onsite edge inference path.”
- “The sponsor adapter is loopback-only and normalizes detections.”
- “We use temporary tracking IDs, not biometric identity.”
- “The anomaly engine reasons over time, not only one frame.”
- “A proposed action is not the same as an authorized action.”
- “Resume is impossible until safe state has been re-verified.”
- “Voice cannot approve a new physical action.”
- “Independent readback is what lets us say the action actually happened.”
- “We measure before we claim.”
- “The customer can keep the cameras and replace the inference hardware independently.”

## Likely judge questions

### Why not just buy AI cameras?

> Because the camera lifecycle and the AI-compute lifecycle should not be the same thing. Many buildings already have large CCTV estates. Guardian lets them upgrade intelligence without replacing working cameras or locking the whole system to one camera vendor.

### What exactly does SiMa do here?

> SiMa provides the edge perception runtime for the onsite demo. It produces the real local inference that Guardian converts into normalized detections and then into temporal reasoning, policy and governed action.

### What exactly does Guardian add beyond YOLO or another detector?

> Detection answers “what is in this frame.” Guardian answers “what has been happening over time, what policy applies, what action is allowed, did it physically happen, and can we prove it.”

### What happens if the AI is wrong?

> A detection is evidence for a decision, not an accusation. The system uses policy, bounded actions and human authority. High-impact actions are denied or require explicit authorization, and the evidence behind the event remains available for review.

### What if somebody says “open the door” by voice?

> The voice layer rejects that. Speechmatics can explain, interrupt, re-verify, resume or cancel within the existing governed lifecycle, but voice cannot create a new approval or bypass physical policy.

### Is the demo actually using SiMa or is SiMa just on the architecture diagram?

If the strict live gate passes:

> The SiMa sidecar is providing the measured inference for this trace. You can see the runtime truth label and the captured evidence source.

If the strict live gate has not passed:

> The Guardian composition is live, but this run is explicitly labeled as a fixture or unverified sponsor runtime. We do not call sponsor inference live until the measured gate passes.

## Pronunciation / pacing

Speak slower than feels natural. Short sentences beat elaborate grammar. When a judge asks a technical question, answer the question first, then add one proof point. Do not turn a twenty-second Q&A slot into a conference keynote because adrenaline has opinions.
