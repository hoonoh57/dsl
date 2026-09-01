$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $Root '.runtime\verification'
New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

function Resolve-Executable([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { throw "$Name was not found in PATH." }
    return $command.Source
}

function Show-FailedCommandOutput([string]$LogPath) {
    if (-not (Test-Path $LogPath)) { return }
    $tail = @(Get-Content -Path $LogPath -Tail 120 -ErrorAction SilentlyContinue)
    if ($tail.Count -eq 0) { return }

    $start = -1
    for ($i = 0; $i -lt $tail.Count; $i++) {
        if ($tail[$i] -match '(?i)(^|\s)not ok\b|FAIL:|FAILED|ERROR:|Traceback|AssertionError|Exception|ERR_|\[ERROR\]|\[FAIL\]') {
            $start = $i
            break
        }
    }

    if ($start -lt 0) {
        $lines = @($tail | Select-Object -Last 30)
    } else {
        $end = [Math]::Min($tail.Count - 1, $start + 59)
        $lines = @($tail[$start..$end])
    }

    foreach ($line in $lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) { Write-Host $line }
    }
}

function Invoke-QuietCheck([string]$Label, [string]$Executable, [string[]]$Arguments) {
    $safe = ($Label -replace '[^A-Za-z0-9._-]', '_')
    $log = Join-Path $RuntimeDir "$safe.log"
    Remove-Item $log -Force -ErrorAction SilentlyContinue

    try {
        & $Executable @Arguments > $log 2>&1
        $exitCode = $LASTEXITCODE
    } catch {
        Write-Host "[ERROR] $Label - $($_.Exception.Message)" -ForegroundColor Red
        Show-FailedCommandOutput $log
        throw
    }

    if ($exitCode -ne 0) {
        Write-Host "[ERROR] $Label" -ForegroundColor Red
        Show-FailedCommandOutput $log
        throw "$Label failed with exit code $exitCode."
    }
}

try {
    $node = Resolve-Executable 'node.exe'
    $python = Resolve-Executable 'python.exe'

    Invoke-QuietCheck 'chart-state' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\chart-single-json-state.test.mjs')
    Invoke-QuietCheck 'workspace-startup' $node @('--test', 'vendor\kiwoom-condition\condition1516\chart-platform\tests\market-chart-workspace-initial-load.test.mjs')
    Invoke-QuietCheck 'product-state-restart' $node @('--test', 'chart_bridge\chart_single_json_state.test.mjs')
    Invoke-QuietCheck 'chart-bridge' $node @('--test', 'chart_bridge\chart_platform_server.test.mjs')
    Invoke-QuietCheck 'frozen-core' $python @('-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_frozen_legacy_core_guard.py')

    Write-Host '[PASS] current verification passed' -ForegroundColor Green
    exit 0
} catch {
    if ($_.Exception.Message -notmatch 'failed with exit code') {
        Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    }
    exit 1
}
