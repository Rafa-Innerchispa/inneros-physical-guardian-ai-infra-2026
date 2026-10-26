# Architecture and safety contract

## End-to-end demo

1. The operator creates a synthetic, labeled incident with signals relevant to a physical environment.
2. The Guardian records `OBSERVE` and generates an incident ID and SHA-256 audit entry.
3. The operator selects deterministic reasoning, local Ollama, or Meta Muse Spark. The selected model **only explains** the fixture; the fixed recommended action comes from the scenario and a deterministic policy gate. Provider errors are explicitly labeled and fall back to deterministic analysis.
4. The policy allows only `notify_operator` or `activate_beacon` within the fixture. Attempts to unlock doors, disable alarms, open gates, reboot, execute a shell or modify firewalls are rejected.
5. An operator must approve the same allowed action. The action is rechecked by policy at execution.
6. An in-process virtual actuator writes a separate state value; verification reads that state. Failure produces `failed_safe`, never a silently fabricated successful readback.
7. Every transition is recorded in a SQLite global hash chain. The evidence endpoint returns an incident, relevant audit entries, full-chain validation and explicit disclaimers.

## Boundaries

No customer credentials, RTSP stream endpoints, personal images, facial identification, access control API tokens or production network mutation are present or needed. Future hardware integrations require explicit tenant authorization, scoped read-only first access, a separately reviewed action allowlist, external verification, authenticated API, and evidence of real execution. No such hardware integration is claimed in this demo.

Meta Model API requests are opt-in, use only synthetic observations, and use the official HTTPS endpoint with environment-based bearer authorization. The first live Meta call must be recorded as an event-specific change after credits are confirmed.

## Security limitations

This MVP has no authentication or CSRF controls. It only binds to loopback by default; Docker maps it to loopback. It should not be deployed publicly before access controls, rate limits and storage quotas are added. SHA-256 chaining detects modifications to historical audit rows when checked against previous stored entries, but is **not** independently notarized, resistant to full-database replacement or a production forensic guarantee. The demo does not preserve the virtual actuator state across process restarts; restart can only make verification fail safe.
