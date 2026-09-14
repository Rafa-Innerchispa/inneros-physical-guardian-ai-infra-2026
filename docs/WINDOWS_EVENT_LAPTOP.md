# Windows Event Laptop Runbook

This is the intended on-site laptop path for the AI Infra Summit judge demo. It keeps the permanent InnerOS product untouched and runs only the hackathon composition repository.

## 1. Bootstrap once

Open PowerShell in the repository root and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_event_bootstrap.ps1
```

The bootstrap:

- locates Python 3.12 or 3.11;
- creates `.venv` inside this repository;
- upgrades pip only inside that venv;
- installs the pinned `speechmatics-rt==1.1.1` plus PyAudio for live microphone capture;
- runs the event preflight with Speechmatics + microphone promoted to required;
- lists Windows/PyAudio input devices without recording audio;
- never asks for, prints, or writes the Speechmatics API key.

If live audio dependencies must be deferred, use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_event_bootstrap.ps1 -SkipLiveAudio
```

The core Guardian demo still works without the voice bonus.

## 2. Secret binding

The project expects the existing Speechmatics credential to be supplied at runtime as:

`SPEECHMATICS_API_KEY`

Do not put the raw key in Git, `.ps1` files, screenshots, README files, coordination messages, or chat. The current server-side logical reference remains `owner_vault:speechmatics/api_key`.

`windows_event_start.ps1` generates an ephemeral `GUARDIAN_VOICE_BRIDGE_TOKEN` in memory if one is not already present. It does not print the token.

## 3. Start the judge demo

Core demo only:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_event_start.ps1
```

Core + live Speechmatics:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_event_start.ps1 -WithVoice -Language en
```

The start script:

1. starts Guardian on `http://127.0.0.1:8787` if it is not already healthy;
2. runs a strict `--require-guardian` preflight;
3. when `-WithVoice` is requested, runs strict Speechmatics + microphone gates;
4. starts the live Speechmatics bridge only after those gates pass;
5. opens the Judge UI in the default browser unless `-NoBrowser` is supplied.

If voice startup fails, Guardian remains available. Voice is a bonus lane, never a dependency of the core demo.

## 4. Check the microphone before judges arrive

```powershell
.\.venv\Scripts\python.exe .\scripts\audio_devices.py
```

The intended microphone should appear with `[DEFAULT]`. If Windows reports the wrong default, change the default input device in Windows before running the live bridge.

This diagnostic does not record audio.

## 5. Final strict gates

Core judge path:

```powershell
.\.venv\Scripts\python.exe .\scripts\event_preflight.py --require-guardian
```

Speechmatics live lane:

```powershell
.\.venv\Scripts\python.exe .\scripts\event_preflight.py --require-speechmatics --require-mic
```

SiMa after the real Modalix sidecar is connected:

```powershell
.\.venv\Scripts\python.exe .\scripts\event_preflight.py --require-sima
```

Physical action/readback after the real local sidecar is connected:

```powershell
.\.venv\Scripts\python.exe .\scripts\event_preflight.py --require-physical-io --require-guardian
```

## 6. Truth boundary

Passing a software preflight is not evidence of real sponsor inference or real hardware readback.

- SiMa becomes real only after actual Modalix inference is observed.
- Speechmatics becomes live only after actual microphone audio produces a final transcript through the official SDK.
- Physical I/O becomes `REAL_LOW_VOLTAGE_HARDWARE` only after independent hardware readback succeeds.
- Typed voice transcripts and mock sponsor sidecars remain explicitly simulated/client-reported.

This separation must remain visible in the Judge UI and Evidence Receipt.
