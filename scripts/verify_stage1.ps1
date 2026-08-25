param(
    [ValidateSet('Quick', 'Full')]
    [string]$Mode = 'Full',
    [string]$ChartRepo = '',
    [string]$BindHost = '127.0.0.1',
    [int]$Stage1Port = 8000,
    [int]$ChartPort = 5174,
    [switch]$InstallDependencies
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DslRoot = Split-Path -Parent $ScriptRoot
$Launcher = Join-Path $ScriptRoot 'start_stage1_stack.ps1'
$StressHarness = Join-Path $DslRoot 'stage1_stress.py'
if ([string]::IsNullOrWhiteSpace($ChartRepo)) {
    $ChartRepo = Join-Path (Split-Path -Parent $DslRoot) 'cascading-feature-solution'
}
$ChartRepo = [System.IO.Path]::GetFullPath($ChartRepo)

function Fail([string]$Message) {
    Write-Host ('[FAIL] ' + $Message)
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

function Get-NodePath {
    $node = Get-CommandPath 'node.exe'
    if ($null -eq $node) { $node = Get-CommandPath 'node' }
    return $node
}

function Invoke-External(
    [string]$Label,
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$WorkingDirectory
) {
    $previous = Get-Location
    $output = @()
    $exitCode = -1
    try {
        Set-Location -LiteralPath $WorkingDirectory
        $output = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Set-Location -LiteralPath $previous.Path
    }
    if ($exitCode -ne 0) {
        $tail = ($output | Select-Object -Last 8) -join ' | '
        throw ($Label + ' failed (exit=' + $exitCode + '): ' + $tail)
    }
}

try {
    if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) {
        throw 'Stage 1 stack launcher is missing.'
    }
    if (-not (Test-Path -LiteralPath $StressHarness -PathType Leaf)) {
        throw 'Stage 1 stress harness is missing.'
    }
    if (-not (Test-Path -LiteralPath $ChartRepo -PathType Container)) {
        throw ('Chart repo not found: ' + $ChartRepo)
    }

    $python = Get-PythonPath
    if ($null -eq $python) { throw 'Python is required.' }
    $node = Get-NodePath
    if ($null -eq $node) { throw 'Node.js is required.' }
    $powershell = Get-CommandPath 'powershell.exe'
    if ($null -eq $powershell) { $powershell = Get-CommandPath 'powershell' }
    if ($null -eq $powershell) { throw 'Windows PowerShell 5.1 is required.' }

    $preflightArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Launcher,
        '-Action', 'Preflight', '-ChartRepo', $ChartRepo,
        '-BindHost', $BindHost, '-Stage1Port', [string]$Stage1Port,
        '-ChartPort', [string]$ChartPort
    )
    if ($InstallDependencies) { $preflightArgs += '-InstallDependencies' }
    Invoke-External 'preflight' $powershell $preflightArgs $DslRoot

    Invoke-External 'python compile' $python @('-m', 'compileall', '-q', '.') $DslRoot
    Invoke-External 'core regression' $python @('-m', 'unittest', '-v', 'test_core.py') $DslRoot
    Invoke-External 'Stage 1 contracts' $python @('-m', 'unittest', 'discover', '-v', '-p', 'test_stage1_*.py') $DslRoot

    $chartContractTests = @(
        './tests/chart_document_renderer.test.mjs',
        './tests/chart_drawing_primitives_contract.test.mjs',
        './tests/chart_drawing_ssot_boundary.test.mjs',
        './tests/responsive_chart_surface.test.mjs',
        './tests/stable_pane_identity_surface.test.mjs'
    )
    $chartArgs = @('--test', '--test-reporter=tap') + $chartContractTests
    Invoke-External 'Stage 1 scoped Chart SSOT contracts' $node $chartArgs $ChartRepo

    Invoke-External 'Stage 1 quick stress' $python @($StressHarness) $DslRoot

    if ($Mode -eq 'Full') {
        Invoke-External 'Stage 1 full stress' $python @($StressHarness, '--full') $DslRoot
    }

    $smokeArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Launcher,
        '-Action', 'Smoke', '-ChartRepo', $ChartRepo,
        '-BindHost', $BindHost, '-Stage1Port', [string]$Stage1Port,
        '-ChartPort', [string]$ChartPort, '-NoBrowser'
    )
    if ($InstallDependencies) { $smokeArgs += '-InstallDependencies' }
    Invoke-External 'live operational smoke' $powershell $smokeArgs $DslRoot

    Write-Host ('[PASS] Stage 1 verification completed: mode=' + $Mode + '.')
    exit 0
}
catch {
    Fail $_.Exception.Message
}
