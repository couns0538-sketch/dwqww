# regime_abba.ps1 - INDICATIVE A/B of the lock exe against one switch-1 exe at several hash sizes (PowerShell 5.1, ASCII).
#
# Why: the search prefetches the child's transposition-table entry before make_move and probes it at the top of the
# child node. Work done between the two (make_move, the stalemate test with its king-line build) overlaps the memory
# wait. A patch that removes such work gains only when the entry is already there at probe time, that is when the
# table sits in cache. With a table far larger than the cache every probe waits for memory and the removed work
# turns into waiting. Hash 1 and Hash 16 against Hash 256 or more separates the two cases on any machine load.
# Node counts differ from the pins when Hash is not 16; spd_uci.py then requires all arms to agree with each other.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File regime_abba.ps1 -Name BUNDLE4 -Tag bn4 [-Hashes 1,16,256]
#                  [-Blocks 6] [-Depth 16] [-Net on] [-ExeB <other exe>] [-Mask 0x08]
# Runs pinned to -Mask (default CPU 3) at Idle; writes under out\regime\<Name>\.
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][string]$Tag,
    [string]$Hashes = '1,16,256',
    [int]$Blocks = 6,
    [int]$Depth = 16,
    [ValidateSet('on', 'off')][string]$Net = 'on',
    [string]$ExeA = '',
    [string]$ExeB = '',
    [switch]$Recopy,
    [ValidateSet('arm', 'block')][string]$RecopyPer = 'arm',
    [switch]$FixedBase,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$lock = Join-Path $OUT 'base\combo29_lock_E1284F7F.exe'
if ($ExeA -ne '') { $lock = $ExeA }
if ($ExeB -eq '') { $ExeB = Join-Path $OUT "build\${Tag}_on\m2use\forge_m2use.exe" }
if (-not (Test-Path $ExeB)) { throw "no exe $ExeB" }
$dir = Join-Path $OUT "regime\$Name"
New-Item -ItemType Directory -Force $dir | Out-Null
# -Recopy: the exes run from copies made anew for every arm (or block); -FixedBase: those copies get the
# "randomise the load address" header flag cleared (diagnostic only). See spd_uci.py abba --recopy.
$extra = $(if ($Recopy -or $FixedBase) { " --recopy `"$OUT\tmp\recopy`" --recopy-per $RecopyPer" } else { '' })
if ($FixedBase) { $extra += ' --fixed-base' }
$kind = $(if ($FixedBase) { 'fb' } elseif ($Recopy) { 'rc' } else { 'h' })
foreach ($h in @($Hashes -split ',' | Where-Object { $_ })) {
    $o = Join-Path $dir ("{0}{1}_d{2}_{3}_{4}" -f $kind, $h, $Depth, $Net, (Get-Date -Format 'HHmmss'))
    $argLine = "-I -B `"$T\spd_uci.py`" abba --a `"$lock`" --b `"$ExeB`" --out `"$o`" --blocks $Blocks --depth $Depth --net $Net --hash $h" + $extra
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $PY, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', "$o.txt")
    & powershell.exe @a | Out-Null
    $rc = $LASTEXITCODE
    Get-Content "$o.txt" | Where-Object { $_ -match '^ABBA INDICATIVE|^ERROR|!=' } | ForEach-Object { Write-Output ("{0} Hash {1} d{2} net {3}: {4}" -f $Name, $h, $Depth, $Net, $_) }
    if ($rc -ne 0) { Write-Output ("{0} Hash {1}: ABBA exit {2}" -f $Name, $h, $rc) }
}
