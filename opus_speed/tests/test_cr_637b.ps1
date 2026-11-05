# test_cr_637b.ps1 - tests for the Code Review items on opus-speed-20261105 @637be9af (PowerShell 5.1).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File test_cr_637b.ps1
# T1 blocker: a pin DIFF build (mutant HistoryMax 16384 -> 16000) must FAIL: exit != 0, FAIL line, no EXE line, FAILED
#    marker, SUMMARY 'RESULT FAIL' and never 'RESULT PASS'.
# T2 positive control: the lock source builds with 'pins OK', exit 0, SUMMARY 'RESULT PASS'.
# T3 blocker, pack: speed_pack on the mutant stops with exit 3 and writes no candidate file.
# T4 SHOULD 1: Write-OspdLf refuses to overwrite; abba writes a run-unique summary file name (code check).
# T5 SHOULD 2: ConvertTo-OspdFen completes placement-only FENs to six fields; the lock accepts the result.
# T6 SHOULD 3: the 300-position TSV header carries the md5 of its source PGN (recomputed here).
# Builds use the fast 'o3' variant (one g++ call each) on CPUs 0-1 at Idle. Exit 0 only if every test passes.
$ErrorActionPreference = 'Stop'
$Tools = Join-Path (Split-Path -Parent $PSScriptRoot) 'tools'
. "$Tools\uci_lib.ps1"
Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
$run = New-OspdRunId
$log = "F:\ospd\logs\test_cr_637b_$run.log"
$results = New-Object System.Collections.Generic.List[string]
function Check([string]$Id, [bool]$Ok, [string]$What) {
  $s = 'FAIL'; if ($Ok) { $s = 'PASS' }
  $line = "{0} {1} {2}" -f $Id, $s, $What
  $results.Add($line); Write-Output $line; Add-OspdLf $log $line
}
Add-OspdLf $log "test_cr_637b run $run start $(Get-OspdNow)"
$mut = 'F:\ospd\src\mut_histmax'; $lock = $script:OspdLockSrc

# T1
$o1 = @(& "$Tools\build_variants.ps1" -SrcDir $mut -Tag "tcr1_$run" -Variant o3); $rc1 = $LASTEXITCODE
$o1 | ForEach-Object { Add-OspdLf $log "  T1> $_" }
$d1 = "F:\ospd\builds\tcr1_${run}_o3"
$sum1 = ''; if (Test-Path "$d1\SUMMARY.txt") { $sum1 = Get-Content "$d1\SUMMARY.txt" -Raw }
Check 'T1a' ($rc1 -ne 0) "mutant build exit code $rc1 (want != 0)"
Check 'T1b' (@($o1 | Where-Object { $_ -like 'EXE *' }).Count -eq 0 -and @($o1 | Where-Object { $_ -like 'FAIL o3*pins DIFF*' }).Count -eq 1) 'no EXE line; one FAIL line naming the pin DIFF'
Check 'T1c' (Test-Path "$d1\FAILED") 'FAILED marker written'
Check 'T1d' ($sum1 -match 'RESULT FAIL' -and $sum1 -notmatch 'RESULT PASS') 'SUMMARY says RESULT FAIL, never RESULT PASS'

# T2
$o2 = @(& "$Tools\build_variants.ps1" -SrcDir $lock -Tag "tcr2_$run" -Variant o3); $rc2 = $LASTEXITCODE
$o2 | ForEach-Object { Add-OspdLf $log "  T2> $_" }
$d2 = "F:\ospd\builds\tcr2_${run}_o3"
$sum2 = ''; if (Test-Path "$d2\SUMMARY.txt") { $sum2 = Get-Content "$d2\SUMMARY.txt" -Raw }
Check 'T2a' ($rc2 -eq 0 -and @($o2 | Where-Object { $_ -like 'EXE o3 * pins OK *' }).Count -eq 1) "lock build exit $rc2 with 'pins OK'"
Check 'T2b' ($sum2 -match 'RESULT PASS' -and -not (Test-Path "$d2\FAILED")) 'SUMMARY RESULT PASS, no FAILED marker'

# T3
$name3 = "tcr3_$run"
$o3 = @(& "$Tools\speed_pack.ps1" -SrcDir $mut -Name $name3 -Variant o3 -SkipAbba); $rc3 = $LASTEXITCODE
$o3 | ForEach-Object { Add-OspdLf $log "  T3> $_" }
$cand3 = Join-Path (Split-Path -Parent $PSScriptRoot) "candidates\$name3.md"
Check 'T3a' ($rc3 -eq 3) "speed_pack on the mutant exit $rc3 (want 3)"
Check 'T3b' (-not (Test-Path $cand3) -and @($o3 | Where-Object { $_ -match 'BUILD FAILED|PINS NOT OK' }).Count -ge 1) 'no candidate file; pack log names the failed build'

# T4
$tmp = "F:\ospd\tmp\tcr4_$run.txt"
Write-OspdLf $tmp @('first')
$threw = $false; try { Write-OspdLf $tmp @('second') } catch { $threw = ($_.Exception.Message -like 'refusing to overwrite*') }
Check 'T4a' ($threw -and ((Get-Content $tmp) -eq 'first')) 'Write-OspdLf refuses to overwrite and keeps the first content'
$abbaSrc = Get-Content "$Tools\abba.ps1" -Raw
Check 'T4b' ($abbaSrc -match 'summary_\{0\}\.txt' -and $abbaSrc -match 'New-OspdRunId') 'abba writes summary_<run id>.txt per run'

# T5
$f1 = ConvertTo-OspdFen 'rnbqkb1r/2ppnppp/pp2p3/8/1P6/3PBN2/P1P1PPPP/RN1QKB1R'
$f2 = ConvertTo-OspdFen 'rnbqkb1r/2ppnppp/pp2p3/8/1P6/3PBN2/P1P1PPPP/RN1QKB1R b KQkq - 1 5'
$bad = $false; try { $null = ConvertTo-OspdFen '8/8/8 w' } catch { $bad = $true }
Check 'T5a' ($f1 -eq 'rnbqkb1r/2ppnppp/pp2p3/8/1P6/3PBN2/P1P1PPPP/RN1QKB1R w - - 0 1' -and $f2.EndsWith(' b KQkq - 1 5') -and $bad) 'placement-only -> side to move w + defaults; full FEN unchanged; bad FEN throws'
$e = Start-OspdEngine $script:OspdLockExe "F:\ospd\logs\test_cr_637b_$run.uci.log"
$null = Initialize-OspdEngine $e @('OwnBook=false')
$okFen = $true; try { $r5 = Invoke-OspdSearch $e $f1 'depth 4' -NewGame } catch { $okFen = $false }
$rawRejected = $false; try { $null = Invoke-OspdSearch $e 'rnbqkb1r/2ppnppp/pp2p3/8/1P6/3PBN2/P1P1PPPP/RN1QKB1R' 'depth 1' -NewGame } catch { $rawRejected = ($_.Exception.Message -like 'engine rejected*') }
$null = Stop-OspdEngine $e
Check 'T5b' ($okFen -and $r5.Best -and $rawRejected) "lock accepts the completed FEN (bestmove $($r5.Best)); the raw placement-only FEN is detected as rejected"

# T6
$tsv = Join-Path (Split-Path -Parent $PSScriptRoot) 'data\game_positions_300.tsv'
$h = (Get-Content $tsv -TotalCount 1)
$m = [regex]::Match($h, '^# pgn_positions\.py source (\S+) md5 ([0-9a-f]{32})$')
$ok6 = $false
if ($m.Success -and (Test-Path $m.Groups[1].Value)) { $ok6 = ((Get-OspdMd5 $m.Groups[1].Value) -eq $m.Groups[2].Value) }
Check 'T6' $ok6 "TSV header names the source PGN and its md5 matches ($($m.Groups[2].Value))"

$nf = @($results | Where-Object { $_ -match '^T\S+ FAIL ' }).Count   # status field only (a PASS line may name FAIL in its text)
$fin = "test_cr_637b run $run end $(Get-OspdNow): $($results.Count - $nf) / $($results.Count) PASS"
Write-Output $fin; Add-OspdLf $log $fin
if ($nf) { exit 1 } else { exit 0 }
