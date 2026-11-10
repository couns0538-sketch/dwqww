# pin_run.ps1 - pinned launcher of job 3 (PowerShell 5.1, ASCII only).
#
# Rule enforced: every process of this job runs on CPU 3-6 only (affinity mask 0x78 or a subset given with -Mask)
# at Idle priority, with TEMP/TMP under out\job3. This host pins and lowers ITSELF first and reads both back.
# Windows hands a child the parent's affinity mask, and an Idle parent hands on the Idle priority class, so the
# target never runs unpinned, not even for its first instruction. It refuses to start when D: is under the floor.
#
# Usage:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File pin_run.ps1 -Exe <path> [-ArgLine "<args>"]
#                  [-InFile <stdin file>] [-OutFile <stdout+stderr file>] [-WorkDir <dir>] [-Mask 0x78]
#                  [-MinFreeGiB 30.3]
# Exit code: the child's exit code; 90-95 are launcher failures (95 = disk guard, nothing was started).
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [string]$ArgLine = '',
    [string]$InFile = '',
    [string]$OutFile = '',
    [string]$WorkDir = '',
    [long]$Mask = 0x78,
    [double]$MinFreeGiB = 30.3
)
$ErrorActionPreference = 'Stop'
$Lane = 0x78
$JobOut = 'D:\forge_jobs_20261109\fable2\out\job3'
if ($Mask -le 0 -or ($Mask -band (-bnot $Lane)) -ne 0) { Write-Output ('pin_run: mask 0x{0:X} is not inside 0x78' -f $Mask); exit 94 }

$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.ProcessorAffinity = [IntPtr]$Mask
$me.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::Idle
$me.Refresh()
if (([int64]$me.ProcessorAffinity) -ne $Mask) { Write-Output 'pin_run: affinity was not applied'; exit 90 }
if ($me.PriorityClass -ne [System.Diagnostics.ProcessPriorityClass]::Idle) { Write-Output 'pin_run: Idle priority was not applied'; exit 91 }

$tmp = Join-Path $JobOut 'tmp'
if (-not (Test-Path -LiteralPath $tmp)) { Write-Output "pin_run: missing $tmp"; exit 92 }
$env:TEMP = $tmp
$env:TMP = $tmp
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:GIT_NO_LAZY_FETCH = '1'
if (-not (Test-Path -LiteralPath $Exe)) { Write-Output "pin_run: missing exe $Exe"; exit 93 }
$free = (Get-PSDrive D).Free / 1GB
if ($free -lt $MinFreeGiB) {
    $msg = ('pin_run: NOT STARTED (disk guard): D: has {0:N2} GiB free, under {1:N1}' -f $free, $MinFreeGiB)
    if ($OutFile -ne '') { try { [System.IO.File]::WriteAllText($OutFile, $msg + "`r`n", [System.Text.Encoding]::ASCII) } catch { } }
    Write-Output $msg
    exit 95
}
if ($WorkDir -ne '') { Set-Location -LiteralPath $WorkDir }

# Redirection goes through cmd.exe and a one-shot .cmd file: no quoting games and no pipe deadlocks.
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
