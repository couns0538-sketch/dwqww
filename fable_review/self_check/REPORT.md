# Self-check agent — independent re-verification of the first seven fable-review-* branches (2026-10-28)

The agent could not write this file itself (permission rules); the main session wrote it from the agent's hand-back
and from the logs in this folder. Everything below is backed by a log here.

## What was re-done, from fresh exports of the branches

| branch | check | result | log |
|---|---|---|---|
| fable-review-buffix | box-recipe build (FMA count), identity vs the AL1 pins, cmake build, `forge_bad_capture_tests` | FMA 0; bench d11/13/16/20/22 + perft5 + kiwipete ALL OK; test accepted=5 failures=0; the 3 source hunks byte-identical to the archived patch | `chain.log`, `build_pc.log`, `identity.log`, `cmake_build.log`, `bad_capture_tests.log` |
| fable-review-S33fix | job test from a CRLF export and from an LF export | OK (11 tests) in both | `job_tests.log`, `logs/S33fix*.log` |
| fable-review-S38 | same | OK (17) in both | `logs/S38*.log` |
| fable-review-S46 | same | OK (9) in both | `logs/S46*.log` |
| fable-review-S42 | same | OK (6) in both | `logs/S42*.log` |
| fable-review-S08fix | same | OK (10) in both | `logs/S08fix*.log` |
| fable-review-r3-stack | tracked `.pyc` count, diff against opus-r3-stack | 0 tracked `.pyc`; diff = the untracking + .gitignore + REVIEW.md | (hand-back) |

Control on the UNFIXED bases (`base_tests.log`, `logs/base_*`): S33fix/S38/S46 pass from an LF export and fail from
a CRLF export (1 / 1 / 30 failures, byte comparisons `\n` vs `\r\n`); S42 and S08fix fail from a CRLF export
(1 error / 2 errors, frozen SHA256 of LF blobs). This confirms the root cause of mistake 3 in the review.

## Remarks handed back (all acted on by the main session in session 4)

1. B1: the buffix branch's CI commit is the whole `fable-nnue-arch` workflow file (also `paths-ignore` and a job
   timeout 180 -> 60 min), not only the `fable-*` trigger. Fine for this branch (1.5-minute runs); the R3 stack
   would need the 180.
2. B2: the archived regression test's stress positions reach at most 50 SEE-losing noisy moves (qa-1: 50, qa-2: 45),
   below the old limit of 64, so the test passes on the unfixed engine too; the `static_assert` is tautological.
   Optional: a position with more than 64 SEE-losing noisy moves.
3. B3: REVIEW.md said the picker defers on `see_ge(move, 0)`; it uses `see_ge(move, -move_score_threshold(move))`.
4. R1: the two `.gitignore` lines added on fable-review-r3-stack duplicate lines already in the base.
5. T1: literal line breaks inside backticks in the REVIEW.md files (cosmetic).
6. T2: the S33fix/S38/S46 REVIEW.md described the failure direction inverted (the unfixed tests fail from a CRLF
   checkout and pass from LF, not the other way round).

Verdict of the agent: all seven branches correct; remarks are documentation and test-strength items, no fix is wrong.
