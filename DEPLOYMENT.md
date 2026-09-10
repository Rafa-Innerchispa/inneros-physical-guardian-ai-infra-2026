# Deployment — Judge Demo

The hackathon judge application is intentionally dependency-light. The default path runs on any Python 3.11+ laptop and binds to loopback only.

## Local judge mode

```bash
python3 scripts/run_demo.py
```

Open `http://127.0.0.1:8787`.

The deterministic runtime is always available and is explicitly labeled as a simulated fixture. It does not claim sponsor inference or benchmark results.

## Optional access control

For any network-accessible deployment, configure both variables:

```bash
export GUARDIAN_DEMO_USER="judge"
export GUARDIAN_DEMO_PASSWORD="<set-outside-git>"
python3 scripts/run_demo.py --host 0.0.0.0 --port 8787
```

If only one variable is configured the server refuses to start. Credentials are never logged or stored in this repository.

## Container

Build from the repository root:

```bash
docker build -f infra/Dockerfile -t inneros-physical-guardian:ai-infra-2026 .
docker run --rm -p 127.0.0.1:8787:8080 inneros-physical-guardian:ai-infra-2026
```

For a hosted judge endpoint, inject `GUARDIAN_DEMO_USER` and `GUARDIAN_DEMO_PASSWORD` from the platform secret store. Keep platform-level authentication enabled where practical.

## Sponsor runtime sidecars

The WebUI does not need to know any sponsor SDK. Configure one of the following local-only bridges when the assigned hardware is available:

- `GUARDIAN_SIMA_RUNTIME_URL=http://127.0.0.1:<port>`
- `GUARDIAN_QUALCOMM_RUNTIME_URL=http://127.0.0.1:<port>`
- `GUARDIAN_INTEL_RUNTIME_URL=http://127.0.0.1:<port>`

The application rejects non-loopback sidecar URLs.

Contract harness:

```bash
python3 scripts/mock_sponsor_sidecar.py --port 8890
export GUARDIAN_SIMA_RUNTIME_URL=http://127.0.0.1:8890
python3 scripts/run_demo.py
```

The mock sidecar reports `SIMULATED_SPONSOR_SDK`; it must never be presented as a sponsor benchmark.

## Health

`GET /api/health` remains unauthenticated for local/container readiness probes. UI, state, evidence and action routes honor optional HTTP Basic access control.
