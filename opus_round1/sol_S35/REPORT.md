# S35 Locked-log watcher test harness: DONE (opus, 2026-10-27)
Branch opus-sol-S35 (base d4f4312 + cherry-pick 0d99f02), head ae1e0209. Tool job, no engine change. Pushes carry [skip ci]; no CI run.

## What was done
- `forge_sol_S35_test_watcher_locked_log_20261027.ps1` (pwsh 7) + `s35_child_runner.ps1`: the harness holds a fastchess-style gate log
  (`<tag>.log`, CRLF, fastchess 1.8 stdout format) under a writer lock and appends a synthetic "loses on time" line. It then runs COPIES
  of the conc watcher tick by tick in a scratch sandbox. Two writer lock modes are used: exclusive (Write + FileShare.Read) and the PC
  driver's Start-Process redirection mode (ReadWrite + Read/Write share).
  - Each live path literal must occur exactly once and is rewritten to the sandbox.
  - The Global mutex becomes a Local one; otherwise the copy would exit at once or collide with the live watcher.
  - taskkill, Stop/Start-Process, Get-CimInstance, Get-Counter and Start-Sleep are stubbed.
  - The patched text is refused if any live root, Global name or unstubbed side effect remains.
- Scenarios: S1 locked log; S2 rotation (the driver's Archive-Partial move) then in-place truncation, one new TL each time; S3 missing
  file, then the log appears; S4 UTF-8 BOM with a TL as the first line (the game count must stay exact).
- Targets (`fixtures/targets.json`, sha256-pinned, with expected results):
  - live copy v2 (= live 15250b63);
  - v1 and v0 from the live `.bak` files: v0 is the real pre-fix watcher that used ReadAllText;
  - the spec negative (v2 with Read-Shared replaced by ReadAllText);
  - planted BOM-blind and missing-file bugs;
  - a v3 proposed rotation fix;
  - autopromote 896663b0 Read-Shared/Log-TLCrash (PowerShell AST extract) and its ReadAllText negative.
- Also: `make_s35_variants.py` (exact-once edits + diffs), `s35_safety_selftest.ps1`, `s35_probe_lock_semantics.ps1`,
  `run_s35_evidence.sh`, README, IDEA_SOURCE, FILES, SHA256SUMS.

## Evidence
| check | command | raw result |
|---|---|---|
| suite | `nice -n 19 pwsh -NoProfile -NonInteractive -File forge_sol_S35_test_watcher_locked_log_20261027.ps1 -Targets fixtures/targets.json -WorkDir F:\opus_scratch\sol_s35\work` | 9/9 targets match; "negative fixtures fail S1 ... True"; exit 0 (logs/step2_suite_run_A.log, _B.log) |
| determinism | cmp of the result tables of two runs | identical (sha256 12debbf7…) |
| live v2 | suite row | S1 PASS (both lock modes: ALERT TL 1, HB games 7, sandbox manifest conc 8->7), S2 FAIL, S3 PASS, S4 PASS (HB games 4) |
| v3 fix | suite row | 4/4 |
| negatives | v0 / v2-NEG rows | 0/4. v0: "loop error: Exception calling "ReadAllText" ... being used by another process"; v2-NEG: no alert and no error line |
| planted | bomblind / missingfile rows | S4 FAIL (HB games 3) / S3 FAIL (loop error "Cannot find path") |
| safety | `pwsh -File s35_safety_selftest.ps1 -WorkDir …` | PASS (5/5 refused, no patched copy written) |
| provenance | logs/step1_provenance.log, step5 | LA copy = live conc7_watch.ps1; extract and variants regenerate byte-identically (also under venv Python 3.10.22) |

## Findings
- **F1 (real defect, live conc7_watch v1/v2):** the per-gate TL/crash counter `$tlSeen[$cur]` is never reset. forge_queue.ps1
  Archive-Partial moves `<tag>.log` away before a partial rerun (for example after a TIME-WATCH pause). A new TL is then alerted only if
  the new file has more bad lines than the old one. With one TL before and one after, S2 ticks 2 and 3 log no ALERT, so the conc-7
  "further TL" and conc-8 rules would not fire. `v3_PROPOSED_rotation_fix.diff` (2 edits) resets the counter when the log is shorter or
  its head changed, and ignores a failed read; it passes 4/4. NOT deployed; needs CR.
- **F2:** a ReadAllText regression in v2's Read-Shared fails silently: no alert and no error line in the watcher log.
- netgate_watch.ps1 (live = 3f929731) never reads the fastchess gate log. It reads RESULT.md with Get-Content, which reads write-locked
  files (probe), NNUE logs with Get-Content -Tail, and the manifest with ReadAllText; the manifest is written via tmp+Move, never held open.
- Observations, impact UNVERIFIED:
  - autopromote's Read-Shared opens without FileShare.Delete, so a move of that log fails during its read.
  - Its crash regex matches words anywhere in the log. No such line exists in the current PC gate logs.

## Left
- CR decision on F1 (v3 diff); a run under pwsh 7.5.

## UNVERIFIED
- pwsh 7.5 (ran 7.6.8); Linux, where .NET does not enforce FileShare, so S1 cannot discriminate.
- Real fastchess writer share mode (emulated with FileStream).
- Live watcher never run.
- NPS-ratio, thermal and RAM paths not exercised.
