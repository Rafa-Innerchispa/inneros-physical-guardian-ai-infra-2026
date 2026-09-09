# Project Brief — InnerOS Physical Guardian

## Problem

Most buildings already have cameras, DVRs/NVRs, access systems and operators, but their video infrastructure is largely passive. Replacing the entire estate with new AI cameras is expensive, disruptive and often unnecessary.

## Thesis

InnerOS Physical Guardian adds a portable Physical AI control layer on top of existing security infrastructure. The system can ingest real camera streams, track activity over time, detect anomalous behavior, escalate meaningful situations, trigger bounded actions and preserve the evidence behind every decision.

## Why this team can build it

The project comes from real deployment constraints in Ecuador and Latin America rather than a simulation-only environment. The permanent InnerOS product stack already works with real Dahua camera/recorder infrastructure and local compute. We also have an explicit deployment path for resource-constrained customer sites where the customer does not need to buy a large local GPU server.

## Hackathon objective

Use the assigned sponsor hardware/runtime to prove that useful Physical AI can run closer to the physical environment while keeping the architecture portable and compatible with existing CCTV estates.

The hackathon layer should demonstrate:

1. real or staged camera/video ingestion through the permanent Guardian product APIs;
2. sponsor-hardware inference or acceleration;
3. low-latency detection/tracking/anomaly flow;
4. a governed action or operator escalation;
5. forensic evidence showing what the system saw and why it acted;
6. measurable latency, throughput, resource use and deployment trade-offs.

## What is already pre-existing

The following belong to the permanent product and must be disclosed as pre-existing:

- RTSP / ONVIF / Dahua ingestion;
- detector/tracker contracts and baseline implementations;
- zones and temporal anomaly engine;
- low-cost event-driven edge gateway;
- tunnel-only remote edge mode;
- Bellini deployment architecture;
- forensic evidence/replay concepts and integrations;
- governed InnerOS action/policy direction.

The hackathon contribution begins at the sponsor-specific integration, benchmark, demo composition and challenge evidence created during the official build window.

## Real-world commercial angle

The target customer does not need to replace a functioning CCTV system to gain AI capability. A site can keep its current recorders and cameras while adding a small edge gateway, shared central compute or optional on-prem acceleration. That opens a path to recurring Physical Guardian service revenue per site/camera while preserving existing customer infrastructure.

## Success statement

A judge should leave the demo understanding one sentence:

**We did not build another smart camera. We built a Physical AI layer that can make existing buildings intelligent.**
