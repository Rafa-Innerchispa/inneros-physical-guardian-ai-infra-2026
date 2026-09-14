param(
    [switch]$SkipLiveAudio
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Resolve-Python {
    $candidates = @(
        @{ Cmd = "py"; Args = @("-3.12") },
        @{ Cmd = "py"; Args = @("-3.11") },
        @{ Cmd = "python"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        try {
            & $candidate.Cmd @($candidate.Args) -c "import sys; assert sys.version_info >= (3, 11)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }
    throw "Python 3.11+ was not found. Install Python 3.12 x64 and rerun this script."
}

$Python = Resolve-Python
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "[1/6] Creating isolated event virtual environment..."
    & $Python.Cmd @($Python.Args) -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv" }
} else {
    Write-Host "[1/6] Existing .venv found. Reusing it."
}

Write-Host "[2/6] Updating pip inside .venv only..."
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }

if ($SkipLiveAudio) {
    Write-Host "[3/6] Installing Speechmatics SDK without microphone extra..."
    & $VenvPython -m pip install -e ".[speechmatics]"
} else {
    Write-Host "[3/6] Installing Speechmatics SDK + live microphone dependency..."
    & $VenvPython -m pip install -e ".[speechmatics-live]"
}
if ($LASTEXITCODE -ne 0) { throw "Speechmatics dependency installation failed" }

Write-Host "[4/6] Running Guardian event preflight..."
if ($SkipLiveAudio) {
    & $VenvPython scripts\event_preflight.py --require-speechmatics
} else {
    & $VenvPython scripts\event_preflight.py --require-speechmatics --require-mic
}
$PreflightCode = $LASTEXITCODE
if ($PreflightCode -eq 2) {
    throw "Required event preflight checks failed"
}

Write-Host "[5/6] Inspecting Windows microphone/input devices..."
if ($SkipLiveAudio) {
    Write-Host "Live audio was skipped by request."
} else {
    & $VenvPython scripts\audio_devices.py
    $AudioCode = $LASTEXITCODE
    if ($AudioCode -eq 2) {
        throw "No usable microphone/input devices were detected"
    }
    if ($AudioCode -eq 1) {
        Write-Warning "Input devices exist but Windows/PyAudio did not report a default microphone. Set the intended mic as Windows default input before the demo."
    }
}

Write-Host "[6/6] Checking optional SiMa.ai host tooling..."
& $VenvPython scripts\sima_onsite_preflight.py
if ($LASTEXITCODE -ne 0) {
    Write-Warning "SiMa.ai optional preflight returned non-zero. Guardian remains usable offline."
}

Write-Host ""
Write-Host "EVENT LAPTOP BOOTSTRAP READY"
Write-Host "Repository: $RepoRoot"
Write-Host "Virtual environment: .venv"
Write-Host "No API key was requested, displayed, or written by this script."
Write-Host "Next: bind SPEECHMATICS_API_KEY securely in the current environment, then run scripts\windows_event_start.ps1 -WithVoice"
Write-Host "When the Modalix DevKit is connected, run: .venv\Scripts\python.exe scripts\sima_onsite_preflight.py --probe-device --probe-modelzoo"
