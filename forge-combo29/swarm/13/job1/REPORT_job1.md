# REPORT_job1 — seat 13, area 3, job 1: perft 1..4 on 5,000 R positions

## What was asked
Area 3 job 1: perft 1 to 4 on 5,000 R positions (equal count per position), comparing the engine against
python-chess, and listing every difference together with its divide.

## The answer
Over 20,000 (position, depth) pairs — 5,000 positions x depths 1,2,3,4 — the engine and python-chess agree
on **every single one**: 0 differences. No refusal, no error, no timeout, no illegal marker on either side.

## How sure
High for the depth-1..4 agreement itself: same positions, same depth, values compared field by field, and the
comparison tooling is shown to be able to report a difference (control B). Not measured here: depth 5 (job 3),
and positions the engine accepts but python-chess refuses (the "accepted and INVALID" class of area 1) are
outside this job's scope — every R position is one python-chess itself generated, so it is valid by construction.

## Honesty numbers
All four pins MATCH on this build (see ../HONESTY.txt): bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, go perft 5 = 4865609.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R position set generated with SEED 1301 (random legal games, one position every 7 plies) | done | `R_1301.fens`, generator `gen_R.py` | 5,000 FENs from 111 games |
| Prediction committed before measuring | done | `prediction.txt` | 0 differences predicted; range on runtime 400–3000 s |
| Engine harness written to file and run from there | done | `engine_perft.py`, `raw_engine.txt`, `raw_engine.txt.meta` | 20,000 records, all marker OK |
| Reference harness (python-chess), sharded over 4 cores | done | `ref_perft.py`, `ref_par.py`, `raw_ref.txt` | 20,000 records, all marker OK |
| Comparison of all records | done | `compare.py`, `comparison.md` | 0 differing pairs at every depth |
| Control: published values reproduced on both sides | done | `control.py`, `control.md` | PASS (startpos 1–5, Kiwipete 1–4) |
| Control: planted wrong number caught by the checker | done | `control.md` | PASS (exactly 1 differing pair reported) |
| Depth-5 comparison | not done | — | this is job 3, not job 1 |

Per-depth summary (pasted from `comparison.md`):

```
depth | engine records | ref records | equal | differing | engine-not-ok | ref-not-ok
1 | 5000 | 5000 | 5000 | 0 | 0 | 0
2 | 5000 | 5000 | 5000 | 0 | 0 | 0
3 | 5000 | 5000 | 5000 | 0 | 0 | 0
4 | 5000 | 5000 | 5000 | 0 | 0 | 0
```

Total perft nodes walked, summed from `raw_engine.txt`: depth 1 = 113,231; depth 2 = 2,678,512;
depth 3 = 77,182,397; depth 4 = 2,260,227,623.

## Findings
- S-F1: **no move-generation difference** between this engine and python-chess at depth 1–4 on 5,000
  seed-1301 random positions (20,000 pairs, 0 differences). Show it again with
  `cd forge-combo29/swarm/13/job1 && python3 compare.py raw_engine.txt raw_ref.txt R_1301.fens /tmp/out.md`
  then `grep 'TOTAL differing' /tmp/out.md`. This is a null result, reported as such: it says the move
  generator is right *on these positions*, not that it is right everywhere (see "not sure" below).

## Suspicions, not proven
- None from this job. Nothing in the data hinted at a fault; with 0 differences there is no locus to suspect.

## What I did NOT do
- Depth 5 and the first 30 of G: that is job 3.
- I did not test positions python-chess refuses but the engine accepts (area 1's ground). My R set is
  python-chess-generated, so it cannot contain them; perft comparison there needs a different reference.
- I did not run this under a sanitizer; job 1 does not ask for it and a 2.26e9-node ASan run is not
  affordable on this 4-core machine within the per-command limit.

## What I am NOT sure about
- The runtime prediction range (400–3000 s) was for the whole run; the measured engine side took 12.2 s and the
  reference side about 850 s wall across 4 shards. The *engine* was far faster than my prediction assumed —
  my range was not killed as a total, but it was far too loose to be a useful test, and I say so.
- Coverage: 5,000 positions concentrated in the opening and early middlegame of random games. Endgame perft
  (few pieces, many promotion races) is under-represented because random games rarely reach it. A difference
  that only shows in sparse endgames could hide behind this 0.

## Times
See `stamps.txt`.

## Last command output
```
$ ls
compare.py
comparison.md
control_cmp.md
control_engine.txt
control_engine.txt.meta
control.fens
control.md
control_mutant.txt
control.py
control_ref.txt
engine.log
engine_perft.py
gen_R.py
prediction.txt
R_1301.fens
raw_engine.txt
raw_engine.txt.meta
raw_ref.txt
ref.log
ref_par.log
ref_par.py
ref_perft.py
REPORT_job1.md
run1.log
run1.sh
run1.status
run2.log
run2.sh
run2.status
stamps.txt
```
