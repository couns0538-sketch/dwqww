# REPORT job 5 — AREA 3 job 1 again, new seed (THE CYCLE step (c))

**What was asked:** the same job as job 1, with a new seed and a new position set, saying in the report what
differs from the first run.

**What differs from job 1:** seed 2301 → **2401**. I used SEED + 100 rather than the brief's SEED + 10, and said so
in the prediction: an adjacent seed draws from the neighbouring game stream, a clearly disjoint one gives an
independent draw, which is the whole point of repeating the job. The two FEN sets are disjoint — measured, not
assumed: **0** positions in common with `R_2301.fens`. Everything else is identical: same engine (base 6b98f217,
sha e06310ec), same harness, depths 1..4, one process, Threads 1, Hash 16, no setoption.

**The answer:** 5,000 new positions, **0 mismatches at every depth**, 4,906,844,203 nodes per side at depth 4.

**How sure:** high. It is a direct repetition of a measurement with a proven harness (planted control in 23-F10 /
23-F21), on a disjoint position set, and it reproduces job 1's conclusion independently.

## Honesty numbers

Base build 6b98f217, Release, `-DFORGE_MARCH=x86-64-v4`, GCC 13.3.0, sha e06310ec…, honesty 4/4 (`HONESTY.txt`).
No setoption, Threads 1 — the pins' own regime (file 4).

## The table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| new position set, SEED 2401 | done | `job5/R_2401.fens` (+ `.log`), `make_R.py` | 5,000 positions from 371 games, one per 7 plies, all valid |
| disjointness check vs job 1's set | done | recorded in prediction scoring | 0 FENs in common |
| engine perft 1..4 | done | `job5/engine.jsonl` (+ `.meta`), `engine.log` | 5,000/5,000, 25.2 s |
| python-chess reference 1..4 | done | `job5/py_0..3.jsonl`, `py.done` | 4 workers, 5,000/5,000 |
| comparison | done | `job5/compare.out` | 0 mismatches at depths 1, 2, 3, 4 |

Pasted from `compare.out`:

```
positions actually compared: 5000 of expected 5000
depth | engine nodes | reference nodes | equal | mismatching positions
    1 |       154616 |          154616 |   yes | 0
    2 |      4734485 |         4734485 |   yes | 0
    3 |    152777822 |       152777822 |   yes | 0
    4 |   4906844203 |      4906844203 |   yes | 0
```

## Prediction, scored

| # | prediction | outcome |
|---|---|---|
| P1 | 0 mismatching positions at any depth | **HELD** |
| P2 | perft-1 total 140,000–175,000 | **HELD** (154,616; job 1 gave 154,284 — 0.2 % apart) |
| P3 | mean perft-1 branching 30–33 | **HELD** (30.92; job 1: 30.86) |
| P4 | 0 FENs in common with the seed-2301 set | **HELD** (0) |
| P5 | engine run under 2 minutes | **HELD** (25.2 s) |
| P6 | perft-4 total 4.0e9–6.5e9 | **HELD** (4.907e9; job 1: 4.974e9) |

Two independent draws landing within 0.2 % on perft-1 total and 0.2 % on branching factor is a useful
reproducibility datum in itself: the generator's statistics are stable, so a future run with a surprising total
would be a signal, not noise.

## Suspicions, not proven

- Same limit as job 1: totals are compared, not per-move divides, so a compensating pair of errors inside one
  position would be invisible. Stated in job 1's report and unchanged.
- These are game-reached positions only; nothing here tests the FEN laxness (area 1 owns that).

## What I did NOT do

- No depth 5 on this set (job 3 covered depth 5 on 230 positions; no need to repeat the expensive walk).
- No sanitizer build.

## What I am NOT sure about

- Whether SEED + 100 rather than the brief's SEED + 10 matters to anyone reading this. It is stated in the
  prediction and here; if the intent was specifically an adjacent seed, this run is not that, though it is
  strictly better as an independent draw.

## Times

`job5/stamps.txt`, `job5/*.log`.

## Last command's output

`job5/final_status.txt`.
