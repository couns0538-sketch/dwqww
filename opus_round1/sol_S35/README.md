# S35: locked-log watcher test harness (opus, 2026-10-27)

Sol's spec (inventory `S35`): a PowerShell 7 test that holds a fastchess-style log open with an exclusive writer lock
and appends a synthetic "loses on time" line; the watcher must see it via FileShare.ReadWrite. It also covers log
rotation/truncation, a missing file and a UTF-8 BOM. Pass: 4/4 scenarios alert or log correctly, and the test FAILS
against a watcher variant that uses `[IO.File]::ReadAllText` (shipped as the negative fixture).

## Files
| file | what |
|---|---|
| `forge_sol_S35_test_watcher_locked_log_20261027.ps1` | the harness (suite mode `-Targets`, single mode `-Watcher`, extract mode `-ExtractFrom`) |
| `s35_child_runner.ps1` | child process: stubs every side effect, dot-sources ONE patched watcher copy, tick handshake |
| `fixtures/targets.json` | the 9 targets with sha256, provenance and the expected result per scenario |
| `fixtures/watchers/` | conc7_watch copies: v2 (live copy), v1 and v0 (live `.bak` files, copied read-only), derived variants + `.diff` |
| `fixtures/functions/` | `Read-Shared` + `Log-TLCrash` extracted verbatim (PowerShell AST) from autopromote.ps1 896663b0, + negative |
| `make_s35_variants.py` | derives the NEG / PLANTED / v3 variants from v2 (each edit must match exactly once) |
| `s35_safety_selftest.ps1` | proves the harness refuses unsafe copies and a live-root WorkDir before running anything |
| `s35_probe_lock_semantics.ps1` | one-file probe of Windows sharing semantics (ReadAllText vs FileShare.ReadWrite, Get-Content, Move-Item) |
| `run_s35_evidence.sh` | regenerates every log in `logs/` |

## Run
```
pwsh -NoProfile -File forge_sol_S35_test_watcher_locked_log_20261027.ps1 -Targets fixtures/targets.json -WorkDir <scratch> [-OutJson <file>]
pwsh -NoProfile -File forge_sol_S35_test_watcher_locked_log_20261027.ps1 -Watcher <copy of conc7_watch.ps1> -Conc 8 -WorkDir <scratch>
```
Suite exit 0 = every target produced its expected result AND every `negative` target FAILS S1. Single mode exit 0 = 4/4.
On the PC wrap it in `nice -n 19` (the child watcher also sets itself to Idle, CPUs 12-15, as the real one does).

## Scenarios (fresh sandbox each; gate `gate_s35_test`, fastchess 1.8 stdout format, CRLF)
| id | what the harness does | pass condition (e2e target) |
|---|---|---|
| S1 | writer holds `<tag>.log` in mode `exclusive` (Write + FileShare.Read) and, separately, in mode `driver` (ReadWrite + FileShare.Read/Write, what `Start-Process -RedirectStandardOutput` uses on the PC); 6 games, then `Finished game 7 (...): 0-1 {White loses on time}` appended under the lock | lock self-check (ReadAllText throws, FileShare.ReadWrite reads) holds; `ALERT conc-N gate gate_s35_test: TL 1 crash 0`; no `loop error`; HB games 7 (if printed); child exit 0 |
| S2 | tick 1: 5 games, TL in game 5. Then the log is moved to `partial_<ts>\` (as forge_queue.ps1 Archive-Partial does before a rerun) and a fresh locked log with ONE new TL is written; tick 2. Then the writer truncates in place and writes one more new TL; tick 3 | ALERT at tick 1, a NEW ALERT at tick 2 and at tick 3; no `loop error` |
| S3 | RUN_INFO present, `<tag>.log` missing; tick 1. The log then appears (locked) with one TL; tick 2 | tick 1: no ALERT, no error, HB games 0 TL 0; tick 2: ALERT TL 1 |
| S4 | locked log starts with EF BB BF and its first line is `Finished game 1 ... loses on time`; 4 finished games | ALERT TL 1; HB games 4 (a BOM that is not stripped blocks `^Finished` on line 1) |

Function targets (autopromote `Log-TLCrash`) are called at the same points and must return the TL/crash counts of the
file as it is at that moment (dedupe is not that function's job).

## Safety (copies only)
- e2e copies are patched in a sandbox: the 4 live path literals (`qa_conc7`, `autorestart`, `D:\grok-pc-data\forge_push`,
  the HWiNFO csv) must each occur exactly once and are rewritten; the `Global\forge_conc7_watch` mutex becomes a unique
  `Local\` name (otherwise the copy would exit at once, or collide with the live watcher). The patched text is refused if
  any live root, a `Global\` name or an unstubbed side-effect command (Remove-Item, web, scheduler, service, shutdown)
  remains. The child runner re-checks it and stubs taskkill / Stop-Process / Start-Process / Get-CimInstance (64 GB free,
  no "our" worker) / Get-Counter / Start-Sleep (tick handshake). Evidence: `stub_calls` in the JSON never shows taskkill.
- The watcher's own side effects (manifest concurrency revert, csv, log) land in the sandbox: after a conc-8 TL the
  sandbox `forge_gates.json` shows `gate_s35_next` 8 -> 7, which proves the alert path ran to the end.
- `s35_safety_selftest.ps1`: 5/5 unsafe inputs refused, no patched copy written (`logs/step3_safety_selftest.log`).

## Results (`logs/step2_suite_run_A.log`, identical table in run B)
| target | role | S1 | S2 | S3 | S4 |
|---|---|---|---|---|---|
| conc7_watch v2 (live copy 15250b63) | subject | PASS | **FAIL** | PASS | PASS |
| conc7_watch v3 PROPOSED rotation fix | fix proposal | PASS | PASS | PASS | PASS |
| conc7_watch v1 (bak_conc8 25579f58) | history | PASS | FAIL | PASS | PASS (games n/a) |
| conc7_watch v0 (bak_sharedread 9ad2cb42, ReadAllText) | negative | FAIL | FAIL | FAIL | FAIL |
| v2 with Read-Shared -> ReadAllText | negative | FAIL | FAIL | FAIL | FAIL |
| v2 PLANTED BOM-blind decode | planted S4 | PASS | FAIL | PASS | FAIL |
| v2 PLANTED missing-file crash | planted S3 | PASS | FAIL | FAIL | PASS |
| autopromote 896663b0 Log-TLCrash | subject | PASS | PASS | PASS | PASS |
| autopromote Log-TLCrash -> ReadAllText | negative | FAIL | FAIL | FAIL | FAIL |

## Findings
- **F1 (real defect in the live watcher, v1 and v2):** the per-gate TL/crash counter `$tlSeen[$cur]` is only compared
  with `$bad -gt $prev` and never reset. When the gate log is rotated or truncated (forge_queue.ps1 `Archive-Partial`
  moves `<tag>.log` to `partial_<ts>\` before a partial rerun, e.g. after a TIME-WATCH pause), a new TL is alerted only
  if the new file has MORE bad lines than the old one. With one TL before and one after, ticks 2 and 3 of S2 log no
  ALERT, so the conc-7 "further TL -> conc 5" and conc-8 rules would not fire for it. `v3_PROPOSED_rotation_fix`
  (diff in `fixtures/watchers/`, 2 edits) resets the counter when the log is shorter or no longer starts with the head
  seen last tick, and ignores a failed read. It passes 4/4. NOT deployed; it needs CR before anyone touches the PC.
- **F2:** the real pre-fix watcher v0 fails S1 with
  `loop error: Exception calling "ReadAllText" ... being used by another process`. The one-line ReadAllText mutation of
  v2 fails silently instead (its Read-Shared catches the exception and returns ''), so a regression like that would
  not show in the watcher log at all.
- **netgate_watch.ps1 does not read the fastchess gate log.** The live file (3f929731 = netgate_watch.AL.ps1) reads
  RESULT.md with `Get-Content -Raw` (Gate-Verdict), NNUE run logs with `Get-Content -Tail 40`, and the manifest with
  `[IO.File]::ReadAllText` (manifest writes are tmp+Move, not a held writer). Get-Content reads a write-locked file
  (`logs/step4_lock_semantics_probe.log`). So S1-S4 apply to the conc watcher and to autopromote's `Log-TLCrash`.
- **Observations, impact UNVERIFIED:** autopromote's Read-Shared opens without FileShare.Delete, so while it reads, a
  Move-Item of that log (Archive-Partial) fails; the window is one read. Its crash regex counts
  `disconnect|stalls|crash|illegal|abandon` anywhere in the log, not only on `Finished game` lines like conc7_watch; a
  fastchess warning containing "illegal" would count as a crash. No such line exists in the gate logs under
  `D:\grok-pc-data\forge_push` today (grep, read-only).

## Limits / UNVERIFIED
- Run with pwsh 7.6.8 on Windows 11 (26200); the spec names 7.5 (not installed). Linux: .NET does not enforce
  FileShare there except FileShare.None, so the S1 lock self-check would fail and the negative fixture could not be
  told apart: Linux is not supported by this test (UNVERIFIED).
- The writer is a .NET FileStream with the two share modes above, not a real fastchess process (UNVERIFIED that
  fastchess 1.8.2 itself uses the same mode; the driver redirection mode is the one that matters for `<tag>.log`).
- The live watcher, driver and autopromote were never run; only copies in a sandbox. The NPS-ratio path (>= 50 games,
  engine_io.log), thermal and RAM stop paths are not exercised (stubbed or below threshold).
