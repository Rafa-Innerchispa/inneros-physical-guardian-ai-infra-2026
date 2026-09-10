# 60-Second Quickstart

## Validate first

```bash
python3 scripts/self_test.py
```

Expected final line:

`ALL ACCEPTANCE CHECKS PASSED`

## Start the judge demo

```bash
python3 scripts/run_demo.py
```

Open `http://127.0.0.1:8787`.

1. Keep `InnerOS demo fixture` selected.
2. Choose `After-hours loitering`.
3. Click **Run live decision**.
4. Explain SEE → UNDERSTAND → DECIDE.
5. Point out that ACT is blocked on human approval.
6. Click **Approve bounded action**.
7. Show VERIFY, PROVE, evidence ID and truth labels.

On assigned sponsor hardware, start the official SDK integration as a loopback sidecar and set the matching `GUARDIAN_*_RUNTIME_URL`. No WebUI redesign is required.
