# Demo Story — Judge Narrative

## The 30-second setup

A building already has dozens of cameras and DVR/NVR infrastructure. Replacing all of it with proprietary AI cameras would be expensive and disruptive.

InnerOS Physical Guardian connects to what is already there and adds an intelligent Physical AI layer.

## Demo flow

1. **Existing infrastructure**
   - real/staged Dahua or compatible camera source;
   - no replacement of the recorder/camera estate.

2. **Edge / sponsor runtime**
   - sponsor hardware processes or accelerates the selected perception workload;
   - exact latency/resource metrics are visible.

3. **Perception**
   - person/object detection;
   - temporary tracking ID;
   - zone transitions;
   - no biometric identity required.

4. **Behavior over time**
   - example: repeated access attempts, loitering, unusual path, restricted-zone activity or unattended object;
   - emphasize that a single frame is not enough: the system reasons over temporal evidence.

5. **Governed decision**
   - Guardian produces an event/risk assessment;
   - policy decides whether to notify, escalate or trigger a bounded action.

6. **Action**
   - operator alert, lighting/Home Assistant, device actuation or other approved action depending on the assigned track/demo environment.

7. **Proof**
   - show the evidence timeline;
   - show what frames/events the system saw;
   - show the reasoning inputs / policy outcome / action result;
   - allow forensic replay.

## Core lines for the presentation

### Opening

> Buildings already have eyes. The problem is that most of those eyes do not understand what they are seeing.

### Product thesis

> We are not asking customers to replace their cameras. We add Physical AI on top of the infrastructure they already own.

### Local-first angle

> The architecture can run at the site edge, on shared local compute, or in a hybrid topology. The customer is not forced into a cloud-only video pipeline.

### Real-world angle

> This project comes from actual building-security deployments in Ecuador, where customers have mixed camera generations, limited hardware budgets and infrastructure that must keep working during the upgrade.

### Evidence angle

> An alert is not enough. Guardian preserves what the system saw, why it escalated and what action it took.

### Closing

> We did not build another smart camera. We built a way to make existing buildings intelligent.

## Judge proof points

A strong demo should visibly prove:

- real input rather than prerecorded UI theater where possible;
- sponsor hardware is materially used;
- measured latency and resource footprint;
- existing CCTV hardware remains usable;
- temporal behavior beats single-frame classification;
- actions are bounded/auditable;
- evidence is replayable;
- architecture remains portable.

## Avoid

- claiming criminal intent from visual behavior;
- using facial recognition as a requirement;
- hiding a cloud service behind an “edge” label;
- adding unrelated sponsor APIs just for logo count;
- spending demo time explaining every InnerOS subsystem;
- presenting Bellini/customer private footage or topology.
