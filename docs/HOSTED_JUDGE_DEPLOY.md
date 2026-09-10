# Hosted Judge Demo Deployment

The same judge application that runs offline can be deployed as a small container for remote review. Keep the local laptop path as the mandatory fallback.

## Security model

Recommended hosted shape:

`HTTPS platform endpoint -> optional platform access control -> Guardian HTTP Basic gate -> judge app`

The application supports:

- `GUARDIAN_DEMO_USER`
- `GUARDIAN_DEMO_PASSWORD`
- platform-provided `PORT`

Do not commit credentials. Inject them from the deployment platform's secret store. If only one Guardian credential variable is present, the server refuses to start.

`/api/health` stays unauthenticated for readiness probes. UI, state, evidence and action routes are protected when Guardian auth is enabled.

## Container

The root `Dockerfile` is the canonical Cloud Build/Cloud Run path. It:

- uses Python 3.12 slim;
- requires no application dependency installation;
- runs as numeric unprivileged UID `65532`;
- respects Cloud Run's `PORT` environment variable;
- exposes `/api/health` as an image health check;
- contains only the application source, WebUI and scripts required at runtime.

Build locally:

```bash
docker build -t guardian-judge .
docker run --rm -p 127.0.0.1:8787:8080 guardian-judge
```

The CI pipeline performs this build and a real container smoke test on every pull request.

## Cloud Run example

Use placeholders here rather than publishing company infrastructure identifiers:

```bash
gcloud builds submit \
  --tag REGION-docker.pkg.dev/PROJECT/REPOSITORY/guardian-ai-infra-2026:COMMIT_SHA

gcloud run deploy guardian-ai-infra-2026 \
  --image REGION-docker.pkg.dev/PROJECT/REPOSITORY/guardian-ai-infra-2026:COMMIT_SHA \
  --region REGION \
  --set-env-vars GUARDIAN_DEMO_USER=judge \
  --set-secrets GUARDIAN_DEMO_PASSWORD=GUARDIAN_DEMO_PASSWORD:latest
```

Whether the Cloud Run service itself allows unauthenticated requests is a deployment decision. If it does, Guardian application authentication must remain enabled and the public endpoint must be HTTPS.

## Post-deploy verification

1. `GET /api/health` returns `ok: true`.
2. Unauthenticated `GET /` returns `401` when Guardian auth is enabled.
3. Valid credentials load the WebUI.
4. Run `After-hours loitering`.
5. Confirm ACT stops on human approval.
6. Approve the bounded action.
7. Confirm VERIFY and PROVE complete and an evidence ID appears.
8. Reset and confirm no previous decision text remains.

## Sponsor hardware

Do not expose sponsor SDK sidecars on the public network. `GUARDIAN_SIMA_RUNTIME_URL`, `GUARDIAN_QUALCOMM_RUNTIME_URL` and `GUARDIAN_INTEL_RUNTIME_URL` intentionally accept loopback targets only.

For a hosted software-only judge review, use the truth-labeled deterministic fallback. For on-site sponsor hardware, run the judge app and sponsor sidecar on the same trusted machine/network namespace.
