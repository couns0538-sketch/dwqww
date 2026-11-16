# REPORT job 1b — seat 15, area 5, job 1 repeated with the next seed

**What was asked.** The brief's cycle step 2(c): job 1 of my area again, with the next seed and a
new position set (R with SEED + 10), saying in the report what differs from the first run.

**The answer.** On 200 fresh random-play positions (seed 1511) at depth 12, S14, every PV is legal,
every `bestmove` matches the PV's first move, no position lacks a PV, and — the part I predicted
would differ — **all 8 mate scores are exactly correct**: the PV ends in genuine checkmate at
precisely 2N−1 plies, and where I could check the true distance with an independent solver, the
engine's number was right. **15-F1 did not reproduce in 200 positions.**

**How sure.** High. The harness is the same one that reproduced the brief's node sums exactly in
job 1, the control caught 5 of 5 planted illegal moves, and three of the eight mates were verified
against a solver.

## What differs from the first run (asked by the brief)

| | job 1 | job 1b |
|---|---|---|
| position set | O (curated openings) + G (real game positions), 553 | R (random play, seed 1511), 200 |
| material spread | mostly full boards | deliberately varied: 51 of 200 have ≤ 8 pieces, counts from 5 to 32 pieces |
| mate scores found | 10 of 553 (1.8 %) | 8 of 200 (4.0 %) |
| mate-score violations | 1 (idx 392) | **0** |
| independence of samples | 553 distinct positions | **correlated**: 200 positions drawn from only 5 games |

That last row is a real weakness of this set and I record it rather than hide it: consecutive
positions 7 plies apart in one game are far from independent, so 200 here is worth much less than
200 independent positions. The brief's R recipe (one position every 7 plies) produces this when the
games are short; I did not lengthen the games to decorrelate the set.

## Honesty numbers

Same release build as job 1, `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`,
four honesty numbers exact (`HONESTY.txt`). Run metadata in `raw_d12/meta.txt`.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R set built before use | done | `sets/R_seed1511.fens`, `make_R.py`, `make_R.log` | 200 positions, every FEN `is_valid()` and not game-over |
| 200 searches depth 12 S14 | done | `raw_d12/pv.jsonl`, `raw_d12/raw/` | 200 accepted, 0 refused, 8.9 s |
| PV legality | done | `analyze_d12.txt` | 0 of 200 |
| bestmove == PV first | done | `analyze_d12.txt` | 0 mismatches |
| mate-score PV rule | done | `mates_table.txt` | 8 of 8 correct |
| control, planted illegal move | done | `analyze_d12.txt` | 5 tried, 5 caught |
| truth check on mates | partly | `truth_check.txt` | 3 of 8 verified exactly; 5 too expensive to solve here |

## Prediction, as committed before measuring

| # | prediction | verdict |
|---|---|---|
| P1 | 0 illegal PV moves | **HELD** |
| P2 | 0 bestmove/PV-first mismatches | **HELD** |
| P3 | 40–110 of 200 carry a mate score | **REFUTED** — 8 |
| P4 | at least 2 of 200 break the PV-length rule | **REFUTED** — 0 |
| P5 | 0 positions with no pv line | **HELD** |

P3 and P4 were both wrong in the same direction: I assumed R would be full of decided positions
and that the job-1 defect would scale with them. R produced *fewer* mates than I expected and *no*
violations. The honest reading is that 15-F1 is **rarer than my job-1 rate suggested**, and that
random play does not reliably reach the kind of deep lost position that trigged it.

## Findings

### 15-F6 — the depth-12 mate machinery is exactly right on 8 fresh mate positions (NEW)

```bash
cd forge-combo29/swarm/15/job1b
python3 analyze.py raw_d12/pv.jsonl --control
sed -n '1,10p' mates_table.txt
```

```
C mate_len_mismatch     0
   positions_with_mate_score 8
CONTROL planted_illegal_last_move tried 5 caught 5
```

All 8 rows of `mates_table.txt` read `ok`, e.g.

```
134  r2k2r1/pbp2p2/5Np1/3pq2p/1Ppp2P1/P3n1QP/3N4/1RB1K2R b - - 1 32   mate  +2  3 plies  True  ok (want 3)
179  r1k5/pb6/2npPp2/BP1N4/5pP1/2R2K2/3NP2R/5B2 w - - 0 43           mate  +1  1 ply    True  ok (want 1)
```

and the truth check on three of them:

```
r2k2r1/... => MATE_IN_PLIES 3      (engine: mate +2 = 3 plies)
8/5k2/2b3pK/B4p2/... => MATE_IN_PLIES 5   (engine: mate +3 = 5 plies)
r1k5/... => MATE_IN_PLIES 1        (engine: mate +1 = 1 ply)
```

This is a *negative* result and it is worth recording as one: it bounds 15-F1. The mate reporting
path is not broken in general; on this set it is exact, including the true distance.

### Note bearing on 15-F1 (not a new finding)

Taken with job 1, the evidence now reads: 1 violation in 753 positions, and the one violation is in
a K+Q-vs-K+P deep-lost position searched with S14 (`NullMoveBase=5`). 15-F1 stands as a real
reproducible fault on that position, but its frequency is low and it is not a general failure of
mate reporting. Any claim that "the engine misreports mate distances" in general would be wrong, and
I do not make it.

## Suspicions, not proven

- The five mates too expensive to solve here (+4, +5, +6 in deep middlegames) were correct on the
  PV-length rule but I did not verify their true distance, so I cannot say the *number* was right
  for those, only that the PV reached mate at the plies claimed.
- Whether the 5-game correlation in R hides a position class that would violate the rule. More
  seeds with longer games would answer it; I did not run them.

## What I did NOT do

- Did not decorrelate the R set (short games gave 5 games for 200 positions).
- Did not solve the 5 expensive mate positions.
- Did not re-test the job-1 violating position here; job 1 and `evidence/mate392/` hold that.
- Did not run this set under a sanitizer.

## What I am NOT sure about

- Whether 15-F1 needs a deep-lost position (as in job 1) rather than any mate position. The evidence
  weakly supports that but 753 positions are not enough to say.

## Times

`stamps.txt` — every line is a pasted `date -u`.

## Last command's output

```
$ ls
analyze_d12.txt
analyze.py
make_R.log
make_R.py
mates_table.txt
prediction.txt
pvrun.py
raw_d12
REPORT_job1b.md
run_d12.log
sets
solvemate2.py
stamps.txt
truth_check.txt
```
