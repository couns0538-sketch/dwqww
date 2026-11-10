# kit_build.ps1 (opus2, PowerShell 5.1) - one QA-kit v2.3 LTO+PGO build inside the job envelope.
# Envelope: own process Idle + affinity 0xF000 (CPUs 12-15) set FIRST and read back (fail closed); TEMP/TMP/TMPDIR on D:;
# D: free >= 20 GiB before starting (job disk floor, plan decision D1); no kills, no deletes.
# The kit copy (out\kit_v23_idle) differs from QA's kit_v23 (build_ltopgo.ps1 md5 729fe727...) only in: priority Idle instead
# of BelowNormal (+ readback) and no process termination on timeout. Everything else (command lines, workload, checks) is QA's.
param(
  [Parameter(Mandatory=$true)][string]$SrcDir,
  [Parameter(Mandatory=$true)][string]$Tag,
  [string]$Work = 'D:\forge_jobs_20261107\opus2\out\k',
  [string]$Kit = 'D:\forge_jobs_20261107\opus2\out\kit_v23_idle',
  [string]$CheckOpt = '',          # one option run, e.g. 'TtLockless=true' (kit -CheckOpt)
  [string]$Pins = 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354',
  [string]$PerftPins = 'startpos=4865609,kiwipete=193690690',
  [string]$Python = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
$Mask = 0xF000
$me = [System.Diagnostics.Process]::GetCurrentProcess(); $me.ProcessorAffinity = [IntPtr]$Mask; $me.PriorityClass = 'Idle'; $me.Refresh()
if (([long]$me.ProcessorAffinity -ne $Mask) -or ("$($me.PriorityClass)" -ne 'Idle')) { Write-Output "ENVELOPE FAIL: aff=0x$('{0:X}' -f [long]$me.ProcessorAffinity) prio=$($me.PriorityClass)"; exit 78 }
$tmp = 'D:\forge_jobs_20261107\opus2\tmp'; $env:TMP = $tmp; $env:TEMP = $tmp; $env:TMPDIR = $tmp; $env:PYTHONDONTWRITEBYTECODE = '1'
$freeGiB = (Get-PSDrive D).Free / 1GB
if ($freeGiB -lt 20) { Write-Output ("DISK FLOOR: D: free {0:N2} GiB < 20 GiB; not starting" -f $freeGiB); exit 75 }
$kitScript = Join-Path $Kit 'build_ltopgo.ps1'
Write-Output ("kit_build {0}: src {1} kit {2} (md5 {3}) D: free {4:N2} GiB, self aff 0x{5:X} {6}" -f $Tag, $SrcDir, $Kit, (Get-FileHash $kitScript -Algorithm MD5).Hash, $freeGiB, [long]$me.ProcessorAffinity, $me.PriorityClass)
$kitArgs = @{ SrcDir = $SrcDir; Tag = $Tag; Work = $Work; Kit = $Kit; Affinity = [long]$Mask; Pins = $Pins; PerftPins = $PerftPins; Python = $Python; Expose = $true }
if ($CheckOpt) { $kitArgs.CheckOpt = @($CheckOpt) }
& $kitScript @kitArgs
$rc = $LASTEXITCODE
Write-Output "kit_build $Tag exit $rc"
exit $rc
