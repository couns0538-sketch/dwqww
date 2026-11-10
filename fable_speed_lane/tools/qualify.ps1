# qualify.ps1 - step 4 identity ladder for one switch-ON build (PowerShell 5.1, ASCII only).
# One result line per stage ("QUAL <Name> <stage>: PASS|FAIL ..."), appended to out\id\<Name>\QUALIFY.log too.
# Everything runs pinned to -Mask (default CPU 3) at Idle, one process at a time, and writes under out\.
#
#   -Stages lockcold    : the lock exe's own cold rows (net on / net off), made once (-Name lock)
#           lockwarm    : the lock exe's own warm transcript and perft set, made once (-Name lock)
#           primfull    : harness built with -Defs over all FENs; transcript must equal the base transcript
#           primverify  : harness built with -VerifyDefs (=2 builds abort on any disagreement); exit 0 and equal
#           targeted    : both harness builds on tests\targeted_fens.txt (one position per risky branch)
#           engverify   : lock-recipe engine built with -VerifyDefs; the 12 pins (an abort ends the run)
#           coldverify  : that engine over all FENs, go depth 13, net on; rows must equal the lock's
#           cold        : the ON exe over all FENs, go depth 13, net on and net off; rows must equal the lock's
#           warm        : warm-table session transcript must equal the lock's
#           soak        : Threads 2-4 soak against the lock's legal-move lists, then a Threads 1 tail
#           perft       : six perft positions against published counts
#
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File qualify.ps1 -Name KING_PAWN_CACHE -Tag kpc `
#       -Defs FORGE_SPD_KING_PAWN_CACHE=1 -Stages primfull,cold,warm,soak,perft
param(
    [Parameter(Mandatory = $true)][string]$Name,
    [string]$Tag = '',
    [string[]]$Defs = @(),
    [string[]]$VerifyDefs = @(),
    [string]$Src = '',
    [string[]]$Stages = @('primfull', 'primverify', 'engverify', 'coldverify', 'cold', 'warm', 'soak', 'perft'),
    [int]$Fens = 0,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$Defs = @($Defs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$VerifyDefs = @($VerifyDefs | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$Stages = @($Stages | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$known = 'lockcold', 'lockwarm', 'primfull', 'primverify', 'targeted', 'engverify', 'coldverify', 'cold', 'warm', 'soak', 'perft'
foreach ($s in $Stages) { if ($known -notcontains $s) { throw "unknown stage $s" } }
$lock = Join-Path $OUT 'base\combo29_lock_E1284F7F.exe'
$fenFile = Join-Path $OUT 'base\fens_12k_v2.txt'
$idDir = Join-Path $OUT "id\$Name"
$lockDir = Join-Path $OUT 'id\lock'
New-Item -ItemType Directory -Force $idDir, $lockDir | Out-Null
if ($Src -eq '') { $Src = Join-Path $OUT "work\$Name\b" }
$onExe = Join-Path $OUT "build\${Tag}_on\m2use\forge_m2use.exe"
$v2Exe = Join-Path $OUT "build\${Tag}_v2\m2use\forge_m2use.exe"
$n = $(if ($Fens -gt 0) { "$Fens" } else { 'all' })
$count = $(if ($Fens -gt 0) { " --count $Fens" } else { '' })
$script:failed = 0

function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function Say([string]$stage, [bool]$ok, [string]$text) {
    if (-not $ok) { $script:failed++ }
    $line = "QUAL {0} {1}: {2} {3} [{4}]" -f $Name, $stage, $(if ($ok) { 'PASS' } else { 'FAIL' }), $text, (NowVienna)
    Add-Content -LiteralPath (Join-Path $idDir 'QUALIFY.log') -Value $line -Encoding ASCII
    Write-Output $line
}
function RunPinned([string]$exe, [string]$argLine, [string]$outFile) {
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $exe, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', $outFile)
    & powershell.exe @a | Out-Null
    return $LASTEXITCODE
}
function Uci([string]$argLine, [string]$outFile) { return (RunPinned $PY ("-I -B `"$T\spd_uci.py`" " + $argLine) $outFile) }
function Tail([string]$p) { $x = Get-Content -LiteralPath $p -Tail 1 -ErrorAction SilentlyContinue; if ($x) { "$x" } else { '(no output)' } }
# number of differing rows of two row files (same length expected)
function RowDiff([string]$a, [string]$b) {
    $x = [System.IO.File]::ReadAllLines($a); $y = [System.IO.File]::ReadAllLines($b)
    $d = [math]::Abs($x.Length - $y.Length)
    for ($i = 0; $i -lt [math]::Min($x.Length, $y.Length); $i++) { if ($x[$i] -cne $y[$i]) { $d++ } }
    return $d
}
# NOTE: PowerShell names are case-insensitive. No parameter or local here may be called $out, $t, $j, $pack,
# $repo, $py, $pin or $lm: it would hide the global of env.ps1 inside that function.
function ColdRows([string]$exe, [string]$net, [string]$rowFile) {
    $opt = $(if ($net -eq 'on') { 'UseNNUE=true' } else { 'UseNNUE=false' })
    return (Uci "cold --exe `"$exe`" --fens `"$fenFile`" --out `"$rowFile`" --depth 13 --options $opt$count" "$rowFile.log")
}
function NeedLock([string]$file) { if (-not (Test-Path (Join-Path $lockDir $file))) { throw ("missing lock rows " + $file + ' - run -Name lock -Stages lockcold,lockwarm first') } }
$targetedFile = Join-Path $PACK 'tests\targeted_fens.txt'
# harness run of one build on the 12k set (-targeted: on tests\targeted_fens.txt); builds the harness exe if absent
function PrimRun([string]$ptag, [string]$tree, [string[]]$defs, [string]$transcript, [bool]$targeted = $false) {
    $pexe = Join-Path $OUT "build\prim_$ptag\prim_dump.exe"
    if (-not (Test-Path $pexe)) {
        $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PACK 'tests\build_prim.ps1'), '-Tag', $ptag, '-Src', $tree, '-Mask', $Mask)
        if ($defs.Count -gt 0) { $a += @('-ExtraDefs', ($defs -join ',')) }
        & powershell.exe @a | Out-File -LiteralPath (Join-Path $idDir "prim_build_$ptag.txt") -Encoding ASCII
        if ($LASTEXITCODE -ne 0) { return 90 }
    }
    if ($targeted) { return (RunPinned $pexe "`"$targetedFile`" `"$transcript`"" "$transcript.log") }
    $tail = $(if ($Fens -gt 0) { " 0 $Fens" } else { '' })
    return (RunPinned $pexe "`"$fenFile`" `"$transcript`"$tail" "$transcript.log")
}
function PrimBase([bool]$targeted = $false) {
    $baseOut = Join-Path $OUT $(if ($targeted) { 'id\prim\base_targeted.tsv' } else { "id\prim\base_$n.tsv" })
    if (-not (Test-Path $baseOut)) {
        New-Item -ItemType Directory -Force (Split-Path $baseOut -Parent) | Out-Null
        $rc = PrimRun 'base' (Join-Path $OUT 'base\combo29_src') @() $baseOut $targeted
        if ($rc -ne 0) { throw "base harness run failed (exit $rc)" }
    }
    return $baseOut
}

foreach ($stage in $Stages) {
    switch ($stage) {
        'lockcold' {
            foreach ($net in 'on', 'off') {
                $o = Join-Path $lockDir "cold_${net}_$n.tsv"
                if (-not (Test-Path $o)) { $rc = ColdRows $lock $net $o } else { $rc = 0 }
                Say "lock cold net $net" ($rc -eq 0) ("{0} rows, sha256 {1}; {2}" -f @(Get-Content $o).Count, (Sha $o), (Tail "$o.log"))
            }
        }
        'lockwarm' {
            $w = Join-Path $lockDir 'warm.txt'
            if (-not (Test-Path $w)) { $rc = Uci "warm --exe `"$lock`" --fens `"$fenFile`" --out `"$w`"" "$w.log" } else { $rc = 0 }
            Say 'lock warm' ($rc -eq 0) (Tail "$w.log")
            $p = Join-Path $lockDir 'perftset.json'
            if (-not (Test-Path $p)) { $rc = Uci "perftset --exe `"$lock`" --out `"$p`"" "$p.log" } else { $rc = 0 }
            Say 'lock perft set' ($rc -eq 0) (Tail "$p.log")
        }
        'primfull' {
            $baseOut = PrimBase
            $o = Join-Path $idDir "prim_on_$n.tsv"
            $rc = PrimRun "${Tag}_on" $Src $Defs $o
            $same = (Test-Path $o) -and ((Sha $o) -eq (Sha $baseOut))
            Say 'harness' ($rc -eq 0 -and $same) ("defs [{0}]; {1}; transcript equal to base: {2}; sha256 {3}" -f ($Defs -join ' '), (Tail "$o.log"), $same, $(if (Test-Path $o) { Sha $o } else { '-' }))
        }
        'primverify' {
            if ($VerifyDefs.Count -eq 0) { continue }
            $baseOut = PrimBase
            $o = Join-Path $idDir "prim_verify_$n.tsv"
            $rc = PrimRun "${Tag}_verify" $Src $VerifyDefs $o
            $same = (Test-Path $o) -and ((Sha $o) -eq (Sha $baseOut))
            Say 'harness, verify build' ($rc -eq 0 -and $same) ("defs [{0}]; exit {1}; {2}; transcript equal to base: {3}" -f ($VerifyDefs -join ' '), $rc, (Tail "$o.log"), $same)
        }
        'targeted' {
            $baseOut = PrimBase $true
            $o = Join-Path $idDir 'prim_targeted_on.tsv'
            $rc = PrimRun "${Tag}_on" $Src $Defs $o $true
            $same = (Test-Path $o) -and ((Sha $o) -eq (Sha $baseOut))
            Say 'harness, targeted positions' ($rc -eq 0 -and $same) ("defs [{0}]; {1}; transcript equal to base: {2}; sha256 {3}" -f ($Defs -join ' '), (Tail "$o.log"), $same, $(if (Test-Path $o) { Sha $o } else { '-' }))
            if ($VerifyDefs.Count -gt 0) {
                $o = Join-Path $idDir 'prim_targeted_verify.tsv'
                $rc = PrimRun "${Tag}_verify" $Src $VerifyDefs $o $true
                $same = (Test-Path $o) -and ((Sha $o) -eq (Sha $baseOut))
                Say 'harness, targeted positions, verify build' ($rc -eq 0 -and $same) ("defs [{0}]; exit {1}; {2}; transcript equal to base: {3}" -f ($VerifyDefs -join ' '), $rc, (Tail "$o.log"), $same)
            }
        }
        'engverify' {
            if ($VerifyDefs.Count -eq 0) { continue }
            if (-not (Test-Path $v2Exe)) {
                $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $T 'spd_build.ps1'), '-Tag', "${Tag}_v2", '-Src', $Src, '-Mask', $Mask, '-ExtraDefs', ($VerifyDefs -join ','))
                & powershell.exe @a | Out-File -LiteralPath (Join-Path $idDir 'build_v2.txt') -Encoding ASCII
                if ($LASTEXITCODE -ne 0) { Say 'engine, verify build' $false "build failed, see $idDir\build_v2.txt"; continue }
            }
            $rc = Uci "pins --exe `"$v2Exe`" --out `"$idDir\pins_v2.json`"" "$idDir\pins_v2.txt"
            Say 'engine, verify build, 12 pins' ($rc -eq 0) ("defs [{0}]; {1} (exit {2}); exe sha256 {3}" -f ($VerifyDefs -join ' '), (Tail "$idDir\pins_v2.txt"), $rc, (Sha $v2Exe))
        }
        'coldverify' {
            if ($VerifyDefs.Count -eq 0) { continue }
            NeedLock "cold_on_$n.tsv"
            $o = Join-Path $idDir "cold_v2_on_$n.tsv"
            $rc = ColdRows $v2Exe 'on' $o
            $d = $(if (Test-Path $o) { RowDiff $o (Join-Path $lockDir "cold_on_$n.tsv") } else { -1 })
            Say 'engine, verify build, cold net on' ($rc -eq 0 -and $d -eq 0) ("rows differing from the lock: {0}; {1}" -f $d, (Tail "$o.log"))
        }
        'cold' {
            foreach ($net in 'on', 'off') {
                NeedLock "cold_${net}_$n.tsv"
                $o = Join-Path $idDir "cold_${net}_$n.tsv"
                $rc = ColdRows $onExe $net $o
                $d = $(if (Test-Path $o) { RowDiff $o (Join-Path $lockDir "cold_${net}_$n.tsv") } else { -1 })
                $rows = $(if (Test-Path $o) { @(Get-Content $o).Count } else { 0 })
                Say "cold net $net" ($rc -eq 0 -and $d -eq 0) ("{0}/{1} rows equal the lock's; sha256 {2}; {3}" -f ($rows - $d), $rows, $(if (Test-Path $o) { Sha $o } else { '-' }), (Tail "$o.log"))
            }
        }
        'warm' {
            NeedLock 'warm.txt'
            $o = Join-Path $idDir 'warm.txt'
            $rc = Uci "warm --exe `"$onExe`" --fens `"$fenFile`" --out `"$o`"" "$o.log"
            $same = (Test-Path $o) -and ((Sha $o) -eq (Sha (Join-Path $lockDir 'warm.txt')))
            Say 'warm' ($rc -eq 0 -and $same) ("transcript equal to the lock's: {0}; {1}" -f $same, (Tail "$o.log"))
        }
        'soak' {
            $o = Join-Path $idDir 'soak'
            if (Test-Path $o) { Rename-Item -LiteralPath $o -NewName ('soak_old_' + (Get-Date -Format 'HHmmss')) }
            $rc = Uci "soak --exe `"$onExe`" --ref `"$lock`" --fens `"$fenFile`" --out `"$o`"" "$o.txt"
            Say 'soak' ($rc -eq 0) (Tail "$o.txt")
        }
        'perft' {
            $o = Join-Path $idDir 'perftset.json'
            $rc = Uci "perftset --exe `"$onExe`" --out `"$o`"" "$o.log"
            Say 'perft set' ($rc -eq 0) (Tail "$o.log")
        }
    }
}
if ($script:failed -ne 0) { exit 3 }
