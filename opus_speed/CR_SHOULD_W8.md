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
| 1 | warm_identity self-pin | IN PROGRESS | - |
| 2 | skill verdict rules | `skills/forge-speed-lock-path/SKILL.md`: new section "Verdict rules". Wall nps of ONE run decides. A wall WIN with a CPU-time NO-WIN is a contradiction, not a lock WIN. CPU time never turns a wall NO-WIN into a WIN. `--pool` is information only and never overrides a wall that does not WIN on its own. Lock-path step 5 = QA's independent ABBA vs the live lock trial_w6. The abba and `--pool` rows, the re-time pitfall and the description no longer let pooled rounds decide. Copied to the user-scope mirror. | doc change (no code) |
| 3 | FINAL_REPORT owner item | Section 8: before ANY lock, QA runs L3b warm_identity vs trial_w6, a Threads 2-4 soak and an independent ABBA vs trial_w6 4181A589... (not FD3A5190), judged by the verdict rules. Section 3b: the pooled statuses are screening labels (NNUE_ZMM: both of its own runs wall NO-WIN). | doc change (no code) |
| 4 | patchrev_qa lock | `tools/patchrev_qa.py`: LOCK_SHA = 4181a589...6fb0 and LOCK = `F:/ospd/packs/trial_w6/forge_trial_w6.exe` (its sha256 is the live lock's). The refusal reads `... is not the live lock trial_w6 (sha256 4181A589...)`. LOCK_ASAN and `--ref-tsv` stay the FD3A5190-source search-identity references. STACKS still lists trial_w6, so a default run now also compares the lock with itself (a harmless A/A). Soak, mutex and mask are unchanged. | pending (W4a / W4b) |

Not done on purpose: no ABBA, soak, warm or 12k run. KING_LINES (W9) and bundles a-d were not retimed, restacked or
locked. The `uci_lib.ps1` lock defaults are unchanged (owner item in FINAL_REPORT section 8).
