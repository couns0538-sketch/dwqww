# mutants.ps1 - does the harness catch a wrong version of each candidate? (PowerShell 5.1, ASCII only)
# For each mutant: copy a source tree to out\tmp, make ONE planted change (the text must occur exactly once), build
# the harness with the switches and run it on tests\targeted_fens.txt and on the first -Fens FENs of the 12k set
# (-Full: on all 12,000 as well).
#   CAUGHT  = the transcript differs from the base transcript, or the harness reports CHECK FAILED (exit 3), or a
#             verify build aborts inside the engine (ENGINE ABORT line). Any other non-zero exit is an ERROR, not a
#             verdict.
#   CONTROL = the same tree and switches WITHOUT the planted change must be clean on the same sets (exit 0,
#             transcript equal to base); a mutant result without a clean control proves nothing.
# -Bundle <NAME> plants the mutants in the bundle tree out\work\<NAME>\b with all of the bundle's switches on.
# One line per run goes to out\id\mutants\MUTANTS[_<bundle>].log. Exit 3 when a mutant that must be caught is not,
# a control is not clean, or a run ends in an error.
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File mutants.ps1 [-Only chk_nodisc] [-Bundle BUNDLE4] [-Full]
param(
    [string[]]$Only = @(),
    [string]$Bundle = '',
    [int]$Fens = 300,
    [switch]$Full,
    [long]$Mask = 0x08
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\tools\env.ps1')
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask
$Only = @($Only | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$nl = "`n"
$swName = @{ KING_PAWN_CACHE = 'FORGE_SPD_KING_PAWN_CACHE'; WITNESS_NOPIN = 'FORGE_SPD_WITNESS_NOPIN'; EVADE_LEGAL = 'FORGE_SPD_EVADE_LEGAL'
             PAWN_CAPMASK = 'FORGE_SPD_PAWN_CAPMASK'; CHECKERS_KL = 'FORGE_SPD_CHECKERS_KL' }
$members = @{ BUNDLE4 = @('WITNESS_NOPIN', 'EVADE_LEGAL', 'PAWN_CAPMASK', 'CHECKERS_KL')
              BUNDLE = @('WITNESS_NOPIN', 'EVADE_LEGAL', 'PAWN_CAPMASK', 'CHECKERS_KL', 'KING_PAWN_CACHE') }
# Id, candidate, switch value, file, text to find, replacement, what the mutant does, must it be caught
$mutants = @(
    @{ Id = 'kpc_anyking'; Name = 'KING_PAWN_CACHE'; Val = 1; File = 'src\eval.cpp'
       Find = 'static_cast<int>(kp->kp_king[kp_us]) == king &&'; Put = 'kp->kp_king[kp_us] >= 0 &&'
       What = 'record used for any king square'; Must = $true },
    @{ Id = 'kpc_keepother'; Name = 'KING_PAWN_CACHE'; Val = 1; File = 'src\eval.cpp'
       Find = 'kp->kp_king[static_cast<std::size_t>(Them)] = -1;'; Put = '(void)0;'
       What = 'other colour''s record kept when the pawns changed'; Must = $true },
    @{ Id = 'kpc_shelter0'; Name = 'KING_PAWN_CACHE'; Val = 1; File = 'src\eval.cpp'
       Find = 'shelter = kp->kp_shelter[kp_us];'; Put = 'shelter = 0;'
       What = 'shelter sum for king danger not restored on a hit'; Must = $true },
    @{ Id = 'wit_pinned_plain'; Name = 'WITNESS_NOPIN'; Val = 1; File = 'src\board.cpp'
       Find = 'if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'; Put = 'if (checkers_ == 0) {'
       What = 'witness accepted without the line test, plain build (shows only where the pinned push is the last hope: targeted row 10)'; Must = $true },
    @{ Id = 'wit_pinned_verify'; Name = 'WITNESS_NOPIN'; Val = 2; File = 'src\board.cpp'
       Find = 'if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'; Put = 'if (checkers_ == 0) {'
       What = 'witness accepted without the line test, verify build'; Must = $true },
    @{ Id = 'wit_incheck'; Name = 'WITNESS_NOPIN'; Val = 1; File = 'src\board.cpp'
       Find = 'if (checkers_ == 0 && attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'; Put = 'if (attacks::line(king_square(side_), to - pawn_push_delta(side_)) == 0) {'
       What = 'witness accepted while in check (shows only at a checkmate with a free pawn push: targeted row 9)'; Must = $true },
    @{ Id = 'evd_nopin'; Name = 'EVADE_LEGAL'; Val = 1; File = 'src\board.cpp'
       Find = 'evade_legal = (king_lines_.pinned & square_bb(move.from)) == 0 ||'; Put = 'evade_legal = true ||'
       What = 'pin rule dropped for check evasions'; Must = $true },
    @{ Id = 'evd_double'; Name = 'EVADE_LEGAL'; Val = 1; File = 'src\board.cpp'
       Find = 'if (!more_than_one(checkers_)) {'; Put = 'if (true) {'
       What = 'double check treated like single check'; Must = $true },
    @{ Id = 'evd_nocapture'; Name = 'EVADE_LEGAL'; Val = 1; File = 'src\board.cpp'
       Find = '((attacks::between(own_king, lsb(checkers_)) | checkers_) & square_bb(move.to))'; Put = '(attacks::between(own_king, lsb(checkers_)) & square_bb(move.to))'
       What = 'capturing the checker no longer counts as an evasion'; Must = $true },
    @{ Id = 'cap_wrongside'; Name = 'PAWN_CAPMASK'; Val = 1; File = 'src\board.cpp'
       Find = ($nl + '        Bitboard capturers = pawns & pawn_attacks_bb(them, enemy);'); Put = ($nl + '        Bitboard capturers = pawns & pawn_attacks_bb(us, enemy);')
       What = 'capturer mask built with the wrong pawn direction'; Must = $true },
    @{ Id = 'chk_nodisc'; Name = 'CHECKERS_KL'; Val = 1; File = 'src\board.cpp'
       Find = '((king_lines_.discoverers & square_bb(move.from)) == 0 ||'; Put = '(true ||'
       What = 'discovered checks ignored'; Must = $true },
    @{ Id = 'chk_promo'; Name = 'CHECKERS_KL'; Val = 1; File = 'src\board.cpp'
       Find = '(move.flags & (EnPassant | Promotion)) == 0U &&'; Put = '(move.flags & EnPassant) == 0U &&'
       What = 'promotions taken through the shortcut (targeted row 4)'; Must = $true },
    @{ Id = 'chk_ep'; Name = 'CHECKERS_KL'; Val = 1; File = 'src\board.cpp'
       Find = '(move.flags & (EnPassant | Promotion)) == 0U &&'; Put = '(move.flags & Promotion) == 0U &&'
       What = 'en passant taken through the shortcut (targeted row 23)'; Must = $true },
    @{ Id = 'chk_kingmoves'; Name = 'CHECKERS_KL'; Val = 1; File = 'src\board.cpp'
       Find = 'if (king_lines_.valid && piece_type(moving) != King &&'; Put = 'if (king_lines_.valid &&'
       What = 'king moves taken through the shortcut (differs only for an illegal king step next to the enemy king)'; Must = $true },
    @{ Id = 'chk_wrongking'; Name = 'CHECKERS_KL'; Val = 1; File = 'src\board.cpp'
       Find = 'attacks::aligned(king_square(them), move.from, move.to))) {'; Put = 'attacks::aligned(king_square(us), move.from, move.to))) {'
       What = 'discoverer line tested against the wrong king (targeted row 24)'; Must = $true }
)
$idDir = Join-Path $OUT 'id\mutants'; New-Item -ItemType Directory -Force $idDir | Out-Null
$logName = $(if ($Bundle) { "MUTANTS_$Bundle.log" } else { 'MUTANTS.log' })
$fenFull = Join-Path $OUT 'base\fens_12k_v2.txt'
$fenTargeted = Join-Path $PSScriptRoot 'targeted_fens.txt'
$sets = @(@{ K = 'targeted'; F = $fenTargeted; N = 0 }, @{ K = "first$Fens"; F = $fenFull; N = $Fens })
if ($Full) { $sets += @{ K = 'all12000'; F = $fenFull; N = 12000 } }
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() }
function Say([string]$line) { Add-Content -LiteralPath (Join-Path $idDir $logName) -Value ($line + ' [' + (NowVienna) + ']') -Encoding ASCII; Write-Output $line }
function RunPinned([string]$exe, [string]$argLine, [string]$outFile) {
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PIN, '-Exe', $exe, '-Mask', $Mask, '-ArgLine', $argLine, '-OutFile', $outFile)
    & powershell.exe @a | Out-Null
    return $LASTEXITCODE
}
function BuildHarness([string]$tag, [string]$tree, [string]$defs) {
    $bdir = Join-Path $OUT ("build\prim_" + $tag)
    if (Test-Path $bdir) { Remove-Item -Recurse -Force $bdir }
    # an empty string would be dropped from a native command line and leave -ExtraDefs without a value
    $a = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'build_prim.ps1'), '-Tag', $tag, '-Src', $tree, '-Mask', $Mask)
    if ($defs -ne '') { $a += @('-ExtraDefs', $defs) }
    & powershell.exe @a | Out-File -LiteralPath (Join-Path $idDir ($tag + '.build.txt')) -Encoding ASCII
    if ($LASTEXITCODE -ne 0) { throw ("harness build failed for " + $tag) }
    return (Join-Path $bdir 'prim_dump.exe')
}
# one harness run on one set; returns verdict text and the class: clean / caught / error
function RunSet([string]$exe, [string]$stem, $set, [string]$baseFile) {
    $o = Join-Path $idDir ($stem + '_' + $set.K + '.tsv')
    if (Test-Path $o) { Remove-Item -Force $o }
    $tail = $(if ($set.N -gt 0) { " 0 " + $set.N } else { '' })
    $rc = RunPinned $exe ("`"" + $set.F + "`" `"" + $o + "`"" + $tail) "$o.log"
    $same = (Test-Path $o) -and ((Sha $o) -eq (Sha $baseFile))
    $log = @(Get-Content "$o.log" -ErrorAction SilentlyContinue)
    $checks = @($log | Where-Object { $_ -match '^CHECK FAILED' })
    $aborts = @($log | Where-Object { $_ -match '^ENGINE ABORT' })
    $fails = @($log | Where-Object { $_ -match '(\d+) self-check failures' } | Select-Object -Last 1)
    $n = $(if ($fails.Count -and $fails[0] -match '(\d+) self-check failures') { $Matches[1] } else { '?' })
    if ($rc -eq 0 -and $same) { return @{ C = 'clean'; T = ($set.K + ': clean') } }
    if ($rc -eq 0 -and -not $same) { return @{ C = 'caught'; T = ($set.K + ': transcript differs'); First = '' } }
    if ($rc -eq 3 -and $checks.Count -gt 0) { return @{ C = 'caught'; T = ($set.K + ": $n self-check failures" + $(if ($same) { '' } else { ', transcript differs' })); First = $checks[0] } }
    if ($rc -eq -1073740791 -and $aborts.Count -gt 0) { return @{ C = 'caught'; T = ($set.K + ': verify abort inside the engine'); First = $aborts[0] } }
    return @{ C = 'error'; T = ($set.K + ": exit $rc without a harness verdict") }
}
# base transcripts of the sets, from a harness built here and now on the lock source (never a leftover exe)
$baseExe = BuildHarness ('mutbase' + $(if ($Bundle) { '_' + $Bundle.ToLower() } else { '' })) (Join-Path $OUT 'base\combo29_src') ''
$baseOf = @{}
foreach ($s in $sets) {
    $b = Join-Path $idDir ('base_' + $s.K + '.tsv')
    $tail = $(if ($s.N -gt 0) { " 0 " + $s.N } else { '' })
    $rc = RunPinned $baseExe ("`"" + $s.F + "`" `"" + $b + "`"" + $tail) "$b.log"
    if ($rc -ne 0) { throw ("base harness run failed on " + $s.K + " (exit $rc): " + (Get-Content "$b.log" -Tail 3 | Out-String)) }
    $baseOf[$s.K] = $b
}
$bad = 0; $controlDone = @{}; $count = 0; $caught = 0
foreach ($m in $mutants) {
    if ($Only.Count -gt 0 -and $Only -notcontains $m.Id) { continue }
    if ($Bundle -and $members[$Bundle] -notcontains $m.Name) { continue }
    $srcName = $(if ($Bundle) { $Bundle } else { $m.Name })
    $defs = $(if ($Bundle) { ($members[$Bundle] | ForEach-Object { $swName[$_] + '=' + $(if ($_ -eq $m.Name) { $m.Val } else { 1 }) }) -join ',' } else { $swName[$m.Name] + '=' + $m.Val })
    $srcTree = Join-Path $OUT ("work\" + $srcName + "\b")
    # control: the unmutated tree with the same switches, once per (tree, switches)
    $ckey = $srcName + '|' + $defs
    if (-not $controlDone.ContainsKey($ckey)) {
        $ctag = 'mutctl_' + $srcName.ToLower() + '_' + ($controlDone.Count + 1)
        $cexe = BuildHarness $ctag $srcTree $defs
        $cres = @($sets | ForEach-Object { RunSet $cexe $ctag $_ $baseOf[$_.K] })
        $cclean = @($cres | Where-Object { $_.C -ne 'clean' }).Count -eq 0
        Say ("CONTROL {0} [{1}]: {2}; {3}" -f $srcName, $defs, $(if ($cclean) { 'clean' } else { 'NOT CLEAN' }), (($cres | ForEach-Object { $_.T }) -join '; '))
        if (-not $cclean) { $bad++ }
        $controlDone[$ckey] = $cclean
    }
    $tree = Join-Path $OUT ("tmp\mut_" + $m.Id)
    if (Test-Path $tree) { Remove-Item -Recurse -Force $tree }
    Copy-Item -Recurse $srcTree $tree
    $file = Join-Path $tree $m.File
    (Get-Item $file).IsReadOnly = $false
    $text = [System.IO.File]::ReadAllText($file)
    $parts = $text.Split(@($m.Find), [StringSplitOptions]::None)
    if ($parts.Count -ne 2) { throw ("mutant " + $m.Id + ": the text to change occurs " + ($parts.Count - 1) + " times in " + $srcName + ", not once") }
    [System.IO.File]::WriteAllText($file, $parts[0] + $m.Put + $parts[1], (New-Object System.Text.UTF8Encoding($false)))
    $mtag = 'mut_' + $m.Id + $(if ($Bundle) { '_' + $Bundle.ToLower() } else { '' })
    $mexe = BuildHarness $mtag $tree $defs
    $res = @($sets | ForEach-Object { RunSet $mexe $mtag $_ $baseOf[$_.K] })
    Remove-Item -Recurse -Force $tree
    $isCaught = @($res | Where-Object { $_.C -eq 'caught' }).Count -gt 0
    $isError = @($res | Where-Object { $_.C -eq 'error' }).Count -gt 0
    $first = @($res | Where-Object { $_.C -eq 'caught' -and $_.First } | Select-Object -First 1)
    $verdict = $(if ($isError) { 'ERROR' } elseif ($isCaught) { 'CAUGHT' } elseif ($m.Must) { 'MISSED' } else { 'not caught (allowed)' })
    $count++; if ($isCaught -and -not $isError) { $caught++ }
    if ($isError -or (-not $isCaught -and $m.Must) -or -not $controlDone[$ckey]) { $bad++ }
    Say ("MUTANT {0} [{1}; {2}; switches {3}]: {4}; {5}; first report: {6}" -f $m.Id, $srcName, $m.What, $defs, $verdict, (($res | ForEach-Object { $_.T }) -join '; '),
        $(if ($first.Count) { $first[0].First } else { '-' }))
}
Say ("SUMMARY {0}: {1} mutants, {2} caught, {3} problems (missed, error or unclean control); sets: {4}" -f $(if ($Bundle) { $Bundle } else { 'singles' }), $count, $caught, $bad, (($sets | ForEach-Object { $_.K }) -join ', '))
if ($bad -ne 0) { exit 3 }
