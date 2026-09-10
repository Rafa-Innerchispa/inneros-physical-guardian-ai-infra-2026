# Final Status — Core Judge Application

**Status: CORE DEMO MERGED / ZERO-DEPENDENCY ACCEPTANCE PASS**

The live hackathon judge application was merged to `main` in PR #4 at commit `cef7d6737a36ecddea43974e0bf6f4f8da724c76`.

The current application includes the responsive one-screen WebUI, HTTP/API server, deterministic offline fallback, human approval and safe rejection paths, bounded action policy, verification/evidence flow, sponsor-neutral runtime bridges, optional hosted authentication, container deployment and judge/submission documentation.

A clean host without global `pytest` can validate the critical path with:

```bash
python3 scripts/self_test.py
```

The zero-dependency acceptance check passes end to end.

## Intentionally pending

Only work that depends on facts or hardware not yet available is left open:

1. exact official track allocation;
2. sponsor SDK-specific sidecar implementation for the assigned hardware;
3. exact model conversion/optimization for that runtime;
4. repeatable real sponsor-hardware benchmark numbers;
5. final LabLab form fields / demo URL after deployment choice is locked.

None of those require redesigning the Guardian judge WebUI or control/evidence chain.
