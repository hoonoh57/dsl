param(
    [string]$OutputPath = (Join-Path $env:TEMP "dsl-realdata2-samsung-dataset.csv")
)

$ErrorActionPreference = "Stop"

$SourceUrl = "https://raw.githubusercontent.com/nileshiq/Samsung-Stock-Price/bcef6f27b803ce89000e2fc336201ddeef7df015/Samsung%20Dataset.csv"
$ExpectedGitBlobSha1 = "68e3b6d861b4bfcf39d9c09c6a073c271369d3a9"

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$client = New-Object System.Net.WebClient
try {
    $bytes = $client.DownloadData($SourceUrl)
}
finally {
    $client.Dispose()
}

if ($null -eq $bytes -or $bytes.Length -eq 0) {
    throw "REALDATA2 source download returned no bytes."
}

$prefixText = "blob $($bytes.Length)`0"
$prefixBytes = [System.Text.Encoding]::UTF8.GetBytes($prefixText)
$gitBlobBytes = New-Object byte[] ($prefixBytes.Length + $bytes.Length)
[System.Array]::Copy($prefixBytes, 0, $gitBlobBytes, 0, $prefixBytes.Length)
[System.Array]::Copy($bytes, 0, $gitBlobBytes, $prefixBytes.Length, $bytes.Length)

$sha1 = [System.Security.Cryptography.SHA1]::Create()
try {
    $actualGitBlobSha1 = ([System.BitConverter]::ToString($sha1.ComputeHash($gitBlobBytes))).Replace("-", "").ToLowerInvariant()
}
finally {
    $sha1.Dispose()
}

if ($actualGitBlobSha1 -ne $ExpectedGitBlobSha1) {
    throw "REALDATA2 Git blob SHA-1 mismatch. expected=$ExpectedGitBlobSha1 actual=$actualGitBlobSha1"
}

[System.IO.File]::WriteAllBytes($OutputPath, $bytes)

$sha256 = [System.Security.Cryptography.SHA256]::Create()
try {
    $contentSha256 = ([System.BitConverter]::ToString($sha256.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
}
finally {
    $sha256.Dispose()
}

Write-Output "[PASS] REALDATA2 exact source verified; bytes=$($bytes.Length); sha256=$contentSha256; path=$OutputPath"
