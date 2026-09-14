# Speechmatics Bonus Integration

Speechmatics is an **optional hackathon adapter**. It adds real-time speech-to-text to the existing Guardian lifecycle without becoming a dependency of the core demo or a substitute for human authorization.

## Current SDK baseline

Verified against the current public Speechmatics/PyPI documentation on September 14, 2026:

- package: `speechmatics-rt`;
- pinned stable version for this hackathon: `1.1.1`;
- Python: 3.9+ upstream, project baseline remains Python 3.11+;
- API key environment variable: `SPEECHMATICS_API_KEY`;
- optional realtime endpoint override supported upstream through `SPEECHMATICS_RT_URL`;
- live microphone example uses 16 kHz PCM S16LE audio and the async realtime client.

The older `speechmatics-python` package is legacy/deprecated. Do not add it to this project.

## Install

Core Guardian remains zero-dependency. Speechmatics is an optional extra:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[speechmatics]'
```

For live microphone capture:

```bash
python -m pip install -e '.[speechmatics-live]'
```

`pyaudio` can require host audio development libraries on some Linux images. If microphone installation is blocked, do not damage the host or replace the demo stack. Keep `speechmatics-rt` installed, use the typed transcript test surface, and finish the microphone dependency on the on-site laptop/known audio environment.

## Secret handling

The owner already has a Speechmatics credential registered server-side under the logical reference:

`owner_vault:speechmatics/api_key`

The raw value must never be copied into this repository, Markdown, CI variables committed to Git, screenshots, coordination messages, or chat.

At runtime, bind the secret to:

```bash
SPEECHMATICS_API_KEY=<server-side secret injection>
```

Optional Guardian bridge truth token:

```bash
GUARDIAN_VOICE_BRIDGE_TOKEN=<ephemeral server-side value>
```

The bridge token is not the Speechmatics API key. It is used only to distinguish an authenticated local live-SDK ingress from a manually typed/browser transcript when truth labels are produced.

## Run

Start Guardian first:

```bash
python3 scripts/run_demo.py
```

Then, in a project environment with microphone support:

```bash
python3 scripts/speechmatics_voice_live.py --language en
```

Default Guardian target is `http://127.0.0.1:8787`. Override only when needed:

```bash
python3 scripts/speechmatics_voice_live.py \
  --guardian-url http://127.0.0.1:8787 \
  --language en
```

The bridge streams microphone audio to Speechmatics and forwards only final transcript text to Guardian. This script does not write raw microphone audio to disk.

## Voice safety matrix

| Voice intent | Allowed | Guardian effect |
| --- | --- | --- |
| Explain trigger / incident | Yes | Read-only explanation |
| Show camera N | Yes | UI/navigation request only |
| Acknowledge incident | Yes | Bounded acknowledgement response |
| Interrupt action | Yes | Enters canonical interrupt → verified safe-state flow |
| Re-verify safe state | Yes | Calls canonical re-verification gate |
| Resume action | Yes, conditionally | Canonical engine refuses unless safe state was re-verified |
| Cancel action | Yes | Safe cancellation |
| Approve / authorize action | **No** | Fail closed |
| Execute action directly | **No** | Fail closed |
| Unlock/open door or gate | **No** | Fail closed |
| Disable alarm/safety | **No** | Fail closed |

Speechmatics is a transcription provider. It is never an authorization provider.

## HTTP surfaces

Readiness:

`GET /api/voice/status`

Bounded transcript ingress:

`POST /api/voice/intent`

Example test body:

```json
{
  "transcript": "interrupt the action",
  "provider": "speechmatics"
}
```

A normal browser/manual request is truth-labelled `CLIENT_REPORTED_TRANSCRIPT`; it is useful for functional testing but is not evidence of a live Speechmatics integration.

## Evidence and privacy

Guardian returns a SHA-256 digest of the normalized transcript for correlation. The voice adapter does not persist raw transcript text into the Evidence Receipt and does not persist raw microphone audio.

Live proof for the Speechmatics bonus must show all of the following in one run:

1. official `speechmatics-rt` client connected with server-side credential;
2. final transcript produced from actual microphone audio;
3. bounded Guardian intent derived from that transcript;
4. forbidden approval/direct execution remains denied;
5. interrupt can move an already authorized action to safe state;
6. resume fails before re-verification;
7. re-verification followed by resume/cancel works;
8. Guardian evidence remains intact and truth-labelled;
9. no API key or raw secret appears in logs or screen capture.

## Failure behavior

If Speechmatics is offline, the key is missing, microphone/PyAudio is unavailable, or authentication fails, the Speechmatics lane fails closed. The primary Guardian judge demo continues using its deterministic/local fallback and the voice panel can still exercise bounded intent parsing using a clearly labelled manual transcript.
