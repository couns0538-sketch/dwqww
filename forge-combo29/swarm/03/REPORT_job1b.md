# REPORT — seat 03, area 3, job 1 RE-RUN with SEED 311 (cycle step 2c)

**What was asked.** The cycle's step 2(c): once jobs 1-3 are done, run job 1 of my area again with the next seed
(311 = SEED + 10) and a new position set, and say in the report what differs from the first run.

**The answer.** Engine side: perft 1..4 on 5,000 new positions, sums 112,193 / 2,606,301 / 74,557,281 /
2,159,914,969, 0 restarts, 0 error lines, and 0 FENs shared with the SEED-301 set. The python-chess side is
**in progress** at the deadline; the comparison is therefore **not done** and is marked so below with the exact next
command.

**How sure.** Sure of the engine numbers (asserted integers at every depth for all 5,000 positions). The agreement
claim is not made yet.

## What differs from the first run (as the cycle requires)

| | first run (job 1) | this run (job 1b) |
|---|---|---|
| seed | 301 | 311 |
| position set | 5,000 FENs from 104 random games | 5,000 FENs from 105 different random games, sha256 `d9954567994ed77bb8745293723eaded8552a2fd9a9af2bf993c042281dd5833` |
| overlap with the other set | — | **0 identical FENs** (measured with `comm`) |
| engine perft-4 sum | 2,196,757,662 | 2,159,914,969 |
| mean perft-1 branching | 22.731 | 22.439 |
| harness | job1/engine_perft.py, job1/py_perft.py, job1/compare.py | the same three files, unchanged |
| extra check | root move SET comparison | planned, plus the same set comparison if time allows |

So the only things that changed are the seed and therefore the positions; the method is identical by design, which
is what makes the two runs comparable.

## Honesty numbers

bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all MATCH (HONESTY.txt, re-proved by
honesty2.py). Perft is cold-equivalent in a warm process (measured in WARM_STATE_AUDIT.md: 1,110,595 ten times in
one process), so running 500 positions per process is safe here.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction pushed alone | done | job1b/prediction.txt | pushed before any measuring command |
| position set generated (seed 311) | done | job1b/set_R311.fens, job1b/stamps.txt | 5,000 fens, 105 games |
| duplicate check vs SEED-301 set | done | `comm -12 <(sort set_R311.fens) <(sort ../job1/set_R.fens)` -> 0 | 0 shared FENs |
| engine perft 1..4 | done | job1b/eng.json (+ .raw/) | 27.1 s, 0 restarts, 0 error lines |
| assertion | done | ../assert_measured.py | `OK ... sums [112193, 2606301, 74557281, 2159914969]` |
| python-chess perft 1..4 | running | job1b/py.log | see the deadline note |
| comparison | not done | — | needs the line above |
| root move SET comparison | not done | — | after the comparison |

## Numbers so far (pasted)

```
$ python3 ../assert_measured.py perft eng.json 4 5000
OK eng.json: 5000 positions x depths 1..4 all integer; sums [112193, 2606301, 74557281, 2159914969]
```

## Prediction against result (engine half)

| # | predicted | killed? | measured |
|---|---|---|---|
| 1 | 0 differing pairs | unknown | python side running |
| 2 | 0 positions differ | unknown | python side running |
| 3 | 0 refused FENs | unknown | python side running |
| 4 | 0 crashes/restarts/error lines | no | 0 / 0 / 0 |
| 5 | perft(4) sum in 2.0e9..2.4e9 | no | 2,159,914,969 |
| 6 | mean branching 21.5..23.5 | no | 22.439 |
| 7 | 0 duplicate FENs vs SEED-301 | no | 0 |
| 8 | 0 root move set disagreements | unknown | not run yet |

## Findings

No finding is claimed from this job until the python side and the comparison land; the engine half alone
establishes nothing new (job 1 already showed depth 1..4 agreement on a different random set).

## What I did NOT do

- Did not finish the comparison (python side in progress at the deadline).
- No sanitizer run (not asked for this job).

## What I am NOT sure about

- Whether the second set would show the same zero if the engine had a position-dependent fault that the first set
  happened to miss; with 0 duplicate FENs the sets are independent, so a comparison over both is stronger than
  either alone — that is exactly what the pending comparison adds.

## Times

`job1b/stamps.txt`, `job1b/py.log`.

## Exact next command

```
cd forge-combo29/swarm/03/job1b && tail -1 py.log \
  && python3 ../assert_measured.py perft py.json 4 5000 \
  && python3 ../job1/compare.py eng.json py.json diffs.txt | tee table.txt \
  && python3 ../job2/divide_sets.py ~/build-rel/forge set_R311.fens div311.txt 250 > div311_summary.txt
```
