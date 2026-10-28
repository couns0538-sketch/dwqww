# FABLE_REVIEW_OPUS.md — review of every opus-* job branch — IN PROGRESS

Reviewer: Fable 5.1, started 2026-10-28 (PC time ~13:45). Branch `fable-review-summary` (base d4f4312, report only;
no engine code here). Per-job corrections go to `fable-review-<job>` branches based on the opus branch, each with
`opus_round1/<job>/REVIEW.md`. Nothing on any opus-* branch is modified. All PC rules apply (no sub-agents, pushes
at least every 30 minutes, finished or not).

## Scope and method

88 branches `opus-*` on GitHub (inventory: `fable_review/inventory.txt`, report titles `fable_review/titles.txt`,
CI runs `fable_review/ci_runs.txt`). Method, in this order:
1. Inventory: head, date, engine diff vs the lock (`src include CMakeLists.txt`), report files, CI conclusions. DONE.
2. CI failures: find the cause of every non-success run and whether a later run fixed it.
3. Engine-changing jobs (highest risk first): read the diff for correctness (defaults OFF, identity, UB, thread
   safety), check that the tests test the claim, re-check identity/bench where the diff looks risky.
4. Tool/analysis jobs: scripts and the numbers in REPORT.md against their logs (gate statistics, data handling).
5. Fixes on `fable-review-<job>` with REVIEW.md; findings and status in this file.

## Inventory summary

| group | branches | engine diff vs lock |
|---|---|---|
| O3 refactor base | opus-O3, opus-O3-pin | 22 files (search.cpp split into .inc files; claimed no-op) |
| O/C jobs on O3 | opus-O1, O1-LTT, O2, O4, O5, O6, O7, O8, C1, C2, C3, C4, C5, C6 | 24-30 files each (O3 + the job) |
| R3 integration | opus-r3-stack (+ cifix, gates, matrix, port-b, port-c, quietnps, selfplay, smp, smpq, sp-linux, spsa, tests) | 48-55 files (every O/C job merged) |
| Sol leftovers with engine changes | opus-sol-A1, S04fix, S08fix, S11, S12, S13, S14, S29, S32, S37, S41, SA2, SA4, SIT | 1-8 files each |
| Sol leftovers, tools/analysis only | opus-sol-A2, A3, A7, S05fix..S07fix, S09fix, S10fix, S15..S28fix, S30, S31, S33fix..S36, S38..S40, S42..S50, SA1, SA3, SA6, SC4, offguard | none |
| summary | opus-summary | O3 tree + progress file |

## CI runs with a non-success conclusion (to be explained one by one)

| branch | run | workflow | conclusion | status of the review |
|---|---|---|---|---|
| opus-C3 | 40498064402 | opus-ci | failure | pending |
| opus-O1 | 40367007552 | opus-ci | failure | pending |
| opus-O1-LTT | 40470578003 | opus-o1-ltt | cancelled | pending |
| opus-O2 | 40381997386 | opus-o2-perf | failure | pending |
| opus-r3-stack | 40564150654 | opus-ci | failure | known: two merged tests used pre-O3 member names, fixed by 2432670b (later runs green) |
| opus-sol-S14 | 40527244836 | opus-sol-s14fu | cancelled | pending |
| opus-sol-S26fix | 40505681846 | opus-sol-s26fix | failure | pending |
| opus-sol-S27fix | 40521425927 | opus-sol-s27fix-linux | failure | pending |
| opus-sol-S49 | 40509722120, 40510697858 | opus-sol-s49-box | failure | pending |

## CI failures: all explained, none outstanding

Every non-success run was followed by a successful run of the same workflow on the same branch (the branch head
is green); the red entries on GitHub belong to superseded commits. Pairs (failed run -> later success):
C3 40498064402 (f07630ec, the C3 TSan hook `hard_deadline_regression_t3` exited 1) -> 40503292559 (581ad5da);
O1 40367007552 (c6956801, tsan job) -> 40381524034 (33b0790b); O1-LTT 40470578003 cancelled -> 40471171993;
O2 40381997386 (runner clock: `ninja: manifest still dirty`) -> 40383970663; r3-stack 40564150654 (two merged tests
used pre-O3 member names) -> 40566615160; S14 40527244836 cancelled -> 40547593226; S26fix 40505681846 ->
40507421791; S27fix 40521425927 -> 40522039382; S49 40509722120 and 40510697858 -> 40517374833. Nothing to fix;
superseded runs cannot be turned green by re-running (same code).

## Identity sweep of every engine-changing branch (DONE)

For each of the 30 branches that change `src`/`include`/`CMakeLists.txt` the latest opus-ci run was checked
(`fable_review/ci_identity_sweep.txt`): all 30 are `success`, each log contains the identity line `ALL OK`
(bench d11/13/16/20/22, perft5, kiwipete against the AL1 pins), `KNOWN-FAILURE CHECK: PASS` in all three jobs
(release, ASan+UBSan, TSan) and `TSan: 0 reports`. So the central claim of every engine job, "option OFF = the
lock", holds on Linux CI for C1-C6, O1, O1-LTT, O2-O8, the R3 stack, A1, S04fix, S08fix, S11-S14, S29, S32, S37,
S41, SA2, SA4 and SIT.

## Findings (engine jobs, read in order of risk)

| job | what was reviewed | verdict |
|---|---|---|
| C3 HardDeadline (opus-C3) | the single-bestmove guard (`run.answered.exchange(true)` claimed by both the search thread (`uci.cpp:619`) and the watchdog (`:284`)), the watchdog's fallback answer (`forced_bestmove`: published pair only if legal / inside searchmoves, else first candidate, else `0000`), the published-move atomic packing, the priority handling (Windows only, documented), ponder searches armed from ponderhit only | **no defect found** in the parts read; the OFF path only gains two cold calls guarded by `hard_deadline_ms > 0` |
| O1 Lazy SMP options (opus-O1) | `SmpExactNodes` (published counts reset before the search, summed after join), `SmpBestThread` (`better_thread_result`: mate scores decide first, then depth, then score; helper results written by one helper each and read after join; `end_search` clears the dangling worker-list pointer) | **no defect found**; the ranking matches the documented rule |
| O1-LTT LocklessTT (opus-O1-LTT) | `tt_lockless.inc`: entry = two relaxed-atomic 64-bit words, word 0 = `move << 32 | key32 ^ hash(move, payload)`, so a torn read (word 0 and word 1 from different stores) fails the key check and reads as a miss; empty-slot and replacement decisions use the payload word only; generation refresh re-stores both words; mode change clears the table; the default path keeps the striped locks | **no defect found** in the parts read (encode/decode, probe, the store's handle checks) |
| C2 CorrHistPlus (opus-C2) | table sizes vs indices (`key_index` masks with `CorrectionSize - 1`; `continuation_index` ranges over 2 x 6 x 64 x 6 x 64; the "previous two moves unknown" sentinel `ContinuationSize` is checked with `index < ContinuationSize` at both use sites before indexing), the power-of-two division helpers with their static_asserts, blend clamps | **no defect found** |
| O5 CorrMargins, O8 CorrExt (opus-O5, opus-O8) | the margin helpers (`corr_margins.hpp`: correction size 0 when in check or without evals, RFP/futility/null-move margins and the LMR reduction scaled by percentage tunables, `lmr_reduction` never below 0; `corr_ext.hpp`: double/triple singular extensions bounded by a per-path budget) | **no defect found** in the helpers; integer ranges are safe (r x correction x pct / 6400 stays far below 2^31) |
| C6 CuckooRep (opus-C6) | `Board::upcoming_repetition` (table build, two-slot cuckoo lookup, opponent-delta XOR, mover/empty/between checks, rule-50 + null-move window `distance < min(halfmove+1, since_null+1, size)` against the lock's `is_repetition` (`span = min(halfmove, plies_from_null, size-1)`, even distances 4..span), root-index rule, second-occurrence scan) and the search bound (`search_cuckoo`/`qsearch_cuckoo`: alpha < 0, not at root, no excluded move, fail-high when beta <= 0, else alpha raised to 0 and `max(result, 0)`) | **no defect found**; the window arithmetic matches the lock's repetition scan exactly and the bound is sound (the drawing move is legal because the opponent-to-move position it recreates was legal) |

| C1 Syzygy (opus-C1), targeted | probe preconditions (`castling_rights() == 0`, piece count <= the loaded tables' maximum), en passant (the WDL probe resolves captures and en passant explicitly, `syzygy.inc` lines 907-993; the report tested 26 en-passant positions) | **no defect found** in the parts read; the 1474-line decoder itself was not re-read line by line |

## Mistakes found (with the correction)

| # | where | mistake | correction |
|---|---|---|---|
| 1 | opus-O1, opus-O1-LTT, opus-O2, opus-sol-S12 and every opus-r3-* branch (8 files on opus-r3-stack) | Python bytecode committed: `opus_round1/O1/__pycache__/ucilib.cpython-314.pyc`, `opus_round1/O2/__pycache__/mutation_check.cpython-314.pyc`, `opus_round1/sol_S12/__pycache__/jobA_cause.cpython-314.pyc`, `opus_round1/sol_S12/followup_nullalias/__pycache__/mutation_check_alias.cpython-314.pyc` and the stack's copies (ctest ran the tools with the system Python inside the source tree) | the fix is `git rm --cached` of the eight files plus `__pycache__/` and `*.pyc` in `.gitignore` on a `fable-review-r3-stack` branch; **the command was denied by the PC's permission rules in this session (it counts as a deletion), exactly as it was for Opus**, so this stays an owner action: `git rm --cached $(git ls-files | grep '\.pyc$')` on a branch off opus-r3-stack, then commit |

| 2 | the AL1 lock engine itself; Opus job S14 found it (`opus-sol-S14` REPORT section 4, "not fixed here") and the lock archive carries the CR-passed fix that was never applied | `MovePicker::bad_captures_` is `std::array<Move, 64>` written at `src/search.cpp:361` without a bounds check; a position with more than 64 SEE-losing noisy moves (capture-promotions count four times) overruns it (undefined behaviour) | branch **`fable-review-buffix`** (base d4f4312): the archived node-identical fix applied (`std::array<Move, MoveList::Capacity>` + static_assert + `tests/bad_capture_tests.cpp`), box build, identity check and the regression test; see its `fable_review/REVIEW.md` |

## Corrections pushed

(none: the only mistake found so far needs a deletion that the permission rules refuse; see above)

## Time estimate

Inventory 1-2 h (done), engine jobs 4-6 h, tool jobs 3-4 h, fixes 2-4 h: about 12-16 hours of work in total,
split over sessions; pushes every 30 minutes.
