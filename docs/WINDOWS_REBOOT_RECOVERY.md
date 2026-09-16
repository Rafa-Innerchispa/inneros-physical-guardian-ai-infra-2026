# Windows reboot recovery — fail-closed judge stack

This recovery path exists for the current operating condition where the SiMa Modalix hardware may be physically disconnected.

## Safety contract

- The recovery script does **not** start, SSH into, reconfigure, reinstall, or otherwise touch the SiMa hardware.
- If the configured local SiMa runtime health endpoint does not answer, `GUARDIAN_SIMA_RUNTIME_URL` is removed from the recovery process environment.
- Historical SiMa evidence is never used to label the current runtime `MEASURED`.
- Guardian may still start so camera-source and policy UI work can continue while SiMa remains `OFFLINE / UNVERIFIED`.
- Unknown processes already listening on the Guardian port are never killed automatically.
- Camera credentials/tokens remain outside the repository.

## Private recovery configuration

By default the script reads:

`%LOCALAPPDATA%\InnerOS\PhysicalGuardian\guardian-recovery.env`

Only variables whose names match `GUARDIAN_[A-Z0-9_]+` are imported into the process. The file is intentionally outside the repository.

Typical non-secret structure:

```text
# Example only. Do not commit real tokens or authenticated camera URLs.
GUARDIAN_CAMERA_SOURCES_JSON=<private JSON value>
GUARDIAN_GYE_BRIDGE_TOKEN=<private value if required by local bridge config>
```

Use the actual environment names expected by the current runtime. Do not copy secrets into this document.

## Run

From PowerShell at the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_reboot_recovery.ps1
```

Status-only check:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows_reboot_recovery.ps1 -StatusOnly
```

The script writes a local diagnostic report to:

`%LOCALAPPDATA%\InnerOS\PhysicalGuardian\recovery-state.json`

and Guardian stdout/stderr logs under the adjacent `logs` directory.

## Expected current result with SiMa physically disconnected

- Guardian server: `READY` if Python/runtime dependencies are intact.
- Camera catalog: reports configured/blocked state from current environment.
- SiMa: `OFFLINE_UNVERIFIED`.
- No current-frame `MEASURED` claim is created.
- Reconnecting SiMa later requires a fresh health response and current-frame proof; reboot recovery itself does not certify live inference.
