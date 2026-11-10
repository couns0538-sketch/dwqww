# qualify_all.ps1 - the whole step 4/5 chain, one process at a time on one CPU (PowerShell 5.1, ASCII only).
# Phases (run in the order given):
#   quick  : lock warm/perft rows; per single: harness over all FENs (=1 and, where a verify mode exists, =2),
#            verify engine on the 12 pins, warm, soak, perft set; bundle: lock-recipe builds, switch-0 byte compare,
#            12 pins, then the same ladder
#   timing : INDICATIVE A/B (lock exe vs switch-1 exe), A/A first, net on and net off
#   cold   : lock cold rows; bundle verify engine cold; bundle and singles cold net on / net off
# A finished step is recorded in out\logs\chain_done.txt and skipped on a restart; a failed step is logged and the
# chain goes on (evidence first, verdict later). Nothing here starts more than one engine at a time, except the
# soak (Threads 2-4 inside one engine, still on the one CPU).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File qualify_all.ps1 -Phases quick,timing,cold
param(
    [string[]]$Phases = @('quick', 'timing', 'cold'),
    [int]$Blocks = 10,
    [int]$Depth = 20,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$Phases = @($Phases | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$logDir = Join-Path $OUT 'logs'; New-Item -ItemType Directory -Force $logDir | Out-Null
$log = Join-Path $logDir 'chain.log'; $doneFile = Join-Path $logDir 'chain_done.txt'
$lock = Join-Path $OUT 'base\combo29_lock_E1284F7F.exe'
$singles = @(
    @{ N = 'KING_PAWN_CACHE'; T = 'kpc'; D = 'FORGE_SPD_KING_PAWN_CACHE'; V = $false },
    @{ N = 'WITNESS_NOPIN'; T = 'wit'; D = 'FORGE_SPD_WITNESS_NOPIN'; V = $true },
    @{ N = 'EVADE_LEGAL'; T = 'evd'; D = 'FORGE_SPD_EVADE_LEGAL'; V = $true },
    @{ N = 'PAWN_CAPMASK'; T = 'cap'; D = 'FORGE_SPD_PAWN_CAPMASK'; V = $false },
    @{ N = 'CHECKERS_KL'; T = 'chk'; D = 'FORGE_SPD_CHECKERS_KL'; V = $true }
)
$bundleOn = ($singles | ForEach-Object { $_.D + '=1' }) -join ','
$bundleVerify = ($singles | ForEach-Object { $_.D + $(if ($_.V) { '=2' } else { '=1' }) }) -join ','

function Note([string]$s) {
    $line = '[' + (NowVienna) + '] ' + $s
    Add-Content -LiteralPath $log -Value $line -Encoding ASCII
    Write-Output $line
}
function Step([string]$id, [string]$script, [string[]]$argv) {
    $done = @(Get-Content -LiteralPath $doneFile -ErrorAction SilentlyContinue)
    if ($done -contains $id) { Note "skip $id (done earlier)"; return }
    if ((DFree) -lt 30.3) { Note ("HOLD " + $id + " - D: has " + (DFree) + " GiB free, under 30.3; step not started"); return }
    Note "start $id"
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $T $script)) + $argv + @('-Mask', $Mask)
    $ErrorActionPreference = 'Continue'
    & powershell.exe @a 2>&1 | ForEach-Object { Note ("  " + "$_") }
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -eq 0) { Add-Content -LiteralPath $doneFile -Value $id -Encoding ASCII; Note "ok $id" } else { Note "FAILED $id (exit $code)" }
}
function Qual([string]$id, [string]$name, [string]$tag, [string]$defs, [string]$vdefs, [string]$stages) {
    $argv = @('-Name', $name, '-Tag', $tag, '-Stages', $stages)
    if ($defs -ne '') { $argv += @('-Defs', $defs) }
    if ($vdefs -ne '') { $argv += @('-VerifyDefs', $vdefs) }
    Step $id 'qualify.ps1' $argv
}
function Abba([string]$id, [string]$name, [string]$a, [string]$b, [string]$net) {
    $done = @(Get-Content -LiteralPath $doneFile -ErrorAction SilentlyContinue)
    if ($done -contains $id) { Note "skip $id (done earlier)"; return }
    $o = Join-Path $OUT ("id\$name\abba_d${Depth}_${net}_" + (Get-Date -Format 'HHmmss'))
    New-Item -ItemType Directory -Force (Split-Path $o -Parent) | Out-Null
    Note "start $id"
    $argLine = "-I -B `"$T\spd_uci.py`" abba --a `"$a`" --b `"$b`" --out `"$o`" --blocks $Blocks --depth $Depth --net $net"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PIN -Exe $PY -Mask $Mask -ArgLine $argLine -OutFile "$o.txt" | Out-Null
    $code = $LASTEXITCODE
    Get-Content "$o.txt" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^ABBA INDICATIVE|^ERROR|!=' } | ForEach-Object { Note ("  $name " + $_) }
    if ($code -eq 0) { Add-Content -LiteralPath $doneFile -Value $id -Encoding ASCII; Note "ok $id" } else { Note "FAILED $id (exit $code)" }
}

Note ("chain start, phases [" + ($Phases -join ' ') + "], mask 0x{0:X}, D: free {1} GiB" -f $Mask, (DFree))
foreach ($phase in $Phases) {
    switch ($phase) {
        'quick' {
            Step 'consistency' 'check_consistency.ps1' @()
            Step 'lock.warm' 'qualify.ps1' @('-Name', 'lock', '-Stages', 'lockwarm')
            foreach ($s in $singles) {
                $v = $(if ($s.V) { $s.D + '=2' } else { '' })
                Qual ("quick." + $s.T) $s.N $s.T ($s.D + '=1') $v 'primfull,primverify,engverify,warm,soak,perft'
            }
            Step 'bundle.build' 'cand_step.ps1' @('-Name', 'BUNDLE', '-Tag', 'bun', '-Def', $bundleOn, '-Stage', 'build')
            Step 'bundle.off' 'cand_step.ps1' @('-Name', 'BUNDLE', '-Tag', 'bun', '-Def', $bundleOn, '-Stage', 'off')
            Step 'bundle.pins' 'cand_step.ps1' @('-Name', 'BUNDLE', '-Tag', 'bun', '-Def', $bundleOn, '-Stage', 'pins')
            Qual 'quick.bun' 'BUNDLE' 'bun' $bundleOn $bundleVerify 'primfull,primverify,engverify,warm,soak,perft'
        }
        'timing' {
            foreach ($net in 'on', 'off') { Abba "abba.aa.$net" 'AA_lock_vs_lock' $lock $lock $net }
            foreach ($net in 'on', 'off') {
                Abba "abba.bun.$net" 'BUNDLE' $lock (Join-Path $OUT 'build\bun_on\m2use\forge_m2use.exe') $net
                foreach ($s in $singles) { Abba ("abba." + $s.T + ".$net") $s.N $lock (Join-Path $OUT ("build\" + $s.T + "_on\m2use\forge_m2use.exe")) $net }
            }
        }
        'cold' {
            Step 'lock.cold' 'qualify.ps1' @('-Name', 'lock', '-Stages', 'lockcold')
            Qual 'cold.bun' 'BUNDLE' 'bun' $bundleOn $bundleVerify 'coldverify,cold'
            foreach ($s in $singles) { Qual ("cold." + $s.T) $s.N $s.T ($s.D + '=1') '' 'cold' }
        }
        default { Note "unknown phase $phase" }
    }
}
Note 'chain end'
