# Judge Demo Runbook — SiMa onsite

## Canonical story

**The building already had eyes. We gave it perception, judgment, controlled action, interruption, verification and memory.**

InnerOS Physical Guardian is the control plane between edge perception and physical action. For the onsite track, SiMa.ai supplies the real edge inference path. Guardian keeps policy, human authorization, safe-state handling, verification and forensic evidence vendor-neutral.

## Before a judge arrives

Run the event preflight:

```bash
python3 scripts/event_preflight.py
```

Run the deterministic rehearsal gate:

```bash
python3 scripts/judge_rehearsal.py
```

When the real SiMa sidecar and Physical I/O bridge are connected, run the strict truth gate:

```bash
python3 scripts/judge_rehearsal.py \
  --runtime sima-slot \
  --require-measured-sponsor \
  --require-live-physical
```

**Do not present the full demo as live unless the strict gate passes.** If it fails, use the fallback path and label the simulated components honestly.

Start the judge UI:

```bash
python3 scripts/run_demo.py
```

Open `http://127.0.0.1:8787`.

## 90-second demo path

1. **Problem — 0–8s**
   “Buildings already have cameras. Replacing working CCTV just to add AI is expensive and creates lock-in.”
2. **SEE with SiMa — 8–20s**
   Run the restricted-zone or after-hours scenario. Point out the SiMa runtime truth label. Do not call it measured until it is `MEASURED_SPONSOR_RUNTIME`.
3. **UNDERSTAND + DECIDE — 20–35s**
   Show temporal context, zone reasoning and policy reason codes. Emphasize that this is not single-frame motion detection.
4. **Governed ACT — 35–50s**
   Show the proposed action blocked on explicit human approval. Approve the bounded low-voltage action. Show independent readback in VERIFY.
5. **Interrupt with voice — 50–65s**
   Use Speechmatics for “Explain why this incident triggered” or “Interrupt the action.” Voice may interrupt/explain, but it cannot approve direct physical actuation.
6. **Safe state + re-verification — 65–78s**
   Show that interruption enters a verified safe state. Attempting resume before re-verification must fail closed. Re-verify, then resume or cancel.
7. **PROVE — 78–90s**
   Show evidence ID, lifecycle timeline, truth labels and measured timings. Close with the vendor-neutral control-plane message.

## Strong English closer

> SiMa gives us efficient edge perception. InnerOS Guardian turns that perception into governed physical action with interruption, verification and evidence. The inference hardware can change. The safety and accountability chain stays intact.

## Speechmatics bonus path

Use only commands that strengthen the main SiMa story:

- “Explain why this incident triggered.”
- “Interrupt the action.”
- “Re-verify safe state.”
- “Resume.”
- “Cancel.”

Voice never approves or directly executes a new physical action. Human authorization remains a separate gate.

## Fallback order

1. real SiMa inference + real local Physical I/O readback + live Speechmatics;
2. real SiMa inference + real Physical I/O readback + typed transcript fallback;
3. real SiMa inference + safe simulated reference actuator;
4. local deterministic inference + real safe actuator;
5. fully offline deterministic judge demo.

A dead WAN link, microphone driver or remote Ecuador connection must not destroy the presentation.

## Truth gates

A component may be described as **live/real** only when its evidence supports it:

- SiMa inference: `MEASURED_SPONSOR_RUNTIME`;
- Physical I/O: `PRODUCT_HTTP_READBACK` or `REAL_LOW_VOLTAGE_HARDWARE`;
- Speechmatics live transcript: authenticated bridge provenance, not typed browser input;
- benchmark numbers: source evidence captured and hashed.

Anything else stays explicitly labeled simulated, unverified or client-reported.

## Freeze rule

After the final pre-event hardening merge, do not add product features or redesign the UI. Changes are allowed only for:

- SiMa SDK/sidecar integration required by the actual DevKit;
- Physical I/O bridge/readback required by the actual actuator;
- event-laptop microphone/driver configuration;
- P0 bug fixes discovered during the real onsite bring-up.

Do not merge FieldOps, VoiceOps or permanent-product experiments into this repo during the event.

## Presenter Q&A anchors

- “The permanent Guardian product is pre-existing and disclosed.”
- “The hackathon delta is the sponsor runtime integration, interruptible judge composition, evidence and benchmark layer.”
- “We do not use biometric identity in this demo.”
- “High-impact actions are denied or require explicit policy and approval.”
- “We measure before we claim.”
