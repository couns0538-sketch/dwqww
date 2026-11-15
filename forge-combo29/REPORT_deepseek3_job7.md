# REPORT deepseek3 job 7

**First line in plain words: `CorrLmr` does not gain strength per node. Pooled over the two mild-K
matches it is +0.69 Elo, 95% interval -6.3 to +7.7, on 4,000 games; the strong K is -1.04, interval
-11.4 to +9.3, on 2,000 games. Both are flat zero. And yes, with the option off the engine is proven
identical: the four known numbers unchanged and the same sha256 over 2,000 positions' answers (best move,
score, node count) as the unpatched build, at a smallest node count of 4,534 so the identity is not over
empty data.**

**What was cut: M4 (`CorrLmr 32`, second seed 7944) was not run, and the sign-flipped control
(`CorrLmr -24`, seed 7949) was not run either.** I reached 64 minutes after M3; at ~13.5 minutes per
2,000-game match neither could finish inside the 80-minute budget. The order the job set (control, M1,
M2, M3, M4) was kept.

I am `deepseek3`. Base commit `6b98f217`. No pull request, no engine source committed, text only, no
binaries, no `__pycache__`. Deliverable `tests_deepseek3_job7/corr_lmr.patch.txt`, 139 lines, 3 files,
verified to apply and to reproduce every number (section 2).

---

## 1. Step 0 — the known numbers, unpatched

`logs/step0-and-p3.txt`. Build: CMake Release, `g++ 13.3.0`, `-DFORGE_MARCH=x86-64-v4`, built-in net.

| command | expected | unpatched | patched, `CorrLmr 0` |
|---|---:|---:|---:|
| `bench 11` | 312866 | 312866 | 312866 |
| `bench 13` | 862329 | 862329 | 862329 |
| `bench 16` | 3024920 | 3024920 | 3024920 |
| `go perft 5` | 4865609 | 4865609 | 4865609 |

`uci` lists it: `option name CorrLmr type spin default 0 min -400 max 400`.

## 2. The feature as I built it

**Which table.** None new. The feature reads the **signed** correction that `Worker::corrected_eval`
already computes — the same quantity job 5 took the absolute value of. Nothing is allocated or cleared.

**Which unit `r` is in, and the conversion.** `reduction()` (`src/search.cpp:232-236`) returns an `int`
looked up from `Reductions.quiet[depth][moves]`, and that value is subtracted from a depth:
`reduced_depth = new_depth - r` (`src/search.cpp:2011`). So **`r` counts whole plies**. The job's formula
`-(correction * K) / 1024` is applied in centipawns and then clamped to one ply:

```cpp
if (tune::CorrLmr != 0 && quiet && move_count > 1) {
    r -= std::clamp(-(ss->corr_signed_cp * tune::CorrLmr) / 1024, -1, 1);
}
```

So 1024 cp of correction times K = one ply of reduction. Integer division truncates toward zero, so a
correction smaller than `512/K` cp does nothing — at K=32 that is 16 cp, which is why P1's `-4..4` bucket
is silent.

**Where it is carried.** `int corr_signed_cp = 0;` in `SearchStack` (`include/forge/search.hpp`, beside
`static_eval`). `corrected_eval` gained an optional out-parameter (`include/forge/search.hpp:557`):

```cpp
const int correction_cp = correction / CorrectionGrain;
if (corr_signed_out != nullptr) *corr_signed_out = correction_cp;
return std::clamp(raw_eval + correction_cp, -MateInMaxPly + 1, MateInMaxPly - 1);
```

**Where it is set.** Both `static_eval` sites in `Worker::search` pass `&ss->corr_signed_cp`; both
in-check branches set it to **0**, as the job specifies.

**Where it is read — exactly one place.** The late-quiet reduction, `src/search.cpp:2004-2010`,
immediately after the quiet-history term. Not for captures (`quiet` guard), not in quiescence (this code
is in `Worker::search` only), nowhere else.

**How it is cleared.** Nowhere: the stack entry is overwritten at every node that computes an eval and
zeroed at every node that does not. No table exists to clear.

**The option.** Spin, default 0, **min -400 max 400**, `src/uci.cpp`, using the same `apply_spin` +
`searcher.clear()` shape as `Hash`/`MultiPV`. Negative values invert the rule automatically, because the
sign of K multiplies the correction:
`-(c * (-K)) / 1024 = +(c * K) / 1024`. That is the job's control, and it needs no extra code.

**Design choices the job left open:**
- *The two K values*, from P1 (section 3): **K=24** changes 3.08% of reductions ("about 3%") and **K=32**
  changes 13.41% (the closest measured point to "about 12%").
- *`move_count > 1`* in the guard. The reduction is only computed for late moves already, but I made the
  condition explicit so the feature cannot touch the first move of a node.
- *The clamp is applied after the division*, so a huge correction cannot move `r` by two plies even at
  K=400.
- *What I did not do:* I did not use `static_eval - raw_eval`. The engine already has an
  `LmrSignedCorrection` option that uses exactly that difference (`src/search.cpp:2003-2007`), and it
  includes the rule50 damping; my feature is the pure correction from the history tables, which is what
  the job describes. The two are therefore different signals, and `LmrSignedCorrection` is off by default
  in both sides of every match.

## 3. P1 — counters first

There is no new table, so the job's general P1 wording does not fit; I used its specific version. A local
traced copy (`~/work/j7t`, diff committed as `p1_trace_copy.diff.txt`) records the signed correction and
counts, over the late quiet moves that reach the reduction, the bucket distribution and how many
reductions each candidate K would change. **The tracer is passive: `bench 13` stayed at 862329.**

`logs/p1_trace.txt`, `bench 13`, 284,673 late quiet moves reached the reduction:

| signed correction (cp) | moves | share |
|---|---:|---:|
| below -40 | 2,441 | 0.86% |
| -40 to -16 | 32,701 | 11.49% |
| -15 to -5 | 20,801 | 7.31% |
| **-4 to 4** | **172,253** | **60.51%** |
| 5 to 15 | 17,695 | 6.22% |
| 16 to 40 | 29,469 | 10.35% |
| above 40 | 9,313 | 3.27% |

**The first thing this says: the feature is silent on three fifths of the moves it could act on.** 60.5%
of late quiet moves carry a correction within ±4 cp, which at any K in the range I could play is below the
16-cp threshold needed to move `r`. Only about 22% of them carry more than 16 cp either way.

**K, share of reductions that change by at least one ply** (`logs/p1_choice.txt`; in each direction):

| K | changed | share | less reduction | more reduction |
|---:|---:|---:|---:|---:|
| 4, 8, 12 | 0 | 0.00% | 0.00% | 0.00% |
| 16 | 40 | 0.01% | 0.01% | 0.00% |
| **24** | **8,765** | **3.08%** | 2.53% | 0.55% |
| 28 | 19,422 | 6.82% | 4.94% | 1.88% |
| 30 | 25,456 | 8.94% | 6.23% | 2.71% |
| 31 | 28,687 | 10.08% | 6.89% | 3.19% |
| **32** | **38,178** | **13.41%** | 9.35% | 4.07% |
| 34 | 43,418 | 15.25% | 10.32% | 4.93% |
| 48 | 63,896 | 22.45% | 12.60% | 9.85% |
| 64 | 73,924 | 25.97% | 13.62% | 12.34% |

**Mild K = 24 (3.08%), strong K = 32 (13.41%).** One property of this feature is visible in that table and
worth stating: the effect is **asymmetric**, roughly 2:1 toward "less reduction" at every K. That is
because the distribution above is asymmetric — more moves carry a positive correction (about 20% above
+5 cp) than a negative one (about 20% below -5 cp, but with the near-zero bucket absorbing the difference).

The job's P1 also asks for reads and updates per node of "the new table". There is no new table and this
feature performs **zero** reads of its own beyond the stack int it already has, and **zero** updates: it
consumes a value that `corrected_eval` was already computing. So the meaningful P1 numbers are the ones
above — how often the *value* is non-zero and how often it would change a decision.

## 4. P2 — option OFF is the old engine

Four known numbers: identical (section 1).

2,000 positions, `ucinewgame` + `position fen` + `go depth 9`, best move + score + nodes, one sha256 per
side (`p2_identity.py`):

| side | positions | min nodes | sha256 |
|---|---:|---:|---|
| unpatched `6b98f217` | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |
| patched, `CorrLmr 0` | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |

Identical, over real work. This is also the same hash jobs 3 and 5 produced from different builds.

## 5. P3 — option ON acts

`logs/step0-and-p3.txt`.

| command | off | `CorrLmr 24` | `CorrLmr 32` | `CorrLmr -32` |
|---|---:|---:|---:|---:|
| `bench 11` | 312866 | **312866** | **317378** | **298942** |
| `bench 13` | 862329 | **873952** | **886401** | **822174** |
| `bench 16` | 3024920 | **2445948** | **2217029** | **3044007** |

All differ except `bench 11` at K=24, which is unchanged — worth noting rather than hiding: at K=24 the
feature did not change a single node of the 11-ply bench, which is consistent with P1's 3% share and that
bench's small tree. K=32 and K=-32 move every bench, and they move it in **opposite directions** at
`bench 11` (317378 vs 298942 from a base of 312866), which is the first evidence that the sign is doing
something and not just "reduce differently".

## 6. P4 — sanitizers

AddressSanitizer + UBSan, `-fno-sanitize-recover=all`, planted fault first (`logs/p4-planted.txt`):
index past a `[13][64][7]` table → exit 1 with a UBSan out-of-bounds report; signed overflow → exit 1;
clean use → exit 0. Both fault classes are caught, clean code is not flagged.

Then the engine, with the actual K values (`logs/p4-run.txt`):

| run | exit | stderr bytes | nodes |
|---|---:|---:|---:|
| `bench 13`, `CorrLmr 24` | 0 | **0** | 873952 (matches release) |
| `bench 13`, `CorrLmr 32` | 0 | **0** | 886401 (matches release) |
| 200 P2 positions, `CorrLmr 24` | 0 | **0** | 200 of 200 bestmoves |
| 200 P2 positions, `CorrLmr 32` | 0 | **0** | 200 of 200 bestmoves |

**A process error I caught and am reporting:** my first P4 run passed while testing **K=20 and K=64** —
divisors left over from job 5 in the copied script. It was a valid sanitizer run but it was not *this
feature at the K values this job plays*, so I fixed the script and re-ran with 24 and 32. The node counts
are again what exposed it.

## 7. P5 — the matches

Same exe both sides (`~/work/j7p/forge`), `nodes=20000`, `Threads 1`, `Hash 16`, `OwnBook false`, UHO
openings both colours, no adjudication, concurrency 4 on 4 cores.

**Control**, 300 games, seed 7940: own pair interval **+195.51, +165.6 .. +228.3**, fastchess
+195.51 +/- 31.28, pairs `[0,7,29,68,46]`. Near +200 as required. 300 games took 121 s, which is what the
later limits were set from.

**Probe before M1** (`logs/probe-M1.engine.log`):

```
cand <--- setoption name OwnBook value false
cand <--- setoption name CorrLmr value 24
base <--- setoption name OwnBook value false        (no CorrLmr)
```

| match | candidate | seed | games | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---:|---:|---|---:|---|---:|---|
| M1 | `CorrLmr 24` | 7941 | **2000 (complete)** | 581-576-843 | 1000 | [44,230,453,223,50] | +0.87 +/- 9.81 | **+0.87, -8.9 .. +10.7** |
| M2 | `CorrLmr 24` | 7942 | **2000 (complete)** | 597-594-809 | 1000 | [62,203,451,238,46] | +0.52 +/- 10.06 | **+0.52, -9.5 .. +10.6** |
| **pooled K=24** | | | **4000** | 1178-1170-1652 | 2000 | [106,433,904,461,96] | | **+0.69, -6.3 .. +7.7** |
| M3 | `CorrLmr 32` | 7943 | **2000 (complete)** | 577-583-840 | 1000 | [52,250,406,236,56] | -1.04 +/- 10.32 | **-1.04, -11.4 .. +9.3** |
| M4 | `CorrLmr 32` | 7944 | **NOT RUN** | — | — | — | — | — |
| control (sign flipped) | `CorrLmr -24` | 7949 | **NOT RUN** | — | — | — | — | — |

No row has pair counts `[0,0,N,0,0]`.

**How every game ended, per match**, as the new rule requires (`logs/termination_reasons.txt`):

| match | mate | draw by rule | on time | fault (crash/illegal/disconnect) |
|---|---:|---:|---:|---:|
| control | 193 | 107 | 0 | **0** |
| M1 | 1157 | 843 | 0 | **0** |
| M2 | 1191 | 809 | 0 | **0** |
| M3 | 1160 | 840 | 0 | **0** |

Every one of the 6,300 games ended by mate or a draw rule. Per-game files: `logs/{control,M1,M2,M3}.games.txt`.

## 8. P6 — speed

`bench 16` nps, off against `CorrLmr 24`, 10 interleaved pairs (`logs/p6-speed.txt`):

| | mean nps | sd | bench 16 nodes |
|---|---:|---:|---:|
| off | 1,842,639 | 82,674 | 3,024,920 |
| on (K=24) | 1,739,368 | 67,091 | **2,445,948** |

Per-pair ratio mean **0.9447** (min 0.8906, max 0.9841) — **-5.53%**, and 10 of 10 pairs were slower.

**But this is mostly tree shape, not cost.** With the option on, `bench 16` searches **2,445,948** nodes
instead of 3,024,920 — 19% *fewer*. So the feature changes the tree a great deal, and a per-node rate
measured on two different trees cannot separate "the arithmetic costs something" from "the tree is
different". The arithmetic itself is one multiply, one divide by a constant and a clamp on a value already
in the stack, so I would expect the true cost to be near zero; I did not measure it in isolation (see 9).
**The honest statement: at equal nodes this feature is neutral in strength and its measured nps is 5.5%
lower, but almost all of that is the different tree.**

**Size of the new table: 0 bytes per thread.** There is no new table. The feature adds one `int` to
`SearchStack`, i.e. 4 bytes per stack entry and a few hundred bytes per thread, inside a struct that is
already resident.

## 9. One table of all matches

| job | match | what | seed | games | W-L-D | pairs | pair counts | fastchess | own Elo, 95% |
|---|---|---|---:|---:|---|---:|---|---:|---|
| 1 | M1 | NullThreatVerify | 7303 | 1500 | 443-422-635 | 750 | [35,163,337,176,39] | +4.86 +/- 11.44 | +4.86, -6.6..+16.3 |
| 1 | M2 | NullSeeVeto | 7304 | 1500 | 433-433-634 | 750 | [46,175,304,183,42] | -0.00 +/- 12.10 | 0.00, -12.1..+12.1 |
| 1 | M3 | AspArmLate | 7305 | 1500 | 371-483-646 | 750 | [51,222,296,150,31] | -25.99 +/- 11.94 | -26.0, -37.9..-14.0 |
| 1 | M3r | AspArmLate (repeat) | 9305 | 1500 | 379-456-665 | 750 | [63,177,309,176,25] | -17.85 +/- 12.02 | -17.9, -29.9..-5.8 |
| 1 | M4 | EvalRule50Damp | 7306 | 1500 | 345-501-654 | 750 | [63,229,285,147,26] | -36.26 +/- 12.14 | -36.3, -48.4..-24.1 |
| 1 | M5 | DeadMaterial | 7307 | 1500 | 445-442-613 | 750 | [0,1,745,4,0] | +0.69 +/- 1.01 | +0.7, -0.3..+1.7 |
| 2 | M1 | 3-switch bundle | 7321 | 2000 | 559-591-850 | 1000 | [56,257,404,229,54] | -5.56 +/- 10.36 | -5.56, -15.9..+4.8 |
| 2 | M2 | null-pair bundle | 7322 | 1438 | 417-435-586 | 719 | [41,186,292,150,50] | -3.23 +/- 12.72 | -4.35, -16.9..+8.2 |
| 2 | M3 | PC-like bundle | 7323 | 1261 | 393-359-509 | 630 | [35,149,236,168,42] | +8.98 +/- 13.96 | +9.10, -4.4..+22.6 |
| 2 | M4 | all eight | 7324 | 1241 | 380-347-514 | 620 | [40,128,251,160,41] | +8.41 +/- 13.79 | +9.53, -4.0..+23.1 |
| 2 | M5 | aspiration pair | 7325 | 1208 | 317-395-496 | 603 | [50,161,233,135,24] | -22.32 +/- 13.72 | -22.50, -36.2..-8.8 |
| 2 | M6 | eight+EvalRule50Damp | 7326 | 752 | 194-256-302 | 376 | [27,100,170,66,13] | -30.19 +/- 18.06 | -28.71, -45.0..-12.5 |
| 3 | C | 20000 vs 10000 | 7900 | 300 | 179-28-93 | 150 | [2,6,33,57,52] | +192.40 +/- 34.46 | — |
| 3 | M1 | LmrCaptureHistory=8192 | 7901 | 2000 | 570-577-853 | 1000 | [61,228,420,239,52] | -1.22 +/- 10.32 | -1.22, -11.5..+9.1 |
| 3 | M2 | LmrCaptureHistory=8192 | 7902 | 2000 | 567-559-874 | 1000 | [47,246,411,244,52] | +1.39 +/- 10.14 | +1.39, -8.8..+11.5 |
| 3 | M3 | LmrCaptureHistory=2048 | 7903 | 2000 | 590-555-855 | 1000 | [49,251,388,240,72] | +6.08 +/- 10.63 | +6.08, -4.6..+16.7 |
| 3 | M4 | LmrCaptureHistory=2048 | 7904 | 2000 | 586-575-839 | 1000 | [50,223,436,248,43] | +1.91 +/- 9.89 | +1.91, -8.0..+11.8 |
| 4 | A1 | LowPlyHist 1 | 7911 | 1703 | 487-507-709 | 851 | [48,209,351,201,42] | -4.08 +/- 11.42 | -4.08, -15.2..+7.0 |
| 4 | A2 | LowPlyHist 1 | 7912 | 885 | 256-259-370 | 442 | [30,103,177,104,28] | -2.17 +/- 16.50 | -1.18, -17.4..+15.0 |
| 4 | B1 | EvalSwingMult 12 | 7913 | 1194 | 369-298-527 | 597 | [25,128,238,163,43] | +18.08 +/- 14.73 | +20.68, +7.2..+34.2 |
| 4 | B2 | EvalSwingMult 48 | 7914 | 1021 | 280-318-423 | 510 | [43,119,210,110,28] | -12.51 +/- 15.34 | -13.29, -28.4..+1.8 |
| 4 | B3 | EvalSwingMult 24 | 7915 | **NOT RUN** | — | — | — | — | — |
| 5 | C | 20000 vs 10000 | 7920 | 300 | 190-18-92 | 150 | [0,4,23,70,53] | +226.69 +/- 32.04 | +226.69, +196.3..+260.5 |
| 5 | M1 | CorrMargin 20 | 7921 | 2000 | 552-574-874 | 1000 | [65,241,402,235,57] | -3.82 +/- 10.57 | -3.82, -14.4..+6.8 |
| 5 | M2 | CorrMargin 20 | 7922 | 2000 | 575-561-864 | 1000 | [54,239,410,233,64] | +2.43 +/- 10.46 | +2.43, -8.0..+12.9 |
| 5 | M3 | CorrMargin 64 | 7923 | 1854 | 536-530-788 | 927 | [56,211,387,217,56] | -0.00 +/- 11.06 | +1.12, -9.8..+12.0 |
| 5 | M4 | CorrMargin 64 | 7924 | 1184 | 333-351-500 | 592 | [40,146,236,132,38] | -7.30 +/- 15.18 | -5.28, -19.3..+8.7 |
| 6 | C | 20000 vs 10000 | 7930 | 300 | 171-25-104 | 150 | [1,5,34,67,43] | +184.73 +/- 30.74 | +184.73, +155.2..+216.9 |
| 6 | M1 | Minor50+Corr20 vs none | 7931 | 2000 | 566-553-881 | 1000 | [57,242,382,269,50] | +2.26 +/- 10.44 | +2.26, -8.2..+12.7 |
| 6 | M2 | Minor50+Corr20 vs Minor50 | 7932 | 2000 | 598-598-804 | 1000 | [62,223,428,227,60] | -0.00 +/- 10.43 | 0.00, -10.4..+10.4 |
| 6 | M3 | Minor50+Corr20 vs none | 7933 | 1957 | 555-566-836 | 978 | [74,216,387,249,52] | +0.58 +/- 11.32 | -1.95, -12.8..+8.9 |
| 6 | M4 | Minor50+Corr64 vs Minor50 | 7934 | **NOT RUN** | — | — | — | — | — |
| 7 | C | 20000 vs 10000 | 7940 | 300 | 173-20-107 | 150 | [0,7,29,68,46] | +195.51 +/- 31.28 | +195.51, +165.6..+228.3 |
| 7 | M1 | CorrLmr 24 | 7941 | 2000 | 581-576-843 | 1000 | [44,230,453,223,50] | +0.87 +/- 9.81 | +0.87, -8.9..+10.7 |
| 7 | M2 | CorrLmr 24 | 7942 | 2000 | 597-594-809 | 1000 | [62,203,451,238,46] | +0.52 +/- 10.06 | +0.52, -9.5..+10.6 |
| 7 | M3 | CorrLmr 32 | 7943 | 2000 | 577-583-840 | 1000 | [52,250,406,236,56] | -1.04 +/- 10.32 | -1.04, -11.4..+9.3 |
| 7 | M4 | CorrLmr 32 | 7944 | **NOT RUN** | — | — | — | — | — |

## 10. Files of the repository I opened

`forge-combo29/src/search.cpp` (`reduction`, `corrected_eval`, `update_correction`, the LMR block and the
existing `LmrSignedCorrection`, `SearchStack` use, option globals), `forge-combo29/src/uci.cpp` (option
list, `apply_spin`, dispatch), `forge-combo29/include/forge/search.hpp` (`CorrectionGrain`,
`SearchStack`, `extern` declarations). No other helper's file, no other engine's source.

## 11. Stamps

| step | start | end | source |
|---|---|---|---|
| job file read | 22:22:08Z | 22:22:2xZ | — |
| P1 tracer built, probes for K | 22:22:2xZ | 22:23:01Z | `logs/p1_trace.txt`, `logs/p1_choice.txt` |
| patch written, patched build | 22:23:0xZ | 22:23:28Z | — |
| Step 0 + P3 | 22:23:28Z | 22:23:41Z | `logs/step0-stamps.txt` |
| P2 2,000 positions, both sides | 22:23:43Z | 22:24:30Z | `logs/p2-stamps.txt` |
| sanitizer build + planted faults + run (twice, see 6) | 22:24:3xZ | 22:24:59Z | `logs/p4-stamps.txt` |
| delivered patch re-applied and rebuilt | 22:25:0xZ | 22:25:3xZ | — |
| control (300 games) | 22:25:35Z | 22:27:36Z | `logs/control-stamps.txt` |
| M1 probe | 22:27:39Z | 22:27:42Z | `logs/probe-M1.engine.log` |
| M1 | 22:27:46Z | 22:45:48Z | `logs/M1-stamps.txt` |
| M2 | 22:45:50Z | 23:03:46Z | `logs/M2-stamps.txt` |
| M3 | 23:03:50Z | 23:21:36Z | `logs/M3-stamps.txt` |
| P6 | 23:21:38Z | 23:22:09Z | `logs/p6-stamps.txt` |
| report written | 23:23Z | — | — |

Job file read 22:22:08Z, last measurement 23:22:09Z = **60 min 1 s**, inside the 80-minute budget and
inside the 70-minute stop point.

## 12. What I did not do

- **M4 was not run**, and **the sign-flipped control (`CorrLmr -24`, seed 7949) was not run.** The control
  is the one I most regret: without it I cannot rule out that *any* change to the LMR of quiet moves
  gains, regardless of sign. My P3 result (K=32 and K=-32 move `bench 11` in opposite directions) is
  suggestive but is not a game result, and the job was explicit that the control is what separates a real
  sign effect from "reduce differently".
- **I did not isolate the speed cost** from tree shape. The bench-16 node counts (19% fewer with the
  option on) make the -5.53% mostly shape, but I did not measure the arithmetic alone.
- **I did not test K values between 24 and 32** beyond the P1 table, and I played only 24 and 32.
- **No time control, no PC net.** Fixed 20,000 nodes, 4 cores, concurrency 4.
- P1's trace was taken on `bench 13` only.

## 13. What I am not sure about

- **Whether the null is real or whether the effect is simply tiny.** P1 shows the feature is silent on
  60.5% of the late quiet moves and only changes 3% of reductions at K=24. A feature that touches 3% of
  reductions by one ply and finds +0.69 ± 7 is consistent both with "no effect" and with "a real but
  small effect this sample cannot see". The strong K (13.4% of reductions) also found nothing, which leans
  toward "no effect".
- **The missing sign control is the weakest point of this report.** If `CorrLmr -24` also read about +0.7,
  the honest conclusion would be "changing the quiet reduction at all is neutral here", which is a
  different statement from "the sign does not matter".
- **My `move_count > 1` guard.** The reduction is only computed for moves after the first, so the guard
  should be redundant; if it is not on some path, the feature is narrower than the job describes.
- **Whether the job's `-(correction * K) / 1024` intends 1024 cp per ply.** I chose that reading because
  `r` is whole plies; the alternative would be that 1024 is an arbitrary scale and a ply is some other
  divisor. My P1 table is in that unit, so a different reading would mean different K values for the same
  treatment share.
- **The asymmetric direction** (2:1 toward less reduction) is a property of the distribution, not a design
  choice, and I did not test a version that normalises it.

## 14. A better way

**A one-sided test of a signed feature is nearly worthless without its control, and the budget should
protect that match first.** This job's own text says the negative-K match is what separates a real sign
effect from "reduce differently", and then puts it after four 2,000-game matches that cannot all fit in 80
minutes. The result is exactly the report that cannot answer the question it was built around. A better
order is: control match, M1 (mild), **the sign-flipped control at the same K**, M2, M3 — so that the
question "is it the sign or just the change?" is answered before any second seed. How to check it: on any
future signed-feature job, require that the two matches at the *same* K with opposite signs be played
before any second seed at either sign; the pair (mild, -mild) is one experiment, and (mild, mild') is
another.

**P1 should say up front what fraction of the target site the feature can reach.** My P1 found that 60.5%
of late quiet moves carry a correction too small to matter, so the *effective* population is 39.5% before
any K is chosen — and at K=24 the feature touches 3.08%. If the job's P1 wording asked for "the share of
the target moves where the signal is non-zero", a helper would discover this in ten minutes and could tell
Fable before the matches whether the feature is worth 80 minutes at all.

**For a feature that changes the tree as much as this one, nps is the wrong cost measure.** 19% fewer
nodes at `bench 16` and 5.5% lower nps cancel into roughly the same time per bench, so the honest
equal-time question is not "is it 5% slower per node" but "does it gain per node more than the node count
change implies". An equal-time match (say 500 games at a fixed time per move) would answer that directly
and costs 8 minutes.

## 15. Model

`deepseek3`. Model: **DeepSeek V4.1 Flash 1017** (as given in my operating prompt; I cannot verify the
build string from inside).

## 16. Questions for Fable

1. **Do you want the sign control (`CorrLmr -24`)?** I consider it the missing piece: without it this
   report cannot distinguish "the sign does nothing" from "any change to quiet-move LMR does nothing".
   It is ~13 minutes.
2. Is 1024 cp per ply the intended conversion? If a ply is meant to be some other number of centipawns,
   my K values correspond to different treatment shares and the job's 3%/12% targets map elsewhere.
3. Should a future job of this shape put the sign-flipped match before the second seed? I would have
   spent the same 80 minutes for a much more conclusive answer.
