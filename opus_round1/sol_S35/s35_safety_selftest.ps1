#requires -Version 7.0
# s35_safety_selftest.ps1 (S35, opus 2026-10-27): the harness must REFUSE unsafe inputs before running anything.
# Builds unsafe watcher variants from the v2 copy inside -WorkDir and checks that every run exits non-zero with a
# refusal message and that no child watcher was started. Writes only under -WorkDir.
param([Parameter(Mandatory = $true)][string]$WorkDir)
$ErrorActionPreference = 'Stop'
$h = Join-Path $PSScriptRoot 'forge_sol_S35_test_watcher_locked_log_20261027.ps1'
$v2 = Join-Path $PSScriptRoot 'fixtures\watchers\conc7_watch.v2_conc8_20261025.ps1'
$WorkDir = [IO.Path]::GetFullPath($WorkDir); New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$src = [IO.File]::ReadAllText($v2)
$cases = [ordered]@{
  'second live gate-root literal' = $src + "`n`$x='D:\grok-pc-data\forge_push'`n"
  'mutex literal missing'         = $src.Replace("'Global\forge_conc7_watch'", "'forge_conc7_watch'")
  'unstubbed Remove-Item'         = $src.Replace('function Temps(){', "function Temps(){ Remove-Item -LiteralPath `$MANF -WhatIf;")
  'live F:\forge_out path'        = $src + "`n`$y='F:\forge_out\forge_push\x.txt'`n"
}
$pw = Join-Path $PSHOME $(if ($IsWindows) { 'pwsh.exe' } else { 'pwsh' })
$fail = 0; $i = 0
foreach ($k in $cases.Keys) {
  $i++; $f = Join-Path $WorkDir ("unsafe_$i.ps1"); [IO.File]::WriteAllText($f, $cases[$k], [Text.UTF8Encoding]::new($true))
  $wd = Join-Path $WorkDir "wd_$i"
  $out = & $pw -NoProfile -NonInteractive -File $h -Watcher $f -Conc 8 -Scenarios S1 -WorkDir $wd 2>&1 | Out-String
  $code = $LASTEXITCODE
  $started = @(Get-ChildItem -LiteralPath $wd -Recurse -Filter 'watcher_patched.ps1' -ErrorAction SilentlyContinue).Count
  $ok = ($code -ne 0 -and $out -match 'patch refused' -and $started -eq 0)
  if (-not $ok) { $fail++ }
  "{0} case '{1}': exit {2}, refusal '{3}', patched copies written {4}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $k, $code, ([regex]::Match($out, 'patch refused[^\r\n]*').Value), $started
}
# a WorkDir that names a live root pattern must be refused before anything is created (path kept inside our scratch)
$bad = Join-Path $WorkDir 'Global\x'
$out = & $pw -NoProfile -NonInteractive -File $h -Watcher $v2 -Conc 8 -Scenarios S1 -WorkDir $bad 2>&1 | Out-String
$code = $LASTEXITCODE; $ok = ($code -ne 0 -and $out -match 'refusing WorkDir' -and -not (Test-Path -LiteralPath $bad)); if (-not $ok) { $fail++ }
"{0} case 'WorkDir matching a live-root pattern': exit {1}, created {2}" -f $(if ($ok) { 'PASS' } else { 'FAIL' }), $code, (Test-Path -LiteralPath $bad)
"safety self-test: $(if ($fail) { "FAIL ($fail case(s))" } else { 'PASS (5/5 refused)' })"
exit $fail
