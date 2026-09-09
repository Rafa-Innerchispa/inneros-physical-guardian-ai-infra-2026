# Submission Draft — AI Infra Summit 2026

This file is a pre-kickoff content scaffold only. Final wording must match the assigned track and actual build evidence.

## Project name

InnerOS Physical Guardian

## Short tagline

Turn existing security infrastructure into governed Physical AI.

## Short description

InnerOS Physical Guardian adds local-first perception, temporal behavior analysis, governed actions and forensic evidence to existing cameras, DVRs/NVRs and building sensors without requiring customers to replace their security infrastructure.

## Long description draft

Most buildings already have a large physical-security infrastructure: analog and IP cameras, DVRs/NVRs, access systems and operators. The problem is that this infrastructure is usually passive. It records what happened, but it does not understand behavior or coordinate intelligent action.

InnerOS Physical Guardian is a local-first Physical AI control layer designed to upgrade the infrastructure customers already own. The permanent product connects to existing video systems using standards and provider adapters such as RTSP, ONVIF and Dahua integrations; normalizes camera and device events; performs detection, temporary tracking, zone transitions and temporal anomaly analysis; routes meaningful situations through governed actions; and preserves the evidence behind every decision for operator review and forensic replay.

The project comes from real deployment constraints in Ecuador and Latin America, where replacing an entire CCTV estate simply to gain AI capability is often economically unrealistic. Guardian therefore supports multiple deployment modes: fully local inference, lightweight customer edge gateways with shared central compute, or hybrid topologies depending on latency, privacy and hardware constraints.

For the AI Infra Summit Hackathon, the permanent Guardian product is explicitly treated as pre-existing. The hackathon contribution will focus on adapting and optimizing a real perception workload for the assigned sponsor edge platform, measuring latency/resource performance, connecting the sponsor runtime through a narrow vendor-neutral adapter, composing the judge-facing end-to-end demo and producing reproducible benchmark/evidence artifacts.

The target demonstration begins with existing camera infrastructure, detects a meaningful physical-security behavior over time, produces an explainable event assessment, triggers a bounded operator or physical action, and preserves the complete evidence chain showing what the system saw and did.

The core idea is simple: customers should not need to throw away working cameras to get Physical AI. We are building the intelligence layer that lets existing buildings see, understand, act and prove what happened.

## Key differentiators

- Works with existing camera/DVR/NVR infrastructure.
- Local-first rather than cloud-only.
- Temporal behavior analysis, not only single-frame detection.
- Vendor-neutral permanent product core.
- Multiple deployment tiers from lightweight edge gateway to local GPU.
- Governed actions and auditable evidence.
- Developed from real Latin American deployment constraints.

## Expected hackathon evidence

- sponsor hardware/runtime version;
- exact model/configuration used;
- inference latency;
- end-to-end event latency;
- throughput;
- memory/resource footprint;
- comparison with product baseline where meaningful;
- recorded end-to-end demo;
- sponsor-specific code isolated to hackathon layer;
- pre-existing disclosure and build-window provenance.

## Track-specific section

Fill after assignment.

### Assigned track
TBD

### Sponsor technology materially used
TBD

### What was built during the official hackathon window
TBD

### Benchmark result
TBD

### Demo URL
TBD

### Public repository
`Rafa-Innerchispa/inneros-physical-guardian-ai-infra-2026`
