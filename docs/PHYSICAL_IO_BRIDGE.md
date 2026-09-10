# Permanent Product Physical I/O Bridge

## Purpose

The hackathon judge app can now cross from its challenge-specific composition into the permanent InnerOS Physical Guardian Physical I/O contract without copying the permanent product into this repository.

The boundary is deliberately small:

```text
judge WebUI
  -> Guardian hackathon policy + human approval
  -> GUARDIAN_PHYSICAL_IO_URL (loopback only)
  -> POST /v1/action
  -> permanent Physical Guardian I/O endpoint
  -> POST /v1/verify
  -> readback
  -> truth-labeled hackathon evidence
```

The permanent implementation and its reusable `HttpPhysicalIOAdapter` remain in:

`Rafa-Innerchispa/inneros-physical-guardian`

This repository owns only the hackathon-side adapter/composition.

## Configuration

No configuration is required for the mandatory offline judge fallback.

To enable the permanent-product HTTP path on the same trusted host or network namespace:

```bash
export GUARDIAN_PHYSICAL_IO_URL=http://127.0.0.1:8765
python3 scripts/run_demo.py
```

Only `localhost`, `127.0.0.1`, and `::1` are accepted. Userinfo, query strings, fragments, and non-HTTP(S) schemes are rejected. The configured URL is never returned in the judge catalog or evidence.

## Action mapping

The judge app keeps policy-oriented action names. The bridge maps only two low-impact actions into the permanent contract:

| Judge action | Permanent action | Logical permanent target |
| --- | --- | --- |
| `beacon_warning` | `beacon.set` | `demo-beacon` |
| `dmx_attention` | `light.set` | `demo-light` |

`notify_operator` remains a local software notification in the current demo. High-impact actions such as door unlock, alarm disable, arbitrary shell execution, and gate opening remain denied before the bridge is reached.

The model/event cannot select a URL, permanent action name, or permanent target. Those mappings are code/configuration owned by the operator.

## Truth labels

Physical I/O evidence uses explicit truth states:

- `SIMULATED_REFERENCE_IO`: no permanent bridge was configured; offline fallback only.
- `PRODUCT_HTTP_READBACK`: `/v1/action` was accepted and `/v1/verify` returned verified, but no claim is made about GPIO/electronics.
- `REAL_LOW_VOLTAGE_HARDWARE`: accepted only when the reviewed local endpoint explicitly returns this truth after real hardware readback.
- `FAILED_CLOSED`: a configured mapped action failed transport, identity validation, acceptance, or readback verification.

A configured bridge never silently falls back to a simulated success for a mapped action. If the bridge is present but cannot verify the output, the trace ends as `ACTION_FAILED_SAFE` and the failure is sealed in evidence.

## Reference bring-up

For contract-level software testing, use the permanent product's dependency-free reference endpoint:

```bash
# In the permanent product repo
python3 scripts/pi_demo_io_server.py --host 127.0.0.1 --port 8765

# In this hackathon repo
export GUARDIAN_PHYSICAL_IO_URL=http://127.0.0.1:8765
python3 scripts/run_demo.py
```

The permanent reference endpoint is intentionally in-memory and therefore produces `PRODUCT_HTTP_READBACK`, not a real-hardware claim.

## Santa Clara hardware swap

On site, keep the judge application and contract unchanged. Replace only the implementation behind the permanent `/v1/action` and `/v1/verify` endpoint:

1. prove the in-memory loop first;
2. connect a reviewed Raspberry Pi, ESP32, Arduino, or equivalent low-voltage interface;
3. keep the same logical targets and allowlisted actions;
4. execute a visible LED/beacon/isolated relay action;
5. add a physical input/readback when possible;
6. return `REAL_LOW_VOLTAGE_HARDWARE` only after that real readback is verified;
7. capture the resulting evidence bundle in the judge UI.

Do not expose this endpoint publicly and do not use it for mains loads, door unlock, or other high-impact access-control actions during the hackathon demo.

## Validation

`tests/test_physical_io.py` exercises:

- fallback state;
- rejection of non-loopback destinations;
- exact action/target mapping;
- idempotency header propagation;
- real loopback `/v1/action -> /v1/verify` flow;
- evidence endpoint redaction;
- fail-closed readback behavior;
- unmapped software notification fallback.

`scripts/self_test.py` also includes a dependency-free ephemeral loopback contract test so a clean judge laptop can validate the bridge without installing packages.
