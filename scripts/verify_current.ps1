$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$RuntimeDir = Join-Path $Root '.runtime\verification'
$CheckTimeoutMs = 180000
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
$RunLogDir = Join-Path $RuntimeDir ("run-{0}-{1}" -f $PID, ([Guid]::NewGuid().ToString('N')))
New-Item -ItemType Directory -Path $RunLogDir -Force | Out-Null

function Resolve-Executable([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { throw "$Name was not found in PATH." }
    return $command.Source
}

function Show-FailedCommandOutput([string[]]$LogPaths) {
    $lines = @()
    foreach ($path in $LogPaths) {
        if (Test-Path $path) {
            $lines += @(Get-Content -Path $path -Tail 120 -ErrorAction SilentlyContinue)
        }
    }
    if ($lines.Count -eq 0) { return }

    $matchIndex = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '(?i)(^|\s)not ok\b|SyntaxError|FAIL:|FAILED|ERROR:|Traceback|AssertionError|Exception|ERR_|\[ERROR\]|\[FAIL\]') {
            $matchIndex = $i
            break
        }
    }

    if ($matchIndex -lt 0) {
        $selected = @($lines | Select-Object -Last 20)
    } else {
        $start = [Math]::Max(0, $matchIndex - 3)
        $end = [Math]::Min($lines.Count - 1, $matchIndex + 24)
        $selected = @($lines[$start..$end])
    }

    foreach ($line in $selected) {
        if (-not [string]::IsNullOrWhiteSpace($line)) { Write-Host $line }
    }
}

function Write-VerificationLog([string]$Path, [string]$Content) {
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Invoke-QuietCheck([string]$Label, [string]$Executable, [string[]]$Arguments) {
    $safe = ($Label -replace '[^A-Za-z0-9._-]', '_')
    $outLog = Join-Path $RunLogDir "$safe.out.log"
    $errLog = Join-Path $RunLogDir "$safe.err.log"

    foreach ($argument in $Arguments) {
        if ([string]$argument -match '\s') {
            throw "$Label contains an unsupported whitespace argument in the verifier."
        }
    }

    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = $Executable
    $startInfo.Arguments = ($Arguments -join ' ')
    $startInfo.WorkingDirectory = $Root
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    $stdoutTask = $null
    $stderrTask = $null

    try {
        if (-not $process.Start()) { throw 'child process did not start.' }
        $stdoutTask = $process.StandardOutput.ReadToEndAsync()
        $stderrTask = $process.StandardError.ReadToEndAsync()

        if (-not $process.WaitForExit($CheckTimeoutMs)) {
            try { $process.Kill() } catch {}
            try { $process.WaitForExit() } catch {}
            $stdout = if ($null -ne $stdoutTask) { [string]$stdoutTask.Result } else { '' }
            $stderr = if ($null -ne $stderrTask) { [string]$stderrTask.Result } else { '' }
            Write-VerificationLog $outLog $stdout
            Write-VerificationLog $errLog $stderr
            Write-Host "[ERROR] $Label - timed out" -ForegroundColor Red
            Show-FailedCommandOutput @($errLog, $outLog)
            throw "$Label timed out."
        }

        $process.WaitForExit()
        $stdout = [string]$stdoutTask.Result
        $stderr = [string]$stderrTask.Result
        $exitCode = [int]$process.ExitCode
        Write-VerificationLog $outLog $stdout
        Write-VerificationLog $errLog $stderr
    } catch {
        if ($_.Exception.Message -notmatch 'timed out') {
            Write-Host "[ERROR] $Label - $($_.Exception.Message)" -ForegroundColor Red
            Show-FailedCommandOutput @($errLog, $outLog)
        }
        throw
    } finally {
        $process.Dispose()
    }

    if ($exitCode -ne 0) {
        Write-Host "[ERROR] $Label - exit code $exitCode" -ForegroundColor Red
        Show-FailedCommandOutput @($errLog, $outLog)
        throw "$Label failed with exit code $exitCode."
    }
}

try {
    $node = Resolve-Executable 'node.exe'
    $python = Resolve-Executable 'python.exe'

    Invoke-QuietCheck 'architecture-compliance' $python @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_implementation_compliance_gate.py')
    Invoke-QuietCheck 'addon-boundaries' $node @('vendor\kiwoom-condition\condition1516\chart-platform\scripts\audit-addon-boundaries.mjs')

    Invoke-QuietCheck 'syntax-product-state-test' $node @('--check', 'chart_bridge\chart_single_json_state.test.mjs')
    Invoke-QuietCheck 'syntax-chart-server' $node @('--check', 'chart_bridge\chart_platform_server.mjs')
    Invoke-QuietCheck 'syntax-state-store' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\server\chart\ChartAddonJsonStore.mjs')
    Invoke-QuietCheck 'syntax-state-model' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartAddonState.mjs')
    Invoke-QuietCheck 'syntax-state-http' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\shell\index-wysiwyg\ChartAddonPersistenceHttpHost.mjs')
    Invoke-QuietCheck 'syntax-state-client' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartAddonJsonPersistenceClient.mjs')
    Invoke-QuietCheck 'syntax-pane-layout' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartPaneLayoutManager.mjs')
    Invoke-QuietCheck 'syntax-primary-layout' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\adapters\chart\PrimaryPaneLayoutSurface.mjs')
    Invoke-QuietCheck 'syntax-stable-pane' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\adapters\chart\StablePaneIdentitySurface.mjs')
    Invoke-QuietCheck 'syntax-runtime-audit' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartStateRuntimeAudit.mjs')
    Invoke-QuietCheck 'syntax-subject-view-manager' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartSubjectViewManager.mjs')
    Invoke-QuietCheck 'syntax-compare-runtime-addon' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\addons\research\CompareSubjectsRuntimeAddon.mjs')
    Invoke-QuietCheck 'syntax-market-chart' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\composition\MarketChart.mjs')
    Invoke-QuietCheck 'syntax-compare-controller' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\addons\research\CompareSubjectsShellController.mjs')
    Invoke-QuietCheck 'syntax-workspace' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\shell\index-wysiwyg\MarketChartWorkspace.mjs')
    Invoke-QuietCheck 'syntax-live-ssot-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-state-live-ssot.test.mjs')
    Invoke-QuietCheck 'syntax-runtime-audit-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-state-runtime-audit.test.mjs')
    Invoke-QuietCheck 'syntax-pane-ratio-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-pane-layout-ratio-restore.test.mjs')
    Invoke-QuietCheck 'syntax-stable-pane-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\stable-pane-identity.test.mjs')
    Invoke-QuietCheck 'syntax-compare-startup-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\compare-subject-startup-restore.test.mjs')
    Invoke-QuietCheck 'syntax-compare-ownership-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\compare-subject-runtime-ownership.test.mjs')
    Invoke-QuietCheck 'syntax-viewport-authority-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-startup-viewport-authority.test.mjs')

    Invoke-QuietCheck 'chart-state' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-single-json-state.test.mjs')
    Invoke-QuietCheck 'chart-state-live-ssot' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-state-live-ssot.test.mjs')
    Invoke-QuietCheck 'chart-state-runtime-audit' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-state-runtime-audit.test.mjs')
    Invoke-QuietCheck 'chart-pane-layout-ratio' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-pane-layout-ratio-restore.test.mjs')
    Invoke-QuietCheck 'stable-pane-identity' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\stable-pane-identity.test.mjs')
    Invoke-QuietCheck 'compare-subject-startup' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\compare-subject-startup-restore.test.mjs')
    Invoke-QuietCheck 'compare-runtime-ownership' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\compare-subject-runtime-ownership.test.mjs')
    Invoke-QuietCheck 'viewport-authority' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-startup-viewport-authority.test.mjs')
    Invoke-QuietCheck 'workspace-startup' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-workspace-initial-load.test.mjs')
    Invoke-QuietCheck 'product-state-restart' $node @('--test', 'chart_bridge\chart_single_json_state.test.mjs')
    Invoke-QuietCheck 'chart-bridge' $node @('--test', 'chart_bridge\chart_platform_server.test.mjs')
    Invoke-QuietCheck 'console-policy' $python @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_console_output_policy.py')
    Invoke-QuietCheck 'frozen-core' $python @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_frozen_legacy_core_guard.py')

    Write-Host '[PASS] current verification passed' -ForegroundColor Green
    exit 0
} catch {
    if ($_.Exception.Message -notmatch 'failed with exit code|timed out') {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}
