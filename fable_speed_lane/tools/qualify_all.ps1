# qualify_all.ps1 - the whole step 4/5 chain, one process at a time on one CPU (PowerShell 5.1, ASCII only).
# Phases (run in the order given):
#   quick  : lock warm/perft rows; per single and per bundle: lock-recipe builds (switch 0 and 1), switch-0 byte
#            compare, 12 pins, harness over all FENs and over the targeted positions (=1 and, where a verify mode
#            exists, =2), verify engine on the 12 pins, warm, soak, perft set; then the consistency check and the
#            planted mutants
#   timing : INDICATIVE A/B (lock exe vs switch-1 exe), A/A first, net on then net off. SUPERSEDED: this phase
#            runs one fixed file per exe, which can bias a result by several percent (BENCH.md section 3.1);
#            use timing2.ps1 (a new copy of the exe per arm) instead
#   cold   : lock cold rows; per bundle: verify engine cold, then cold net on / net off; then the singles
# Bundles: BUNDLE4 = the four candidates that are new under ruling 1 (DUPCHECK.md); BUNDLE = those four plus
# KING_PAWN_CACHE, whose mechanism was built before on another branch (kept as a labelled extra).
# A finished step is recorded in out\logs\chain_done.txt and skipped on a restart; a failed step is logged and the
# chain goes on (evidence first, verdict later). When D: is under 30.3 GiB free the chain waits (it starts nothing)
# until space is back. Nothing here starts more than one engine at a time, except the soak (Threads 2-4 inside one
# engine, still on the one CPU).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File qualify_all.ps1 -Phases quick,timing,cold
param(
    [string[]]$Phases = @('quick', 'timing', 'cold'),
    [int]$Blocks = 10,
    [int]$BundleBlocks = 30,
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
    @{ N = 'WITNESS_NOPIN'; G = 'wit'; D = 'FORGE_SPD_WITNESS_NOPIN'; V = $true },
    @{ N = 'EVADE_LEGAL'; G = 'evd'; D = 'FORGE_SPD_EVADE_LEGAL'; V = $true },
    @{ N = 'PAWN_CAPMASK'; G = 'cap'; D = 'FORGE_SPD_PAWN_CAPMASK'; V = $false },
    @{ N = 'CHECKERS_KL'; G = 'chk'; D = 'FORGE_SPD_CHECKERS_KL'; V = $true },
    @{ N = 'KING_PAWN_CACHE'; G = 'kpc'; D = 'FORGE_SPD_KING_PAWN_CACHE'; V = $false }
)
function DefsOf([string[]]$names, [bool]$verify) {
    return (($singles | Where-Object { $names -contains $_.N } | ForEach-Object { $_.D + $(if ($verify -and $_.V) { '=2' } else { '=1' }) }) -join ',')
}
$four = @('WITNESS_NOPIN', 'EVADE_LEGAL', 'PAWN_CAPMASK', 'CHECKERS_KL')
$three = @('EVADE_LEGAL', 'PAWN_CAPMASK', 'CHECKERS_KL')
$five = $four + @('KING_PAWN_CACHE')
# BUNDLE3 joined on 2026-11-10 at 14:44, after the timing showed WITNESS_NOPIN to cost time under load. On that day
# its steps were run by hand with the same scripts (cand_step.ps1, qualify.ps1, mutants.ps1); it is listed here so
# that a fresh run of this chain covers it.
$bundles = @(
    @{ N = 'BUNDLE4'; G = 'bn4'; On = (DefsOf $four $false); Ver = (DefsOf $four $true) },
    @{ N = 'BUNDLE3'; G = 'bn3'; On = (DefsOf $three $false); Ver = (DefsOf $three $true) },
    @{ N = 'BUNDLE'; G = 'bun'; On = (DefsOf $five $false); Ver = (DefsOf $five $true) }
)

function Note([string]$s) {
    $line = '[' + (NowVienna) + '] ' + $s
    Add-Content -LiteralPath $log -Value $line -Encoding ASCII
    Write-Output $line
}
function IsDone([string]$id) { return (@(Get-Content -LiteralPath $doneFile -ErrorAction SilentlyContinue) -contains $id) }
function MarkDone([string]$id) { Add-Content -LiteralPath $doneFile -Value $id -Encoding ASCII }
function WaitForDisk([string]$id) {
    $told = $false
    for ($i = 0; $i -lt 360 -and (DFree) -lt 30.3; $i++) {
        if (-not $told) { Note ("HOLD before " + $id + " - D: has " + (DFree) + " GiB free, under 30.3; waiting, nothing started"); $told = $true }
        Start-Sleep -Seconds 120
    }
    if ($told) { Note ("D: has " + (DFree) + " GiB free; going on with " + $id) }
    return ((DFree) -ge 30.3)
}
function Step([string]$id, [string]$script, [string[]]$argv) {
    if (IsDone $id) { Note "skip $id (done earlier)"; return }
    if (-not (WaitForDisk $id)) { Note ("GAVE UP " + $id + " - D: still under 30.3 GiB after 12 h"); return }
    Note "start $id"
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $T $script)) + $argv + @('-Mask', $Mask)
    $ErrorActionPreference = 'Continue'
    & powershell.exe @a 2>&1 | ForEach-Object { Note ("  " + "$_") }
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -eq 0) { MarkDone $id; Note "ok $id" } else { Note "FAILED $id (exit $code)" }
}
function Qual([string]$id, [string]$name, [string]$tag, [string]$defs, [string]$vdefs, [string]$stages) {
    $argv = @('-Name', $name, '-Tag', $tag, '-Stages', $stages)
    if ($defs -ne '') { $argv += @('-Defs', $defs) }
    if ($vdefs -ne '') { $argv += @('-VerifyDefs', $vdefs) }
    Step $id 'qualify.ps1' $argv
}
function Abba([string]$id, [string]$name, [string]$exeA, [string]$exeB, [string]$net, [int]$nBlocks) {
    if (IsDone $id) { Note "skip $id (done earlier)"; return }
    if (-not (WaitForDisk $id)) { return }
    $o = Join-Path $OUT ("id\$name\abba_d${Depth}_${net}_" + (Get-Date -Format 'HHmmss'))
    New-Item -ItemType Directory -Force (Split-Path $o -Parent) | Out-Null
    Note "start $id ($nBlocks blocks)"
    $argLine = "-I -B `"$T\spd_uci.py`" abba --a `"$exeA`" --b `"$exeB`" --out `"$o`" --blocks $nBlocks --depth $Depth --net $net"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $PIN -Exe $PY -Mask $Mask -ArgLine $argLine -OutFile "$o.txt" | Out-Null
    $code = $LASTEXITCODE
    Get-Content "$o.txt" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^ABBA INDICATIVE|^ERROR|!=' } | ForEach-Object { Note ("  $name " + $_) }
    if ($code -eq 0) { MarkDone $id; Note "ok $id" } else { Note "FAILED $id (exit $code)" }
}
function OnExe([string]$tag) { return (Join-Path $OUT ("build\" + $tag + "_on\m2use\forge_m2use.exe")) }

Note ("chain start, phases [" + ($Phases -join ' ') + "], mask 0x{0:X}, D: free {1} GiB" -f $Mask, (DFree))
foreach ($phase in $Phases) {
    switch ($phase) {
        'quick' {
            Step 'lock.warm' 'qualify.ps1' @('-Name', 'lock', '-Stages', 'lockwarm')
            # every item gets its lock-recipe builds (skipped when present), the switch-0 byte compare and the 12 pins
            foreach ($x in @($singles) + @($bundles)) {
                $on = $(if ($x.ContainsKey('On')) { $x.On } else { $x.D + '=1' })
                $ver = $(if ($x.ContainsKey('Ver')) { $x.Ver } elseif ($x.V) { $x.D + '=2' } else { '' })
                Step ("build." + $x.G) 'cand_step.ps1' @('-Name', $x.N, '-Tag', $x.G, '-Def', $on, '-Stage', 'build')
                Step ("off." + $x.G) 'cand_step.ps1' @('-Name', $x.N, '-Tag', $x.G, '-Def', $on, '-Stage', 'off')
                Step ("pins." + $x.G) 'cand_step.ps1' @('-Name', $x.N, '-Tag', $x.G, '-Def', $on, '-Stage', 'pins')
                Qual ("quick." + $x.G) $x.N $x.G $on $ver 'primfull,primverify,targeted,engverify,warm,soak,perft'
            }
            Step 'consistency.all' 'check_consistency.ps1' @('-Cands', 'WITNESS_NOPIN:wit,EVADE_LEGAL:evd,PAWN_CAPMASK:cap,CHECKERS_KL:chk,KING_PAWN_CACHE:kpc,BUNDLE4:bn4,BUNDLE3:bn3,BUNDLE:bun')
            # planted mutants: in each single tree, in BUNDLE4 and BUNDLE3 (all their switches on), and the eval
            # mutants in BUNDLE
            Step 'mutants.singles' '..\tests\mutants.ps1' @()
            Step 'mutants.bn4' '..\tests\mutants.ps1' @('-Bundle', 'BUNDLE4')
            Step 'mutants.bn3' '..\tests\mutants.ps1' @('-Bundle', 'BUNDLE3')
            Step 'mutants.bun' '..\tests\mutants.ps1' @('-Bundle', 'BUNDLE', '-Only', 'kpc_anyking,kpc_keepother,kpc_shelter0')
        }
        'timing' {
            # bundles get -BundleBlocks blocks with the net on (they are the lock candidates); everything else -Blocks
            foreach ($net in 'on', 'off') {
                Abba "abba.aa.$net" 'AA_lock_vs_lock' $lock $lock $net $Blocks
                foreach ($b in $bundles) { Abba ("abba." + $b.G + ".$net") $b.N $lock (OnExe $b.G) $net $(if ($net -eq 'on') { $BundleBlocks } else { $Blocks }) }
                foreach ($s in $singles) { Abba ("abba." + $s.G + ".$net") $s.N $lock (OnExe $s.G) $net $Blocks }
            }
        }
        'cold' {
            Step 'lock.cold' 'qualify.ps1' @('-Name', 'lock', '-Stages', 'lockcold')
            foreach ($b in $bundles) { Qual ("cold." + $b.G) $b.N $b.G $b.On $b.Ver 'coldverify,cold' }
            foreach ($s in $singles) { Qual ("cold." + $s.G) $s.N $s.G ($s.D + '=1') '' 'cold' }
        }
        default { Note "unknown phase $phase" }
    }
}
Note 'chain end'
