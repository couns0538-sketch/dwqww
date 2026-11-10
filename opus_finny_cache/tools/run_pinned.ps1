# run_pinned.ps1 (opus2, PowerShell 5.1) - run ONE program inside the job envelope and wait for its normal exit.
# Sets Idle + affinity 0xF000 (CPUs 12-15) on ITSELF first and reads both back (exit 78 on mismatch), so the child inherits
# both from its first instruction; TEMP/TMP/TMPDIR on D:; D: floor 20 GiB (exit 75). Never ends any process: if the program
# does not exit within -TimeoutSec, this script reports it (exit 124) and leaves it running for the owner to inspect.
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File run_pinned.ps1 -Exe <exe> -ArgLine "<args>" -Out <file>
#        [-WorkDir <dir>] [-In <stdin file>] [-TimeoutSec 7200] [-Mask 0xF000]
param(
  [Parameter(Mandatory=$true)][string]$Exe,
  [string]$ArgLine = '',
  [Parameter(Mandatory=$true)][string]$Out,
  [string]$WorkDir = '',
  [string]$In = '',
  [int]$TimeoutSec = 7200,
  [long]$Mask = 0xF000
)
$ErrorActionPreference = 'Stop'
if (($Mask -le 0) -or (($Mask -band (-bnot 0xF000)) -ne 0)) { Write-Output "mask outside CPUs 12-15"; exit 78 }
$me = [System.Diagnostics.Process]::GetCurrentProcess(); $me.ProcessorAffinity = [IntPtr]$Mask; $me.PriorityClass = 'Idle'; $me.Refresh()
if (([long]$me.ProcessorAffinity -ne $Mask) -or ("$($me.PriorityClass)" -ne 'Idle')) { Write-Output "ENVELOPE FAIL"; exit 78 }
$tmp = 'D:\forge_jobs_20261107\opus2\tmp'; $env:TMP = $tmp; $env:TEMP = $tmp; $env:TMPDIR = $tmp; $env:PYTHONDONTWRITEBYTECODE = '1'
if (-not ($env:PATH -like '*msys64\ucrt64\bin*')) { $env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH }
if (((Get-PSDrive D).Free / 1GB) -lt 20) { Write-Output "DISK FLOOR: D: < 20 GiB free"; exit 75 }
$sa = @{ FilePath = $Exe; NoNewWindow = $true; PassThru = $true; RedirectStandardOutput = $Out; RedirectStandardError = "$Out.stderr.txt" }
if ($ArgLine) { $sa.ArgumentList = $ArgLine }
if ($WorkDir) { $sa.WorkingDirectory = $WorkDir }
if ($In) { if (-not (Test-Path -LiteralPath $In)) { Write-Output "stdin file missing: $In"; exit 127 }; $sa.RedirectStandardInput = $In }
$p = Start-Process @sa; $null = $p.Handle
if (-not $p.WaitForExit($TimeoutSec * 1000)) { Write-Output "TIMEOUT after $TimeoutSec s: pid $($p.Id) left running (never ended by this job)"; exit 124 }
$p.WaitForExit()
Write-Output ("run_pinned: exit {0} ({1})" -f $p.ExitCode, $Exe)
exit $p.ExitCode
