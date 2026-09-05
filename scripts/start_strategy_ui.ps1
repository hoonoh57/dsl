param(
    [ValidateSet('Start', 'Stop')]
    [string]$Action = 'Start',
    [string]$ChartRepo = '..\cascade-chart-validation-20260904',
    [string]$KiwoomEnvDir = '..\kiwoom-auto',
    [string]$BindHost = '127.0.0.1',
    [int]$DslPort = 8000,
    [int]$ChartPort = 5174,
    [switch]$NoBrowser
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DslRoot = Split-Path -Parent $ScriptRoot
$ChartRoot = [System.IO.Path]::GetFullPath((Join-Path $DslRoot $ChartRepo))
$KiwoomEnvRoot = if ([System.IO.Path]::IsPathRooted($KiwoomEnvDir)) {
    [System.IO.Path]::GetFullPath($KiwoomEnvDir)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $DslRoot $KiwoomEnvDir))
}
$RuntimeDir = Join-Path $DslRoot '.runtime\strategy-ui'
$DslPidFile = Join-Path $RuntimeDir 'dsl.pid'
$ChartPidFile = Join-Path $RuntimeDir 'chart.pid'
$DslOut = Join-Path $RuntimeDir 'dsl.out.log'
$DslErr = Join-Path $RuntimeDir 'dsl.err.log'
$ChartOut = Join-Path $RuntimeDir 'chart.out.log'
$ChartErr = Join-Path $RuntimeDir 'chart.err.log'

function Fail([string]$Message, [string]$LogFile = '') {
    Write-Host '[ERROR] Strategy UI launch failed.'
    Write-Host ('[FAIL] ' + $Message)
    if ($LogFile -and (Test-Path -LiteralPath $LogFile -PathType Leaf)) {
        Get-Content -LiteralPath $LogFile -Tail 12 | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { Write-Host ('  ' + $_) }
    }
    exit 1
}

function Get-CommandPath([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { return $null }
    return $command.Source
}

function Get-PythonPath {
    $venvPython = Join-Path $DslRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) { return $venvPython }
    $python = Get-CommandPath 'python.exe'
    if ($null -eq $python) { $python = Get-CommandPath 'python' }
    return $python
}

function Get-UrlResponse([string]$Url) {
    try {
        return Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
    }
    catch { return $null }
}

function Test-Url([string]$Url) {
    $response = Get-UrlResponse $Url
    if ($null -eq $response) { return $false }
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
}

function Test-UrlContains([string]$Url, [string]$Expected) {
    $response = Get-UrlResponse $Url
    if ($null -eq $response) { return $false }
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) { return $false }
    return ([string]$response.Content).Contains($Expected)
}

function Wait-Url([string]$Url) {
    for ($attempt = 0; $attempt -lt 50; $attempt += 1) {
        if (Test-Url $Url) { return $true }
        Start-Sleep -Milliseconds 200
    }
    return $false
}

function Stop-PidFile([string]$PidFile) {
    if (-not (Test-Path -LiteralPath $PidFile -PathType Leaf)) { return }
    $raw = (Get-Content -LiteralPath $PidFile -Raw).Trim()
    $pidValue = 0
    if ([int]::TryParse($raw, [ref]$pidValue)) {
        Stop-Process -Id $pidValue -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

if ($Action -eq 'Stop') {
    Stop-PidFile $ChartPidFile
    Stop-PidFile $DslPidFile
    Write-Host '[PASS] Strategy UI stopped.'
    exit 0
}

if (-not (Test-Path -LiteralPath $ChartRoot -PathType Container)) { Fail ('Chart workspace not found: ' + $ChartRoot) }
$KiwoomEnvFile = Join-Path $KiwoomEnvRoot '.env'
if (-not (Test-Path -LiteralPath $KiwoomEnvFile -PathType Leaf)) { Fail ('Kiwoom .env not found: ' + $KiwoomEnvFile) }

$python = Get-PythonPath
if ($null -eq $python) { Fail 'Python is required.' }
$node = Get-CommandPath 'node.exe'
if ($null -eq $node) { $node = Get-CommandPath 'node' }
if ($null -eq $node) { Fail 'Node.js is required.' }

$dslUrl = 'http://' + $BindHost + ':' + $DslPort
$chartUrl = 'http://' + $BindHost + ':' + $ChartPort
$dslReadyUrl = $dslUrl + '/api/strategy-workspace/strategies'
$chartReadyUrl = $chartUrl + '/__cascade_health'
$managerModuleUrl = $chartUrl + '/src/addons/strategy/managed/ManagerAddon.mjs'
$managerUiModuleUrl = $chartUrl + '/src/addons/strategy/managed/DslStrategyManagerUi.mjs'
$startedDsl = $false
$startedChart = $false

try {
    if (-not (Test-Url $dslReadyUrl)) {
        Remove-Item -LiteralPath $DslOut,$DslErr -Force -ErrorAction SilentlyContinue
        $dslProcess = Start-Process -FilePath $python -ArgumentList @(
            '-m','uvicorn','main:app','--host',$BindHost,'--port',[string]$DslPort,'--log-level','warning'
        ) -WorkingDirectory $DslRoot -RedirectStandardOutput $DslOut -RedirectStandardError $DslErr -WindowStyle Hidden -PassThru
        Set-Content -LiteralPath $DslPidFile -Value ([string]$dslProcess.Id) -Encoding ascii
        $startedDsl = $true
    }

    if (-not (Wait-Url $dslReadyUrl)) {
        if ($startedDsl) { Stop-PidFile $DslPidFile }
        Fail ('DSL Strategy Workspace did not become ready at ' + $dslReadyUrl) $DslErr
    }

    Stop-PidFile $ChartPidFile
    Remove-Item -LiteralPath $ChartOut,$ChartErr -Force -ErrorAction SilentlyContinue
    $previousTarget = $env:DSL_STRATEGY_WORKSPACE_URL
    $previousKiwoomEnvDir = $env:KIWOOM_ENV_DIR
    try {
        $env:DSL_STRATEGY_WORKSPACE_URL = $dslUrl
        $env:KIWOOM_ENV_DIR = $KiwoomEnvRoot
        $chartProcess = Start-Process -FilePath $node -ArgumentList @(
            'scripts/serve.mjs','--host',$BindHost,'--port',[string]$ChartPort
        ) -WorkingDirectory $ChartRoot -RedirectStandardOutput $ChartOut -RedirectStandardError $ChartErr -WindowStyle Hidden -PassThru
        Set-Content -LiteralPath $ChartPidFile -Value ([string]$chartProcess.Id) -Encoding ascii
        $startedChart = $true
    }
    finally {
        if ($null -eq $previousTarget) { Remove-Item Env:DSL_STRATEGY_WORKSPACE_URL -ErrorAction SilentlyContinue }
        else { $env:DSL_STRATEGY_WORKSPACE_URL = $previousTarget }
        if ($null -eq $previousKiwoomEnvDir) { Remove-Item Env:KIWOOM_ENV_DIR -ErrorAction SilentlyContinue }
        else { $env:KIWOOM_ENV_DIR = $previousKiwoomEnvDir }
    }

    if (-not (Wait-Url $chartReadyUrl)) {
        if ($startedChart) { Stop-PidFile $ChartPidFile }
        if ($startedDsl) { Stop-PidFile $DslPidFile }
        Fail ('Chart did not become ready at ' + $chartReadyUrl) $ChartErr
    }

    if (-not (Test-UrlContains $chartReadyUrl '"app":"cascading-feature-solution"')) {
        if ($startedChart) { Stop-PidFile $ChartPidFile }
        if ($startedDsl) { Stop-PidFile $DslPidFile }
        Fail ('Unexpected process is serving Chart port: ' + $chartReadyUrl) $ChartErr
    }

    if (-not (Test-UrlContains $managerModuleUrl 'STRATEGY_MANAGER_ADDON_ID')) {
        if ($startedChart) { Stop-PidFile $ChartPidFile }
        if ($startedDsl) { Stop-PidFile $DslPidFile }
        Fail ('Strategy Manager module is not being served by the active Chart process: ' + $managerModuleUrl) $ChartErr
    }

    if (-not (Test-UrlContains $managerUiModuleUrl 'export class DslStrategyManagerUi')) {
        if ($startedChart) { Stop-PidFile $ChartPidFile }
        if ($startedDsl) { Stop-PidFile $DslPidFile }
        Fail ('Strategy Manager UI module is not being served by the active Chart process: ' + $managerUiModuleUrl) $ChartErr
    }

    $entryUrl = $chartUrl + '/chart.html?manager=1'
    if (-not $NoBrowser) { Start-Process $entryUrl | Out-Null }
    Write-Host ('[PASS] Strategy UI ready: ' + $entryUrl)
    exit 0
}
catch {
    if ($startedChart) { Stop-PidFile $ChartPidFile }
    if ($startedDsl) { Stop-PidFile $DslPidFile }
    Fail $_.Exception.Message
}
