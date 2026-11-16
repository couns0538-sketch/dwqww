# My findings re-run on the PC build under PC20

seat 19 · area 9 · build **PC r15** (FABLE_TO_swarm_5 patch, sha256 `d6bd72c531f785f4…`) · **Threads 1** throughout.

File 5 asks: run my own base-tree finds on the PC build under PC20, and say in each finding line which build
and settings it used. This is that re-run.

## Summary table

| my finding | build + settings | state on PC r15 under PC20 | evidence |
|---|---|---|---|
| **19-F12** quit/EOF fabricates a bestmove | PC r15, none **and** PC20 | **STILL PRESENT** | `pcver/quitabort_pc/`, `pcver/quitabort_pc20/` |
| **19-F25** *which* fabrication (the refinement) | PC r15, none | **first generated move**, not stale, not literal | `pcver/f12path/` |
| **19-F15** tie order is load-bearing | PC r15, none **and** PC20 | **STILL PRESENT**, and identical numbers on the none regime | this file §2 |
| **19-F20** which pins see an ordering change | PC r15, PC20 | **all three bench depths see it; perft 5 cannot** | §3 |
| **19-F21** timing noise floor ±2.29 % at 10 rounds | PC r15, none, 6 rounds | **holds at ±2.91 % at 6 rounds** (consistent: fewer rounds, wider CI) | §4 |
| 19-F22 warm vs cold | PC r15 | not re-run | — |
| 19-F23 bench is self-clearing | PC r15 | not re-run (mechanism is in `uci.cpp`'s bench loop, unchanged by the patch) | — |
| 19-F16/F17 toolchain pins | base tree | not applicable to PC r15 | — |
| 19-F18/F19 | — | **retracted** (warm state), see `CORRECTION_19F18.md` | — |

## 2. 19-F15 on the PC build — and a striking coincidence

The `std::sort` → `std::stable_sort` ablation, **none** regime (fresh process per line, Threads 1):

| pin | PC r15 | PC r15 + stable_sort | base tree + stable_sort (earlier) |
|---|---|---|---|
| bench 11 | 312,866 | **292,627** | 292,627 |
| bench 13 | 862,329 | **939,494** | 939,494 |
| bench 16 | 3,024,920 | **2,925,608** | 2,925,608 |
| perft 5 | 4,865,609 | 4,865,609 | 4,865,609 |

**The PC build's post-ablation numbers are identical, digit for digit, to the base tree's.** The PC patch
changes 11 files and ~1,200 lines, yet the same one-word sort change produces exactly the same perturbed node
counts. That is a strong statement about where this effect lives: it is a property of the picker's tie order and
of how the tree responds to it, not of anything the PC patch touches — and the patch's own switches
(`CuckooRep`, `HistRework 2`, `TtPruneV2`, `CorrHistV2`, the bare-king fixes) are all off or inactive in the
none regime, which is the most likely explanation. I have not proven that explanation; I am recording the
coincidence because it is exact.

Under **PC20** (S14 + the six), same ablation:

| pin | PC20 | PC20 + stable_sort | change |
|---|---|---|---|
| bench 11 | 278,024 | 254,023 | **−8.6 %** |
| bench 13 | 587,276 | 620,794 | **+5.7 %** |
| bench 16 | 2,343,893 | 1,998,716 | **−14.7 %** |

So 19-F15 holds on the PC build under the settings the owner actually uses. **The owner's own node-count pins
are sensitive to picker tie order under PC20** — which is the practical consequence, and it applies to the PC
build itself, not just to the base tree.

## 3. 19-F20 on the PC build under PC20

Same ablation, PC20, all pins measured:

| pin | sees an ordering change? |
|---|---|
| bench 11 | **yes**, −8.6 % |
| bench 13 | **yes**, +5.7 % |
| bench 16 | **yes**, −14.7 % |
| perft 5 | **no** (perft never uses the picker) |

19-F20's rule — a bench pin is sensitive to anything that changes the search tree and blind to cost in a
rarely-taken path — reproduces on the PC build with the same shape as on base: the three bench depths all
move, and they disagree in direction (11 and 16 down, 13 up), which is why quoting one depth is not enough.

## 4. 19-F21 noise floor on the PC build

`job4/noise_floor.py` with PC r15, base against base, 6 alternating rounds, R_1911 first 200, depth 12:

| quantity | PC r15 | base tree (10 rounds, for comparison) |
|---|---|---|
| node total, identical every run | 316,716 | 286,628 |
| sd of sweep time | 3.10 % / 1.91 % | 3.01 % / 2.14 % |
| A-vs-B ratio (true 1.0) | 0.9924 | 0.9956 |
| **95 % CI half-width** | **±2.91 % (6 rounds)** | **±2.29 % (10 rounds)** |

Consistent: fewer rounds gives a wider interval, and the underlying per-run spread (≈2–3 %) is the same on both
builds. So 19-F21's method and its conclusion — a timed sweep of this workload resolves a few percent at
reasonable cost, and nothing smaller — hold for the PC build. **The numbers to quote for the PC build are
±2.9 % at 6 rounds, or ≈±2.2 % at 10 rounds** by the 1/√n law.

## 5. What I did NOT do

- I did not re-run 19-F22 (warm vs cold) on PC r15. It should be re-run before anyone trusts a PC-build table
  that shares a process between positions.
- I did not re-run 19-F23 (bench self-clearing) on PC r15 — the patch does not touch the bench loop, but that
  is a reading, not a measurement.
- I did not build PC r15 with `FORGE_FIX_ABORT_PUBLISH=1` to see whether 19-F12 survives a build that actually
  compiles the fix in. Named as open in `REPORT_19F12_path.md` §6.
- The 19-F15 PC20 numbers are a single run per pin, not repeated; they are node counts, which are
  deterministic at Threads 1, so repetition would add nothing — but I state that rather than imply I repeated.

## Files

`pcver/pc20_bench.sh`, `pcver/quitabort_pc/`, `pcver/quitabort_pc20/`, `pcver/f12path/`,
`pcver/noise_pc/RESULT.txt`, `REPORT_19F12_path.md`, `REPORT_pcbuild.md`.
