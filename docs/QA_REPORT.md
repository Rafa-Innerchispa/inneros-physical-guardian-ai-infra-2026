# QA Report — Judge Application

Date: 2026-09-10

## Acceptance environment

Validated on the primary InnerOS development node from the merged hackathon baseline. The host does not have `pytest` installed globally, which was useful for confirming that the application itself and its acceptance test do not depend on third-party packages.

## Zero-dependency acceptance result

Command:

```bash
python3 scripts/self_test.py
```

Result: **PASS**

Covered checks:

- offline deterministic runtime is ready;
- SiMa.ai slot remains explicitly `NOT_BENCHMARKED` until real hardware/SDK integration;
- high-impact door unlock is denied;
- scenario execution stops at explicit human approval;
- fixture inference is labeled `SIMULATED_FIXTURE`;
- approved bounded action reaches `VERIFIED`;
- evidence ID is produced;
- rejected action becomes `REJECTED_SAFE` with no output;
- dangerous action fails closed at approval;
- ephemeral loopback HTTP server starts successfully;
- `/api/health` is healthy;
- single-screen WebUI is served with critical controls;
- HTTP demo flow reaches approval and verification;
- hosted auth leaves health available while protecting the UI;
- valid hosted credentials unlock the UI.

## Previous developer-suite validation

Before PR #4 was merged:

- `python3 -m pytest -q`: **12 PASS**;
- `python3 -m compileall -q src scripts tests`: **PASS**;
- `git diff --check`: **PASS**.

## Publication hygiene

- generated `__pycache__` / `.pyc` files were removed before publication;
- `.gitignore` blocks generated Python bytecode, virtual environments and local `.env` files;
- no customer credentials, camera IP addresses, private topology or private footage are included;
- sponsor benchmark values are not fabricated.

## Remaining on-site QA

The only mandatory QA that cannot be completed before assigned sponsor hardware is available is the exact sponsor SDK/model conversion path and measured hardware benchmark. The judge UI, approval chain, evidence path and offline fallback are independent of that final adapter.
