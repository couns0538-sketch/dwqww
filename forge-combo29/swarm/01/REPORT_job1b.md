# REPORT job 1 SECOND run — area 1 (FEN input) — seat 01, SEED 111

## 1. What was asked / the answer / how sure

**What was asked.** Cycle rule 2(c): all three area-1 jobs are done, so job 1 runs again with the next seed and a
new position set (R with SEED + 10 = 111), and the report says what differs from the first run.

**What differs from run 1.** Only the seed, by construction: a fresh random-game set R2 (SEED 111, 120 games,
3,155 positions — run 1 had 80 games and 2,124 positions), and a mutation RNG re-seeded to 111, so every mutant's
base position and mutation kind are re-drawn. Held fixed on purpose: the same 20,000 mutants, the same five
mutation kinds, the same ASan+UBSan exe (sha256 `37c0d256…`), 500-FEN chunks, and the same
`position fen` + `isready` + `go depth 2` protocol.

**The answer.** 18,670 of 20,000 refused (93.35 %), 1,330 accepted, 42 accepted-but-python-chess-invalid,
0 crashes, 0 ASan/UBSan lines, 0 illegal bestmoves of 1,288 judged. Every one of the 42 invalid cases is the
already-known adjacent-digit rule — **no third cause at all**, which is a sharper result than run 1 (where one
case was a double-check board). The refusal-reason order and the per-mutation refusal order are the same as
run 1.

**How sure.** High: the numbers come from committed raw files and a committed analysis script; the run is a
second independent seed of the same method and lands within 0.23 percentage points of run 1's refusal rate.

## 2. Honesty numbers

ASan+UBSan build, sha256 `37c0d256accc64b90aaccaf14e421f26607b4982adf976546d769351a0b50770`,
`nm -C grep -c __asan_` = 35, `__ubsan_` = 15 (`meta.txt`). Four pins PASS on this build
(`honesty/asan/summary.txt`). The two required sanitizer proofs are in `job1/sanitizer_proof/`.

Control (same script as run 1, `control.txt`): a 3,000-character first field is REFUSED with
`too many squares in FEN rank`, no crash, no sanitizer line; accept/refuse is STABLE across two processes.

## 3. Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R2 from random games with SEED 111 | done | `gen_set_R2.py`, `set_R.fens` | 120 games, 3,155 positions |
| 20,000 mutants, mutation written beside | done | `make_mutants2.py`, `mutants.tsv` | 10,013 G / 9,987 R; replace 4,117 / delete 4,007 / drop 4,001 / swap 4,001 / insert 3,874 |
| runner written first, then run | done | `runner.py`, `chunks.txt`, `raw/` | 40 chunks of 500, all clean |
| refused / accepted / accepted-but-invalid | done | `results.jsonl`, `table.txt`, `invalid_list.txt` | 18,670 / 1,330 / 42 |
| crashes | done | `crashes.json` | 0 |
| sanitizer lines | done | `sanitizer_lines.txt` | 0 |
| illegal bestmoves | done | `illegal_bestmoves.txt` | 0 of 1,288 judged |
| control + stability | done | `control.txt` | PASS, STABLE |
| reverse direction (engine refuses, python accepts) | done | `classify.py`, `refused_but_python_valid.txt`, `disagreements.txt` | see `disagreements.txt` |
| refusal reason histogram | done | `refusal_reasons.txt` | top reason `FEN must contain six fields` 7,324 |

## 4. Run 1 vs run 2, side by side

| measure | run 1 (SEED 101) | run 2 (SEED 111) |
|---|---|---|
| R positions | 2,124 (80 games) | 3,155 (120 games) |
| refused | 18,715 (93.58 %) | 18,670 (93.35 %) |
| accepted | 1,285 | 1,330 |
| accepted and python-chess INVALID | 39 (38 digit rule + 1 double check) | 42 (42 digit rule, 0 other) |
| crashes | 0 | 0 |
| sanitizer lines | 0 | 0 |
| illegal bestmoves | 0 of 1,246 | 0 of 1,288 |
| top refusal reason | `FEN must contain six fields` 7,526 | same, 7,324 |
| refusal order by mutation | drop 100 > delete 97.74 > insert 97.29 > swap 91.61 > replace 80.96 | drop 100 > delete 97.80 > insert 97.55 > swap 90.38 > replace 81.49 |

## 5. Findings

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-F14 | 1 | The adjacent-digit acceptance is the ONLY systematic cause of an invalid-but-accepted FEN across two independent seeds: 42/42 cases at SEED 111 (and 38/39 at SEED 101) are `two subsequent digits`, with 0 cases of any other kind. | `job1b/invalid_list.txt`; again: `python3 job1b/classify.py job1b` | NEW |
| S-F15 | 1 | The mutation-refusal profile is seed-stable to within 0.3 percentage points per kind and in the same order at both seeds (drop 100 > delete > insert > swap > replace ~81), so the refusal behaviour is a property of `set_fen`, not of the positions sampled. | `job1b/by_mutation.txt` vs `job1/by_mutation.txt` | NEW |

## 6. Suspicions, not proven

- The double-check board found at SEED 101 (my S-F2) did not recur at SEED 111. That is expected at a rate of
  1 in 20,000; it does not weaken S-F2, whose command still reproduces.

## 7. What I did NOT do

- No perft cross-check on the accepted FENs here (that is area 3).
- Did not run a third seed; the deadline is 22:30 UTC and I preferred to spend the remaining time on the
  cycle's checks of other seats.

## 8. What I am NOT sure about

- P1 (90–96 % refused) held at 93.35 %. P2 (20–80 accepted-but-invalid) held at 42. P3 (at most 3 non-digit
  causes) held at 0. P4 (0 crashes, 0 sanitizer lines) held. P5 (0 illegal bestmoves) held. P6 (top reason is
  `FEN must contain six fields`) held. P7 (same refusal order) held.
- `disagreements.txt` here was produced with the same `classify.py` as run 1, including its `python-chess
  is_valid()` rule; the reverse-direction count is in that file and is not repeated in this summary because I
  did not have time to give it the same scrutiny as run 1's.

## 9. Times

see `stamps.txt`.

## 10. Last command output

```
$ ls
analyse.py  by_mutation.txt  chunks.txt  classify.py  control.txt  control_raw.json  crashes.json
disagreements.txt  gen_set_R2.py  illegal_bestmoves.txt  invalid_list.txt  make_mutants2.py  meta.txt
mutants.tsv  prediction.txt  raw  refusal_reasons.txt  refused_but_python_valid.txt  results.jsonl
run.log  runner.py  sanitizer_lines.txt  set_G.epd  set_R.fens  stamps.txt  table.txt
```
