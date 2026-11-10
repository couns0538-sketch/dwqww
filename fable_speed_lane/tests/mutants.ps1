# mutants.ps1 - does the harness catch a wrong version of each candidate? (PowerShell 5.1, ASCII only)
# For each mutant: copy the candidate's work tree to out\tmp, make ONE planted change (the text must occur exactly
# once), build the harness with the candidate's switch and run the first -Fens FENs. A mutant counts as CAUGHT when
# the run does not exit 0 or its transcript differs from the base transcript. One line per mutant, also appended
# to out\id\mutants\MUTANTS.log. Exit 3 when a mutant that must be caught is not.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File mutants.ps1 [-Only chk_nodisc] [-Fens 300]
param(
    [string[]]$Only = @(),
    [int]$Fens = 300,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\tools\env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$nl = "`n"
# Id, candidate, harness defines, file, text to find, replacement, what the mutant does, must the plain run catch it
$mutants = @(
    @{ Id = 'kpc_anyking'; Name = 'KING_PAWN_CACHE'; Defs = 'FORGE_SPD_KING_PAWN_CACHE=1'; File = 'src\eval.cpp'
       Find = 'static_cast<int>(kp->kp_king[kp_us]) == king &&'; Put = 'kp->kp_king[kp_us] >= 0 &&'
       What = 'record used for any king square'; Must = $true },
    @{ Id = 'wit_pinned_plain'; Name = 'WITNESS_NOPIN'; Defs = 'FORGE_SPD_WITNESS_NOPIN=1'; File = 'src\board.cpp'
       Find = 'if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'; Put = 'if (checkers_ == 0) {'
       What = 'witness accepted without the line test, plain build (the boolean rarely changes: other legal moves exist)'; Must = $false },
    @{ Id = 'wit_pinned_verify'; Name = 'WITNESS_NOPIN'; Defs = 'FORGE_SPD_WITNESS_NOPIN=2'; File = 'src\board.cpp'
       Find = 'if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'; Put = 'if (checkers_ == 0) {'
       What = 'witness accepted without the line test, verify build'; Must = $true },
    @{ Id = 'wit_incheck'; Name = 'WITNESS_NOPIN'; Defs = 'FORGE_SPD_WITNESS_NOPIN=1'; File = 'src\board.cpp'
       Find = 'if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'; Put = 'if (attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'
       What = 'witness accepted while in check (shows only at a checkmate with a free pawn push: needs the full FEN set, 3 failures in 971,469 positions; the first 300 FENs hold no such position)'; Must = $true; N = 12000 },
    @{ Id = 'evd_nopin'; Name = 'EVADE_LEGAL'; Defs = 'FORGE_SPD_EVADE_LEGAL=1'; File = 'src\board.cpp'
       Find = 'evade_legal = (king_lines_.pinned & square_bb(move.from)) == 0 ||'; Put = 'evade_legal = true ||'
       What = 'pin rule dropped for check evasions'; Must = $true },
    @{ Id = 'cap_wrongside'; Name = 'PAWN_CAPMASK'; Defs = 'FORGE_SPD_PAWN_CAPMASK=1'; File = 'src\board.cpp'
       Find = ($nl + '        Bitboard capturers = pawns & pawn_attacks_bb(them, enemy);'); Put = ($nl + '        Bitboard capturers = pawns & pawn_attacks_bb(us, enemy);')
       What = 'capturer mask built with the wrong pawn direction (main generator)'; Must = $true },
    @{ Id = 'chk_nodisc'; Name = 'CHECKERS_KL'; Defs = 'FORGE_SPD_CHECKERS_KL=1'; File = 'src\board.cpp'
       Find = '((king_lines_.discoverers & square_bb(move.from)) == 0 ||'; Put = '(true ||'
       What = 'discovered checks ignored'; Must = $true },
    @{ Id = 'chk_promo'; Name = 'CHECKERS_KL'; Defs = 'FORGE_SPD_CHECKERS_KL=1'; File = 'src\board.cpp'
       Find = ('if (king_lines_.valid && (move.flags & (EnPassant | KingCastle | QueenCastle | Promotion)) == 0U &&'); Put = ('if (king_lines_.valid && (move.flags & (EnPassant | KingCastle | QueenCastle)) == 0U &&')
       What = 'promotions taken through the shortcut (the promoted piece is not a pawn)'; Must = $false }
)
$idDir = Join-Path $OUT 'id\mutants'; New-Item -ItemType Directory -Force $idDir | Out-Null
$fenFile = Join-Path $OUT 'base\fens_12k_v2.txt'
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function RunPinned([string]$exe, [string]$argLine, [string]$outFile) {
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $exe, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', $outFile)
    & powershell.exe @a | Out-Null
    return $LASTEXITCODE
}
$baseDone = @{}
function BaseRun([int]$count) {
    $b = Join-Path $idDir "base_$count.tsv"
    if (-not $baseDone.ContainsKey($count)) {
        $rc = RunPinned (Join-Path $OUT 'build\prim_base\prim_dump.exe') "`"$fenFile`" `"$b`" 0 $count" "$b.log"
        if ($rc -ne 0) { throw "base harness run failed (exit $rc)" }
        $baseDone[$count] = $true
    }
    return $b
}
$missed = 0
$defaultFens = $Fens
foreach ($m in $mutants) {
    if ($Only.Count -gt 0 -and $Only -notcontains $m.Id) { continue }
    $Fens = $(if ($m.ContainsKey('N') -and $m.N -gt $defaultFens) { $m.N } else { $defaultFens })
    $baseOut = BaseRun $Fens
    $tree = Join-Path $OUT ("tmp\mut_" + $m.Id)
    $bdir = Join-Path $OUT ("build\prim_mut_" + $m.Id)
    foreach ($d in $tree, $bdir) { if (Test-Path $d) { Remove-Item -Recurse -Force $d } }
    Copy-Item -Recurse (Join-Path $OUT ("work\" + $m.Name + "\b")) $tree
    $file = Join-Path $tree $m.File
    (Get-Item $file).IsReadOnly = $false
    $text = [System.IO.File]::ReadAllText($file)
    $parts = $text.Split(@($m.Find), [StringSplitOptions]::None)
    if ($parts.Count -ne 2) { throw ("mutant " + $m.Id + ": the text to change occurs " + ($parts.Count - 1) + " times, not once") }
    [System.IO.File]::WriteAllText($file, $parts[0] + $m.Put + $parts[1], (New-Object System.Text.UTF8Encoding($false)))
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'build_prim.ps1') -Tag ("mut_" + $m.Id) -Src $tree -ExtraDefs $m.Defs -Mask $Mask | Out-File -LiteralPath (Join-Path $idDir ($m.Id + '.build.txt')) -Encoding ASCII
    if ($LASTEXITCODE -ne 0) { throw ("mutant " + $m.Id + " did not build") }
    $o = Join-Path $idDir ($m.Id + "_$Fens.tsv")
    if (Test-Path $o) { Remove-Item -Force $o }
    $rc = RunPinned (Join-Path $bdir 'prim_dump.exe') "`"$fenFile`" `"$o`" 0 $Fens" "$o.log"
    $same = (Test-Path $o) -and ((Sha $o) -eq (Sha $baseOut))
    $caught = ($rc -ne 0) -or (-not $same)
    $first = @(Get-Content "$o.log" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^CHECK FAILED|^ENGINE ABORT' } | Select-Object -First 1)
    $fails = @(Get-Content "$o.log" -ErrorAction SilentlyContinue | Where-Object { $_ -match 'self-check failures' } | Select-Object -Last 1)
    $verdict = $(if ($caught) { 'CAUGHT' } elseif ($m.Must) { 'MISSED' } else { 'not caught (expected: see description)' })
    if (-not $caught -and $m.Must) { $missed++ }
    $line = "MUTANT {0} [{1}; {2}]: {3}; exit {4}; transcript equal to base: {5}; {6}; first report: {7} [{8}]" -f $m.Id, $m.Name, $m.What, $verdict, $rc, $same,
        $(if ($fails.Count) { $fails[0] } else { 'no summary line (aborted)' }), $(if ($first.Count) { $first[0] } else { '-' }), (NowVienna)
    Add-Content -LiteralPath (Join-Path $idDir 'MUTANTS.log') -Value $line -Encoding ASCII
    Write-Output $line
    Remove-Item -Recurse -Force $tree
}
if ($missed -ne 0) { exit 3 }
