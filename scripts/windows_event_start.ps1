param(
    [switch]$WithVoice,
    [string]$Language = "en",
    [switch]$NoBrowser
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    throw "Missing .venv. Run scripts\windows_event_bootstrap.ps1 first."
}
Set-Location $RepoRoot

function Test-GuardianHealth {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/health" -Method Get -TimeoutSec 2
        return ($null -ne $response)
    } catch {
        return $false
    }
}

if (-not $env:GUARDIAN_VOICE_BRIDGE_TOKEN) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    } finally {
        $rng.Dispose()
    }
    $env:GUARDIAN_VOICE_BRIDGE_TOKEN = [Convert]::ToBase64String($bytes)
    Write-Host "Generated an ephemeral Guardian voice bridge token for this PowerShell session."
}

$GuardianProcess = $null
if (Test-GuardianHealth) {
    Write-Host "Guardian is already healthy on http://127.0.0.1:8787"
} else {
    Write-Host "Starting Guardian judge application..."
    $GuardianProcess = Start-Process -FilePath $VenvPython -ArgumentList @("scripts\run_demo.py") -WorkingDirectory $RepoRoot -PassThru
    $Healthy = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-GuardianHealth) {
            $Healthy = $true
            break
        }
        if ($GuardianProcess.HasExited) {
            break
        }
    }
    if (-not $Healthy) {
        throw "Guardian did not become healthy on loopback. Run .venv\Scripts\python.exe scripts\self_test.py for diagnostics."
    }
    Write-Host "Guardian is healthy."
}

Write-Host "Running strict Guardian readiness gate..."
& $VenvPython scripts\event_preflight.py --require-guardian
if ($LASTEXITCODE -ne 0) {
    throw "Guardian readiness gate failed"
}

$VoiceProcess = $null
if ($WithVoice) {
    Write-Host "Running strict Speechmatics + microphone readiness gate..."
    & $VenvPython scripts\event_preflight.py --require-speechmatics --require-mic
    if ($LASTEXITCODE -ne 0) {
        throw "Speechmatics/microphone readiness gate failed. Guardian remains available on loopback."
    }
    if (-not $env:SPEECHMATICS_API_KEY) {
        throw "SPEECHMATICS_API_KEY is not bound in this PowerShell session. Guardian remains available; the secret was not requested or written by this script."
    }

    Write-Host "Starting Speechmatics live voice bridge..."
    $VoiceProcess = Start-Process -FilePath $VenvPython -ArgumentList @(
        "scripts\speechmatics_voice_live.py",
        "--language", $Language
    ) -WorkingDirectory $RepoRoot -PassThru
    Start-Sleep -Seconds 1
    if ($VoiceProcess.HasExited) {
        throw "Speechmatics voice bridge exited during startup. Guardian remains available."
    }
    Write-Host "Speechmatics bridge started."
}

if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:8787"
}

Write-Host ""
Write-Host "INNEROS PHYSICAL GUARDIAN EVENT RUNTIME READY"
Write-Host "Judge UI: http://127.0.0.1:8787"
if ($null -ne $GuardianProcess) {
    Write-Host "Guardian PID: $($GuardianProcess.Id)"
}
if ($null -ne $VoiceProcess) {
    Write-Host "Voice bridge PID: $($VoiceProcess.Id)"
}
Write-Host "Bridge token and Speechmatics API key are never printed by this script."
