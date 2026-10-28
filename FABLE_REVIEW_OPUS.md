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

## Findings

(none yet)

## Corrections pushed

(none yet)

## Time estimate

Inventory 1-2 h (done), engine jobs 4-6 h, tool jobs 3-4 h, fixes 2-4 h: about 12-16 hours of work in total,
split over sessions; pushes every 30 minutes.
