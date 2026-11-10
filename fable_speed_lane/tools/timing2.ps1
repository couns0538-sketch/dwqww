# timing2.ps1 - INDICATIVE A/B with a new copy of the exe for every arm (PowerShell 5.1, ASCII only).
#
# Why a second timing step: the first one (qualify_all.ps1, phase "timing") ran the same two exe files for all
# blocks. On this PC, at times, an exe file carries its own speed offset for as long as it stays loaded:
# byte-identical copies of the lock, each run from its own new file, were measured up to 6 % apart, and BUNDLE4
# against the lock gave -3.65 % and, two hours later on the same two files, +0.30 % (BENCH.md section 3.1). A fixed
# pair of files can therefore give a tight but biased result. Here every arm of every block runs from a copy made
# for that arm, odd blocks run B A A B, and many blocks are taken.
# Lock exe (A) against the switch-1 exe (B); "aa" = lock against lock, the null result of the method.
# -Plan is a list of steps "NAME:tag:net:blocks" separated by ";" (tag aa = the lock itself, any other tag =
# out\build\<tag>_on). -Round names the run; a finished step is recorded as <Round>.<tag>.<net> in
# out\logs\timing2_done.txt and skipped on a restart. One engine at a time, CPU 3.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File timing2.ps1 [-Plan "..."] [-Round t2] [-Depth 16]
param(
    [string]$Plan = 'AA_lock_vs_lock:aa:on:40;BUNDLE4:bn4:on:100;BUNDLE:bun:on:60;WITNESS_NOPIN:wit:on:30;EVADE_LEGAL:evd:on:30;PAWN_CAPMASK:cap:on:30;CHECKERS_KL:chk:on:30;KING_PAWN_CACHE:kpc:on:30;AA_lock_vs_lock:aa:off:20;BUNDLE4:bn4:off:40;BUNDLE:bun:off:30',
    [string]$Round = 't2',
    [int]$Depth = 16,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$logDir = Join-Path $OUT 'logs'; New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir 'timing2.log'; $doneFile = Join-Path $logDir 'timing2_done.txt'
$lock = Join-Path $OUT 'base\combo29_lock_E1284F7F.exe'
$copies = Join-Path $OUT 'tmp\recopy'
function Note([string]$s) {
    $line = '[' + (NowVienna) + '] ' + $s
    Add-Content -LiteralPath $log -Value $line -Encoding ASCII
    Write-Output $line
}
function IsDone([string]$id) { return (@(Get-Content -LiteralPath $doneFile -ErrorAction SilentlyContinue) -contains $id) }
function Abba2([string]$id, [string]$name, [string]$exeB, [string]$net, [int]$nBlocks) {
    if ($nBlocks -le 0) { return }
    if (IsDone $id) { Note "skip $id (done earlier)"; return }
    if (-not (Test-Path $exeB)) { Note "FAILED $id (no exe $exeB)"; return }
    for ($i = 0; $i -lt 360 -and (DFree) -lt 30.3; $i++) {
        if ($i -eq 0) { Note ("HOLD before " + $id + " - D: has " + (DFree) + " GiB free, under 30.3; waiting, nothing started") }
        Start-Sleep -Seconds 120
    }
    if ((DFree) -lt 30.3) { Note "GAVE UP $id - D: still under 30.3 GiB"; return }
    $o = Join-Path $OUT ("id\$name\abbarc_d${Depth}_${net}_" + (Get-Date -Format 'HHmmss'))
    New-Item -ItemType Directory -Force (Split-Path $o -Parent) | Out-Null
    Note "start $id ($nBlocks blocks, bench $Depth, net $net, new copy per arm, order alternating)"
    $argLine = "-I -B `"$T\spd_uci.py`" abba --a `"$lock`" --b `"$exeB`" --out `"$o`" --blocks $nBlocks --depth $Depth --net $net --recopy `"$copies`" --recopy-per arm --alternate"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PIN -Exe $PY -Mask $Mask -ArgLine $argLine -OutFile "$o.txt" | Out-Null
    $code = $LASTEXITCODE
    Get-Content "$o.txt" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^ABBA INDICATIVE|^ERROR|!=|left behind' } | ForEach-Object { Note ("  $name " + $_) }
    if ($code -eq 0) { Add-Content -LiteralPath $doneFile -Value $id -Encoding ASCII; Note "ok $id" } else { Note "FAILED $id (exit $code)" }
}
Note ("timing2 start, round $Round, bench $Depth, mask 0x{0:X}, D: free {1} GiB" -f $Mask, (DFree))
foreach ($step in @($Plan -split ';' | Where-Object { $_ })) {
    $f = @($step -split ':')
    if ($f.Count -ne 4) { Note "bad plan step '$step'"; continue }
    $exeB = $(if ($f[1] -eq 'aa') { $lock } else { Join-Path $OUT ("build\" + $f[1] + "_on\m2use\forge_m2use.exe") })
    Abba2 ($Round + '.' + $f[1] + '.' + $f[2]) $f[0] $exeB $f[2] ([int]$f[3])
}
Note "timing2 end, round $Round"
