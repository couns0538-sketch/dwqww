# REPORT_job1b — seat 13, area 3, job 1 REPEAT (cycle step c): perft 1..4 on a second 5,000-position set

## What was asked
The brief's cycle step (c): once all three area jobs are done, job 1 again with the next seed and a
new position set, and say in the report what differs from the first run.

## The answer
**20,000 of 20,000 (position, depth) pairs compared, 0 differing.** Same verdict as the first run,
on a completely different set of positions, measured with the hardened tooling.

## How sure
High, and more so than the first run, because this run used the checker that fails loudly. The
first run used a `compare.py` that skipped missing records silently; this one refuses to report a
pass unless every pair is present and numeric on both sides.

## What differs from my first run (as the brief asks)
1. **Seed 1301 -> 1311.** An entirely different 5,000 positions from different random games (same
   generator, one position every 7 plies, 111 games).
2. **Hardened tooling.** `compare.py` now raises on an empty, truncated or non-numeric reference
   file and refuses to pass with zero pairs compared; `ref_par.py` uses a fresh tempdir and asserts
   each shard's record count. My first run used the version with the silent-skip hole described in
   `../INTEGRITY_AUDIT.md`, so this repeat is the first job 1 result I would defend without caveat.
3. **Sharded reference.** The first run's reference was one serial pass (~850 s); this is 4-way
   sharded with asserted counts (612 s).

## Honesty numbers
All four pins MATCH, re-run interactively: bench 11 = 312866, bench 13 = 862329,
bench 16 = 3024920, go perft 5 = 4865609. See `../honesty/honesty_recheck.txt`.

## Prediction vs result
| predicted | predicted value | actual | verdict |
|---|---|---|---|
| differing pairs | 0 | 0 | held |
| pairs compared | 20,000 (all present, numeric) | 20,000 | held |
| engine runtime | under 120 s | 12.3 s | held |
| a difference would be rare, not systematic | if any, <= 100 positions | no differences at all | held trivially |

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| New set from SEED 1311 | done | `gen_R.py`, `R_1311.fens` | 5,000 FENs, 111 games |
| Prediction before measuring | done | `prediction.txt` | 0 differences predicted |
| Engine perft 1..4, interactive runner | done | `raw_engine.txt` + `.meta` | 20,000 records, all OK, 12.3 s |
| Reference perft, 4 shards, fresh tempdir, counts asserted | done | `ref_par.py`, `raw_ref.txt`, `ref_par.log` | 20,000 records = 5,000 x 4, 612 s |
| Hardened comparison | done | `compare.py`, `comparison.md` | 20,000 compared, 0 differing |

## Findings
- S-F4: the perft 1..4 agreement from job 1 **reproduces on an independent seed** — 5,000 fresh
  positions (SEED 1311), 20,000 pairs, 0 differences — so job 1's null result is not an artefact of
  one lucky position set. Show it again with
  `cd forge-combo29/swarm/13/job1b && python3 compare.py raw_engine.txt raw_ref.txt R_1311.fens /tmp/o.md 5000`
  then `grep -E 'compared|differing' /tmp/o.md`.

## Suspicions, not proven
- None.

## What I did NOT do
- Perft 5 on this set (job 1 is 1..4; job 3 covered depth 5 on 230 positions).
- No sanitizer.

## What I am NOT sure about
- Both sets come from the same generator, so they share its bias: random games cluster in the
  opening and early middlegame and rarely reach sparse endgames. Two seeds test the *sampling*, not
  the *generator*; a class of position this generator never produces is still untested by jobs 1
  and 1b. Jobs 2 and 3 partly cover that with selected special positions.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
compare.py
comparison.md
engine_perft.py
gen_R.py
prediction.txt
R_1311.fens
raw_engine.txt
raw_engine.txt.meta
raw_ref.txt
refdone.txt
ref_par.log
ref_par.py
ref_perft.py
REPORT_job1b.md
stamps.txt
```
