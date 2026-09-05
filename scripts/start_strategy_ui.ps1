param(
    [ValidateSet('Start', 'Stop')]
    [string]$Action = 'Start',
    [string]$ChartRepo = '..\cascade-chart-validation-20260904',
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

function Test-Url([string]$Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch { return $false }
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

$python = Get-PythonPath
if ($null -eq $python) { Fail 'Python is required.' }
$node = Get-CommandPath 'node.exe'
if ($null -eq $node) { $node = Get-CommandPath 'node' }
if ($null -eq $node) { Fail 'Node.js is required.' }

$dslUrl = 'http://' + $BindHost + ':' + $DslPort
$chartUrl = 'http://' + $BindHost + ':' + $ChartPort
$dslReadyUrl = $dslUrl + '/api/strategy-workspace/strategies'
$chartReadyUrl = $chartUrl + '/__cascade_health'
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

    if (-not (Test-Url $chartReadyUrl)) {
        Remove-Item -LiteralPath $ChartOut,$ChartErr -Force -ErrorAction SilentlyContinue
        $previousTarget = $env:DSL_STRATEGY_WORKSPACE_URL
        try {
            $env:DSL_STRATEGY_WORKSPACE_URL = $dslUrl
            $chartProcess = Start-Process -FilePath $node -ArgumentList @(
                'scripts/serve.mjs','--host',$BindHost,'--port',[string]$ChartPort
            ) -WorkingDirectory $ChartRoot -RedirectStandardOutput $ChartOut -RedirectStandardError $ChartErr -WindowStyle Hidden -PassThru
            Set-Content -LiteralPath $ChartPidFile -Value ([string]$chartProcess.Id) -Encoding ascii
            $startedChart = $true
        }
        finally {
            if ($null -eq $previousTarget) { Remove-Item Env:DSL_STRATEGY_WORKSPACE_URL -ErrorAction SilentlyContinue }
            else { $env:DSL_STRATEGY_WORKSPACE_URL = $previousTarget }
        }
    }

    if (-not (Wait-Url $chartReadyUrl)) {
        if ($startedChart) { Stop-PidFile $ChartPidFile }
        if ($startedDsl) { Stop-PidFile $DslPidFile }
        Fail ('Chart did not become ready at ' + $chartReadyUrl) $ChartErr
    }

    $entryUrl = $chartUrl + '/?stage=strategies'
    if (-not $NoBrowser) { Start-Process $entryUrl | Out-Null }
    Write-Host ('[PASS] Strategy UI ready: ' + $entryUrl)
    exit 0
}
catch {
    if ($startedChart) { Stop-PidFile $ChartPidFile }
    if ($startedDsl) { Stop-PidFile $DslPidFile }
    Fail $_.Exception.Message
}
