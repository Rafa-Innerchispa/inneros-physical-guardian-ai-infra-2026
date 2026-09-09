# On-Site Hardware Playbook — AI Infra Summit 2026

Status: **pre-kickoff planning only**. Exact implementation begins after the official build window opens and the assigned track/hardware is confirmed.

## Goal

Use the hardware available in Santa Clara to prove that InnerOS Physical Guardian is a **closed-loop Physical AI system**, not merely another camera dashboard.

Target proof:

`existing camera/sensor -> edge accelerator -> temporal Guardian policy -> bounded physical action -> verification -> forensic evidence`

The permanent product already owns the provider-neutral `EdgeRuntimeAdapter`, `PhysicalIOAdapter` and action guardrails. The hackathon contribution is the assigned hardware/runtime adapter, optimization, benchmark, demo composition and evidence.

## What should stay constant across every track

Regardless of sponsor hardware:

1. camera/event contracts remain vendor-neutral;
2. perception output is normalized before Guardian policy sees it;
3. the model never directly controls a door/relay/robot;
4. policy produces an explicit bounded action;
5. physical output uses a `PhysicalIOAdapter`;
6. action execution is allowlisted, idempotent and time-bounded;
7. verification/readback is shown when possible;
8. the evidence timeline records sensor -> inference -> policy -> action -> verification;
9. sponsor SDK objects do not leak into permanent product contracts.

## Demo that works with almost any sponsor hardware

### Scenario: restricted-zone escalation

- A live/staged camera observes a person entering a configured demo zone.
- The assigned accelerator runs the selected detector/perception workload.
- Guardian tracking + temporal rules establish that the event is meaningful rather than a single-frame trigger.
- Policy produces a bounded action, for example `beacon.set` or `relay.pulse`.
- A low-voltage LED/beacon/relay or other safe actuator changes state.
- A GPIO/readback/API acknowledgment verifies the result.
- The judge UI shows latency, runtime/device, event evidence, policy decision, action status and verification.

The physical endpoint can be swapped without changing the story.

## Provisional track plans

### Plan A — SiMa.ai preferred

Strongest product fit: real-time vision at the building/camera edge.

Hackathon work if assigned:

1. inspect the provided MLSoC/devkit and supported model path;
2. choose the smallest useful Guardian perception workload that can be converted reliably;
3. implement a challenge-side `EdgeRuntimeAdapter`;
4. benchmark latency, throughput, memory and power telemetry exposed by the platform;
5. feed normalized detections/events back into Guardian tracking/zones/policy;
6. execute and verify a physical action;
7. compare measured sponsor-hardware performance with the pre-existing baseline.

Do not spend the hackathon porting the entire InnerOS stack onto the board. The board should accelerate the part it is good at.

### Plan B — Qualcomm

Strong fit: model-to-device / on-device inference plus a natural path to embedded physical I/O.

Hackathon work if assigned:

1. inspect the exact Snapdragon/Genie/QNN and companion-board workflow provided on-site;
2. run or convert the selected perception model through the supported deployment path;
3. implement the challenge-side runtime adapter;
4. use a companion microcontroller/board for a visible bounded action when useful;
5. show local inference -> Guardian policy -> physical action -> verification;
6. capture end-to-end latency rather than only model-kernel latency.

This track can be especially strong if the hardware bundle provides both AI compute and a simple physical-control board.

### Plan C — Intel Physical AI

Use the challenge hardware naturally, but do not rewrite Guardian into a robot-only product.

If the track centers on a robotic arm/VLA workflow:

1. treat the robot/arm as another physical actuator/sensor endpoint;
2. keep Guardian perception/policy/evidence contracts unchanged;
3. use the provided Intel runtime/OpenVINO/VLA stack only where it materially serves the challenge;
4. bind one bounded robot action to a Guardian event or verification step;
5. preserve the larger product story: the same control plane works with buildings, cameras, relays and physical agents.

A robot is a compelling demo endpoint, not the permanent architecture.

## Physical endpoint options

Preferred in order of simplicity/reliability:

1. **low-voltage LED or beacon** — visually obvious and difficult to break;
2. **opto-isolated relay / dry contact** — demonstrates real building integration;
3. **Raspberry Pi GPIO** — familiar, portable and easy to verify with input/readback;
4. **ESP32 / microcontroller over MQTT or HTTP** — tiny physical node;
5. **Home Assistant device** — demonstrates building integration if networking permits;
6. **sponsor-provided Arduino/companion board** — excellent if supplied by the assigned track;
7. **robot/arm/mobile platform** — high visual impact if available and reliable.

No mains/high-current demo wiring. Keep on-site hardware low-voltage and portable.

## Portable demo kit

Bring only what is useful and easy to carry:

- development laptop + chargers;
- Ethernet adapter/cable and USB hub;
- Raspberry Pi if readily available;
- Pi power supply and known-good microSD;
- one ESP32 or similar microcontroller if readily available;
- small breadboard;
- jumper wires;
- a few LEDs + suitable resistors;
- one low-voltage opto-isolated relay module if available;
- push button/reed/contact sensor for verification;
- USB cables, especially USB-C data-capable cables;
- small owned IP camera if convenient, otherwise use staged/owned footage and the available on-site camera path.

Do not make the trip dependent on this kit. Sponsor hardware remains the main on-site target.

## Demo reliability ladder

The demo must survive conference Wi-Fi and ordinary human sabotage by networking equipment.

### Level 1 — fully local

Owned/staged video -> sponsor board -> Guardian -> local LED/relay -> local evidence.

This should be the guaranteed fallback.

### Level 2 — local live camera

Local IP/USB/sponsor camera -> same pipeline -> actuator.

### Level 3 — Ecuador home-lab live source

Remote Dahua/XVR source -> secure outbound/remote path -> on-site runtime -> action/evidence.

This is impressive but must never be the only demo path because conference networks have a long tradition of discovering new ways to ruin live demonstrations.

## Judge-facing metrics

Show only measured values:

- sensor/frame timestamp;
- runtime/device name;
- model/reference;
- inference latency p50/p95 where enough samples exist;
- end-to-end event-to-action latency;
- throughput/FPS;
- memory use;
- power/energy telemetry if the platform exposes it reliably;
- action execution latency;
- verification latency;
- evidence correlation ID.

Never label an estimated number as measured.

## Day-one on-site sequence

As soon as the assigned hardware is physically available:

1. photograph/record exact board/devkit model and software image/version;
2. capture SDK/runtime version and official starter repository/references;
3. run vendor hello-world/sample unchanged;
4. preserve that output as baseline evidence;
5. inspect supported model formats/operators;
6. choose the smallest Guardian model path that gives a working demo quickly;
7. get one real inference result through `EdgeRuntimeAdapter` before optimizing anything;
8. connect one bounded physical output;
9. establish end-to-end evidence;
10. only then optimize and add visual polish.

Working end-to-end first. Heroic optimization of a pipeline that does not yet run is a traditional hackathon method for manufacturing regret.

## Definition of done

The on-site build is successful when a judge can see, in one coherent flow:

1. a physical-world signal;
2. inference materially running on the assigned sponsor hardware;
3. Guardian understanding context over time/policy;
4. a visible bounded physical action;
5. verification of that action;
6. forensic evidence showing exactly what happened;
7. measured sponsor-hardware performance;
8. a clear explanation of what was pre-existing vs built during the hackathon.
