param(
    [ValidateSet('Start', 'Status', 'Stop', 'Preflight', 'Smoke')]
    [string]$Action = 'Start',
    [string]$ChartRepo = '',
    [string]$BindHost = '127.0.0.1',
    [int]$TacticalPort = 8000,
    [int]$ChartPort = 5174,
    [switch]$InstallDependencies,
    [switch]$NoBrowser,
    [switch]$KeepRunning
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DslRoot = Split-Path -Parent $ScriptRoot

function Resolve-ChartRepo([string]$RequestedPath) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        return [System.IO.Path]::GetFullPath($RequestedPath)
    }
    if (-not [string]::IsNullOrWhiteSpace($env:CASCADE_CHART_REPO)) {
        $fromEnvironment = [System.IO.Path]::GetFullPath($env:CASCADE_CHART_REPO)
        if (Test-Path -LiteralPath $fromEnvironment -PathType Container) { return $fromEnvironment }
    }
    $sibling = Join-Path (Split-Path -Parent $DslRoot) 'cascading-feature-solution'
    if (Test-Path -LiteralPath $sibling -PathType Container) {
        return [System.IO.Path]::GetFullPath($sibling)
    }
    $workspaceRoot = Split-Path -Parent (Split-Path -Parent $DslRoot)
    $matches = @()
    if (Test-Path -LiteralPath $workspaceRoot -PathType Container) {
        $levelOne = Get-ChildItem -LiteralPath $workspaceRoot -Directory -ErrorAction SilentlyContinue
        foreach ($first in $levelOne) {
            $candidate = Join-Path $first.FullName 'cascading-feature-solution'
            if (Test-Path -LiteralPath $candidate -PathType Container) {
                $matches += [System.IO.Path]::GetFullPath($candidate)
            }
            $levelTwo = Get-ChildItem -LiteralPath $first.FullName -Directory -ErrorAction SilentlyContinue
            foreach ($second in $levelTwo) {
                $candidate = Join-Path $second.FullName 'cascading-feature-solution'
                if (Test-Path -LiteralPath $candidate -PathType Container) {
                    $matches += [System.IO.Path]::GetFullPath($candidate)
                }
            }
        }
    }
    $matches = @($matches | Sort-Object -Unique)
    if ($matches.Count -eq 1) { return $matches[0] }
    if ($matches.Count -gt 1) {
        throw ('Multiple Chart repos found. Pass -ChartRepo explicitly: ' + ($matches -join ', '))
    }
    return [System.IO.Path]::GetFullPath($sibling)
}

$ChartRepo = Resolve-ChartRepo $ChartRepo
$PidFile = Join-Path $env:TEMP 'quant-dsl-tactical-stack.json'
$LogRoot = Join-Path $env:TEMP 'quant-dsl-tactical-logs'
$TacticalBase = 'http://{0}:{1}' -f $BindHost, $TacticalPort
$ChartBase = 'http://{0}:{1}' -f $BindHost, $ChartPort
$TacticalHealth = $TacticalBase + '/api/stage1/tactical/health'
$ChartHealth = $ChartBase + '/__cascade_health'
$TacticalUrl = $TacticalBase + '/tactical?chartSsot=' + [Uri]::EscapeDataString($ChartBase)

function Fail([string]$Message) { Write-Host ('[FAIL] ' + $Message); exit 1 }

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

function Test-HttpMarker([string]$Url, [string]$Marker) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        return ($response.StatusCode -eq 200 -and [string]$response.Content -like ('*' + $Marker + '*'))
    }
    catch { return $false }
}

function Test-PortOpen([string]$ComputerName, [int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try { $client.Connect($ComputerName, $Port); return $true }
    catch { return $false }
    finally { $client.Close() }
}

function Wait-Health([string]$Url, [string]$Marker, [System.Diagnostics.Process]$Process, [int]$Seconds = 30) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-HttpMarker $Url $Marker) { return $true }
        if ($null -ne $Process) {
            try { $Process.Refresh(); if ($Process.HasExited) { return $false } }
            catch { return $false }
        }
        Start-Sleep -Milliseconds 300
    }
    return $false
}

function Read-PidState {
    if (-not (Test-Path -LiteralPath $PidFile -PathType Leaf)) { return $null }
    try { return (Get-Content -LiteralPath $PidFile -Raw -Encoding UTF8 | ConvertFrom-Json) }
    catch { return $null }
}

function Write-PidState([object]$State) {
    $json = $State | ConvertTo-Json -Depth 5
    $utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($PidFile, $json, $utf8NoBom)
}

function Remove-PidState { if (Test-Path -LiteralPath $PidFile) { Remove-Item -LiteralPath $PidFile -Force } }

function Stop-TrackedProcess([object]$PidValue, [string]$ExpectedMarker) {
    if ($null -eq $PidValue) { return }
    $id = 0
    if (-not [int]::TryParse([string]$PidValue, [ref]$id)) { return }
    $process = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($null -eq $process) { return }
    try {
        $cim = Get-CimInstance Win32_Process -Filter ('ProcessId = {0}' -f $id) -ErrorAction Stop
        if ($null -eq $cim -or [string]$cim.CommandLine -notlike ('*' + $ExpectedMarker + '*')) { return }
    }
    catch { return }
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
}

function Assert-Preflight {
    if ($TacticalPort -lt 1 -or $TacticalPort -gt 65535) { Fail 'TacticalPort must be 1..65535.' }
    if ($ChartPort -lt 1 -or $ChartPort -gt 65535) { Fail 'ChartPort must be 1..65535.' }
    if ($TacticalPort -eq $ChartPort) { Fail 'TacticalPort and ChartPort must be different.' }
    if (-not (Test-Path -LiteralPath (Join-Path $DslRoot 'tactical_main.py') -PathType Leaf)) { Fail 'tactical_main.py is missing.' }
    if (-not (Test-Path -LiteralPath $ChartRepo -PathType Container)) { Fail ('Chart repo not found: ' + $ChartRepo) }
    if (-not (Test-Path -LiteralPath (Join-Path $ChartRepo 'scripts\serve.mjs') -PathType Leaf)) { Fail 'Chart repo scripts\serve.mjs is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $ChartRepo 'src\shell\chart-document-viewer.html') -PathType Leaf)) { Fail 'Chart Document viewer is missing.' }

    $node = Get-CommandPath 'node.exe'; if ($null -eq $node) { $node = Get-CommandPath 'node' }
    if ($null -eq $node) { Fail 'Node.js is required.' }
    $nodeText = (& $node --version 2>&1 | Select-Object -First 1)
    $nodeMajorText = ([string]$nodeText).Trim().TrimStart('v').Split('.')[0]
    $nodeMajor = 0
    if (-not [int]::TryParse($nodeMajorText, [ref]$nodeMajor) -or $nodeMajor -lt 24) { Fail ('Chart SSOT requires Node.js >= 24; found ' + $nodeText) }

    $python = Get-PythonPath
    if ($null -eq $python) { Fail 'Python is required.' }
    $pythonVersionText = (& $python --version 2>&1 | Select-Object -First 1)
    & $python -c 'import fastapi,uvicorn,numpy,pydantic,pymysql; import tactical_main' 2>$null
    if ($LASTEXITCODE -ne 0) {
        if (-not $InstallDependencies) { Fail 'Tactical Python dependencies/imports are missing. Re-run with -InstallDependencies.' }
        & $python -m pip install -r (Join-Path $DslRoot 'requirements.txt')
        if ($LASTEXITCODE -ne 0) { Fail 'Python dependency installation failed.' }
        & $python -c 'import fastapi,uvicorn,numpy,pydantic,pymysql; import tactical_main' 2>$null
        if ($LASTEXITCODE -ne 0) { Fail 'tactical_main import failed after dependency installation.' }
    }

    $chartDependency = Join-Path $ChartRepo 'node_modules\lightweight-charts\package.json'
    if (-not (Test-Path -LiteralPath $chartDependency -PathType Leaf)) {
        if (-not $InstallDependencies) { Fail 'Chart dependencies are missing. Re-run with -InstallDependencies.' }
        $npm = Get-CommandPath 'npm.cmd'; if ($null -eq $npm) { $npm = Get-CommandPath 'npm' }
        if ($null -eq $npm) { Fail 'npm is required.' }
        Push-Location $ChartRepo
        try { & $npm install; if ($LASTEXITCODE -ne 0) { Fail 'Chart dependency installation failed.' } }
        finally { Pop-Location }
    }
    return @{ Node=$node; Python=$python; NodeVersion=[string]$nodeText; PythonVersion=[string]$pythonVersionText }
}

if ($Action -eq 'Status') {
    $chartOk = Test-HttpMarker $ChartHealth '"app":"cascading-feature-solution"'
    $tacticalOk = Test-HttpMarker $TacticalHealth '"schema":"tactical_research/v1"'
    if ($chartOk -and $tacticalOk) { Write-Host ('[PASS] Tactical stack ready: ' + $TacticalUrl); exit 0 }
    Write-Host ('[FAIL] Tactical stack status: tactical=' + $(if ($tacticalOk) {'ready'} else {'down'}) + ', chart=' + $(if ($chartOk) {'ready'} else {'down'})); exit 1
}

if ($Action -eq 'Stop') {
    $state = Read-PidState
    if ($null -ne $state) {
        Stop-TrackedProcess $state.tacticalPid 'tactical_main:app'
        Stop-TrackedProcess $state.chartPid 'serve.mjs'
        Remove-PidState
    }
    Write-Host '[PASS] Tracked Tactical stack processes stopped.'
    exit 0
}

$preflight = Assert-Preflight
if ($Action -eq 'Preflight') {
    Write-Host ('[PASS] Tactical preflight: Python ' + $preflight.PythonVersion + ', Node ' + $preflight.NodeVersion)
    exit 0
}

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$chartOut = Join-Path $LogRoot ('chart-' + $stamp + '.out.log')
$chartErr = Join-Path $LogRoot ('chart-' + $stamp + '.err.log')
$tacticalOut = Join-Path $LogRoot ('tactical-' + $stamp + '.out.log')
$tacticalErr = Join-Path $LogRoot ('tactical-' + $stamp + '.err.log')
$chartProcess = $null; $tacticalProcess = $null; $startedChart = $false; $startedTactical = $false

try {
    if (-not (Test-HttpMarker $ChartHealth '"app":"cascading-feature-solution"')) {
        if (Test-PortOpen $BindHost $ChartPort) { throw ($ChartBase + ' is occupied by a non-Cascade service.') }
        $chartArgs = @((Join-Path $ChartRepo 'scripts\serve.mjs'), '--host', $BindHost, '--port', [string]$ChartPort)
        $chartProcess = Start-Process -FilePath $preflight.Node -ArgumentList $chartArgs -WorkingDirectory $ChartRepo -RedirectStandardOutput $chartOut -RedirectStandardError $chartErr -PassThru -WindowStyle Hidden
        $startedChart = $true
        if (-not (Wait-Health $ChartHealth '"app":"cascading-feature-solution"' $chartProcess 30)) { throw ('Chart SSOT failed to become healthy. Log: ' + $chartErr) }
    }
    if (-not (Test-HttpMarker $TacticalHealth '"schema":"tactical_research/v1"')) {
        if (Test-PortOpen $BindHost $TacticalPort) { throw ($TacticalBase + ' is occupied by a non-Tactical service.') }
        $tacticalArgs = @('-m', 'uvicorn', 'tactical_main:app', '--host', $BindHost, '--port', [string]$TacticalPort)
        $tacticalProcess = Start-Process -FilePath $preflight.Python -ArgumentList $tacticalArgs -WorkingDirectory $DslRoot -RedirectStandardOutput $tacticalOut -RedirectStandardError $tacticalErr -PassThru -WindowStyle Hidden
        $startedTactical = $true
        if (-not (Wait-Health $TacticalHealth '"schema":"tactical_research/v1"' $tacticalProcess 30)) { throw ('Tactical API failed to become healthy. Log: ' + $tacticalErr) }
    }

    if ($Action -eq 'Smoke') {
        if (-not (Test-HttpMarker ($TacticalBase + '/tactical') 'Tactical Multi-Symbol Lab')) { throw 'Tactical UI route did not render expected marker.' }
        if (-not $KeepRunning) {
            if ($startedTactical -and $null -ne $tacticalProcess) { Stop-Process -Id $tacticalProcess.Id -Force -ErrorAction SilentlyContinue }
            if ($startedChart -and $null -ne $chartProcess) { Stop-Process -Id $chartProcess.Id -Force -ErrorAction SilentlyContinue }
        }
        Write-Host '[PASS] Tactical live operational smoke completed.'
        exit 0
    }

    $tacticalPidValue = $null
    $chartPidValue = $null
    if ($startedTactical -and $null -ne $tacticalProcess) { $tacticalPidValue = $tacticalProcess.Id }
    if ($startedChart -and $null -ne $chartProcess) { $chartPidValue = $chartProcess.Id }
    $state = [ordered]@{
        tacticalPid = $tacticalPidValue
        chartPid = $chartPidValue
        tacticalUrl = $TacticalUrl
        tacticalBase = $TacticalBase
        chartBase = $ChartBase
        createdAt = (Get-Date).ToString('o')
    }
    Write-PidState $state
    if (-not $NoBrowser) { Start-Process $TacticalUrl | Out-Null }
    Write-Host ('[PASS] Tactical stack ready: ' + $TacticalUrl)
}
catch {
    if ($startedTactical -and $null -ne $tacticalProcess) { Stop-Process -Id $tacticalProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($startedChart -and $null -ne $chartProcess) { Stop-Process -Id $chartProcess.Id -Force -ErrorAction SilentlyContinue }
    Fail $_.Exception.Message
}
