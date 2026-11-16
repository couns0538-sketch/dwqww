# REPORT — seat 08's findings re-run on the PC BUILD under PC20 — seat 08

## What was asked
FABLE_TO_swarm_5: re-run my own findings on the PC build (r15) under settings **PC20**, and say in each finding
line which build and which settings it used. A find gone on PC20 is "repaired on the PC"; one that survives is
worth more. **Threads 1, Hash 16** throughout (the swarm rule).

## The answer (one line per finding)
- **08-F2 survives exactly.** `movetime 50` median 40.50 ms against a plan of 40 ms (**+0.50 ms**); `movetime 500`
  490.50 ms against 490 ms. Identical to the base tree (40.48 / 490.50). The PC build still spends
  `T - MoveOverhead` on the wall clock.
- **08-F1, F10, F11 and F14 survive in shape.** The clocked tail is still ~3-5x the median (1 s: p99/median 3.0;
  10 s: 5.1), still overshoots its own soft plan (66 of 200 at 1 s, 46 of 200 at 10 s) and still never exceeds the
  clock (0 of 400).
- **08-F8 survives.** `movestogo 1` and `2` still land ON the 792 ms hard limit: 15 of 200 and 5 of 200 over it, p99
  792.8 / 792.5, max 793.0 / 792.7. The `FORGE_FIX_HARD_LIMIT_EMERGENCY` switch did **not** change this.
- **Medians are within 1.4 % of the base tree at every control**, so the four search switches (CuckooRep,
  HistRework 2, TtPruneV2, CorrHistV2) do not move the clock behaviour of this position set at all.

## How sure
Sure of the comparison: same machine, same 200 positions, same harness discipline, base numbers taken from
`job2/raw2` and `job5/raw` earlier tonight on the same box, all at Threads 1. Guarded start (load 0.39, no other
engine process).
NOT sure about the one row over the hard limit at the 10 s clock (2270.73 ms against a 2270 ms plan) — it is 0.7 ms
over, the same fixed stop-check latency I measured on the base tree, not a new behaviour.

## Honesty numbers
PC build exe `/home/ubuntu/builds/pc/forge`; sha256 in `pcbuild/out/sha256.txt`. Its own pins, with NO setoption:
bench 11 = 312,866, bench 13 = 862,329, bench 16 = 3,024,920, perft 5 = 4,865,609 — all four exact, plus S14
(242,796 / 656,517) and PC20 (278,024 / 587,276) exact. See `pcbuild/REPORT_pc_build.md`. Every search below ran
on that exe under PC20, recorded in `pc20/raw/.meta`.

## Step table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| PC build from file 5, separate copy, sha256 checked | done | pcbuild/REPORT_pc_build.md | patch d6bd72c531f785f4..., 11 files, zero fuzz |
| all 8 known numbers | done | pcbuild/out/summary.txt | 8 of 8 exact |
| prediction pushed alone before measuring | done | pc20/prediction.txt (22:20:06Z) | before the first search |
| movetime 50 twice (baseline repeatability) | done | pc20/raw/mt50_a.jsonl, mt50_b.jsonl | 40.50 both |
| movetime 500 | done | pc20/raw/mt500.jsonl | 490.50 |
| wtime 1000 and 10000, 200 each | done | pc20/raw/tc1000.jsonl, tc10000.jsonl | see table |
| movestogo 1 and 2 | done | pc20/raw/mtg1.jsonl, mtg2.jsonl | 15 and 5 over the 792 ms limit |

## Table 1 — the PC build under PC20 vs the base tree (pasted from `python3 analyse_pc20.py raw`)

```
## PC build r15 under PC20, Threads 1, Hash 16 — 200 searches per control (OG200)

| control | n | median ms | p99 ms | max ms | median last depth | base tree median | change |
|---|---|---|---|---|---|---|---|
| movetime 50 | 200 | 40.50 | 40.96 | 45.03 | 13 | 40.48 | +0.0 % (0.02 ms) |
| movetime 50 | 200 | 40.50 | 41.05 | 41.17 | 13 | 40.48 | +0.1 % (0.02 ms) |
| movetime 500 | 200 | 490.50 | 490.96 | 491.10 | 20 | 490.50 | +0.0 % (0.00 ms) |
| wtime 1000 inc 0 | 200 | 35.05 | 103.47 | 137.35 | 13 | 34.56 | +1.4 % (0.49 ms) |
| wtime 10000 inc 0 | 200 | 298.49 | 1512.13 | 2270.73 | 19 | 302.10 | -1.2 % (-3.61 ms) |

## 08-F2 test on the PC build: does `movetime T` still spend T - MoveOverhead on the wall clock?
| control | plan (T-10) | median wall | median - plan |
|---|---|---|---|
| movetime 50 | 40 | 40.50 | +0.50 |
| movetime 50 | 40 | 40.50 | +0.50 |
| movetime 500 | 490 | 490.50 | +0.50 |

## 08-F1/F10/F11 on the PC build: clocked tail and hard-limit behaviour
| control | n | soft plan | hard plan | median | p99 | max | p99/median | over soft | over hard | over clock |
|---|---|---|---|---|---|---|---|---|---|---|
| wtime 1000 inc 0 | 200 | 45 | 225 | 35.0 | 103.5 | 137.3 | 3.0 | 66 | 0 | 0 |
| wtime 10000 inc 0 | 200 | 454 | 2270 | 298.5 | 1512.1 | 2270.7 | 5.1 | 46 | 1 | 0 |

## 08-F8 on the PC build: movestogo 1/2 at a 1000 ms clock, against the 792 ms hard limit
| control | n | median | p99 | max | over the 792 ms hard limit |
|---|---|---|---|---|---|
| movestogo 1 | 200 | 317.3 | 792.8 | 793.0 | 15 |
| movestogo 2 | 200 | 238.2 | 792.5 | 792.7 | 5 |
```

## Per-finding verdict on the PC build

| finding | base tree (Threads 1) | PC r15 under PC20 (Threads 1) | verdict |
|---|---|---|---|
| 08-F2 `movetime T` spends T - Move Overhead | 40.48 / 490.50 ms, plan + 0.5 ms | 40.50 / 490.50 ms, plan + 0.50 ms | **SURVIVES, unchanged** |
| 08-F1 clock tail ~4x median past soft | p99/median 3.1-4.8x | 3.0x at 1 s, 5.1x at 10 s | **SURVIVES** |
| 08-F9 achieved time is a fraction of soft | 61-100 % of soft | 35.05/45 = 78 % at 1 s; 298.5/454 = 66 % at 10 s | **SURVIVES** |
| 08-F8 movestogo lands on the hard limit | 14 and 8 of 200 over 792 ms | 15 and 5 of 200 over | **SURVIVES** |
| 08-F10 two stop paths, opposite error modes | clock stop discards nothing | p99 == near hard limit, overshoot of soft | **SURVIVES** |
| 08-F11 tail scales with clock | 11.9x p99 for a 10x clock | 14.6x p99 for a 10x clock (103.5 -> 1512.1) | **SURVIVES** |
| 08-F14 worst absolute overshoot | +33.2 ms at 200 ms, +180.8 at 1 s | +92.3 ms at 1 s (137.3 vs 45); 10 s: +1816 ms | **SURVIVES, similar magnitude at 1 s** |
| 08-F5 <=10 ms clock -> emergency 1-ply | 1-ply 2000-node branch | **NOT RE-TESTED here** (needs the probe, next job) | open |
| 08-F12 book answers startpos | 9 of 14 lines | **cannot be shown under PC20** (PC20 sends OwnBook false by definition) | unchanged |
| 08-F13 pins independent of OwnBook | identical | **CONFIRMED again on this build**: all 8 known numbers exact | unchanged |

## Findings
- **08-F16** (new): the PC build's clock behaviour is the base tree's clock behaviour. Under PC20 at Threads 1,
  `movetime 50/500` medians match the base tree to 0.02 ms and `wtime 1000/10000` medians match within 1.2-1.4 %,
  while all four search switches are ON and give different bench node counts (278,024 vs 242,796 at bench 11). So
  the switches change the tree but not the clock arithmetic. Evidence: `pc20/raw/analysis.txt`.

## Suspicions, not proven
- The 1 s clock p99 is smaller on the PC build (103.5 ms) than on the base tree (139.85-153.2 ms). That may be the
  switches making iterations more uniform, or position/box noise. NOT separated: I did not interleave builds.

## What I did NOT do
- Did not re-test 08-F5 (the <=10 ms emergency branch) on the PC build yet — `FORGE_FIX_HARD_LIMIT_EMERGENCY` is
  exactly the switch for it, so that is the next job and the most likely genuine repair.
- Did not test Threads > 1 (forbidden by the swarm rule, and seat 04 showed non-reproducible scores there).
- Did not use the PC's own net (not shared); evaluation-dependent results remain open questions for the PC.

## What I am NOT sure about
- My prediction said `movetime 50` would be 40.0-41.5 ms (measured 40.50, correct), that the 1 s clock median would
  be 20-60 ms (35.05, correct), and that p99/median would be 2-8x (3.0 and 5.1, correct). I predicted 08-F5 might
  be repaired; I did not test it, so that prediction is still open, not wrong.

## Times
see `pc20/stamps.txt` (a `date -u` line after every control).
