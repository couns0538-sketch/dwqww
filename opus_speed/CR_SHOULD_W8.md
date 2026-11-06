# Code Review SHOULD tooling notes (4) - speed job W8 follow-up, 2026-11-05 18:26-18:38 PC clock

- **Who wrote the fixes:** worker toolrev (fable), from 18:26, after bundles (a)-(d) were pushed. The owner's brief
  allows these notes only once every bundle is pushed.
- **What the worker did not finish:** it ran out of model credits right after its edits. It wrote no report and ran
  no test.
- **What the main session did:** reviewed the diffs and fixed the test's PS 5.1 quoting bug (W2b). It ran the test
  from Git Bash on CPUs 0-1 at Idle, with the lock exe only and a few seconds of engine time: 5 / 5 PASS. It also
  copied the skill change to the user-scope mirror.
- **Source of the readings:** the CR text is not on the PC. The brief names the notes by title only, so each reading
  below is the narrowest one that removes the defect the title names.
- **Not done:** no ABBA, and no warm-identity / 1a-1e / 12k re-run on the six stacks.

| # | title | reading | fix | test (`tests/test_cr_should_w8.ps1`, run 20261105-183748-1788) |
|---|---|---|---|---|
| 1 | warm_identity invalid-FEN | `warm_identity.py` compared transcripts even when the engine rejected a FEN. The lock prints `info string invalid FEN: ...` and keeps its PREVIOUS position, so both exes would agree on the wrong position (the same trap as the withdrawn placement-only L3). | `tools/warm_identity.py:113`: any `info string ... invalid` line after a `position` raises, so the run exits 1 with the rejected FEN's index. `:159`: the degenerate-reference guard of bitexact_check L3 (n >= 100 and fewer than n / 10 distinct depth / score / nodes / bestmove rows -> exit 1). Docstring and skill table row updated. | **W1a** PASS: the lock vs itself on 4 FENs with a placement-only line at index 2 gives exit 1, and the ERROR names FEN 2 and the engine's invalid-FEN line. **W1b** PASS: no IDENTICAL line. **W1c** PASS: the 3 valid FENs give exit 0, IDENTICAL, 3 searches, 3 distinct rows. |
| 2 | patchrev soak mask 0xF | The job rule keeps CPU 2 for nps timing and CPU 3 free. The soak's required `--mask 0xF` used both with no guard against a running ABBA. | `tools/patchrev_qa.py:112` `hold_timing_mutex()`: a mask that touches CPUs 2-3 takes abba.ps1's named mutex `Local\ospd_abba_timing` before any exe check or engine start (`--mutex-wait-min`, default 240; 0 = refuse at once). WAIT_ABANDONED counts as acquired, and the mutex is released at exit (`:627`, atexit). The soak keeps 0xF as the one documented exception. | **W2a** PASS: with the mutex held by the test, `soak --mask 0xF --mutex-wait-min 0` exits 1 before any exe check; the refusal names the mutex and no engine log exists. **W2b** PASS: `hold_timing_mutex(0x3)` is a no-op; 0xF acquires and releases while the mutex is free. |
| 3 | FINAL_REPORT headline tag | The report's headline speed numbers carried no lock-path status. Readers could take BIT-EXACT + ABBA as a lock. | `FINAL_REPORT.md:9`: one status tag for every speed number (the 5 lock-path steps; the six stacks have steps 1-4 and are NOT a lock until QA's re-time; the single changes are BIT-EXACT 2,000 + ABBA screening only). `:35` and `:239` repeat it at the summary headline and at "What QA should time first". No table was rewritten. | doc change (no code) |
| 4 | skill CPU-contradict wording | The skill said both "CPUs 0-3 only, CPU 3 gets no own work" and "soak `--mask 0xF`", which contradict each other. The owner's briefs say "CPUs 0-3 (mask 0xF)". | `skills/forge-speed-lock-path/SKILL.md` job rules: CPUs 0-3 (0xF) are the envelope. Builds and checks use 0x3, timing uses CPU 2, and CPU 3 stays free while a timing run can be on CPU 2. The ONE exception is the soak, which holds the timing mutex for its whole run. The two tool rows were updated to match. The same text is in the user-scope copy `C:\Users\Administrator\<cfg>\skills\forge-speed-lock-path\SKILL.md`. | doc change (no code) |

**Test bug fixed by the main session (W2b).** The first run was 4 / 5. Its `python -c` one-liner held `exec("...")`, and
PowerShell 5.1 strips embedded double quotes from native-program arguments, so Python got `exec(try:` and raised a
SyntaxError. The snippet now goes through a file in the run folder, and the second run passed 5 / 5.

## Leftovers of the independent CR of 73f4041d..00d19e56 (APPROVE, 0 BLOCKER, 4 SHOULD) - 2026-11-05 from 19:43 PC clock

Main session, start tip 00d19e56. Live lock = trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0.
Reading change: note 4 above ("skill CPU-contradict wording") was read as the CPU-mask wording. The CR's leftover 2
shows that the intended rule is CPU-time nps vs wall nps; row 2 adds it now.

| # | leftover | fix | test |
|---|---|---|---|
| 1 | warm_identity self-pin | `tools/warm_identity.py`: `place()` sets mask 0x3 + Idle on this process and reads both back before the out dir, the FENs or any engine. `read_back()` then checks every engine on its own process handle before its first command; this is printed only and is not part of the compared transcript. A failed call or a mismatch is exit 1 (fail closed), and the engine ends with quit + EOF, never a kill. The invalid-FEN and degenerate-reference guards are unchanged. | **W3a** PASS: the positive-control run printed `placement: mask 0x3 Idle (read back)` and 2 / 2 engine read-backs. W1a-c still PASS. |
| 2 | skill verdict rules | `skills/forge-speed-lock-path/SKILL.md`: new section "Verdict rules". Wall nps of ONE run decides. A wall WIN with a CPU-time NO-WIN is a contradiction, not a lock WIN. CPU time never turns a wall NO-WIN into a WIN. `--pool` is information only and never overrides a wall that does not WIN on its own. Lock-path step 5 = QA's independent ABBA vs the live lock trial_w6. The abba and `--pool` rows, the re-time pitfall and the description no longer let pooled rounds decide. Copied to the user-scope mirror. | doc change (no code) |
| 3 | FINAL_REPORT owner item | Section 8: before ANY lock, QA runs L3b warm_identity vs trial_w6, a Threads 2-4 soak and an independent ABBA vs trial_w6 4181A589... (not FD3A5190), judged by the verdict rules. Section 3b: the pooled statuses are screening labels (NNUE_ZMM: both of its own runs wall NO-WIN). | doc change (no code) |
| 4 | patchrev_qa lock | `tools/patchrev_qa.py`: LOCK_SHA = 4181a589...6fb0 and LOCK = `F:/ospd/packs/trial_w6/forge_trial_w6.exe` (its sha256 is the live lock's). The refusal reads `... is not the live lock trial_w6 (sha256 4181A589...)`. LOCK_ASAN and `--ref-tsv` stay the FD3A5190-source search-identity references. STACKS still lists trial_w6, so a default run now also compares the lock with itself (a harmless A/A). Soak, mutex and mask are unchanged. | **W4a** PASS: LOCK_SHA = 4181a589... and sha256(LOCK) = LOCK_SHA. **W4b** PASS: with LOCK pointed at the FD3A5190 exe, `protocol --mask 0x3` refuses before any engine, names trial_w6 and writes no lock.log. W2a-b still PASS. |

Test `tests/test_cr_should_w8.ps1`, run 20261105-194720-5676 (19:47, Git Bash, CPUs 0-1 Idle, lock exe only, a few
seconds of engine time): **8 / 8 PASS**. Log: `F:\ospd\logs\cr_should_w8_20261105-194720-5676\test.log`.

Not done on purpose: no ABBA, soak, warm or 12k run. KING_LINES (W9) and bundles a-d were not retimed, restacked or
locked. The `uci_lib.ps1` lock defaults are unchanged (owner item in FINAL_REPORT section 8).

## Leftover jobs 1-3 (owner brief) - 2026-11-05 from 19:5x PC clock, main session, start tip 38559f1b

| job | what | fix | test |
|---|---|---|---|
| 1 | tool default lock = trial_w6 | `tools/uci_lib.ps1`: `$OspdLockExe` = `forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`, `$OspdLockSha` = 4181A589...6FB0 (file hash checked). New `$OspdOldLockExe` = FD3A5190 (search identity only). `$OspdLockSrc` and the pin tables are unchanged. The default-lock labels in abba_queue (IDENTICAL.txt, `-LabelA`), bitexact_check (usage, ref log line) and speed_pack (`LabelA`) say "live lock trial_w6". The lp_v1 = FD3A5190 lines and historical notes stay. bitexact_check's first default-Ref run builds the cache `F:\ospd\ref\4181a589\`. | **W6a** PASS: the default lock file's sha256 = `$OspdLockSha` = 4181a589. **W4b** now uses `$OspdOldLockExe`. |
| 2 | warm_identity refusal path | New `tests/warm_refusal_check.py` (fault injection; the tool is unchanged). | **W5a** PASS: silent SetProcessAffinityMask on 0x1 gives exit 1 before the out dir / any engine. **W5b** PASS: silent SetPriorityClass while BelowNormal gives exit 1 the same way. **W5c** / **W5d** PASS: an engine inheriting 0x1 Idle / 0x3 BelowNormal is refused, and its PID ended (quit + EOF). **W5e** PASS: no IDENTICAL, no engine claimed pinned. |
| 3a | patchrev mutex before placement | `tools/patchrev_qa.py` main(): mask range check (refused at once), then `hold_timing_mutex`, then `place(mask)`. A run waiting up to `--mutex-wait-min` never sits on CPUs 2-3 meanwhile. The docstring says so. | **W2a** / **W2b** / **W4b** still PASS (the refusal with the mutex held; the trial_w6 check). |
| 3b | KING_LINES is_legal contract comment | Three comment lines above `is_legal` in `include/forge/board.hpp` of `F:\ospd\src\trial_w9` and `F:\ospd\src\w9dev` (the trees were identical before and after). `patches/trial_w9.patch` ddefd1fe -> 8bf44bab and `patches/b4_king_lines_after_w8.patch` 21ecde2e -> d680f9bf, regenerated with `diff -ruN`; the recipe first reproduced both old files byte for byte. Comment only: no rebuild, no retime, no lock. | Old vs new patch: only the comment, the hunk offsets and one timestamp. `patch -p1 -F0` onto fresh lock copies (trial_w9.patch alone; trial_w8.patch + b4) gives `diff -r` identical to trial_w9, with no offset or fuzz. Proof: `F:\ospd\tmp\k3proof_20261105-200606`. |
| 3c | test python not hard-coded | `tests/test_cr_should_w8.ps1`: `param([string]$Py = $env:OSPD_PY)`. No interpreter is hard-coded; a run without one, or with a python that cannot `import chess`, throws before any check. | Without `-Py` / OSPD_PY: throws, exit 1. With `-Py C:\Python315\python.exe` (no chess): throws, exit 1. With `-Py <venv python>`: 14 / 14 PASS. |

Test runs (Git Bash, CPUs 0-1 Idle, the default lock exe only): 20261105-200352-9252 (20:03, after job 2) **14 / 14 PASS**;
20261105-200713-5164 (20:07, after job 3, with `-Py`) **14 / 14 PASS**. The skill and its user-scope mirror now name the
lock defaults and warm_identity's self-pin. Not done on purpose: no ABBA / soak / 12k / L3b; KING_LINES and bundles a-d
were not retimed or locked.

**Bug-hunt pass over 00d19e56..33601a5b (20:08-20:10, own, NOT independent):**
- One glitch found and fixed: the SHOULD 1 edit had turned `CYCLE = [` into `CYCLE =[` in `warm_identity.py`. It was
  whitespace only, with no behaviour change. The test was re-run: 14 / 14 PASS (20261105-200930-9164).
- No trailing whitespace in any added code line.
- The only FD3A5190 path left in the Python tools is patchrev_qa's `--ref-tsv` (kept on purpose).
- LOW, not changed (outside the NIT's line): `tests/test_stack_poison.ps1:16` and `tools/commit_push.sh` still name
  the venv python.
- LOW, not changed: `warm_identity.py` pins to 0x3 by design (`MASK`). A QA run on other cores must change that
  constant, or the run is refused.

**Extras after the bug hunt (20:12-20:15, own, NOT independent; owner goal "finish as much as you can"):**
- `pin_check` (forge-uci MCP, full, Idle 0x3, 20:12:37-20:12:59) of the default lock exe
  `forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe` (sha256 4181a589): PASS. Bench d11-d22 =
  312866 / 862329 / 3024920 / 12389307 / 34048354 and perft5 4865609 / 193690690 = the uci_lib pin tables. The
  net-off pins are not part of this tool.
- The first LOW above is fixed for `tests/test_stack_poison.ps1`: `-Py` / OSPD_PY, no venv path, and it throws
  before any build without one (checked: exit 1). The full poison test (builds + bitexact) was not re-run.
  `tools/commit_push.sh` keeps its PC-specific venv path (the commit gate).
- Skill rows: `test_stack_poison.ps1 -Py`, and a new row for `test_cr_should_w8.ps1 -Py`. The user-scope mirror was
  copied (md5 56c55eba).
- `tests/test_cr_637b.ps1` re-run after the default-lock change (o3 builds only, no ABBA; run 20261105-201312-4460,
  20:13-20:14): **13 / 13 PASS**. T3 speed_pack on the mutant still exits 3 before any ABBA. T5b: the default lock
  (now trial_w6) accepts the completed FEN. Output: `F:\ospd\logs\test_cr_637b_after_leftovers.out`.
