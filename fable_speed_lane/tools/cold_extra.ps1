# cold_extra.ps1 - one cold run (12,000 FENs, go depth 13) of one exe into a row file of its own name
# (PowerShell 5.1, ASCII only).
# Why: on 2026-11-10 some cold runs had to start before the script instance that owns them (qualify.ps1, started
# earlier and still busy with the run before) could start them, because D: was about to fall under the 30.3 GiB
# guard. Two runs must never write one row file, so such a run writes <name>.par.tsv next to the canonical
# <name>.tsv. When the owning instance has ended without making its own run, the .par file is renamed to the
# canonical name by hand and judged with qualify.ps1 -Stages coldcheck (STATUS.md says where that was done).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File cold_extra.ps1 -Exe <exe> -Net on|off -Rows <out.par.tsv>
param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [Parameter(Mandatory = $true)][ValidateSet('on', 'off')][string]$Net,
    [Parameter(Mandatory = $true)][string]$Rows,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
if (Test-Path $Rows) { throw "refusing: $Rows exists" }
$opt = $(if ($Net -eq 'on') { 'UseNNUE=true' } else { 'UseNNUE=false' })
$argLine = "-I -B `"$T\spd_uci.py`" cold --exe `"$Exe`" --fens `"$OUT\base\fens_12k_v2.txt`" --out `"$Rows`" --depth 13 --options $opt"
$a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $PY, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', "$Rows.log")
& powershell.exe @a | Out-Null
$rc = $LASTEXITCODE
Write-Output ((NowVienna) + " cold_extra exit $rc : " + (Get-Content "$Rows.log" -Tail 1 -ErrorAction SilentlyContinue))
exit $rc
