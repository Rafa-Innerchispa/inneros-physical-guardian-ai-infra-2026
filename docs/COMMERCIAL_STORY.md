# Commercial Story - InnerOS Physical Guardian

## One-Line Thesis

InnerOS Physical Guardian turns existing cameras and building sensors into governed Physical AI without forcing customers to replace their security infrastructure.

## The Problem

Real buildings already have security infrastructure. They have analog cameras through DVRs, IP cameras through NVRs, access panels, alarms, lights, gates, intercoms, sensors and site-specific low-voltage wiring.

The problem is that most of those systems are passive. They record what happened. They do not understand behavior over time, decide under policy, require human authorization, act safely, verify the physical result or preserve a complete evidence chain.

Replacing the whole estate with proprietary AI cameras is expensive and disruptive. It can also move the customer into a new lock-in cycle where the camera, AI accelerator, software and cloud service are tied together.

## The Buyer

Physical Guardian is built for owners and operators who already have infrastructure:

- residential buildings and gated communities;
- commercial buildings and campuses;
- warehouses and industrial sites;
- security integrators and managed service providers;
- organizations with mixed CCTV generations and limited replacement budgets.

## The Pain

Buyers need better intelligence, but they cannot casually replace every camera or recorder. They need to preserve uptime, avoid exposing private video, keep costs bounded, and prove why a physical action happened.

A security integrator also needs a portable offering. They cannot rebuild the solution every time a site has a different camera vendor, recorder generation or edge compute option.

## The Solution

Physical Guardian is a retrofit-first Physical AI layer.

It keeps the existing camera/sensor estate and adds:

- local or edge perception through a runtime such as SiMa Modalix;
- normalized detections and temporary tracking;
- temporal context across frames, zones or repeated events;
- policy that separates alerting from action;
- human approval before bounded physical effects;
- interruption and safe-state handling;
- independent verification/readback;
- Evidence Receipts for audit and replay.

## Why Retrofit Beats Rip-And-Replace

Retrofit preserves working infrastructure. It lowers replacement capital expense, reduces disruption and lets customers upgrade intelligence independently from camera hardware.

It also lets the inference hardware evolve. Today the edge runtime may be SiMa Modalix. Tomorrow it could be another accelerator. Guardian remains above that layer and keeps the safety and accountability chain stable.

## Local-First And Privacy

Physical Guardian is local-first. The system can process perception near the building and keep sensitive video out of a mandatory cloud-video pipeline. Hybrid management or reporting can be added where appropriate, but the safety model does not depend on pushing raw building video to the cloud.

The public repository must not expose private customer names, footage, credentials, LAN addresses or topology.

## Deployment Models

### Site Edge

A local Guardian node runs at the building, connects to existing camera/sensor sources, uses an onsite perception runtime and controls only mapped, bounded outputs.

### Shared Local Compute

One local compute node serves multiple camera feeds or zones, keeping video inside the site network while centralizing policy and evidence.

### Hybrid

Local perception and action control stay onsite. Remote dashboards, reporting or managed-service supervision can be added through controlled, outbound-style connectivity.

## Differentiators

- Retrofit-first: no forced camera replacement.
- Vendor-neutral control plane: perception hardware can change.
- Governed actions: perception never directly controls physical outputs.
- Human approval boundary: high-impact action cannot be hidden inside a model result.
- Fail-closed truth: missing proof becomes `BLOCKED` or `UNVERIFIED`, not marketing success.
- Evidence Receipts: source, inference, policy, approval, action and verification stay inspectable.
- Practical origin: built from real building-security constraints in Ecuador and Latin America.

## Value And Outcomes

Physical Guardian can help customers:

- preserve existing camera investment;
- avoid large rip-and-replace projects;
- reduce cloud-video dependence and bandwidth pressure;
- add edge perception where it makes sense;
- create consistent policy across mixed camera estates;
- give operators explainable action proposals;
- prove what happened after an incident;
- create a recurring service path per site, camera group or managed deployment.

This repository does not invent pricing, TAM or customer results. It explains the product wedge and the measured technical proof available today.

## Integrator Wedge

For a security integrator, the wedge is simple:

> Keep the cameras. Add a local Guardian layer. Start with one bounded use case. Expand by zone, building or customer site.

A first deployment can focus on operator escalation, after-hours monitoring, restricted-zone activity, unattended object review or a bounded beacon/notification action. The integrator can later add more camera feeds, more policy rules and more verified output devices without replacing the whole CCTV estate.

## Objection Handling

### Why not buy AI cameras?

AI cameras can be useful, but they tie intelligence to camera replacement. Guardian separates the camera lifecycle from the AI compute lifecycle.

### Is this just video analytics?

No. Video analytics usually stops at detection or alerting. Guardian adds temporal context, policy, approval, bounded physical action, readback verification and evidence.

### Is the system autonomous?

No high-impact physical action is autonomous in this demo. Guardian is governed and human-approved. It is built around bounded actions and fail-closed behavior.

### What if the model is wrong?

A detection is one input, not a verdict. Policy, human approval, action limits and evidence review are part of the safety model.

### Does the customer lose privacy?

The architecture is local-first and can avoid mandatory cloud video. Deployment must still follow customer policy and local law.

### Can it work with old cameras?

That is the point. Existing cameras and recorders can be treated as sources, while perception and policy are added above them.

## Elevator Pitches

### Buyer

> We do not sell another camera. We add intelligence and accountability to the cameras you already own.

### Judge

> SiMa gives the building efficient edge perception. InnerOS Guardian turns that perception into governed physical action with interruption, verification and evidence. The inference hardware can change. The safety and accountability chain stays intact.

### Integrator

> Physical Guardian lets you offer AI upgrades to existing CCTV customers without ripping out the estate. Start with one site, one safe action and one auditable evidence loop.

### Closing

> We did not build another smart camera. We built a Physical AI layer that can make existing buildings intelligent.
