# TT VALIDATION RECIPE — how to measure a transposition-table change where the table actually fills

seat 19 · area 9. A short recipe as asked: the command line, the exact expected counters, the runtime, and
the ranges that mean "you ran it right".

## Why this file exists

19-F18 showed that `bench 13` reaches the transposition table's age/depth replacement scan on
**50 of 861,904 probes (0.006 %)**, while the R_1911 set at the same Hash 16 reaches it on
**8,310,172 of 15,184,039 probes (54.7 %)**. Any TT patch validated on `bench` alone is therefore exercised by
almost nothing. This is the substitute: a workload where the code under test actually runs, with counters that
are **bit-for-bit deterministic** (three reps, identical output — `job4/determinism.txt`).

## The recipe

```
# 1. build the instrumented engine (scratch copy, never committed as a patch)
cd ~ && cp -a base/forge-combo29 tt && cd tt
python3 <swarm19>/job4/instrument_tt.py
# hook dump_tt_counters() into main() of src/uci.cpp, then:
cmake -S . -B ~/tt_build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ && make -C ~/tt_build -j4

# 2. run it over the workload, Hash pinned to 16 so the comparison matches bench
python3 <swarm19>/job4/drive_hash16.py ~/tt_build/forge <swarm19>/job1b/R_1911.fens out.err 16
```

`R_1911.fens` is at `forge-combo29/swarm/19/job1b/R_1911.fens` — 11,192 positions (400 random python-chess
games with seed 1911, one position every 7 plies); the recipe takes the **first 200**.

**Runtime: 8.3–8.5 s** for 200 positions at depth 12 (three reps: 8,314 / 8,373 / 8,543 ms).

## Expected counters on the unmodified 6b98f217

If you get exactly these, you reproduced it:

```
Hash 16 MB | positions 200 | total nodes 15238023 | zero-node searches 0
TTPROBE calls=15184039 hit=5334400 stale_gen=23278 full=8310172 empty_none=0 \
        hit_slot=1387446/1353887/1328984/1264083 empty_slot=363224/389915/395562/390766
```

| quantity | expected value | accept range |
|---|---|---|
| probes (`calls`) | 15,184,039 | any change means the search changed — that is the point |
| hit rate | 35.1 % | 30–40 % |
| full-table misses (`full`) | 8,310,172 = **54.7 %** | **45–65 %** |
| misses finding an empty slot | 10.1 % | 5–20 % |
| `empty_none` | **0** | must be 0; anything else means the instrumentation missed a path |
| zero-node searches | **0** | must be 0; anything else means you hit 19-F12 (a terminator during a search) |
| hit slot spread (0/1/2/3) | 26.0 / 25.4 / 24.9 / 23.7 % | should be near-flat; heavy slot-0 skew means you ran bench by mistake |

## How to use it on a TT patch

1. Run the recipe on the **base** build and on the **patched** build.
2. `calls`, `hit`, `hit_slot` and `empty_slot` should be **identical** if the patch does not change the search
   (a pure probe-path optimisation). If they move, the patch changed which entries are found — that is a
   behaviour change and it must keep the four honesty numbers, and then it is a search change, not a
   speed-only change.
3. `full` is the counter that says your patch's code is being exercised: if it is under ~45 %, you are on a
   workload that does not stress the replacement path (bench gives you 50, which is 0.006 %).
4. For the *speed* claim, use the alternating protocol in `job2/pair_bench.sh` / `job2/ratio_ci.py`, but note
   those drive `bench`. A timing version of this recipe needs its own paired runner; I did not write one in
   the time available and I am not claiming a speed number here.

## Honest limits

- The counters measure **probe activity**, not time. A patch that removes work from the replacement scan will
  show the same `full` count (the scan still runs) — the counter proves the code is *reached*, not that it
  is *faster*.
- 54.7 % is a property of this position set at depth 12 with Hash 16. A different set will differ; the
  accept range in the table is deliberately wide.
- The instrumented build is a scratch build in `~/tt`, not a committed patch. Only the script is committed.

## Files

`job4/instrument_tt.py`, `job4/drive_hash16.py`, `job4/tt_R1911_hash16.err`, `job4/determinism.txt`,
`job1b/R_1911.fens`.
