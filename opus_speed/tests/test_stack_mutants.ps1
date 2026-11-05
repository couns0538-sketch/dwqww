# test_stack_mutants.ps1 - deliberate-failure test on every stacked source (speed job follow-up, PowerShell 5.1).
# Per stack, the pipeline must fail closed before any ABBA when the stacked source carries a move-order mutant:
#   (K1) source + switches of the stack's own pack (first line of F:\ospd\packs\<stack>\pack.log: src + defines);
#   (K2) fresh copy of that LF source + opus_speed\patches\mutant_pickbest_ge.patch (pick_best tie-break '>' -> '>=')
#        with GNU patch -p1 -F0 after a dry run, the mutant line present exactly once (if the patch does not apply,
#        the one-constant mutant mutant_histmax.patch is used and named in the line);
#   (K3) speed_pack -Define <the pack's defines> -Variant lp_v1 -Quick on the copy exits 3 (build pin DIFF or NOT
#        BIT-EXACT), and leaves no abba_d* folder and no candidate file (= test_moveorder_mutant M1 per stack).
# Verify builds only. usage: powershell -NoProfile -ExecutionPolicy Bypass -File test_stack_mutants.ps1
#   [-Stacks stack_w1,..] ; exit 0 = every check PASS, 1 = a FAIL or an error.
param([string[]]$Stacks = @('stack_w1', 'stack_w2', 'stack_w3', 'stack_w4', 'stack_w5', 'trial_w6'))
$ErrorActionPreference = 'Stop'
$Repo = Split-Path -Parent $PSScriptRoot
$Tools = Join-Path $Repo 'tools'
. "$Tools\uci_lib.ps1"
$Stacks = @($Stacks | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
$PatchExe = 'C:\Program Files\Git\usr\bin\patch.exe'
Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
$run = New-OspdRunId
$outRoot = "F:\ospd\qa2\mutants\$run"; New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
$log = Join-Path $outRoot 'test_stack_mutants.log'
$results = New-Object System.Collections.Generic.List[string]
function Check([string]$Id, [bool]$Ok, [string]$What) {
  $s = 'FAIL'; if ($Ok) { $s = 'PASS' }
  $line = "{0} {1} {2}" -f $Id, $s, $What; $results.Add($line); Write-Output $line; Add-OspdLf $log $line
}
function Invoke-Tool([string]$Exe, [object[]]$ToolArgs) {
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $o = @(& $Exe @ToolArgs 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { $ErrorActionPreference = $eap }
  return [pscustomobject]@{ Rc = $rc; Out = $o }
}
Add-OspdLf $log "test_stack_mutants run $run start $(Get-OspdNow); stacks $($Stacks -join ',')"
$tsv = @("stack`tsource`tdefines`tmutant`tspeed_pack_exit`tabba_folders`tcandidate_file`tstop_line`tverdict")
foreach ($s in $Stacks) {
  $head = Get-Content "F:\ospd\packs\$s\pack.log" -TotalCount 1
  $m = [regex]::Match($head, ' src (\S+) variant \S+ defines \[([^\]]*)\]')
  Check "$s.K1" $m.Success "pack source and defines read from F:\ospd\packs\$s\pack.log"
  if (-not $m.Success) { $tsv += "$s`t-`t-`t-`t-`t-`t-`t-`tFAIL"; continue }
  $src = $m.Groups[1].Value.Replace('/', '\'); $defs = @($m.Groups[2].Value -split ' ' | Where-Object { $_ })
  $dst = "F:\ospd\src\mutpb_${s}_$run"
  $null = Assert-OspdDisk -PlannedGB 0.05
  New-Item -ItemType Directory -Path $dst | Out-Null
  foreach ($sub in 'include', 'src') { Copy-Item -Recurse -LiteralPath (Join-Path $src $sub) -Destination (Join-Path $dst $sub) }
  Get-ChildItem -Recurse -File $dst | ForEach-Object { $_.IsReadOnly = $false }
  $mutant = 'mutant_pickbest_ge'
  $pf = Join-Path $Repo "patches\$mutant.patch"
  $dry = Invoke-Tool $PatchExe @('-p1', '-F0', '--dry-run', '-d', $dst, '-i', $pf)
  if ($dry.Rc -ne 0) {
    $mutant = 'mutant_histmax'; $pf = Join-Path $Repo "patches\$mutant.patch"
    $dry = Invoke-Tool $PatchExe @('-p1', '-F0', '--dry-run', '-d', $dst, '-i', $pf)
  }
  $ap = $null; if ($dry.Rc -eq 0) { $ap = Invoke-Tool $PatchExe @('-p1', '-F0', '-d', $dst, '-i', $pf) }
  @($dry.Out) + @(if ($ap) { $ap.Out }) | ForEach-Object { Add-OspdLf $log "  $s K2> $_" }
  $want = 'if (moves_[i].score >= moves_[best].score) best = i;'; if ($mutant -eq 'mutant_histmax') { $want = 'constexpr int HistoryMax = 16000;' }
  $hits = @(Select-String -LiteralPath (Join-Path $dst 'src\search.cpp') -SimpleMatch $want).Count
  Check "$s.K2" ($null -ne $ap -and $ap.Rc -eq 0 -and $hits -eq 1) "$mutant applied with patch -p1 -F0 to a copy of $src (mutant line found $hits time(s))"
  if ($null -eq $ap -or $ap.Rc -ne 0 -or $hits -ne 1) { $tsv += "$s`t$src`t$($defs -join ' ')`t$mutant`t-`t-`t-`t-`tFAIL"; continue }
  $name = "mutpb_${s}_$run"
  $so = @(& "$Tools\speed_pack.ps1" -SrcDir $dst -Name $name -Define ($defs -join ',') -Variant lp_v1 -Quick); $src3 = $LASTEXITCODE
  $so | ForEach-Object { Add-OspdLf $log "  $s K3> $_" }
  $abba = @(Get-ChildItem "F:\ospd\packs\$name" -Directory -Filter 'abba_d*' -ErrorAction SilentlyContinue).Count
  $cand = @(Get-ChildItem (Join-Path $Repo 'candidates') -Filter "$name*.md" -ErrorAction SilentlyContinue).Count
  $stop = @($so | Where-Object { "$_" -match 'BUILD FAILED|NOT BIT-EXACT|PINS NOT OK' } | Select-Object -First 1) -join ''
  Check "$s.K3" ($src3 -eq 3 -and $abba -eq 0 -and $cand -eq 0 -and $stop) "speed_pack exit $src3 (want 3), abba folders $abba, candidate files $cand; $($stop.Substring(0, [Math]::Min(160, $stop.Length)))"
  $v = 'FAIL'; if ($src3 -eq 3 -and $abba -eq 0 -and $cand -eq 0 -and $stop) { $v = 'PASS' }
  $tsv += ("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}`t{7}`t{8}" -f $s, $src, ($defs -join ' '), $mutant, $src3, $abba, $cand, $stop.Replace("`t", ' '), $v)
}
Write-OspdLf (Join-Path $outRoot 'results.tsv') $tsv
$nf = @($results | Where-Object { $_ -match '^\S+ FAIL ' }).Count
$fin = "test_stack_mutants run $run end $(Get-OspdNow): $($results.Count - $nf) / $($results.Count) PASS; results $outRoot\results.tsv"
Write-Output $fin; Add-OspdLf $log $fin
if ($nf) { exit 1 } else { exit 0 }
