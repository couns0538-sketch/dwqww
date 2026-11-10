# Pinned launcher for the fable52 search-gap job (PowerShell 5.1 compatible, ASCII only).
#
# Rule being enforced: every build, bench, probe or analysis script of this job runs on
# CPU cores 3-6 only (affinity mask 0x78) at Idle priority, with TEMP/TMP on D:.
#
# How: this PowerShell host pins and lowers ITSELF first. Windows gives every child process
# the parent's affinity mask, and an Idle parent hands the Idle priority class to its children,
# so the target never runs unpinned, not even for its first instruction.
# (Same idea as the crew's opus_r13/tools/run_pinned.py, which uses BelowNormal; this job needs Idle.)
#
# Usage:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File pin.ps1 -Exe <path> [-ArgLine "<args>"]
#                  [-InFile <stdin file>] [-OutFile <stdout+stderr file>] [-WorkDir <dir>]
# Exit code: the child's exit code; 90-93 are launcher failures.
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$InFile = '',
    [string]$OutFile = '',
    [string]$WorkDir = ''
)
$ErrorActionPreference = 'Stop'
$Mask = 0x78
$JobRoot = 'D:\forge_jobs_20261109\fable52'

$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]$Mask
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
$me.Refresh()
if (([int64]$me.ProcessorAffinity) -ne $Mask) { Write-Output 'pin.ps1: affinity was not applied'; exit 90 }
if ($me.PriorityClass -ne [System.Diagnostics.ProcessPriorityClass]::Idle) { Write-Output 'pin.ps1: Idle priority was not applied'; exit 91 }

$tmp = Join-Path $JobRoot 'out\tmp'
if (-not (Test-Path -LiteralPath $tmp)) { Write-Output "pin.ps1: missing $tmp"; exit 92 }
$env:TEMP = $tmp
$env:TMP = $tmp
$env:PYTHONDONTWRITEBYTECODE = '1'
if (-not (Test-Path -LiteralPath $Exe)) { Write-Output "pin.ps1: missing exe $Exe"; exit 93 }
if ($WorkDir -ne '') { Set-Location -LiteralPath $WorkDir }

# Redirection is delegated to cmd.exe through a one-shot .cmd file: no quoting games, no pipe deadlocks.
$line = '"' + $Exe + '" ' + $ArgLine
if ($InFile -ne '') { $line += ' < "' + $InFile + '"' }
if ($OutFile -ne '') { $line += ' > "' + $OutFile + '" 2>&1' }
$cmdFile = Join-Path $tmp ('pin_' + [System.Guid]::NewGuid().ToString('N') + '.cmd')
[System.IO.File]::WriteAllText($cmdFile, "@echo off`r`n" + $line + "`r`nexit /b %ERRORLEVEL%`r`n", [System.Text.Encoding]::ASCII)
try {
    & $env:ComSpec /d /c $cmdFile
    $code = $LASTEXITCODE
} finally {
    Remove-Item -LiteralPath $cmdFile -Force -ErrorAction SilentlyContinue
}
exit $code
