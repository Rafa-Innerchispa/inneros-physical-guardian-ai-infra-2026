param(
    [int]$DemoPort = 8787,
    [string]$RecoveryEnv = "",
    [string]$SimaRuntimeUrl = "http://127.0.0.1:8890",
    [switch]$StatusOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$StateRoot = Join-Path $env:LOCALAPPDATA "InnerOS\PhysicalGuardian"
$LogRoot = Join-Path $StateRoot "logs"
$StateFile = Join-Path $StateRoot "recovery-state.json"
$DefaultRecoveryEnv = Join-Path $StateRoot "guardian-recovery.env"
$DemoHealthUrl = "http://127.0.0.1:$DemoPort/api/health"
$DemoSystemUrl = "http://127.0.0.1:$DemoPort/api/system/status"
$DemoCameraUrl = "http://127.0.0.1:$DemoPort/api/camera/sources"

New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null

function Test-JsonEndpoint {
    param([Parameter(Mandatory = $true)][string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -ne 200) { return $null }
        return ($response.Content | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

function Import-GuardianEnvFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return @()
    }

    $loaded = @()
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        $parts = $trimmed -split "=", 2
        if ($parts.Count -ne 2) { continue }
        $name = $parts[0].Trim()
        $value = $parts[1]
        if ($name -notmatch '^GUARDIAN_[A-Z0-9_]+$') { continue }
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
        $loaded += $name
    }
    return $loaded
}

function Resolve-PythonCommand {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        return @{ File = $python.Source; Prefix = @() }
    }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        return @{ File = $py.Source; Prefix = @("-3") }
    }
    throw "Python 3 was not found in PATH."
}

function Get-ListeningPortOwner {
    param([int]$Port)
    try {
        return Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
    }
    catch {
        return $null
    }
}

$selectedEnv = if ($RecoveryEnv) { $RecoveryEnv } elseif ($env:PHYSICAL_GUARDIAN_RECOVERY_ENV) { $env:PHYSICAL_GUARDIAN_RECOVERY_ENV } else { $DefaultRecoveryEnv }
$loadedVars = @(Import-GuardianEnvFile -Path $selectedEnv)

# Never trust a stale SiMa runtime variable after a reboot. Only expose a runtime
# to Guardian when its local health endpoint answers right now. This script does
# not start, SSH into, reconfigure, or otherwise touch the Modalix hardware.
$simaHealthUrl = $SimaRuntimeUrl.TrimEnd('/') + "/health"
$simaHealth = Test-JsonEndpoint -Url $simaHealthUrl
$simaOnline = $null -ne $simaHealth
if ($simaOnline) {
    [Environment]::SetEnvironmentVariable("GUARDIAN_SIMA_RUNTIME_URL", $SimaRuntimeUrl.TrimEnd('/'), "Process")
}
else {
    Remove-Item Env:\GUARDIAN_SIMA_RUNTIME_URL -ErrorAction SilentlyContinue
}

$existingDemo = Test-JsonEndpoint -Url $DemoHealthUrl
$listener = Get-ListeningPortOwner -Port $DemoPort
$demoStarted = $false
$demoPid = $null

if (-not $existingDemo -and -not $StatusOnly) {
    if ($listener) {
        throw "Port $DemoPort is already listening but Guardian health is unavailable. Refusing to kill or replace an unknown process."
    }

    $python = Resolve-PythonCommand
    $oldPythonPath = $env:PYTHONPATH
    $srcPath = Join-Path $RepoRoot "src"
    $env:PYTHONPATH = if ($oldPythonPath) { "$srcPath;$oldPythonPath" } else { $srcPath }

    $stdout = Join-Path $LogRoot "guardian-demo.stdout.log"
    $stderr = Join-Path $LogRoot "guardian-demo.stderr.log"
    $args = @($python.Prefix) + @("-m", "guardian_demo.server", "--port", "$DemoPort")
    $proc = Start-Process -FilePath $python.File -ArgumentList $args -WorkingDirectory $RepoRoot -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $demoPid = $proc.Id
    $demoStarted = $true

    $deadline = (Get-Date).AddSeconds(8)
    do {
        Start-Sleep -Milliseconds 250
        $existingDemo = Test-JsonEndpoint -Url $DemoHealthUrl
    } while (-not $existingDemo -and (Get-Date) -lt $deadline)
}

$systemStatus = if ($existingDemo) { Test-JsonEndpoint -Url $DemoSystemUrl } else { $null }
$cameraCatalog = if ($existingDemo) { Test-JsonEndpoint -Url $DemoCameraUrl } else { $null }
$guardianReady = $null -ne $existingDemo

$cameraConfigured = $false
if ($cameraCatalog -and $cameraCatalog.remote) {
    $cameraConfigured = [bool]$cameraCatalog.remote.configured
}

$report = [ordered]@{
    status = if ($guardianReady) { "READY" } else { "BLOCKED" }
    guardian_ready = $guardianReady
    guardian_started_by_recovery = $demoStarted
    guardian_pid = $demoPid
    ui_url = "http://127.0.0.1:$DemoPort/"
    recovery_config_path = $selectedEnv
    recovery_config_present = (Test-Path -LiteralPath $selectedEnv -PathType Leaf)
    loaded_guardian_variables = $loadedVars
    camera_configured = $cameraConfigured
    camera_catalog = $cameraCatalog
    sima_online = $simaOnline
    sima_truth = if ($simaOnline) { "AVAILABLE_FOR_CURRENT_FRAME_VERIFICATION" } else { "OFFLINE_UNVERIFIED" }
    sima_runtime_url_bound = if ($simaOnline) { $SimaRuntimeUrl.TrimEnd('/') } else { $null }
    system_status = $systemStatus
    safety = @{
        starts_sima_hardware = $false
        uses_historical_evidence_as_live = $false
        kills_unknown_processes = $false
        secrets_written_to_repo = $false
    }
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
}

$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $StateFile -Encoding UTF8
$report | ConvertTo-Json -Depth 8

if (-not $guardianReady) { exit 1 }
exit 0
