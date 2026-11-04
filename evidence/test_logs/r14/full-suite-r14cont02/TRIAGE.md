# Triage of the final R14-scope suite run (full-suite-r14cont02)

Run: tree 87ef93eeab1830f3c1c78c242af6b77d813323e3 (first line of output.log), CPU 1 at Idle via opus_lowrun.py
--mask 0x2, 2026-11-04 13:54:30-13:55:42, 72.10 s, exit 1. Scope: 26 D:\a14\tests\test_*.py files + tests\r14_native +
tests\r14_qualification (selected_files.txt, 28 paths). Result: 5 failed, 331 passed, 67 subtests passed.
CPU check before the run (13:54:05, tmp\opus_cpu01_check.ps1): no forge_ltopgo / fastchess / kit process on CPUs 0-1,
CPU 0 14.1 %, CPU 1 9.4 %; after the run (13:56:09): CPU 0 12.4 %, CPU 1 8.5 %, still none.

| failed test | class | note |
|---|---|---|
| tests\test_r14_suite.py::test_real_pytest_receipts_are_exact_and_fixture_scoped[False] | F-003 (known, accepted) | pytest 9.2 built-in subtest accounting vs the runner's expected counts; the three CPU-admission cases of F-003 ([True], [deadline], [log_cap]) passed on the quiet CPU 1 |
| tests\r14_native\test_native.py::NativeFixtures::test_consecutive_fen_digits_are_invalid | F-005 (known, accepted) | default chain_native.exe answers UNREACHABLE instead of UNKNOWN |
| tests\r14_native\test_native.py::NativeFixtures::test_interactive_reply_before_eof | F-005 (known, accepted) | no reply within 2 s from the default exe |
| tests\test_r14_runtime_setup.py::test_live_refusal_stops_only_owned_process_tree[guard] | F-006 (known timing item) | FileNotFoundError: the guard fired after one 500 ms poll before the Idle probe child wrote child.json |
| tests\test_r14_preflight.py::test_floor_breach_after_hash_writes_no_receipt | NEW, environmental, not caused by the R14 finish | see below |

## The new failure

`assert 0 != 0`: the mocked Verify-R14Inputs.ps1 exited 0 and printed real receipts (its last stdout line is the
receipt of D:\o14b\r2\proof\jobA\prepare.json with the real md5 1d7fd43dcd2f0d5553d940012cdc8bd7, match true,
1273 bytes). The test passed in run 3 (10:37, tree 0883cee) and in Astra's runs of 2026-11-03; neither the test
(tests\test_r14_preflight.py) nor the script (tools\Verify-R14Inputs.ps1) changed on this branch.

Reproduction: `pytest tests\test_r14_preflight.py` alone on CPU 1 at 13:59: 1 failed, 1 passed (same test).

Mechanism (minimal scripts tmp\floor_debug.ps1, floor_debug2.ps1, floor_debug3.ps1, run under
C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -File, PSVersion 5.1.26100.7462):
- The test's prefix defines `function Get-FileHash` and `function Get-PSDrive` at the top of the script so that the
  disk floor "breaches" right after the first hash. With nothing else in between, the mocks work (floor_debug.ps1:
  hash 78d231a8..., hashed=True, Free=0).
- In Windows PowerShell 5.1 the real Get-FileHash is a *function* exported by Microsoft.PowerShell.Utility
  (`Get-Command Microsoft.PowerShell.Utility\Get-FileHash` -> Function). No module is loaded at script start
  (-NoProfile). The script's line 44, `$utf8=New-Object System.Text.UTF8Encoding($false)`, is the first Utility
  command, so command discovery auto-imports Microsoft.PowerShell.Utility into the running scope - and its exported
  Get-FileHash replaces the script's mock (floor_debug2.ps1 STEP1: after New-Object, `Get-Command Get-FileHash` ->
  Function, source Microsoft.PowerShell.Utility; the hash of PLAN.md is its real md5; `$script:hashed` stays False;
  STEP3: the mock is no longer among the candidates). The Get-PSDrive mock survives (Get-PSDrive is a cmdlet in
  Microsoft.PowerShell.Management and a function beats a cmdlet), so the mocked floor stays at 100 GB, every real
  hash matches its pin, the receipt is written and the script exits 0.
- Proposed one-line fix in the test's prefix, verified (floor_debug3.ps1): `Import-Module
  Microsoft.PowerShell.Utility, Microsoft.PowerShell.Management` before the mock definitions; then the mock hash,
  hashed=True and Free=0 all hold after New-Object and Join-Path. Not applied here: the test is Astra's as-found code
  and the cause is outside the R14-finish diff (owner item, also in evidence\R14_OPEN_ISSUES.md).
- Why it passed earlier is not established (no PowerShell module changed in the last day; the module analysis cache
  is dated 2026-10-31); what is established is that the failure is deterministic now (13:55, 13:59, 14:00, 14:02).

Written 2026-11-04 by Opus (R14 finish). The run's own artifacts: output.log, command.txt, command.ps1,
selected_files.txt, timing.txt, exit.txt (md5s in FINAL_REPORT.md and its appendix).
