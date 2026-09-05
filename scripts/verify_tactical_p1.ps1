param(
    [ValidateSet('Quick', 'Full')]
    [string]$Mode = 'Full',
    [string]$ChartRepo = '',
    [string]$BindHost = '127.0.0.1',
    [switch]$InstallDependencies
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DslRoot = Split-Path -Parent $ScriptRoot
$BaseVerifier = Join-Path $ScriptRoot 'verify_stage1.ps1'
$TacticalLauncher = Join-Path $ScriptRoot 'start_tactical_stack.ps1'
$TacticalStress = Join-Path $ScriptRoot 'tactical_contract_stress.py'

function Fail([string]$Message) { Write-Host ('[FAIL] ' + $Message); exit 1 }

function Get-CompactFailureOutput([object[]]$Output) {
    $kept = @()
    foreach ($item in @($Output)) {
        $line = [string]$item
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
        if ($trimmed -match '^\[PASS\]') { continue }
        if ($trimmed -match '^(?:✔|ok\s+\d+\b)') { continue }
        if ($trimmed -match '^#\s+(?:tests|suites|pass|fail|cancelled|skipped|todo|duration_ms)\b') { continue }
        if ($trimmed -match '^Ran\s+\d+\s+tests?\b') { continue }
        if ($trimmed -eq 'OK') { continue }
        $kept += $line
    }
    if ($kept.Count -eq 0) {
        $kept = @($Output | Select-Object -Last 20)
    }
    return @($kept | Select-Object -Last 40)
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

function Get-FreeTcpPort([string]$HostName, [string]$PythonPath) {
    $previousErrorActionPreference = $ErrorActionPreference
    $output = @(); $exitCode = -1
    try {
        $ErrorActionPreference = 'Continue'
        $probe = 'import socket,sys; s=socket.socket(); s.bind((sys.argv[1],0)); print(s.getsockname()[1]); s.close()'
        $output = & $PythonPath -c $probe $HostName 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $previousErrorActionPreference }
    if ($exitCode -ne 0) { throw 'Unable to allocate isolated tactical verification port.' }
    $port = 0
    $text = [string]($output | Select-Object -Last 1)
    if (-not [int]::TryParse($text.Trim(), [ref]$port) -or $port -lt 1 -or $port -gt 65535) {
        throw ('Invalid isolated port: ' + $text)
    }
    return $port
}

function Invoke-External(
    [string]$Label,
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$WorkingDirectory
) {
    $previous = Get-Location
    $previousErrorActionPreference = $ErrorActionPreference
    $output = @(); $exitCode = -1
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $ErrorActionPreference = 'Continue'
        $output = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        Set-Location -LiteralPath $previous.Path
    }
    if ($exitCode -ne 0) {
        $compact = (Get-CompactFailureOutput $output) -join [Environment]::NewLine
        throw ($Label + ' failed (exit=' + $exitCode + ')' + [Environment]::NewLine + $compact)
    }
}

try {
    if (-not (Test-Path -LiteralPath $BaseVerifier -PathType Leaf)) { throw 'Base Stage 1 verifier is missing.' }
    if (-not (Test-Path -LiteralPath $TacticalLauncher -PathType Leaf)) { throw 'Tactical launcher is missing.' }
    if (-not (Test-Path -LiteralPath $TacticalStress -PathType Leaf)) { throw 'Tactical stress harness is missing.' }

    $python = Get-PythonPath
    if ($null -eq $python) { throw 'Python is required.' }
    $powershell = Get-CommandPath 'powershell.exe'
    if ($null -eq $powershell) { $powershell = Get-CommandPath 'powershell' }
    if ($null -eq $powershell) { throw 'Windows PowerShell 5.1 is required.' }

    $baseArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$BaseVerifier,'-Mode',$Mode)
    if (-not [string]::IsNullOrWhiteSpace($ChartRepo)) { $baseArgs += @('-ChartRepo',$ChartRepo) }
    if ($InstallDependencies) { $baseArgs += '-InstallDependencies' }
    Invoke-External 'base Stage 1 Full boundary' $powershell $baseArgs $DslRoot

    $preflightArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$TacticalLauncher,'-Action','Preflight')
    if (-not [string]::IsNullOrWhiteSpace($ChartRepo)) { $preflightArgs += @('-ChartRepo',$ChartRepo) }
    if ($InstallDependencies) { $preflightArgs += '-InstallDependencies' }
    Invoke-External 'tactical preflight' $powershell $preflightArgs $DslRoot

    Invoke-External 'tactical quick stress' $python @($TacticalStress) $DslRoot
    if ($Mode -eq 'Full') {
        Invoke-External 'tactical full stress' $python @($TacticalStress,'--full') $DslRoot
    }

    $tacticalPort = Get-FreeTcpPort $BindHost $python
    do { $chartPort = Get-FreeTcpPort $BindHost $python } while ($chartPort -eq $tacticalPort)
    $smokeArgs = @(
        '-NoProfile','-ExecutionPolicy','Bypass','-File',$TacticalLauncher,
        '-Action','Smoke','-BindHost',$BindHost,
        '-TacticalPort',[string]$tacticalPort,'-ChartPort',[string]$chartPort,
        '-NoBrowser'
    )
    if (-not [string]::IsNullOrWhiteSpace($ChartRepo)) { $smokeArgs += @('-ChartRepo',$ChartRepo) }
    if ($InstallDependencies) { $smokeArgs += '-InstallDependencies' }
    Invoke-External 'tactical live smoke' $powershell $smokeArgs $DslRoot

    Write-Host ('[PASS] Tactical P1 verification completed: mode=' + $Mode + '.')
    exit 0
}
catch { Fail $_.Exception.Message }
