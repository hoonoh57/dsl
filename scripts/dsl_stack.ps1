param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('start', 'restart', 'stop')]
    [string]$Action = 'start'
)

$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $Root '.runtime\dsl-stack'
$BrowserProfile = Join-Path $RuntimeDir 'browser-profile'
$LivePidFile = Join-Path $RuntimeDir 'live-studio.pid'
$ChartPidFile = Join-Path $RuntimeDir 'chart-bridge.pid'
$BrowserPidFile = Join-Path $RuntimeDir 'chart-browser.pid'
$LiveOutLog = Join-Path $RuntimeDir 'live-studio.out.log'
$LiveErrLog = Join-Path $RuntimeDir 'live-studio.err.log'
$ChartOutLog = Join-Path $RuntimeDir 'chart-bridge.out.log'
$ChartErrLog = Join-Path $RuntimeDir 'chart-bridge.err.log'
$LiveUrl = 'http://127.0.0.1:8010/api/capabilities'
$ChartHealthUrl = 'http://127.0.0.1:3032/__chart_health'
$ChartUrl = 'http://127.0.0.1:3032/'

function Write-Info([string]$Message) {
    Write-Host "[INFO] $Message"
}

function Write-Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Read-ProcessId([string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    $text = (Get-Content -Path $Path -Raw -ErrorAction SilentlyContinue).Trim()
    $value = 0
    if ([int]::TryParse($text, [ref]$value) -and $value -gt 0) { return $value }
    return $null
}

function Get-CommandLine([int]$ProcessId) {
    try {
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction Stop
        return [string]$process.CommandLine
    } catch {
        return ''
    }
}

function Test-ExpectedCommand([string]$CommandLine, [string[]]$Needles) {
    if ([string]::IsNullOrWhiteSpace($CommandLine)) { return $false }
    foreach ($needle in $Needles) {
        if ($CommandLine.IndexOf($needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
    }
    return $false
}

function Stop-ProcessTree([int]$ProcessId) {
    if ($ProcessId -le 0) { return }
    try {
        & taskkill.exe /PID $ProcessId /T /F 2>$null | Out-Null
    } catch {
        try { Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
}

function Stop-TrackedProcess([string]$PidFile, [string[]]$Needles, [string]$Label) {
    $processId = Read-ProcessId $PidFile
    if ($null -eq $processId) {
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
        return
    }

    $commandLine = Get-CommandLine $processId
    if (Test-ExpectedCommand $commandLine $Needles) {
        Write-Info "Stopping $Label (PID $processId)"
        Stop-ProcessTree $processId
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

function Stop-ExpectedPortOwner([int]$Port, [string[]]$Needles, [string]$Label) {
    $connections = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    foreach ($connection in $connections) {
        $processId = [int]$connection.OwningProcess
        if ($processId -le 0) { continue }
        $commandLine = Get-CommandLine $processId
        if (-not (Test-ExpectedCommand $commandLine $Needles)) {
            throw "Port $Port is occupied by an unrelated process (PID $processId). Refusing to terminate it."
        }
        Write-Info "Stopping stale $Label listener on port $Port (PID $processId)"
        Stop-ProcessTree $processId
    }
}

function Stop-ChartBrowser {
    $processId = Read-ProcessId $BrowserPidFile
    if ($null -ne $processId) {
        $commandLine = Get-CommandLine $processId
        if ($commandLine.IndexOf($BrowserProfile, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            Write-Info "Stopping chart browser (PID $processId)"
            Stop-ProcessTree $processId
        }
    }
    Remove-Item $BrowserPidFile -Force -ErrorAction SilentlyContinue

    try {
        $profileProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -and $_.CommandLine.IndexOf($BrowserProfile, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        })
        foreach ($process in $profileProcesses) {
            Stop-Process -Id ([int]$process.ProcessId) -Force -ErrorAction SilentlyContinue
        }
    } catch {}
}

function Stop-All {
    Stop-ChartBrowser
    Stop-TrackedProcess $ChartPidFile @('chart_platform_server.mjs') 'Chart Bridge'
    Stop-TrackedProcess $LivePidFile @('live_studio_main.py') 'Live Studio'
    Stop-ExpectedPortOwner 3032 @('chart_platform_server.mjs') 'Chart Bridge'
    Stop-ExpectedPortOwner 8010 @('live_studio_main.py') 'Live Studio'
}

function Resolve-Executable([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { throw "$Name was not found in PATH." }
    return $command.Source
}

function Resolve-Browser {
    $candidates = @(
        (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:LocalAppData 'Microsoft\Edge\Application\msedge.exe'),
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe')
    ) | Where-Object { $_ -and (Test-Path $_) }

    if ($candidates.Count -gt 0) { return $candidates[0] }

    foreach ($name in @('msedge.exe', 'chrome.exe')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($null -ne $command) { return $command.Source }
    }
    throw 'Microsoft Edge or Google Chrome is required for the managed chart window.'
}

function Wait-Url([string]$Url, [string]$Label, [int]$TimeoutSeconds = 25) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
                Write-Pass "$Label ready"
                return
            }
        } catch {}
        Start-Sleep -Milliseconds 300
    } while ((Get-Date) -lt $deadline)

    throw "$Label did not become ready within $TimeoutSeconds seconds."
}

function Test-Url([string]$Url) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
    } catch {
        return $false
    }
}

function Start-ChartBrowser {
    Stop-ChartBrowser
    New-Item -ItemType Directory -Path $BrowserProfile -Force | Out-Null
    $browser = Resolve-Browser
    $arguments = @(
        "--user-data-dir=`"$BrowserProfile`"",
        '--no-first-run',
        '--disable-session-crashed-bubble',
        "--app=$ChartUrl"
    )
    $process = Start-Process -FilePath $browser -ArgumentList $arguments -PassThru
    Set-Content -Path $BrowserPidFile -Value $process.Id -Encoding ascii
    Write-Pass "Chart opened: $ChartUrl"
}

function Start-Servers {
    New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null
    foreach ($log in @($LiveOutLog, $LiveErrLog, $ChartOutLog, $ChartErrLog)) {
        Remove-Item $log -Force -ErrorAction SilentlyContinue
    }

    $python = Resolve-Executable 'python.exe'
    $node = Resolve-Executable 'node.exe'

    Write-Info 'Starting Live Studio on 127.0.0.1:8010'
    $live = Start-Process -FilePath $python -ArgumentList @('.\live_studio_main.py') -WorkingDirectory $Root -RedirectStandardOutput $LiveOutLog -RedirectStandardError $LiveErrLog -WindowStyle Hidden -PassThru
    Set-Content -Path $LivePidFile -Value $live.Id -Encoding ascii
    Wait-Url $LiveUrl 'Live Studio'

    Write-Info 'Starting Chart Bridge on 127.0.0.1:3032'
    $chart = Start-Process -FilePath $node -ArgumentList @('.\chart_bridge\chart_platform_server.mjs') -WorkingDirectory $Root -RedirectStandardOutput $ChartOutLog -RedirectStandardError $ChartErrLog -WindowStyle Hidden -PassThru
    Set-Content -Path $ChartPidFile -Value $chart.Id -Encoding ascii
    Wait-Url $ChartHealthUrl 'Chart Bridge'
}

New-Item -ItemType Directory -Path $RuntimeDir -Force | Out-Null

try {
    switch ($Action) {
        'start' {
            Write-Info 'Resetting the DSL chart stack'
            Stop-All
            Start-Servers
            Start-ChartBrowser
            Write-Pass 'DSL chart stack started'
        }
        'restart' {
            if (-not (Test-Url $LiveUrl) -or -not (Test-Url $ChartHealthUrl)) {
                throw 'Servers are not both running. Use start.bat instead; restart.bat never restarts servers.'
            }
            Start-ChartBrowser
            Write-Pass 'Chart restarted without restarting servers'
        }
        'stop' {
            Stop-All
            Write-Pass 'DSL servers and chart stopped'
        }
    }
    exit 0
} catch {
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    if ($Action -eq 'start') {
        try { Stop-All } catch {}
        Write-Host "[INFO] Logs: $RuntimeDir"
    }
    exit 1
}
