$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$RuntimeDir = Join-Path $Root '.runtime\verification'
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

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

function Invoke-QuietCheck([string]$Label, [string]$Executable, [string[]]$Arguments) {
    $safe = ($Label -replace '[^A-Za-z0-9._-]', '_')
    $outLog = Join-Path $RuntimeDir "$safe.out.log"
    $errLog = Join-Path $RuntimeDir "$safe.err.log"
    Remove-Item $outLog, $errLog -Force -ErrorAction SilentlyContinue

    try {
        $process = Start-Process -FilePath $Executable -ArgumentList $Arguments -WorkingDirectory $Root -RedirectStandardOutput $outLog -RedirectStandardError $errLog -Wait -PassThru -WindowStyle Hidden
    } catch {
        Write-Host "[ERROR] $Label - $($_.Exception.Message)" -ForegroundColor Red
        Show-FailedCommandOutput @($errLog, $outLog)
        throw
    }

    if ($process.ExitCode -ne 0) {
        Write-Host "[ERROR] $Label" -ForegroundColor Red
        Show-FailedCommandOutput @($errLog, $outLog)
        throw "$Label failed with exit code $($process.ExitCode)."
    }
}

try {
    $node = Resolve-Executable 'node.exe'
    $python = Resolve-Executable 'python.exe'

    Invoke-QuietCheck 'syntax-product-state-test' $node @('--check', 'chart_bridge\chart_single_json_state.test.mjs')
    Invoke-QuietCheck 'syntax-chart-server' $node @('--check', 'chart_bridge\chart_platform_server.mjs')
    Invoke-QuietCheck 'syntax-state-store' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\server\chart\ChartAddonJsonStore.mjs')
    Invoke-QuietCheck 'syntax-state-model' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartAddonState.mjs')
    Invoke-QuietCheck 'syntax-state-http' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\shell\index-wysiwyg\ChartAddonPersistenceHttpHost.mjs')
    Invoke-QuietCheck 'syntax-state-client' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartAddonJsonPersistenceClient.mjs')
    Invoke-QuietCheck 'syntax-pane-layout' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\runtime\chart\ChartPaneLayoutManager.mjs')
    Invoke-QuietCheck 'syntax-primary-layout' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\src\adapters\chart\PrimaryPaneLayoutSurface.mjs')
    Invoke-QuietCheck 'syntax-live-ssot-test' $node @('--check', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-state-live-ssot.test.mjs')

    Invoke-QuietCheck 'chart-state' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-single-json-state.test.mjs')
    Invoke-QuietCheck 'chart-state-live-ssot' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-state-live-ssot.test.mjs')
    Invoke-QuietCheck 'workspace-startup' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-workspace-initial-load.test.mjs')
    Invoke-QuietCheck 'product-state-restart' $node @('--test', 'chart_bridge\chart_single_json_state.test.mjs')
    Invoke-QuietCheck 'chart-bridge' $node @('--test', 'chart_bridge\chart_platform_server.test.mjs')
    Invoke-QuietCheck 'console-policy' $python @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_console_output_policy.py')
    Invoke-QuietCheck 'frozen-core' $python @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_frozen_legacy_core_guard.py')

    Write-Host '[PASS] current verification passed' -ForegroundColor Green
    exit 0
} catch {
    if ($_.Exception.Message -notmatch 'failed with exit code') {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}
