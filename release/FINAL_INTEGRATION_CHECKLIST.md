# Final Integration Checklist

Status: **PREPARED — BLOCKED ON CODEX A SHA AND `READY_FOR_HARDWARE_VALIDATION`**
Release/QA owner: **CODEX B**
Prepared: **2026-09-15**

This is a release gate, not evidence that the final candidate already passed. Do not merge or promote a candidate while any P0 item below is open.

## Frozen inputs

| Input | Exact ref | State |
| --- | --- | --- |
| Integration baseline | `8358622374dbb9ef62e7d6cf8a805b5aadf51036` | Available; includes the existing SiMa gate, strict E2E suite and launcher history. |
| CODEX A backend/runtime candidate | `<A_SHA_PENDING>` | Wait for a pushed 40-character SHA and the exact verdict `READY_FOR_HARDWARE_VALIDATION`. |
| Judge Console V2 from CODEX C | `1de192a9b396de8a46fe6e49ac34e1e0d508f35b` | Available; changes only `app/app.js`, `app/index.html`, and `app/styles.css` relative to the baseline. |
| CODEX B release docs | `<B_RELEASE_SHA_PENDING>` | This checklist and `release/RELEASE_NOTES.md` only. |

CODEX C's visual acceptance reported PASS at 1920×1080 and laptop widths, fail-closed UI truth gating, webcam/error handling, and Evidence Receipt rendering, with zero visual P0 blockers. That result does not waive backend contract or combined-candidate regression testing.

## Exact integration order

Use a fresh integration worktree. Do not switch branches in A's, B's, or C's worktree, and do not merge `main` from the QA lane.

1. Record the current target SHA and create a rollback label/ref before integration.
2. Verify A's published SHA is a descendant of baseline `8358622374dbb9ef62e7d6cf8a805b5aadf51036`, is present on A's remote branch, and has a clean tree.
3. Run CODEX B's read-only/adversarial QA against **A's exact published SHA**. Stop on `CHANGES_REQUIRED`.
4. Build the integration candidate from **A's exact SHA**. This brings the existing linear SiMa foundation with it; do not cherry-pick only A's tip onto an unrelated target.
5. Apply UI C commit `1de192a9b396de8a46fe6e49ac34e1e0d508f35b` **after A**.
   - A's truth/provenance and API contracts remain authoritative.
   - C's visual structure and truthful presentation remain authoritative for the three `app/*` files.
   - If the three UI files conflict, stop for an explicit integration resolution; never accept a resolution that drops new A response fields or lets the UI infer `REAL`/`MEASURED` locally.
6. Apply B's release-document commit after C. B's commit must contain only:
   - `release/FINAL_INTEGRATION_CHECKLIST.md`
   - `release/RELEASE_NOTES.md`
7. Run the full non-hardware QA matrix on the combined A+C+B candidate and record the exact candidate SHA.
8. Only after non-hardware QA is PASS, hand the exact combined candidate SHA to the hardware validator. Hardware validation must capture fresh frame-linked evidence; an old benchmark file is not live-frame proof.
9. Promote/tag only the exact SHA that passed both QA and hardware validation. Promotion to `main`, if authorized separately, is owned by the integration owner—not CODEX B in this task.

If the target starts at repository `main` (`1bfd6cf3d6a72566cac81a971b133a37598a73cd` when this document was prepared), the existing foundation ancestry is:

`1bfd6cf3` → `ac60f6dd` → `25aa4571` → `e920b42e` → `389c3a70` → `83586223` → `<A_SHA>` → `1de192a9` → `<B_RELEASE_SHA>`

Prefer advancing a temporary integration branch to A's full SHA and then applying C and B. Do not replay or reorder the already-linear foundation commits.

## CODEX B read-only QA gate on A's SHA

Checkout/detach A's exact SHA in an isolated worktree. Do not edit product code, hardware/runtime configuration, or network state.

Record:

- exact A SHA and remote ref;
- `git status --short` before and after (both clean);
- Python and test environment used;
- every test command and exit code;
- no repository, hardware, firmware, runtime, or network mutation.

Required checks:

- `python -m pytest -q`
- focused truth/provenance tests, including all new adversarial tests supplied by A;
- `python scripts/self_test.py`
- `python -m compileall -q src scripts tests`
- `node --check app/app.js`
- `git diff --check`
- safe loopback HTTP smoke only; no hardware-destructive or strict-live command from the QA laptop.

## FINAL QA GATE — execute only on A's new published SHA

Do **not** run this acceptance against `8358622374dbb9ef62e7d6cf8a805b5aadf51036`. Replace the placeholder only after A publishes a different 40-character remote SHA and the exact signal `READY_FOR_HARDWARE_VALIDATION`.

### Exact checkout and identity commands

Run in PowerShell:

```powershell
$aSha = '<NEW_40_CHARACTER_A_SHA>'
$aRemoteRef = 'refs/heads/codex/sima-final-live-console-20260915'
$qaRoot = "C:\WINDOWS\system32\guardian-final-qa-$($aSha.Substring(0, 12))"
$qaPytestDeps = 'C:\Users\hrlg\codex-sima-work\inneros-physical-guardian-ai-infra-2026\.test-deps'

if ($aSha -eq '8358622374dbb9ef62e7d6cf8a805b5aadf51036') { throw 'Refusing final QA on old baseline' }
if ($aSha -notmatch '^[0-9a-f]{40}$') { throw 'A SHA must be exactly 40 lowercase hex characters' }

git fetch origin codex/sima-final-live-console-20260915
$remoteSha = ((git ls-remote origin $aRemoteRef) -split '\s+')[0]
if ($remoteSha -ne $aSha) { throw "Published ref mismatch: expected $aSha, got $remoteSha" }

git cat-file -e "$aSha^{commit}"
git merge-base --is-ancestor 8358622374dbb9ef62e7d6cf8a805b5aadf51036 $aSha
if ($LASTEXITCODE -ne 0) { throw 'A SHA is not a descendant of the frozen baseline' }

git worktree add --detach $qaRoot $aSha
Set-Location $qaRoot
git rev-parse HEAD
git status --short --untracked-files=all
```

The first and last `git status --short --untracked-files=all` outputs must be empty. The detached HEAD must equal `$aSha`.

### Exact non-hardware commands

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPYCACHEPREFIX = "$env:TEMP\guardian-final-qa-$($aSha.Substring(0, 12))-pycache"

python --version
node --version

python -c "import sys; sys.path[:0]=[r'$qaPytestDeps', r'src']; import pytest; raise SystemExit(pytest.main(['--collect-only','-q','-p','no:cacheprovider']))"

python -c "import sys; sys.path[:0]=[r'$qaPytestDeps', r'src']; import pytest; raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','tests/test_sima_adapter.py','tests/test_runtime.py','tests/test_frame_input.py','tests/test_camera_sources.py','tests/test_engine.py','tests/test_server.py','tests/test_physical_io.py','tests/test_sima_live_e2e.py','tests/test_sima_live_evidence_gate.py']))"

python -c "import sys; sys.path[:0]=[r'$qaPytestDeps', r'src']; import pytest; raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','-k','persistent or multiple_frames or invalid_frame or worker_failure or ssh_failure or provenance or low_confidence or confidence_threshold or reject or deny or unknown_physical or missing_physical or oversized or payload_too_large or evidence_receipt or strict_live or fail_closed']))"

python -c "import sys; sys.path[:0]=[r'$qaPytestDeps', r'src']; import pytest; raise SystemExit(pytest.main(['-q','-p','no:cacheprovider']))"

python scripts/self_test.py
python -m compileall -q src scripts tests
node --check app/app.js
git diff --check $aSha^ $aSha
git diff --check
git status --short --untracked-files=all
```

Every command must exit zero. The focused `-k` run must select tests (exit code 5/no tests is `CHANGES_REQUIRED`). `PYTHONDONTWRITEBYTECODE`, `PYTHONPYCACHEPREFIX`, and `-p no:cacheprovider` keep bytecode/cache writes outside the detached checkout.

### Required read-only adversarial checklist

- [ ] **Persistent Modalix worker:** at least three valid frame inferences reuse one established SSH/worker session. Worker/session identity or start counter stays constant; frame/execution IDs remain unique. No per-frame SSH process or PyNeat/model reload is hidden behind a passing response.
- [ ] **Multiple frames, same session:** sequential frames A/B/C produce three responses tied to their own bytes, IDs, timestamps and source while the same healthy Modalix worker remains alive. No detections or provenance leak between frames.
- [ ] **Recovery after invalid frame:** a malformed/undecodable/out-of-bounds frame returns a controlled 4xx error without measured truth or detections; the next valid frame succeeds without restarting the service or inheriting the invalid frame's state.
- [ ] **SSH/worker failure fails closed:** connection refusal, timeout, worker EOF/nonzero exit, malformed worker JSON and unavailable PyNeat/model yield stable unavailable/failed-closed truth. They never emit fixture detections, historical metrics as live, `REAL`, or `MEASURED_SPONSOR_RUNTIME`.
- [ ] **Frame/source provenance:** request and response bind exact `frame_id`, `source_id`, capture timestamp, inference/execution ID, model/runtime/device identity and evidence correlation. Swapped, replayed, missing or stale frame/source evidence is rejected and clears UI overlay eligibility.
- [ ] **Confidence below 0.25:** detections at `0.249999` and lower cannot propose or execute an action. Boundary behavior at `0.25` is explicit and policy-owned; NaN, infinity, strings and values outside `[0,1]` reject the detection/response.
- [ ] **DENY means nothing executed:** rejection returns `REJECTED_SAFE`/not verified/`NOT_EXECUTED`; the PhysicalIO mock records zero action and zero verify calls; later state/evidence cannot relabel the rejected action as approved or verified.
- [ ] **PhysicalIO unknown/missing is never VERIFIED:** missing truth, unknown truth enum, missing verify response, identity mismatch, timeout or `verified:false` ends `ACTION_FAILED_SAFE`/`FAILED_CLOSED` with `verified:false`. Only matching independent readback may verify.
- [ ] **Oversized HTTP body is stable:** a body one byte above the documented frame limit returns a deterministic 4xx response (preferably 413) with bounded JSON, no traceback, no hang and no partial inference/action. A subsequent `/api/health` and valid bounded request still work.
- [ ] **Evidence Receipt provenance:** receipt binds the exact camera/source/frame, capture and inference timestamps, execution ID, Modalix/MLA device/runtime/model identity, validated detections, policy threshold/reason, human decision, physical action identity, readback truth and evidence seal. It never substitutes historical benchmark provenance for current-frame provenance.
- [ ] **No simulated fallback in strict-live:** fixture sidecar, deterministic scenario, prerecorded inference fixture, static evidence JSON, import fallback and historical benchmark cannot satisfy strict-live. If current Modalix proof is absent, strict-live returns blocked/unverified/failed-closed with no simulated success.

For the HTTP and worker cases, use only loopback mocks/fakes supplied by the test suite. Do not contact or mutate the real DevKit, SSH configuration, network, firmware or Physical I/O hardware from this QA lane.

### Verdict rule

- Report `PASS` only when all commands pass, every checklist item has direct test evidence, the checkout remains clean, and the tested SHA exactly equals A's published SHA.
- Report `CHANGES_REQUIRED` for any failed command, absent/zero-selected required test, ambiguous truth/provenance, dirty checkout, SHA mismatch or missing evidence. Include exact failing node IDs, command output and contract gap; do not patch `src/*`, `app/*` or `scripts/*`.

### Adversarial acceptance requirements

- **Fixture → measured rejection:** fixture, prerecorded fallback, mock sidecar, static evidence JSON, or scenario metadata cannot produce `MEASURED_SPONSOR_RUNTIME`. A measured label must be tied to the current inference response and current frame.
- **Fail closed:** missing SDK/import, unavailable sidecar/worker, timeout, malformed JSON, stale evidence, missing evidence, unknown enum, and incomplete provenance must return unavailable/unverified/failed-closed—not a fixture success.
- **Truth/provenance:** device/runtime/model identity, model hash or immutable identifier, execution/inference ID, timestamps, and evidence source must be internally consistent. Historical benchmark data must be labeled historical and must not certify current live frames.
- **Frame/source binding:** response `frame_id`, source identity, capture/inference timestamps, and request correlation must match the submitted frame. Replayed or mismatched evidence is rejected.
- **Bounding boxes:** every bbox is finite, ordered, in the declared coordinate space, and inside the associated frame dimensions; confidence is finite and within `[0, 1]`; malformed detections reject the response rather than disappearing into a measured success.
- **PhysicalIO verification:** an action reaches verified physical truth only after accepted actuation plus matching independent readback. Mismatched identities, missing verification, unknown truth, timeout, or transport error must end `ACTION_FAILED_SAFE`/`FAILED_CLOSED`.
- **Policy semantics:** a detection below threshold cannot become an approved physical action; high-impact actions remain denied; no voice/UI path can synthesize approval.
- **UI/backend contract:** UI C renders backend truth verbatim, clears overlays on unverified/mismatched frames, and never promotes camera-preview availability into SiMa runtime truth.

Any failure above is `CHANGES_REQUIRED`, even if the broad suite is green.

## Existing QA that must remain green

The repository already contains these relevant checks; their presence is not a substitute for rerunning them on the final SHA:

- `docs/QA_REPORT.md`: historical zero-dependency acceptance, approval/rejection safety, auth and HTTP smoke.
- `tests/test_engine.py`: bounded approval, evidence, safe rejection and dangerous-action denial.
- `tests/test_runtime.py`: fixture truth labels, unbenchmarked slots, loopback-only runtime bridge.
- `tests/test_judge_rehearsal.py`: strict rejection of simulated sponsor inference and simulated Physical I/O.
- `tests/test_sima_live_evidence_gate.py`: schema, measured flag, sample/metric, confidence and missing-file validation.
- `tests/test_sima_live_e2e.py`: strict rehearsal plumbing. Its fixture/mock composition is test scaffolding only and **must not** be accepted as proof of a current measured Modalix frame.
- `tests/test_physical_io.py`: loopback restriction, mapping/idempotency, action→verify readback and fail-closed behavior.
- `tests/test_interruptible_lifecycle.py`: interrupt, safe-state re-verification, resume/cancel boundaries.
- `tests/test_server.py` and `tests/test_judge_lifecycle_ui.py`: HTTP/auth and judge lifecycle UI contracts.
- `tests/test_event_preflight.py`, `tests/test_sima_onsite.py`, and `tests/test_judge_live_launcher.py`: preflight, evidence capture and launcher lifecycle.

## P0 demo gate

- [ ] A publishes a remote 40-character SHA and says `READY_FOR_HARDWARE_VALIDATION`.
- [ ] B reports PASS on A's exact SHA; no unresolved `CHANGES_REQUIRED` finding exists.
- [ ] A SHA is based on `8358622374dbb9ef62e7d6cf8a805b5aadf51036` and contains no accidental unrelated files or secrets.
- [ ] Fixture/mock/prerecorded input cannot be promoted to measured current-frame truth.
- [ ] Missing/unavailable SiMa runtime fails closed with no detections presented as real.
- [ ] Current-frame source/provenance, bbox/confidence and timestamp validation pass adversarial tests.
- [ ] Physical I/O actuation requires matching verified readback; unknown truth is rejected.
- [ ] UI C is integrated after A and combined API/DOM/static regression passes.
- [ ] Camera preview and SiMa inference truth are visibly separate.
- [ ] Approval, deny, interrupt, reverify, resume and cancel states remain safe and judge-readable.
- [ ] Evidence Receipt binds camera/source/frame, inference, policy, approval, physical action and readback.
- [ ] Strict hardware rehearsal passes on the exact combined candidate with fresh evidence.
- [ ] Presenter uses only truth claims supported by the live gate; fallback is explicitly simulated/unverified.
- [ ] Rollback path and offline fallback are rehearsed before the judge session.

## Cosmetic items that do not block release

These may be deferred only when truth labels, controls and evidence remain readable:

- minor spacing/alignment differences outside the primary 1920×1080 and laptop layouts;
- operating-system font rendering and scrollbar appearance;
- small color/gradient, shadow, border-radius or icon refinements;
- nonessential transition/animation timing;
- punctuation, capitalization and copy polish that does not alter a truth or safety claim;
- optional decorative charts, background texture or extra telemetry visualization;
- cosmetic wrapping in the collapsed raw-JSON view when the structured Evidence Receipt is intact.

Not cosmetic: hidden/truncated truth badges, inaccessible approval/deny controls, overlay/frame mismatch, unreadable evidence, false measured/live claims, broken responsive layout in the accepted demo sizes, or any safety-state ambiguity.

## Rollback

1. Preserve the pre-integration target SHA and every candidate SHA; never force-push or rewrite A/C branches.
2. Before promotion, rollback means abandoning the temporary integration worktree/branch and returning the launcher to the recorded known-good ref. Do not reset another agent's worktree.
3. If C causes a combined regression, remove/revert C from the temporary candidate and run A's UI with truthful labels while the conflict is resolved. Do not weaken backend validation to accommodate UI assumptions.
4. If A fails non-hardware QA, do not start hardware validation as a release claim. Use baseline/offline demo mode only, explicitly labeled `SIMULATED_FIXTURE` / `SPONSOR_RUNTIME_UNVERIFIED`.
5. If live SiMa fails on site, fall back in the order documented in `docs/JUDGE_DEMO_RUNBOOK.md`; never reuse historical metrics as current telemetry.
6. If Physical I/O readback fails, leave the action in `FAILED_CLOSED` and use safe simulated reference I/O or no actuation. Never bypass verification.
7. If a promoted commit must be undone, use auditable revert commits in reverse integration order (B docs if necessary, then C, then A) and rerun the same gates. Do not use `git reset --hard`, destructive cleanup or force push.

## Sign-off record

| Gate | Exact SHA | Verdict | Owner/evidence |
| --- | --- | --- | --- |
| A published candidate |  |  |  |
| B adversarial read-only QA on A |  |  |  |
| A+C+B combined non-hardware QA |  |  |  |
| Hardware validation |  |  |  |
| Final promoted/tagged candidate |  |  |  |
