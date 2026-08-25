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

function Resolve-ChartRepo([string]$RequestedPath) {
    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        return [System.IO.Path]::GetFullPath($RequestedPath)
    }

    if (-not [string]::IsNullOrWhiteSpace($env:CASCADE_CHART_REPO)) {
        $fromEnvironment = [System.IO.Path]::GetFullPath($env:CASCADE_CHART_REPO)
        if (Test-Path -LiteralPath $fromEnvironment -PathType Container) {
            return $fromEnvironment
        }
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
    if ($matches.Count -eq 1) {
        return $matches[0]
    }
    if ($matches.Count -gt 1) {
        throw ('Multiple Chart repos found. Pass -ChartRepo explicitly: ' + ($matches -join ', '))
    }

    return [System.IO.Path]::GetFullPath($sibling)
}

$ChartRepo = Resolve-ChartRepo $ChartRepo

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

function Get-FreeTcpPort([string]$HostName, [string]$PythonPath) {
    $previousErrorActionPreference = $ErrorActionPreference
    $output = @()
    $exitCode = -1
    try {
        $ErrorActionPreference = 'Continue'
        $probe = 'import socket,sys; s=socket.socket(); s.bind((sys.argv[1],0)); print(s.getsockname()[1]); s.close()'
        $output = & $PythonPath -c $probe $HostName 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        throw ('Unable to allocate an isolated verification port on ' + $HostName + '.')
    }
    $portText = [string]($output | Select-Object -Last 1)
    $port = 0
    if (-not [int]::TryParse($portText.Trim(), [ref]$port) -or $port -lt 1 -or $port -gt 65535) {
        throw ('Invalid isolated verification port: ' + $portText)
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
    $output = @()
    $exitCode = -1
    try {
        Set-Location -LiteralPath $WorkingDirectory
        # Native tools such as Python unittest legitimately write progress to stderr.
        # In Windows PowerShell 5.1, 2>&1 can otherwise promote that stderr record
        # into a terminating NativeCommandError when the global preference is Stop.
        # Native process success/failure is governed exclusively by LASTEXITCODE.
        $ErrorActionPreference = 'Continue'
        $output = & $FilePath @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
        Set-Location -LiteralPath $previous.Path
    }
    if ($exitCode -ne 0) {
        $tail = ($output | Select-Object -Last 60) -join [Environment]::NewLine
        throw ($Label + ' failed (exit=' + $exitCode + ')' + [Environment]::NewLine + $tail)
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

    # The verifier owns an isolated live-smoke instance by default. Common
    # development ports may already belong to unrelated services; verification
    # must neither kill nor silently reuse them. Explicit user-supplied ports
    # remain authoritative and retain the launcher's fail-closed collision rule.
    $smokeStage1Port = $Stage1Port
    $smokeChartPort = $ChartPort
    if (-not $PSBoundParameters.ContainsKey('Stage1Port')) {
        $smokeStage1Port = Get-FreeTcpPort $BindHost $python
    }
    if (-not $PSBoundParameters.ContainsKey('ChartPort')) {
        do {
            $smokeChartPort = Get-FreeTcpPort $BindHost $python
        } while ($smokeChartPort -eq $smokeStage1Port)
    }

    $smokeArgs = @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $Launcher,
        '-Action', 'Smoke', '-ChartRepo', $ChartRepo,
        '-BindHost', $BindHost, '-Stage1Port', [string]$smokeStage1Port,
        '-ChartPort', [string]$smokeChartPort, '-NoBrowser'
    )
    if ($InstallDependencies) { $smokeArgs += '-InstallDependencies' }
    Invoke-External 'live operational smoke' $powershell $smokeArgs $DslRoot

    Write-Host ('[PASS] Stage 1 verification completed: mode=' + $Mode + '.')
    exit 0
}
catch {
    Fail $_.Exception.Message
}
