# Release Notes — Physical Guardian SiMa Judge Candidate

Release state: **CANDIDATE DOCUMENTATION; NOT YET RELEASED**
Prepared: **2026-09-15**

Final release remains blocked until CODEX A publishes a pushed SHA with `READY_FOR_HARDWARE_VALIDATION`, CODEX B completes adversarial read-only QA on that exact SHA, and the combined candidate passes hardware validation.

## Candidate composition

- Existing integration baseline: `8358622374dbb9ef62e7d6cf8a805b5aadf51036`.
- CODEX A backend/runtime/frame-provenance candidate: `<A_SHA_PENDING>`.
- Judge Console V2 UI from CODEX C: `1de192a9b396de8a46fe6e49ac34e1e0d508f35b`.
- CODEX B release package: `<B_RELEASE_SHA_PENDING>`; limited to the two files under `release/`.

The existing linear SiMa foundation incorporated by the baseline is:

- `ac60f6dd58300ea795dce16636ecd02b9419f996` — initial Modalix adapter, benchmark evidence and sidecar;
- `25aa457109ca582686e7dc2c4f2d1e385370d63c` — deterministic live-evidence gate and judge contract;
- `e920b42e3d0f5463854039e016cf3a2fae937123` — strict evidence gate CLI, contract docs and tests;
- `389c3a70c2a28498b48051cb06c6b76a1ff02f61` — strict live E2E rehearsal suite;
- `8358622374dbb9ef62e7d6cf8a805b5aadf51036` — hardened judge launcher and scoped recovery/cleanup.

## What the candidate is intended to deliver

- Real per-frame SiMa Modalix/MLA inference behind a fail-closed local boundary.
- Explicit runtime, model, device, frame and source provenance without fixture-to-measured promotion.
- Validated detections whose bbox/confidence data is bound to the submitted frame.
- Guardian policy and explicit human approval before bounded physical action.
- Physical action truth based on independent readback, with unknown or failed verification rejected.
- Judge Console V2 with separate camera-preview and inference-truth surfaces, backend-driven overlays, health strip, guided pipeline and structured Evidence Receipt.
- Honest fallback states: historical benchmark, simulated fixture, prerecorded local source and unavailable runtime remain distinct from current live measured inference.

These are release requirements, not completed claims, until the final sign-off table in `release/FINAL_INTEGRATION_CHECKLIST.md` is filled.

## Existing QA evidence

### Historical repository acceptance

`docs/QA_REPORT.md` records the earlier zero-dependency judge-app acceptance: `scripts/self_test.py` PASS, safe approval/rejection behavior, evidence creation, HTTP health/UI flow and hosted-auth checks. It also records an earlier 12-test pytest run, compileall PASS and diff hygiene PASS. Those results predate the final A and C candidates and are retained as regression history only.

### Current baseline test assets

The baseline contains broad regression and safety coverage for:

- engine policy, dangerous-action denial and evidence;
- runtime truth labels and loopback-only sidecar boundaries;
- strict rehearsal rejection of simulated sponsor/physical truth;
- SiMa evidence schema and metric validation;
- Physical I/O action→verify identity/readback and fail-closed behavior;
- interrupt→safe state→reverify→resume/cancel lifecycle;
- HTTP/auth/UI contracts, preflight, onsite evidence and launcher lifecycle.

The baseline's mock/fixture strict-E2E plumbing is not sponsor-hardware proof. Final acceptance specifically requires A's implementation to reject any attempt to use fixtures, mocks, static historical evidence or prerecorded input as certification of a current measured frame.

### Judge Console V2 acceptance

The UI candidate at `1de192a9b396de8a46fe6e49ac34e1e0d508f35b` received visual acceptance PASS with:

- single-screen 1920×1080 presentation and responsive laptop layout;
- webcam permission and fallback handling;
- separation of local camera preview from backend inference truth;
- cleared overlays and `UNVERIFIED`/`BLOCKED` state when backend proof is absent;
- structured Evidence Receipt and collapsible/raw evidence presentation;
- zero visual P0 blockers reported.

Combined A+C contract testing is still mandatory because C changes the same three `app/*` files that A may have evolved during backend/UI integration.

## Existing demo, pitch and disclosure material

Use the existing documents; do not fork the story during release hardening:

- `docs/ENGLISH_PITCH.md` — 15/30/60/90-second pitch, judge Q&A, truth-aware SiMa answers and provenance wording.
- `docs/DEMO_STORY.md` — existing-infrastructure narrative and governed Physical AI flow.
- `docs/JUDGE_DEMO_RUNBOOK.md` — 90-second path, strict truth gate, fallback order and freeze rule.
- `docs/SUBMISSION_FINAL_DRAFT.md` — submission copy and explicit hold on hardware numbers until measured onsite.
- `docs/PROJECT_BRIEF.md` — product thesis and judge takeaway.
- `docs/SIMA_LIVE_EVIDENCE_CONTRACT.md` — evidence schema and truth hierarchy; final implementation may strengthen this contract.
- `docs/PHYSICAL_IO_BRIDGE.md` — bounded action mapping and readback truth states.
- `docs/EVENT_PREFLIGHT.md` and `docs/ONSITE_HARDWARE_PLAYBOOK.md` — preflight, hardware sequence and fallback discipline.
- `PREEXISTING_DISCLOSURE.md`, `BASELINE_PROVENANCE.json` and `HACKATHON_SCOPE.md` — permanent-product versus hackathon-delta boundary.

Pitch discipline for the final demo:

- Say **measured/live SiMa inference** only when the current-frame strict gate passes.
- Describe stored performance evidence as **historical benchmark**, never live telemetry.
- A live camera preview alone proves only camera availability.
- `PRODUCT_HTTP_READBACK` proves the local HTTP action/readback contract; claim `REAL_LOW_VOLTAGE_HARDWARE` only after actual physical readback.
- If a gate fails, use the prepared fallback and name its simulated/unverified truth plainly.

## P0 release blockers

- Missing A remote SHA or missing `READY_FOR_HARDWARE_VALIDATION` declaration.
- Any fixture/mock/prerecorded/static-evidence path reaching current `MEASURED_SPONSOR_RUNTIME`.
- Runtime/SDK/import/transport failure silently returning detections or measured truth.
- Stale, missing or mismatched frame/source/provenance accepted as current evidence.
- Invalid/out-of-frame bbox, invalid confidence or mismatched frame dimensions accepted.
- Physical action shown as verified without matching independent readback.
- UI deriving live/measured state locally or drawing detections for a different/unverified frame.
- Approval, deny, interrupt, safe-state, reverify, resume or cancel regression.
- Secrets, private topology/footage or unsafe external endpoint exposure.
- Failure of full non-hardware QA or final exact-SHA hardware validation.

## Non-blocking cosmetic backlog

Provided truth, evidence and controls stay readable, the following do not block the demo:

- minor pixel alignment, spacing and system-font differences;
- scrollbar, shadow, radius, gradient and icon polish;
- nonessential motion/transition tuning;
- decorative telemetry charts or background treatments;
- copy capitalization/punctuation that does not change a claim;
- cosmetic raw-JSON wrapping outside the primary structured receipt.

## Known release constraints

- The final A SHA and final combined SHA are not known at preparation time.
- Real Modalix current-frame proof and real low-voltage hardware proof require the hardware-validation lane.
- Optional WAN-dependent or microphone/voice enhancements must not be allowed to destabilize the core local demo.
- No code fix, branch merge to `main`, hardware mutation or network mutation is part of CODEX B's release-document preparation.

## Rollback summary

Keep the pre-integration SHA and every candidate SHA immutable. If A fails, remain on the truthful offline/baseline path. If C introduces a combined regression, revert/remove C from the temporary candidate without weakening A's truth contract. If live SiMa or Physical I/O fails onsite, fall back to explicitly simulated/unverified modes. Any post-promotion rollback uses auditable revert commits in reverse integration order; no force push or destructive reset.

See `release/FINAL_INTEGRATION_CHECKLIST.md` for the exact integration, QA and sign-off sequence.
