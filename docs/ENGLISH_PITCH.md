# English Pitch Practice — InnerOS Physical Guardian

## 20-second version

> InnerOS Physical Guardian turns existing security cameras and DVR/NVR systems into a local-first Physical AI network. Instead of replacing a building’s CCTV infrastructure, we add edge intelligence that can detect behavior, understand events over time, trigger governed actions and preserve forensic evidence.

## 60-second version

> We build security and automation systems in Ecuador, and one problem we see constantly is that buildings already have dozens of cameras, but most of those cameras are passive. Replacing everything with new AI cameras is expensive and often unnecessary. InnerOS Physical Guardian adds a Physical AI layer on top of the infrastructure customers already own. We connect to existing DVRs, NVRs and IP cameras using standard protocols, perform detection, tracking, zone and temporal behavior analysis, and then route meaningful events through governed actions and forensic evidence. Our architecture is local-first and can run on site, on shared edge compute, or in a hybrid model. For this hackathon we want to prove that the same real-world system can use the sponsor’s edge hardware for low-latency Physical AI without locking the customer into a cloud-only platform.

## 3-minute structure

### 1. Problem

> Buildings already have cameras, but they mostly record evidence after something happened.

### 2. Constraint

> Real customers cannot replace sixty-four cameras and two recorders just to adopt AI.

### 3. Solution

> Guardian connects to the infrastructure they already own and adds perception, temporal behavior analysis, governed actions and evidence.

### 4. Real-world proof

> We already run the permanent product with real Dahua video infrastructure in Ecuador and are designing a low-cost deployment for existing buildings where the customer does not need a local GPU server.

### 5. Hackathon contribution

> During the hackathon we are adapting the perception path to the assigned edge platform, measuring latency and resource use, and connecting that result back into the vendor-neutral Guardian control plane.

### 6. Why it matters

> This creates a migration path from passive CCTV to Physical AI without forcing customers to throw away working infrastructure.

## Technical Q&A phrases

Use these instead of trying to improvise long sentences:

- “The product core is vendor-neutral.”
- “This adapter is specific to the hackathon hardware.”
- “The video source stays compatible with standard RTSP and ONVIF infrastructure.”
- “We use temporary tracking IDs, not biometric identity.”
- “The anomaly engine reasons over time, not only one frame.”
- “The action path is bounded and auditable.”
- “The evidence store preserves what the system saw and what it did.”
- “We measure latency end to end instead of claiming real time without evidence.”
- “The customer can choose local, hybrid, or shared central inference.”
- “We are not replacing the recorder. We are adding intelligence on top of it.”

## Questions a judge is likely to ask

### Why not just buy AI cameras?

> Because many customers already have large CCTV estates. Replacing all of the cameras is expensive, creates vendor lock-in and is often unnecessary. Guardian lets them upgrade intelligence independently from the camera lifecycle.

### Is the video sent to the cloud?

> Not necessarily. Guardian is local-first. The deployment can be fully local, hybrid, or use shared central compute depending on customer constraints.

### What did you build during the hackathon?

> The permanent Guardian product is pre-existing and disclosed. During the hackathon we build the sponsor-specific integration, optimization, benchmark and judge-facing demo layer.

### How is this different from motion detection?

> Motion is only one signal. Guardian tracks objects over time, understands zones and temporal sequences, and can distinguish patterns such as repeated attempts, loitering or restricted-area behavior before escalating.

### What happens if the AI is wrong?

> An alert is a review candidate, not an accusation. Actions are governed by policy, and the evidence behind the event is preserved for operator review and forensic replay.

## Pronunciation / pacing rule

Speak slower than feels natural. Short sentences are better than complicated grammar. A technical answer that is clear in ten words is stronger than a perfect forty-word sentence delivered under stress.
