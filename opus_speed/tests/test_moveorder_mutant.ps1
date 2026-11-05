# test_moveorder_mutant.ps1 - Job B deliberate-failure test (PowerShell 5.1): a change that alters move order must fail
# the bit-exact proof, so no ABBA ever starts for it.
# Mutant: F:\ospd\src\mut_pickbest_ge = lock source with pick_best's tie-break '>' changed to '>=' (patch
# opus_speed/patches/mutant_pickbest_ge.patch): equal scores now pick the LAST maximum instead of the first.
# M1 the pipeline: speed_pack on the mutant stops with exit 3 before any ABBA (no abba_d* folder, no candidate file).
# M2 the proof itself: bitexact_check on the mutant's kept LTO+PGO exe ends 'VERDICT NOT BIT-EXACT' with exit 3.
$ErrorActionPreference = 'Stop'
$Tools = Join-Path (Split-Path -Parent $PSScriptRoot) 'tools'
. "$Tools\uci_lib.ps1"
Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
$run = New-OspdRunId
$log = "F:\ospd\logs\test_moveorder_mutant_$run.log"
$results = New-Object System.Collections.Generic.List[string]
function Check([string]$Id, [bool]$Ok, [string]$What) {
  $s = 'FAIL'; if ($Ok) { $s = 'PASS' }
  $line = "{0} {1} {2}" -f $Id, $s, $What; $results.Add($line); Write-Output $line; Add-OspdLf $log $line
}
Add-OspdLf $log "test_moveorder_mutant run $run start $(Get-OspdNow)"
$name = "tmo_$run"
$o1 = @(& "$Tools\speed_pack.ps1" -SrcDir 'F:\ospd\src\mut_pickbest_ge' -Name $name -Variant lp_v1 -Quick); $rc1 = $LASTEXITCODE
$o1 | ForEach-Object { Add-OspdLf $log "  M1> $_" }
$pack = "F:\ospd\packs\$name"
$abbaDirs = @(Get-ChildItem $pack -Directory -Filter 'abba_d*' -ErrorAction SilentlyContinue)
$candFile = Join-Path (Split-Path -Parent $PSScriptRoot) "candidates\$name.md"
Check 'M1a' ($rc1 -eq 3) "speed_pack on the move-order mutant exit $rc1 (want 3)"
Check 'M1b' ($abbaDirs.Count -eq 0 -and -not (Test-Path $candFile)) 'no ABBA folder and no candidate file'
$exe = "F:\ospd\builds\pack_${name}_lp_v1_pc1\src_copy\forge_lp_v1.exe"
if (Test-Path $exe) {
  $o2 = @(& "$Tools\bitexact_check.ps1" -Cand $exe -Out "F:\ospd\logs\bx_moveorder_$run" -Quick -SkipSan); $rc2 = $LASTEXITCODE
  $o2 | ForEach-Object { Add-OspdLf $log "  M2> $_" }
  $v = @($o2 | Where-Object { $_ -like 'VERDICT*' }) -join ' '
  Check 'M2' ($rc2 -eq 3 -and $v -like 'VERDICT NOT BIT-EXACT*') "bitexact_check on the mutant exe: exit $rc2, $v"
} else { Check 'M2' $false "mutant exe missing: $exe" }
$nf = @($results | Where-Object { $_ -match '^M\S+ FAIL ' }).Count
$fin = "test_moveorder_mutant run $run end $(Get-OspdNow): $($results.Count - $nf) / $($results.Count) PASS"
Write-Output $fin; Add-OspdLf $log $fin
if ($nf) { exit 1 } else { exit 0 }
