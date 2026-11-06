# test_cr_should_w8.ps1 - tests for the Code Review SHOULD tooling notes 1 and 2 (speed job W8, PowerShell 5.1).
# W1 'warm_identity invalid-FEN': the lock exe vs itself on 4 FENs, one of them placement-only (the lock answers
#    'info string invalid FEN: FEN must contain six fields' and keeps the previous position): warm_identity.py must exit 1
#    with an ERROR line naming the rejected FEN (index 2) and print no IDENTICAL line; W1c positive control: the same list
#    without the bad line -> exit 0 and IDENTICAL with 3 searches.
# W2 'patchrev soak mask 0xF': while the timing mutex Local\ospd_abba_timing is held (by this test, or by a running ABBA),
#    patchrev_qa.py soak --mask 0xF --mutex-wait-min 0 must refuse before any exe check or engine start (exit != 0, the
#    refusal names the mutex, no lock.log in its out folder); W2b hold_timing_mutex() is a no-op for a mask inside 0x3 and,
#    for 0xF, acquires + releases when the mutex is free or refuses when it is held (no engine).
# Engines: the lock exe only, 7 x go nodes 2000 + bench 1 / bench 13 (a few seconds), CPUs 0-1 at Idle. Run it from Git
# Bash: powershell.exe -NoProfile -ExecutionPolicy Bypass -File opus_speed\tests\test_cr_should_w8.ps1 ; exit 0 = all PASS.
$ErrorActionPreference = 'Stop'
$Tools = Join-Path (Split-Path -Parent $PSScriptRoot) 'tools'
. "$Tools\uci_lib.ps1"
Set-OspdPlacement -Mask 0x3 -Priority 'Idle'
$Py = 'C:\Users\Administrator\grok-pc\nnue\.venv\Scripts\python.exe'
$run = New-OspdRunId
$outRoot = "F:\ospd\logs\cr_should_w8_$run"; New-Item -ItemType Directory -Path $outRoot | Out-Null
$log = Join-Path $outRoot 'test.log'
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
Add-OspdLf $log "test_cr_should_w8 run $run start $(Get-OspdNow)"
$lock = $script:OspdLockExe
# three six-field FENs (= data\fens_12k_v2.txt rows 1-3) and one placement-only line the lock rejects
$good = @('rnbqkb1r/2ppnppp/pp2p3/8/1P6/3PBN2/P1P1PPPP/RN1QKB1R w KQkq - 1 5',
  'rn1qkb1r/1bppnppp/pp2p3/8/1P6/2PPBNP1/P3PP1P/RN1QKB1R b KQkq - 0 6',
  'rn1qk2r/1bppnppp/pp2p3/8/1P6/2PP1NP1/P3PP1P/RN1QKB1R w KQkq - 0 9')
$badFen = 'rnbqkb1r/2ppnppp/pp2p3/8/1P6/3PBN2/P1P1PPPP/RN1QKB1R'

# W1: one rejected FEN in the list -> exit 1, ERROR names it, no IDENTICAL
$f1 = Join-Path $outRoot 'fens_with_bad.txt'; Write-OspdLf $f1 @($good[0], $good[1], $badFen, $good[2])
$r1 = Invoke-Tool $Py @('-I', '-B', (Join-Path $Tools 'warm_identity.py'), $lock, $lock, $f1, (Join-Path $outRoot 'w1'), '--n', '4', '--nodes', '2000')
$r1.Out | ForEach-Object { Add-OspdLf $log "  W1> $_" }
$t1 = $r1.Out -join ' '
Check 'W1a' ($r1.Rc -eq 1 -and $t1 -match 'ERROR: engine rejected FEN 2 ' -and $t1 -match 'info string invalid FEN') "warm_identity with a placement-only FEN at index 2: exit $($r1.Rc) (want 1), ERROR names FEN 2 and the engine's invalid-FEN line"
Check 'W1b' ($t1 -notmatch 'IDENTICAL') 'no IDENTICAL line for the bad list'
# W1c positive control: the three valid FENs -> exit 0, IDENTICAL, 3 searches
$f2 = Join-Path $outRoot 'fens_good.txt'; Write-OspdLf $f2 $good
$r2 = Invoke-Tool $Py @('-I', '-B', (Join-Path $Tools 'warm_identity.py'), $lock, $lock, $f2, (Join-Path $outRoot 'w1c'), '--n', '3', '--nodes', '2000')
$r2.Out | ForEach-Object { Add-OspdLf $log "  W1c> $_" }
$t2 = $r2.Out -join ' '
Check 'W1c' ($r2.Rc -eq 0 -and $t2 -match 'IDENTICAL: .* 3 searches' -and $t2 -match 'ref: 3 distinct result rows') "positive control: exit $($r2.Rc) (want 0), IDENTICAL with 3 searches, 3 distinct ref rows"

# W2: the soak's 0xF (any mask touching CPUs 2-3) must be refused while the timing mutex is held
$mutex = New-Object System.Threading.Mutex($false, 'Local\ospd_abba_timing')
$held = $false
try { $held = $mutex.WaitOne(0) } catch [System.Threading.AbandonedMutexException] { $held = $true }
try {
  # a stack name that does not exist: if the gate ever let the run through, it would stop at 'missing exe' before any engine
  $r3 = Invoke-Tool $Py @('-I', '-B', (Join-Path $Tools 'patchrev_qa.py'), 'soak', '--out', (Join-Path $outRoot 'w2'), '--mask', '0xF', '--stacks', 'no_such_stack_w8', '--movetime', '20', '--mutex-wait-min', '0')
  $r3.Out | ForEach-Object { Add-OspdLf $log "  W2> $_" }
  $t3 = $r3.Out -join ' '
  Check 'W2a' ($r3.Rc -ne 0 -and $t3 -match 'ospd_abba_timing' -and $t3 -notmatch 'missing exe' -and -not (Test-Path (Join-Path $outRoot 'w2\lock.log'))) "soak --mask 0xF with the timing mutex held (by this test: $held): exit $($r3.Rc) (want != 0), the refusal names the mutex, no exe check, no engine log"
} finally { if ($held) { $mutex.ReleaseMutex() } }
$mutex.Dispose()
# W2b: the gate function alone (no engine): no-op inside 0x3; 0xF acquires + releases when free, refuses when held
# the snippet goes through a file: PS 5.1 strips embedded double quotes from native arguments (a -c one-liner with
# exec("...") arrived without its quotes and failed with a SyntaxError on 2026-11-05 18:37)
$pyFile = Join-Path $outRoot 'w2b_gate.py'
Write-OspdLf $pyFile @('import sys', "sys.path.insert(0, r'$Tools')", 'import patchrev_qa as p',
  'p.hold_timing_mutex(0x3, 0)()', "print('inside-0x3 ok')", 'try:',
  "    p.hold_timing_mutex(0xF, 0)()", "    print('0xF acquired and released')", 'except SystemExit as x:',
  "    print('0xF refused while held elsewhere:', x)")
$r4 = Invoke-Tool $Py @('-I', '-B', $pyFile)
$r4.Out | ForEach-Object { Add-OspdLf $log "  W2b> $_" }
$t4 = $r4.Out -join ' '
Check 'W2b' ($r4.Rc -eq 0 -and $t4 -match 'inside-0x3 ok' -and $t4 -match '0xF (acquired and released|refused while held elsewhere)') "hold_timing_mutex: no-op inside 0x3; 0xF: $(if ($t4 -match '0xF acquired') { 'acquired + released (mutex was free)' } elseif ($t4 -match 'refused') { 'refused (an ABBA holds the mutex)' } else { 'NO RESULT' })"

$nf = @($results | Where-Object { $_ -match '^W\S+ FAIL ' }).Count
$fin = "test_cr_should_w8 run $run end $(Get-OspdNow): $($results.Count - $nf) / $($results.Count) PASS; log $log"
Write-Output $fin; Add-OspdLf $log $fin
if ($nf) { exit 1 } else { exit 0 }
