# test_stack_poison.ps1 - patch review QA test 5 on every stacked source (speed job follow-up, PowerShell 5.1).
# Per stack: (P1) poison copy of its kit source (tools\make_poison.py: the authors' own 0xA5 fill of every array that
# lost its zero fill, on the stack's src_kit with all its switches ON); (P2) plain o3 build with
# -Define FORGE_SPD_NO_ZERO_MOVELISTS_POISON=1 (build_variants: quick pins bench 11/13/16 fail closed); (P3) the fill is
# compiled in: g++ -E of the copy's search.cpp with the same define holds the six 0xA5 fills (objdump count of 0xa5
# immediates in the exe reported for information); (P4) bitexact_check -Quick -SkipSan on the poison exe: L1 bench net
# on + off d11-d22, L2 perft, L3 2,000 FENs at depth 13 vs the cached lock reference -> VERDICT BIT-EXACT, and the
# LOCK PROOF INCOMPLETE line follows it. A read of an unwritten slot would see 0xA5 garbage and change nodes.
# Verify builds only, never for QA. usage: powershell -NoProfile -ExecutionPolicy Bypass -File test_stack_poison.ps1
#   [-Stacks stack_w1,..] ; exit 0 = every stack PASS, 1 = a FAIL or an error.
#   -Py <python.exe> (or set OSPD_PY): the interpreter for make_poison.py (stdlib only); none is hard-coded here.
param([string[]]$Stacks = @('stack_w1', 'stack_w2', 'stack_w3', 'stack_w4', 'stack_w5', 'trial_w6'), [string]$Py = $env:OSPD_PY)
$ErrorActionPreference = 'Stop'
$Tools = Join-Path (Split-Path -Parent $PSScriptRoot) 'tools'
. "$Tools\uci_lib.ps1"
$Stacks = @($Stacks | ForEach-Object { $_ -split ',' } | Where-Object { $_ })
if (-not $Py) { throw 'test_stack_poison: pass -Py <python.exe> or set OSPD_PY (no interpreter is hard-coded)' }
$Gpp = 'C:\msys64\ucrt64\bin\g++.exe'; $Objdump = 'C:\msys64\ucrt64\bin\objdump.exe'
$env:PATH = 'C:\msys64\ucrt64\bin;' + $env:PATH
Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
$run = New-OspdRunId
$outRoot = "F:\ospd\qa2\poison\$run"; New-Item -ItemType Directory -Force -Path $outRoot | Out-Null
$log = Join-Path $outRoot 'test_stack_poison.log'
$results = New-Object System.Collections.Generic.List[string]
function Check([string]$Id, [bool]$Ok, [string]$What) {
  $s = 'FAIL'; if ($Ok) { $s = 'PASS' }
  $line = "{0} {1} {2}" -f $Id, $s, $What; $results.Add($line); Write-Output $line; Add-OspdLf $log $line
}
function Invoke-Tool([string]$Exe, [object[]]$ToolArgs) {
  # native tool with stderr merged; 'Continue' so a stderr line is not a terminating error under PS 5.1
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { $o = @(& $Exe @ToolArgs 2>&1 | ForEach-Object { "$_" }); $rc = $LASTEXITCODE } finally { $ErrorActionPreference = $eap }
  return [pscustomobject]@{ Rc = $rc; Out = $o }
}
Add-OspdLf $log "test_stack_poison run $run start $(Get-OspdNow); stacks $($Stacks -join ',')"
$tsv = @("stack`tpoison_src`texe`tsha256`tpins`tpreproc_fills`tobjdump_a5_imm`tbitexact`tverdict")
foreach ($s in $Stacks) {
  $src = "F:\ospd\packs\$s\src_kit"; $dst = "F:\ospd\src\poison_${s}_$run"; $tag = "poison_${s}_$run"
  $null = Assert-OspdDisk -PlannedGB 0.1
  $mp = Invoke-Tool $Py @('-I', '-B', (Join-Path $Tools 'make_poison.py'), $src, $dst)
  $mp.Out | ForEach-Object { Add-OspdLf $log "  $s P1> $_" }
  Check "$s.P1" ($mp.Rc -eq 0) "poison copy $dst (make_poison exit $($mp.Rc))"
  if ($mp.Rc -ne 0) { $tsv += "$s`t$dst`t-`t-`t-`t-`t-`t-`tFAIL"; continue }
  $bo = @(& "$Tools\build_variants.ps1" -SrcDir $dst -Tag $tag -Variant o3 -Define 'FORGE_SPD_NO_ZERO_MOVELISTS_POISON=1'); $brc = $LASTEXITCODE
  $bo | ForEach-Object { Add-OspdLf $log "  $s P2> $_" }
  $em = $bo | ForEach-Object { [regex]::Match("$_", '^EXE o3 (\S+) sha256 (\S+) md5 (\S+) pins OK') } | Where-Object { $_.Success } | Select-Object -First 1
  Check "$s.P2" ($brc -eq 0 -and $null -ne $em) "o3 poison build exit $brc, quick pins $(if ($em) { 'OK' } else { 'NOT OK' })"
  if ($brc -ne 0 -or $null -eq $em) { $tsv += "$s`t$dst`t-`t-`tFAIL`t-`t-`t-`tFAIL"; continue }
  $exe = $em.Groups[1].Value; $sha = $em.Groups[2].Value
  # P3: the define reaches the code (preprocessor view of the poison copy), plus an objdump count for information.
  # -march=znver5 as in the build: a SLIDER_PEXT source stops at its own '#error' without __BMI2__ (first run, 14:2x)
  Push-Location $dst
  try { $pp = Invoke-Tool $Gpp @('-std=c++20', '-E', '-P', '-march=znver5', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS_POISON=1', '-Iinclude', 'src\search.cpp') } finally { Pop-Location }
  $fills = @($pp.Out | Where-Object { $_ -match 'memset\(&\w+, 0xA5' }).Count
  $od = Invoke-Tool $Objdump @('-d', '--no-show-raw-insn', $exe)
  $a5 = @($od.Out | Where-Object { $_ -match '\$0xa5\b|\$0xffffffa5\b|0xa5a5a5a5' }).Count
  Check "$s.P3" ($pp.Rc -eq 0 -and $fills -eq 6) "preprocessed search.cpp holds $fills of 6 0xA5 fills (g++ -E exit $($pp.Rc)); 0xa5 immediates in the exe: $a5"
  $bxOut = Join-Path $outRoot "$s\bitexact"; New-Item -ItemType Directory -Force -Path (Split-Path $bxOut) | Out-Null
  $xo = @(& "$Tools\bitexact_check.ps1" -Cand $exe -Out $bxOut -Quick -SkipSan); $xrc = $LASTEXITCODE
  $xo | ForEach-Object { Add-OspdLf $log "  $s P4> $_" }
  $v = @($xo | Where-Object { $_ -like 'VERDICT*' }) -join ' '
  $lp = @($xo | Where-Object { $_ -like 'LOCK PROOF INCOMPLETE:*' }).Count
  $ok4 = ($xrc -eq 0 -and $v -like 'VERDICT BIT-EXACT*' -and $lp -eq 1)
  Check "$s.P4" $ok4 "bitexact_check exit $xrc, $v; LOCK PROOF INCOMPLETE line $lp"
  # the TSV verdict needs every check line, P3's g++ -E exit code included (the 14:17 run wrote PASS rows for w4-w6
  # while their P3 lines said FAIL)
  $all = ($mp.Rc -eq 0 -and $brc -eq 0 -and $pp.Rc -eq 0 -and $fills -eq 6 -and $ok4)
  $tsv += ("{0}`t{1}`t{2}`t{3}`tOK`t{4}`t{5}`t{6}`t{7}" -f $s, $dst, $exe, $sha, $fills, $a5, $v, $(if ($all) { 'PASS' } else { 'FAIL' }))
}
Write-OspdLf (Join-Path $outRoot 'results.tsv') $tsv
$nf = @($results | Where-Object { $_ -match '^\S+ FAIL ' }).Count
$fin = "test_stack_poison run $run end $(Get-OspdNow): $($results.Count - $nf) / $($results.Count) PASS; results $outRoot\results.tsv"
Write-Output $fin; Add-OspdLf $log $fin
if ($nf) { exit 1 } else { exit 0 }
