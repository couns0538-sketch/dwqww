# What makes the PC build stop at 0.62 of soft where base stops at 0.76 — the answer is the SWITCHES, not the code

Answer to the question in S-F26. Verdict: **the source is equivalent; the difference is a runtime quantity,
and it is the four PC20 search switches making each iteration cheaper so fewer fit before the stop.**

## 1. The stop-decision source is byte-identical

Diffed the exact region — the soft-limit decision block that runs after every completed iteration:

```
diff of base search.cpp:2560-2640 vs PC r15 search.cpp:2937-3017
→ 0 differing lines
```

All five plan inputs and every soft-factor default are equal too, read from each exe's own `uci` answer AND
from source:

| constant | base | PC r15 |
|---|---|---|
| Move Overhead | 10 | 10 |
| TmSoftDivisor | 22 | 22 |
| TmIncrementPercent | 75 | 75 |
| TmHardPercent | 60 | 60 |
| TmHardSoftMultiple | 5 | 5 |
| TmStableFactor | 60 | 60 |
| TmSemiStableFactor | 80 | 80 |
| TmUnstableFactor | 140 | 140 |
| TmMinFactorPercent | 45 | 45 |
| TmFinishIteration | false | false |
| TmNodeShare | false | false |

The only soft-limit write anywhere in the PC patch is inside `FORGE_FIX_HARD_LIMIT_EMERGENCY`
(`soft_limit_ms_ = hard_limit_ms_ = 0`), and that path can only fire when `elapsed_ms() >= hard_limit_ms_`
at search entry — 2270 ms at wtime 10000 — which no search here reaches (they end at ~300 ms). **So the
emergency fix is not the cause.**

## 2. The stop fraction is not noise, and it tracks the switches

Two repeats per cell on each build, 24 positions, `go wtime 10000`, Threads 1 (`stopcause_base.txt`,
`stopcause_pc20.txt`):

| build | run | median achieved | achieved/soft | median #iterations | median last-iteration cost |
|---|---|---|---|---|---|
| base | 1 | 346.8 | 0.764 | 20 | 98 ms |
| base | 2 | 349.3 | 0.769 | 20 | 98 ms |
| PC20 | 1 | 282.8 | 0.623 | 19 | 60 ms |
| PC20 | 2 | 287.3 | 0.633 | 19 | 62 ms |

The gap is ~0.14 of soft and is stable within each build, so it is a real difference and not sampling.

## 3. It is the switches, proven by turning them off on the SAME binary

`switch_isolate.py`, 24 positions, wtime 10000, one switch off at a time (`switch_isolate_out.txt`):

| configuration | achieved/soft | median #iter | median last depth |
|---|---|---|---|
| PC20 (all on) | 0.640 | 19 | 19 |
| CuckooRep off | 0.668 | 19 | 19 |
| HistRework off | 0.711 | **20** | **20** |
| TtPruneV2 off | 0.738 | **20** | **20** |
| CorrHistV2 off | 0.656 | 19 | 19 |
| MateAlphaGuard off | 0.625 | 19 | 19 |

And the cleanest single line — **the PC binary with ALL FIVE SWITCHES OFF**:

```
PC binary, ALL FIVE SWITCHES OFF: achieved 355.8 ms = 0.784 of soft, iters 20, depth 20
base binary                      : achieved 349.3 ms = 0.769 of soft, iters 20, depth 20
PC20 all-on                      : achieved 287.3 ms = 0.633 of soft, iters 19, depth 19
```

With the switches off, the PC binary reproduces the base tree's behaviour (0.784 vs 0.769, 20 iterations,
depth 20). With them on, it stops at 0.63 and loses the ply. **The PC patch's code is not the cause; its
default switch settings are.**

## 4. The mechanism, in numbers

24 positions, wtime 10000, medians over the last completed iteration:

| build | nodes | last-iteration time | nodes/second |
|---|---|---|---|
| base | 754,624 | 346 ms | 2,180,994 |
| PC20 | 556,389 | 287 ms | 1,938,638 |

PC20 visits **26 % fewer nodes in 17 % less time**, so its node rate is actually 11 % LOWER — the switches
make the tree smaller, not the machine faster. Cheaper iterations mean the ladder reaches a given budget in
fewer, smaller steps, and the iteration that was in flight when soft expired is discarded. So the engine
stops earlier on the clock, at a shallower depth.

Note on isolation: `HistRework off` and `TtPruneV2 off` each individually restore 20 iterations, and both
together give 0.671 — not additive. The switches are not independent in their effect on the tree, so
"which one" is not a clean single answer; "the switch set" is. I am not claiming one culprit.

## The answer for the owner, in one line

Nothing in the timing code changed: with the PC's switches off, the PC binary behaves exactly like the base
tree. The 10 s ply is lost because `HistRework`/`TtPruneV2` (and the set they belong to) shrink the tree so
each iteration costs less and fewer fit inside the same 454 ms soft budget — so this is **a switch-policy
trade-off, not a bug and not a constant to tune**, and the knob to reach for is the switch set, not
`TmSoftDivisor`.
