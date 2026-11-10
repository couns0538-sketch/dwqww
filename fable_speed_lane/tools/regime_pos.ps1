# regime_pos.ps1 - lock against one switch-1 exe with `go depth N` on the eight bench positions at ONE hash size,
# a new copy of the exe for every arm (PowerShell 5.1, ASCII only). INDICATIVE.
#
# Why: `bench` always builds its own 16 MB table, so the Hash option cannot vary the size of the transposition
# table there; `go` uses it. A patch whose effect depends on how long the table entry takes to arrive (work removed
# between the prefetch in the parent and the probe in the child) should read differently with a 1 MB table, which
# stays in cache, and with a 256 MB table, which does not. A patch whose own code costs time should read the same.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File regime_pos.ps1 -Name WITNESS_NOPIN -Tag wit -Hash 256
#                  [-Depth 16] [-Blocks 16] [-Net on] [-Mask 0x08]
# Runs pinned to -Mask (default CPU 3) at Idle; writes out\regime\<Name>\pos_d<Depth>_<Net>_h<Hash>[.txt].
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][int]$Hash,
    [int]$Depth = 16,
    [int]$Blocks = 16,
    [ValidateSet('on', 'off')][string]$Net = 'on',
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$lock = Join-Path $OUT 'base\combo29_lock_E1284F7F.exe'
$exeB = Join-Path $OUT "build\${Tag}_on\m2use\forge_m2use.exe"
if (-not (Test-Path $exeB)) { throw "no exe $exeB" }
$dir = Join-Path $OUT "regime\$Name"
New-Item -ItemType Directory -Force $dir | Out-Null
$o = Join-Path $dir ("pos_d{0}_{1}_h{2}" -f $Depth, $Net, $Hash)
if (Test-Path $o) { $o = $o + '_' + (Get-Date -Format 'HHmmss') }
$argLine = "-I -B `"$T\pos_cycles.py`" --a `"$lock`" --b `"$exeB`" --out `"$o`" --depth $Depth --net $Net --hash $Hash --blocks $Blocks --recopy `"$OUT\tmp\recopy`""
$a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $PY, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', "$o.txt")
& powershell.exe @a | Out-Null
$rc = $LASTEXITCODE
Get-Content "$o.txt" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^POS_CYCLES (BLOCKS|TOTAL)|NOT STARTED|rror|differs' } | ForEach-Object { Write-Output ("{0} Hash {1}: {2}" -f $Name, $Hash, $_) }
exit $rc
