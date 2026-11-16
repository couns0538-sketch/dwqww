# REPORT_job3 — seat 13, area 3, job 3: perft 5 on 200 R positions and the first 30 of G

## What was asked
Area 3 job 3: perft 5 on 200 R positions and on the first 30 of G.

## The answer
**230 positions, 460 (position, depth) pairs, 0 differences.** Both depths completed and compared:
perft 4 = 230/230 equal, perft 5 = 230/230 equal. Engine total at perft 5 over the 230 positions:
4,380,654,195 nodes.

## How sure
High. The comparison asserts the record count on both sides (230 x 2 = 460) and refuses to report a
pass if zero pairs were compared, after the integrity faults recorded in `../INTEGRITY_AUDIT.md`.
Contrary to my own prediction, the reference did finish — see "prediction vs result" below.

## Honesty numbers
All four pins MATCH (re-run interactively): bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920,
go perft 5 = 4865609. See `../honesty/honesty_recheck.txt`.

## Prediction vs result (my prediction was wrong, and here is how)
My committed prediction said the reference perft 5 would NOT finish for all 230 positions before
22:30, estimating ~1.6e10 nodes from a 1e6 nodes/s reference. It finished in 1,301 s (21.7 min).
Two reasons, both worth recording:
- my node estimate was too high: the real total was 4.38e9, not 1.6e10;
- I under-estimated the sharded reference throughput (4 shards ran concurrently).
Prediction items 1, 2, 4 held (0 differences; all 230 engine records OK; the depth-4 comparison I
promised as a fallback was included and also 0). Item 5 (engine under 600 s) held: 20.2 s.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R200 = first 200 of R_1301.fens; G30 = first 30 of set_G.epd | done | `R200.fens`, `G30.fens`, `all230.fens` | 230 positions |
| Prediction committed before measuring | done | `prediction.txt` | predicted 0 differences; wrongly predicted the reference would not finish |
| Engine perft 4 and 5, interactive runner | done | `raw_engine.txt` + `.meta` | 460/460 records OK, 20.2 s |
| Reference perft 4 and 5, 4 shards, fresh tempdir | done | `ref_par.py`, `raw_ref.txt`, `ref_par.log` | 460 records in 1,301 s |
| Hardened comparison | done | `compare.py`, `comparison.md` | 460 compared, 0 differing |
| Sanitizer run | not done | — | job 3 does not ask for one |

## Findings
- S-F3: move generation matches python-chess at **perft 5** on 230 positions (200 seed-1301 R
  positions + the first 30 of G): 460 pairs compared, 0 differences, including a 4.38e9-node walk.
  Show it again with
  `cd forge-combo29/swarm/13/job3 && python3 compare.py raw_engine.txt raw_ref.txt all230.fens /tmp/o.md 230`
  then `grep -E 'compared|differing' /tmp/o.md`.

## Suspicions, not proven
- None. Nothing in the data suggested a fault.

## What I did NOT do
- Perft 6 (not asked).
- The full G set at perft 5 (job 3 asks for the first 30 only).
- No sanitizer run, no timing analysis (those are other areas).

## What I am NOT sure about
- Depth 5 is deeper than jobs 1-2 but still shallow. A move-generation fault that needs a very
  specific rare configuration could survive all three jobs; my coverage is broad (5,494 distinct
  positions across jobs 1-3) but it is sampled, not exhaustive.
- My prediction's runtime estimate was wrong by a wide margin. The *result* is unaffected — the
  comparison either matches or it does not — but it is a reminder that my cost estimates are rough.

## Times
See `stamps.txt`.

## Last command output

```
$ ls
all230.fens
compare.py
comparison.md
engine_perft.py
G30.fens
perft_determinism.py
prediction.txt
R200.fens
raw_engine.txt
raw_engine.txt.meta
raw_ref.txt
refdone.txt
ref_par.log
ref_par.py
ref_perft.py
REPORT_job3.md
stamps.txt
```
