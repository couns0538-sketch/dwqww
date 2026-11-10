# selftest.ps1 - runs every no-engine test of the pack and writes TESTS.md (Windows PowerShell 5.1).
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File selftest.ps1 [-Scratch <dir>] [-Mask 0xF000]
# Tests: R9 saved-run replay equivalence, harness (synthetic/replay/crash at every boundary/refusals/rollback),
# confirmation pack (statistical controls, crash boundaries, holdout misuse, replay, audit). No engine, no games.
param(
    [string]$Scratch = 'D:\forge_jobs_20261107\opus3\out\tests\selftest',
    [long]$Mask = 0xF000,
    [string]$Python = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe',
    [string]$TempDir = 'D:\forge_jobs_20261107\opus3\tmp'
)
$ErrorActionPreference = 'Stop'
$me = [System.Diagnostics.Process]::GetCurrentProcess()
$me.PriorityClass = 'Idle'; $me.ProcessorAffinity = [IntPtr]$Mask; $me.Refresh()
if ([long]$me.ProcessorAffinity -ne $Mask -or "$($me.PriorityClass)" -ne 'Idle') { throw 'placement not applied' }
if ($TempDir) { New-Item -ItemType Directory -Force -Path $TempDir | Out-Null; $env:TEMP = $TempDir; $env:TMP = $TempDir }
$env:PYTHONDONTWRITEBYTECODE = '1'
$pack = Split-Path -Parent $PSScriptRoot
$tests = Join-Path $pack 'tests'
$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$base = Join-Path $Scratch $stamp
New-Item -ItemType Directory -Force -Path $base | Out-Null
$rows = @()
# Windows PowerShell 5.1 turns a native command's stderr line into an error record; with 'Stop' the first one would
# abort the script before TESTS.md is written. Run the suites under 'Continue' and keep every line as text.
$ErrorActionPreference = 'Continue'
$r9 = & $Python -I -B (Join-Path $tests 'test_r9_equivalence.py') 2>&1 | ForEach-Object { "$_" }
$rows += [pscustomobject]@{ suite = 'R9 saved-run replay equivalence'; exit = $LASTEXITCODE; lines = @($r9) }
$hs = & $Python -I -B (Join-Path $tests 'test_spsa_harness.py') (Join-Path $base 'harness') (Join-Path $base 'harness.json') 2>&1 | ForEach-Object { "$_" }
$rows += [pscustomobject]@{ suite = 'SPSA harness'; exit = $LASTEXITCODE; lines = @($hs) }
$cf = & $Python -I -B (Join-Path $tests 'test_confirm.py') (Join-Path $base 'confirm') (Join-Path $base 'confirm.json') 2>&1 | ForEach-Object { "$_" }
$rows += [pscustomobject]@{ suite = 'Confirmation pack'; exit = $LASTEXITCODE; lines = @($cf) }
$ErrorActionPreference = 'Stop'
$md = @('# TESTS (selftest.ps1)', '', "Run: $stamp (UTC, PC clock - see STATUS.md for the clock offset). Scratch: $base",
        'All tests use synthetic outcomes or saved/generated PGNs: no engine, no games, no Elo.', '')
foreach ($r in $rows) {
    $md += "## $($r.suite): $(if ($r.exit -eq 0) { 'PASS' } else { 'FAIL' }) (exit $($r.exit))"
    $md += ''
    $md += '```'
    $md += ($r.lines | ForEach-Object { "$_" })
    $md += '```'
    $md += ''
}
$ok = -not ($rows | Where-Object { $_.exit -ne 0 })
[IO.File]::WriteAllText((Join-Path $pack 'TESTS.md'), (($md -join "`n") + "`n"))
"selftest: $(if ($ok) { 'ALL PASS' } else { 'FAILURES' }); TESTS.md written"
if ($ok) { exit 0 } else { exit 1 }
