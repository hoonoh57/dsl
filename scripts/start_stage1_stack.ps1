param(
    [ValidateSet('Start', 'Status', 'Stop', 'Preflight', 'Smoke')]
    [string]$Action = 'Start',
    [string]$ChartRepo = '',
    [string]$BindHost = '127.0.0.1',
    [int]$Stage1Port = 8000,
    [int]$ChartPort = 5174,
    [switch]$InstallDependencies,
    [switch]$NoBrowser,
    [switch]$KeepRunning
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DslRoot = Split-Path -Parent $ScriptRoot
if ([string]::IsNullOrWhiteSpace($ChartRepo)) {
    $ChartRepo = Join-Path (Split-Path -Parent $DslRoot) 'cascading-feature-solution'
}
$ChartRepo = [System.IO.Path]::GetFullPath($ChartRepo)
$PidFile = Join-Path $env:TEMP 'quant-dsl-stage1-stack.json'
$LogRoot = Join-Path $env:TEMP 'quant-dsl-stage1-logs'
$Stage1Base = 'http://{0}:{1}' -f $BindHost, $Stage1Port
$ChartBase = 'http://{0}:{1}' -f $BindHost, $ChartPort
$Stage1Health = $Stage1Base + '/api/stage1/health'
$ChartHealth = $ChartBase + '/__cascade_health'
$Stage1Url = $Stage1Base + '/stage1?chartSsot=' + [Uri]::EscapeDataString($ChartBase)

function Fail([string]$Message) {
    Write-Host ('[FAIL] ' + $Message)
    exit 1
}

function Get-CommandPath([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { return $null }
    return $command.Source
}

function Test-HttpMarker([string]$Url, [string]$Marker) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
        return ($response.StatusCode -eq 200 -and [string]$response.Content -like ('*' + $Marker + '*'))
    }
    catch {
        return $false
    }
}

function Test-PortOpen([string]$ComputerName, [int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $client.Connect($ComputerName, $Port)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

function Wait-Health([string]$Url, [string]$Marker, [System.Diagnostics.Process]$Process, [int]$Seconds = 25) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-HttpMarker $Url $Marker) { return $true }
        if ($null -ne $Process) {
            try {
                $Process.Refresh()
                if ($Process.HasExited) { return $false }
            }
            catch { return $false }
        }
        Start-Sleep -Milliseconds 300
    }
    return $false
}

function Read-PidState {
    if (-not (Test-Path -LiteralPath $PidFile -PathType Leaf)) { return $null }
    try {
        return (Get-Content -LiteralPath $PidFile -Raw -Encoding UTF8 | ConvertFrom-Json)
    }
    catch {
        return $null
    }
}

function Write-PidState([object]$State) {
    $json = $State | ConvertTo-Json -Depth 5
    $utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($PidFile, $json, $utf8NoBom)
}

function Remove-PidState {
    if (Test-Path -LiteralPath $PidFile) {
        Remove-Item -LiteralPath $PidFile -Force
    }
}

function Stop-TrackedProcess([object]$PidValue, [string]$ExpectedMarker) {
    if ($null -eq $PidValue) { return }
    $id = 0
    if (-not [int]::TryParse([string]$PidValue, [ref]$id)) { return }
    $process = Get-Process -Id $id -ErrorAction SilentlyContinue
    if ($null -eq $process) { return }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedMarker)) {
        try {
            $cim = Get-CimInstance Win32_Process -Filter ('ProcessId = {0}' -f $id) -ErrorAction Stop
            if ($null -eq $cim -or [string]$cim.CommandLine -notlike ('*' + $ExpectedMarker + '*')) { return }
        }
        catch { return }
    }
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
}

function Get-PythonPath {
    $venvPython = Join-Path $DslRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $venvPython -PathType Leaf) { return $venvPython }
    $python = Get-CommandPath 'python.exe'
    if ($null -eq $python) { $python = Get-CommandPath 'python' }
    return $python
}

function Assert-Preflight {
    if ($Stage1Port -lt 1 -or $Stage1Port -gt 65535) { Fail 'Stage1Port must be 1..65535.' }
    if ($ChartPort -lt 1 -or $ChartPort -gt 65535) { Fail 'ChartPort must be 1..65535.' }
    if ($Stage1Port -eq $ChartPort) { Fail 'Stage1Port and ChartPort must be different.' }
    if (-not (Test-Path -LiteralPath (Join-Path $DslRoot 'stage1_main.py') -PathType Leaf)) { Fail 'stage1_main.py is missing.' }
    if (-not (Test-Path -LiteralPath $ChartRepo -PathType Container)) { Fail ('Chart repo not found: ' + $ChartRepo) }
    if (-not (Test-Path -LiteralPath (Join-Path $ChartRepo 'scripts\serve.mjs') -PathType Leaf)) { Fail 'Chart repo scripts\serve.mjs is missing.' }
    if (-not (Test-Path -LiteralPath (Join-Path $ChartRepo 'src\shell\chart-document-viewer.html') -PathType Leaf)) { Fail 'Chart Document viewer is missing in the Chart SSOT repo.' }
    if ($Action -eq 'Smoke' -and -not (Test-Path -LiteralPath (Join-Path $DslRoot 'scripts\stage1_operational_smoke.py') -PathType Leaf)) { Fail 'Stage 1 operational smoke harness is missing.' }

    $node = Get-CommandPath 'node.exe'
    if ($null -eq $node) { $node = Get-CommandPath 'node' }
    if ($null -eq $node) { Fail 'Node.js is required.' }
    $nodeText = (& $node --version 2>&1 | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0) { Fail 'Unable to read Node.js version.' }
    $nodeMajorText = ([string]$nodeText).Trim().TrimStart('v').Split('.')[0]
    $nodeMajor = 0
    if (-not [int]::TryParse($nodeMajorText, [ref]$nodeMajor) -or $nodeMajor -lt 24) { Fail ('Chart SSOT requires Node.js >= 24; found ' + $nodeText) }

    $python = Get-PythonPath
    if ($null -eq $python) { Fail 'Python is required.' }
    $pythonVersionText = (& $python --version 2>&1 | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0) { Fail 'Unable to read Python version.' }

    $pythonDepsOk = $true
    & $python -c 'import fastapi, uvicorn, numpy, pydantic' 2>$null
    if ($LASTEXITCODE -ne 0) { $pythonDepsOk = $false }
    if (-not $pythonDepsOk) {
        if (-not $InstallDependencies) { Fail 'Python dependencies are missing. Re-run with -InstallDependencies.' }
        & $python -m pip install -r (Join-Path $DslRoot 'requirements.txt')
        if ($LASTEXITCODE -ne 0) { Fail 'Python dependency installation failed.' }
    }

    $chartDependency = Join-Path $ChartRepo 'node_modules\lightweight-charts\package.json'
    if (-not (Test-Path -LiteralPath $chartDependency -PathType Leaf)) {
        if (-not $InstallDependencies) { Fail 'Chart dependencies are missing. Re-run with -InstallDependencies.' }
        $npm = Get-CommandPath 'npm.cmd'
        if ($null -eq $npm) { $npm = Get-CommandPath 'npm' }
        if ($null -eq $npm) { Fail 'npm is required to install Chart dependencies.' }
        Push-Location $ChartRepo
        try {
            & $npm install
            if ($LASTEXITCODE -ne 0) { Fail 'Chart dependency installation failed.' }
        }
        finally { Pop-Location }
    }

    return @{
        Node = $node
        Python = $python
        NodeVersion = [string]$nodeText
        PythonVersion = [string]$pythonVersionText
    }
}

function Show-Status {
    $chartOk = Test-HttpMarker $ChartHealth '"app":"cascading-feature-solution"'
    $stage1Ok = Test-HttpMarker $Stage1Health '"schema":"stage1_factory/v1"'
    if ($chartOk -and $stage1Ok) {
        Write-Host ('[PASS] Stage 1 stack ready: ' + $Stage1Url)
        exit 0
    }
    $chartState = if ($chartOk) { 'ready' } else { 'down' }
    $stage1State = if ($stage1Ok) { 'ready' } else { 'down' }
    Write-Host ('[FAIL] Stage 1 stack status: stage1=' + $stage1State + ', chart=' + $chartState)
    exit 1
}

if ($Action -eq 'Status') { Show-Status }

if ($Action -eq 'Stop') {
    $state = Read-PidState
    if ($null -ne $state) {
        Stop-TrackedProcess $state.stage1Pid 'stage1_main:app'
        Stop-TrackedProcess $state.chartPid 'serve.mjs'
        Remove-PidState
    }
    Write-Host '[PASS] Tracked Stage 1 stack processes stopped.'
    exit 0
}

$preflight = Assert-Preflight
if ($Action -eq 'Preflight') {
    Write-Host ('[PASS] Stage 1 preflight: Python ' + $preflight.PythonVersion + ', Node ' + $preflight.NodeVersion)
    exit 0
}

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$chartOut = Join-Path $LogRoot ('chart-' + $stamp + '.out.log')
$chartErr = Join-Path $LogRoot ('chart-' + $stamp + '.err.log')
$stage1Out = Join-Path $LogRoot ('stage1-' + $stamp + '.out.log')
$stage1Err = Join-Path $LogRoot ('stage1-' + $stamp + '.err.log')
$chartProcess = $null
$stage1Process = $null
$startedChart = $false
$startedStage1 = $false
$pidStateWritten = $false

try {
    $chartReady = Test-HttpMarker $ChartHealth '"app":"cascading-feature-solution"'
    if (-not $chartReady) {
        if (Test-PortOpen $BindHost $ChartPort) { throw ($ChartBase + ' is occupied by a non-Cascade service.') }
        $chartArgs = @((Join-Path $ChartRepo 'scripts\serve.mjs'), '--host', $BindHost, '--port', [string]$ChartPort)
        $chartProcess = Start-Process -FilePath $preflight.Node -ArgumentList $chartArgs -WorkingDirectory $ChartRepo -RedirectStandardOutput $chartOut -RedirectStandardError $chartErr -PassThru -WindowStyle Hidden
        $startedChart = $true
        if (-not (Wait-Health $ChartHealth '"app":"cascading-feature-solution"' $chartProcess 30)) {
            throw ('Chart SSOT failed to become healthy. Log: ' + $chartErr)
        }
    }

    $stage1Ready = Test-HttpMarker $Stage1Health '"schema":"stage1_factory/v1"'
    if (-not $stage1Ready) {
        if (Test-PortOpen $BindHost $Stage1Port) { throw ($Stage1Base + ' is occupied by a non-Stage1 service.') }
        $stage1Args = @('-m', 'uvicorn', 'stage1_main:app', '--host', $BindHost, '--port', [string]$Stage1Port)
        $stage1Process = Start-Process -FilePath $preflight.Python -ArgumentList $stage1Args -WorkingDirectory $DslRoot -RedirectStandardOutput $stage1Out -RedirectStandardError $stage1Err -PassThru -WindowStyle Hidden
        $startedStage1 = $true
        if (-not (Wait-Health $Stage1Health '"schema":"stage1_factory/v1"' $stage1Process 30)) {
            throw ('Stage 1 API failed to become healthy. Log: ' + $stage1Err)
        }
    }

    $oldState = Read-PidState
    $stage1Pid = $null
    $chartPid = $null
    if ($startedStage1) { $stage1Pid = $stage1Process.Id }
    elseif ($null -ne $oldState) { $stage1Pid = $oldState.stage1Pid }
    if ($startedChart) { $chartPid = $chartProcess.Id }
    elseif ($null -ne $oldState) { $chartPid = $oldState.chartPid }

    $state = [ordered]@{
        stage1Pid = $stage1Pid
        chartPid = $chartPid
        stage1Url = $Stage1Url
        stage1Base = $Stage1Base
        chartBase = $ChartBase
        createdAt = (Get-Date).ToString('o')
    }

    if ($Action -ne 'Smoke' -or $KeepRunning) {
        Write-PidState $state
        $pidStateWritten = $true
    }

    if ($Action -eq 'Smoke') {
        $smokeScript = Join-Path $DslRoot 'scripts\stage1_operational_smoke.py'
        $smokeOutput = & $preflight.Python $smokeScript '--stage1-base' $Stage1Base '--chart-base' $ChartBase 2>&1
        $smokeExit = $LASTEXITCODE
        if ($smokeExit -ne 0) {
            $tail = ($smokeOutput | Select-Object -Last 5) -join ' | '
            throw ('Operational smoke failed: ' + $tail)
        }
        if (-not $KeepRunning) {
            if ($startedStage1 -and $null -ne $stage1Process) { Stop-Process -Id $stage1Process.Id -Force -ErrorAction SilentlyContinue }
            if ($startedChart -and $null -ne $chartProcess) { Stop-Process -Id $chartProcess.Id -Force -ErrorAction SilentlyContinue }
        }
        $passLine = [string]($smokeOutput | Select-Object -Last 1)
        if (-not $passLine.StartsWith('[PASS]')) { $passLine = '[PASS] Stage 1 operational smoke completed.' }
        Write-Host $passLine
        exit 0
    }

    if (-not $NoBrowser) { Start-Process $Stage1Url | Out-Null }
    Write-Host ('[PASS] Stage 1 stack ready: ' + $Stage1Url)
}
catch {
    if ($startedStage1 -and $null -ne $stage1Process) {
        Stop-Process -Id $stage1Process.Id -Force -ErrorAction SilentlyContinue
    }
    if ($startedChart -and $null -ne $chartProcess) {
        Stop-Process -Id $chartProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($pidStateWritten) { Remove-PidState }
    Fail $_.Exception.Message
}
