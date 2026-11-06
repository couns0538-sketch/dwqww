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
