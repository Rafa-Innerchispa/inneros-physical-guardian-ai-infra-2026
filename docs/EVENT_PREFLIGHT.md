# AI Infra Summit Event Preflight

Run this before a judge session and again after binding any on-site sponsor hardware.

```bash
python3 scripts/event_preflight.py
```

The default mode answers one question: **can the core Guardian demo run even if optional providers or hardware are absent?** Core failures exit with code `2`; unavailable optional lanes are warnings and do not invalidate the offline/local fallback.

## Promote a lane only when proving it live

Speechmatics live proof:

```bash
python3 scripts/event_preflight.py --require-speechmatics --require-mic
```

SiMa live proof:

```bash
python3 scripts/event_preflight.py --require-sima
```

Physical action/readback proof while Guardian is already running:

```bash
python3 scripts/event_preflight.py --require-physical-io --require-guardian
```

Multiple gates may be combined for the final judge setup.

## What it checks

- Python 3.11+;
- core Judge application files;
- current Git HEAD for provenance;
- pinned `speechmatics-rt==1.1.1` when Speechmatics is promoted to required;
- presence of `SPEECHMATICS_API_KEY` without printing its value;
- presence of the optional Guardian voice bridge token without printing its value;
- PyAudio availability for live microphone capture;
- SiMa sidecar configuration;
- Physical I/O sidecar configuration;
- local Guardian `/api/health` reachability.

SiMa and Physical I/O endpoints are accepted only when they are loopback HTTP(S) endpoints without embedded credentials, query strings or fragments. The report deliberately hides the configured endpoint address.

## Truth discipline

A `PASS` for the Speechmatics SDK does not prove that a live transcription occurred. A `PASS` for the SiMa sidecar configuration does not prove a real Modalix inference. A `PASS` for Physical I/O configuration does not prove real hardware readback.

Those truth claims still require the actual live run and the evidence labels already enforced by Guardian.

## Expected pre-hardware result

Before the event hardware and laptop microphone are connected, it is normal for the report to show:

- core Python/files/Git: `PASS`;
- Speechmatics/voice token/microphone: `WARN` unless running from the prepared event environment;
- SiMa sidecar: `WARN` until the real DevKit sidecar is bound;
- Physical I/O sidecar: `WARN` until a real local bridge is bound;
- Guardian health: `WARN` when the demo server is not currently running.

The important result in that state is `READY: all required preflight checks passed.`
