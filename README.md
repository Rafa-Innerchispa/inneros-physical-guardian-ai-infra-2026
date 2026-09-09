# InnerOS Physical Guardian — AI Infra Summit 2026

Hackathon-specific repository for the AI Infra Summit Hackathon 2026 submission built on top of the canonical InnerOS Physical Guardian product.

## Team

**InnerOS Physical Guardian**

LabLab team created on September 9, 2026. Join requests are intentionally open so the team can add complementary on-site talent, especially an English-speaking technical presenter and an Edge AI / embedded optimization engineer.

## One-line thesis

**Turn existing security infrastructure into governed Physical AI without replacing the cameras, recorders, or customer network.**

## Current concept

InnerOS Physical Guardian connects to existing DVRs, NVRs, IP cameras and building sensors, then adds a local-first Physical AI layer for perception, temporal behavior analysis, governed actions and forensic evidence.

The permanent product already has reusable building blocks for:

- Dahua / RTSP / ONVIF camera ingestion;
- normalized camera and event contracts;
- detector + tracking + zone transitions;
- temporal anomaly detection;
- event-driven low-cost edge gateways;
- tunnel-only edge deployment for constrained Windows VMS workstations;
- multi-camera / multi-site product direction;
- governed action paths;
- forensic evidence and replay.

For the hackathon, we will **not duplicate the product**. We will build only the sponsor-specific integration, benchmark, demo composition, judge experience and submission evidence needed for the assigned track.

## Real-world validation context

This is not a greenfield simulation-only concept.

- **Home lab, Ecuador:** real Dahua XVR / cameras, local compute and full video-to-event pipeline validation.
- **Bellini pilot direction:** existing Dahua estates, constrained Windows viewing PC, hybrid edge / central inference without requiring a new GPU server at the customer site.
- **Product thesis:** support customers who already own CCTV infrastructure and cannot economically replace it just to adopt AI.

## On-site track preference

1. **SiMa.ai** — strongest alignment with low-power, real-time Physical AI at the camera/building edge.
2. **Qualcomm** — strong fit for model-to-device and portable on-device inference.
3. **Intel Physical AI** — valuable VLA / Physical AI experimentation, but less directly aligned with the current building-security product than the first two.

Speechmatics is considered a complementary bonus layer only if voice materially improves the operator workflow.

## Team recruiting focus

Open to join requests, with preference for teammates who add capabilities we do not already have:

- fluent English technical presenter / pitch lead;
- Edge AI / embedded / on-device optimization engineer;
- computer vision deployment experience;
- demo UX and technical storytelling.

The goal is a small, execution-focused team, not maximum headcount.

## Relationship to the product

Permanent technology lives in:

`Rafa-Innerchispa/inneros-physical-guardian`

This repository exists only for hackathon-specific work: sponsor integrations, challenge adapters, demo composition, benchmarks, evidence and submission assets.

## Pre-kickoff boundary

Before the official build window begins, this repository is limited to planning, architecture, disclosure, team preparation, dependency inventory and reproducibility scaffolding. New sponsor-specific implementation begins only after the official rules/build window permit it.

See:

- `PREEXISTING_DISCLOSURE.md`
- `HACKATHON_SCOPE.md`
- `LABLAB_TEAM_PROFILE.md`
- `docs/PROJECT_BRIEF.md`
- `docs/TRACK_STRATEGY.md`
- `docs/TEAM_RECRUITING.md`
- `docs/DEMO_STORY.md`
- `docs/ENGLISH_PITCH.md`
- `docs/SUBMISSION_DRAFT.md`
- `docs/PREKICKOFF_CHECKLIST.md`
