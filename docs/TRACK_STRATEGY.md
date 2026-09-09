# Track Strategy — AI Infra Summit 2026

## Ranking

### 1. SiMa.ai — preferred

Strongest fit for the existing product thesis: low-power, real-time Physical AI at the edge using existing camera infrastructure.

Hackathon angle:
- run/optimize the perception path on the assigned SiMa.ai hardware/runtime;
- demonstrate low-latency camera/event processing close to the physical environment;
- compare sponsor-edge execution with the existing central/local baseline;
- preserve the same provider-neutral Guardian contracts so the sponsor integration remains an adapter, not a permanent lock-in.

Best demo story:
**Existing building cameras -> Guardian -> SiMa edge inference -> behavior/anomaly -> governed action -> forensic evidence.**

### 2. Qualcomm Model-to-Device

Strong second choice because the product must eventually run across inexpensive edge hardware without requiring a large GPU at every customer site.

Hackathon angle:
- port a focused perception component to the assigned Snapdragon/Qualcomm device;
- benchmark latency/power/resource footprint;
- show portable edge deployment while the larger reasoning/control plane remains hardware-neutral.

Best demo story:
**A low-cost customer edge device becomes the intelligent bridge between existing CCTV and the Guardian control plane.**

### 3. Intel Physical AI

Technically valuable but less directly aligned with the current building-security product because the on-site brief emphasizes robotics/VLA.

Hackathon angle if assigned:
- reuse Guardian perception/evidence contracts;
- add a bounded physical action/verification loop using the supplied robotic platform;
- position the robot as an actuator in the same Physical Guardian fabric rather than changing the product into a robotics-only submission.

Best demo story:
**Guardian detects a physical condition, reasons through policy, commands a bounded actuator and verifies the result.**

## Speechmatics bonus

Only add Speechmatics if it makes the operator workflow materially better. Good example:

> “Guardian, show me why camera 17 was escalated.”

Voice should query evidence or approve a bounded action. Do not add voice merely to qualify for a bonus.

## Sponsor integration rules

- Sponsor SDK/runtime stays in this hackathon repo unless later generalized.
- Permanent product contracts remain vendor-neutral.
- Record exact runtime, model and hardware versions used for benchmark evidence.
- Do not claim pre-existing Guardian components as hackathon-built.
- Prefer a single excellent sponsor integration over three shallow logos.

## Assignment response

Once LabLab assigns the on-site track, immediately freeze:

1. assigned track;
2. official challenge text/rules;
3. provided hardware/runtime versions;
4. judging criteria;
5. eligible submission requirements;
6. build-window baseline commit;
7. first measurable technical hypothesis.
