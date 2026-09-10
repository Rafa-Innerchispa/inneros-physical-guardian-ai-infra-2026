# Judge Demo Runbook

## One-command start

```bash
python3 scripts/run_demo.py
```

Open `http://127.0.0.1:8787`.

## 90-second demo path

1. **Problem, 10s** — “Buildings already have cameras. The expensive mistake is replacing all of them just to add AI.”
2. **Run scenario, 15s** — Select *After-hours loitering* and click **Run live decision**.
3. **Explain the chain, 25s** — Point at SEE → UNDERSTAND → DECIDE. Emphasize temporal context and policy, not merely object detection.
4. **Governance, 15s** — Show that ACT is blocked on explicit human approval. Mention that door unlock and other high-impact actions are denied in this demo.
5. **Approve, 10s** — Click **Approve bounded action**. VERIFY and PROVE complete.
6. **Evidence, 10s** — Show the evidence ID, truth labels and measured composition timing.
7. **Hardware portability, 5s** — Point at SiMa.ai / Qualcomm / Intel runtime slots. The same Guardian loop survives a runtime swap.

## Strong English closer

> Physical Guardian is the control plane between perception and physical action. The inference hardware can change. The policy, verification and evidence chain stays intact.

## Keyboard shortcuts

- `R`: run selected scenario;
- `A`: approve when an action is awaiting approval;
- `X`: reset for the next judge.

## Fallback order

1. assigned sponsor hardware + local sidecar + safe reference actuator;
2. assigned sponsor hardware + local fixture input;
3. local deterministic runtime + safe reference actuator;
4. fully offline deterministic judge demo.

The final fallback is intentionally complete. A dead WAN link must not destroy the presentation.

## Do not claim

- sponsor hardware performance before measured runs exist;
- customer camera footage as part of the hackathon demo unless explicit permission and sanitization are in place;
- official AMD/SiMa/Qualcomm/Intel endorsement;
- automatic high-impact access-control actions;
- simulated timings as inference benchmark results.

## Presenter handoff

A teammate can take the pitch without learning the full codebase. The screen itself follows the story in order. The technical lead should remain available for questions about runtime integration, policy boundaries, evidence provenance and existing product architecture.
