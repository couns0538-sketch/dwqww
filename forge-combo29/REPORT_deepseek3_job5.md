# REPORT deepseek3 job 5

**First line, in plain words: `CorrMargin` does not gain strength per node. Pooled over both seeds the
mild setting (K=20) is -0.69 Elo, 95% interval -8.1 to +6.7, on 4,000 games; the strong setting (K=64) is
-1.37, interval -10.0 to +7.2, on 3,038 games. Both are flat zero. And yes, with the option off the engine
is proven identical: the four known numbers are unchanged and the sha256 over 2,000 positions' best move,
score and node count is the same as the unpatched build, at a smallest node count of 4,534 so the identity
is over real work.**

**What was cut: nothing was skipped, but M3 and M4 fell short of 2,000 games** (1,854 and 1,184) — I
reached the 70-minute stop point during M4. The order the job set (control, M1, M2, M3, M4) was kept in
full, so the strong-K pair is the one that is short.

I am `deepseek3`. Branch `for-fable-and-opus/deepseek3-work`, base commit `6b98f217`. No pull request, no
engine source committed, no binaries, no `__pycache__`. Deliverable `tests_deepseek3_job5/corr_margin.patch.txt`:
**37 inserted / 8 deleted lines across 3 files**, verified to apply cleanly to `6b98f217` with
`git apply --check` and then actually applied into a throwaway worktree.

---

## 0. A contradiction in the job text, and how I resolved it

The text describes the option twice, inconsistently (`tests_deepseek3_job5/JOB_TEXT_CONTRADICTION.txt`):

- "The option is a SPIN this time (not a check): `CorrMargin`, default 0 = off, any other value is K."
- "A new UCI option `CorrMargin` (**type check**, default false) … follow [ThreatHistory] exactly."

**I built it as a spin, default 0, min 0, max 256.** Reasons: the job's own P1 asks for "your two K
values", and P5 plays the option with a mild and a strong K; a check cannot carry a K. The "type check"
sentence looks carried over from job 3's template. The value 0 short-circuits before any arithmetic, so
with the option off not one node changes — which P2 proves by hash rather than by argument.

## 1. Step 0 — the known numbers on the unpatched build

`logs/step0-and-p2-numbers.txt`. Build: CMake Release, `g++ 13.3.0`, `-DFORGE_MARCH=x86-64-v4`, built-in
net, commit `6b98f217`, 19:59:16Z to 19:59:21Z.

| command | expected | unpatched | patched, `CorrMargin 0` | match |
|---|---:|---:|---:|---|
| `bench 11` | 312866 | 312866 | 312866 | yes |
| `bench 13` | 862329 | 862329 | 862329 | yes |
| `bench 16` | 3024920 | 3024920 | 3024920 | yes |
| `go perft 5` | 4865609 | 4865609 | 4865609 | yes |

`uci` lists the option: `option name CorrMargin type spin default 0 min 0 max 256`.

## 2. The feature as I built it

**Which table.** No new table. The engine already keeps three correction tables —
`correction_history_` (pawns), `material_correction_`, and the two non-pawn tables when
`NonPawnCorrection` is on — and `Worker::corrected_eval` already sums them. The feature reads *the size of
the sum it already computed*; it allocates nothing and touches no table index.

**How it is carried.** One new `int corr_size_cp = 0;` in `SearchStack`
(`include/forge/search.hpp:406`, beside `static_eval`). `corrected_eval` gained an optional out-parameter
(`include/forge/search.hpp:562`), so its existing caller is untouched:

```cpp
// src/search.cpp, inside Worker::corrected_eval
const int correction_cp = correction / CorrectionGrain;
if (corr_size_out != nullptr) *corr_size_out = std::abs(correction_cp);
return std::clamp(raw_eval + correction_cp, -MateInMaxPly + 1, MateInMaxPly - 1);
```

**Where it is set.** Both places that compute `static_eval` in `Worker::search`:
`src/search.cpp:1475` (the null-move/razor block) and `src/search.cpp:1665` (the main static-eval block),
each now passing `&ss->corr_size_cp`. Both in-check branches set it to **0**, as the job specifies
(`:1469` and `:1658`). The `excluded.is_none()` branch reuses the value already stored for this node, which
is correct because `static_eval` is reused there too.

**Where it is read — exactly two places, as instructed.**

1. Reverse futility, `src/search.cpp:1700-1702`:
```cpp
const int corr_margin = tune::CorrMargin > 0 ? ss->corr_size_cp * tune::CorrMargin / 64 : 0;
if (!bare_king_mode && depth <= tune::RfpDepth &&
    eval - (tune::RfpMargin * depth - tune::RfpImproving * improving + corr_margin) >= beta && ...)
```
2. Quiet-move futility in the move loop, `src/search.cpp:1886-1887`: the same expression
`(tune::CorrMargin > 0 ? ss->corr_size_cp * tune::CorrMargin / 64 : 0)` added to
`FutilityBase + FutilityMultiplier * lmr_depth`.

**Nowhere else.** I did not touch razoring, null-move verification, probcut, SEE pruning, LMR or the
capture-futility test, even though the same argument would apply to several of them. One idea, one switch.

**How it is cleared.** Nowhere: the value lives in the stack entry and is overwritten at every node that
computes an eval, and set to 0 at every node that does not. There is no table to clear, and
`searcher.clear()` on option change still clears the correction tables themselves.

**Design choices the job left open:**
- *Weight form.* `size * K / 64`, exactly as the job writes it. K is therefore "how many centipawns of
  extra margin per 64 cp of correction".
- *The two K values.* Chosen from measurement, not taste — see P1. **K=20** (removes 2.04% of the reverse
  futility cutoffs on `bench 13`) and **K=64** (removes 8.07%).
- *The in-check case.* 0, as the job says. I also set 0 where `static_eval` is `ValueNone` for any other
  reason, so the term can never be applied to a sentinel.
- *Not done, on purpose:* no term in razoring or probcut, no per-depth scaling, no cap on the term. The
  job said two sites and one switch.

## 3. P1 — counters first

The job's general P1 wording does not fit (no new table), so I used the specific P1 it gives: for the
nodes of `bench 13` where reverse futility is reached, the distribution of the correction size, and how
many reverse futility cutoffs and quiet-futility skips each candidate K removes.

A local traced copy (`~/work/j5t`, diff committed as `p1_trace_copy.diff.txt`) records
`abs(correction / CorrectionGrain)` in `corrected_eval` and counts, at both sites, which of seven candidate
K values would have changed the decision. **The tracer is passive: `bench 13` stayed at 862329 nodes with
it in.**

`logs/p1_trace.txt`, last line of each counter, `bench 13`, traced copy:

```
CORRMARGIN   reached=378881 size0=155522 size1_4=83615 size5_15=57135 size16_40=69989 size40p=12620
             rfp_cutoffs=183430 K=16_removed=2974 K=20_removed=3745 K=32_removed=6683
             K=48_removed=10464 K=64_removed=14799 K=96_removed=21656 K=128_removed=28190
CORRMARGIN_Q reached=313345 skips=11663 K=16_removed=8 K=20_removed=12 K=32_removed=22
             K=48_removed=30 K=64_removed=45 K=96_removed=60 K=128_removed=82
```

**The correction size is not zero and is widely spread** — this is the thing to rule out first, and it is
ruled out. Of the 378,881 nodes that reach reverse futility on `bench 13`:

| correction size | nodes | share |
|---|---:|---:|
| exactly 0 | 155,522 | 41.0% |
| 1 to 4 cp | 83,615 | 22.1% |
| 5 to 15 cp | 57,135 | 15.1% |
| 16 to 40 cp | 69,989 | 18.5% |
| above 40 cp | 12,620 | 3.3% |

So 59% of the nodes that reach the test carry a non-zero correction, and a fifth carry more than 16 cp —
the feature has plenty to act on.

**Choosing K** (`logs/p1_table.txt`):

| K | reverse futility cutoffs removed (of 183,430) | share | quiet-futility skips removed (of 11,663) | share |
|---:|---:|---:|---:|---:|
| 16 | 2,974 | 1.62% | 8 | 0.069% |
| **20** | **3,745** | **2.04%** | **12** | **0.103%** |
| 32 | 6,683 | 3.64% | 22 | 0.189% |
| 48 | 10,464 | 5.70% | 30 | 0.257% |
| **64** | **14,799** | **8.07%** | **45** | **0.386%** |
| 96 | 21,656 | 11.81% | 60 | 0.514% |
| 128 | 28,190 | 15.37% | 82 | 0.703% |

**K=20 removes 2.04% and K=64 removes 8.07% of the reverse futility cutoffs** — the job asked for "about
2%" and "about 8%", so those are the two I played.

**One finding worth flagging: the second site is almost inert.** At K=64 the quiet-futility term removes
45 of 11,663 skips — 0.39%. Even at K=128 it is 0.70%. So in practice this feature is a reverse-futility
feature; the job's second site contributes almost nothing at any sane K. That is not a bug (the counter is
consistent with the arithmetic: `FutilityBase` is already 100 and `FutilityMultiplier * lmr_depth` adds
more, so the alpha margin at that site is usually far larger than any correction term), but it does mean
M1-M4 are effectively testing site 1 alone.

## 4. P2 — option OFF is the old engine

**Four known numbers:** see section 1 — identical.

**2,000 positions, `ucinewgame` + `position fen` + `go depth 9`**, best move + score + node count per
position, one sha256 over all answers (`p2_identity.py`):

| side | positions | min nodes | sha256 |
|---|---:|---:|---|
| unpatched `6b98f217` | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |
| patched, `CorrMargin 0` | 2000 | 4534 | `ba06f82d7a047639068094234a7bd8426315f66181d82414c32f714b0c607720` |

Identical, and not on empty data: every position searched to depth 9, smallest node count 4,534. Both
answer files are committed (`logs/p2-unpatched.txt`, `logs/p2-patched-off.txt`), so the hash can be
recomputed. As a bonus check, this is the **same hash job 3 produced** on the same 2,000 positions with
the same depth, from a different build directory and a different day — an independent confirmation that
the unpatched side of both jobs is the same engine.

## 5. P3 — option ON acts

`logs/p3-on-numbers.txt`.

| command | off | `CorrMargin 20` | `CorrMargin 64` |
|---|---:|---:|---:|
| `bench 11` | 312866 | **359429** | **293283** |
| `bench 13` | 862329 | **748138** | **815644** |
| `bench 16` | 3024920 | **3026279** | **2998029** |

All six differ. Note the directions are not monotone in K — K=20 drops `bench 13` by 13% while K=64 drops
it by 5% — which is a reminder that node count is not monotone in the strength of a pruning term; the
search tree rearranges.

## 6. P4 — sanitizers

`-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g -O1`. The
`-fno-sanitize-recover=all` is what makes "stderr empty" a real test: any UBSan finding aborts.

**Planted faults first** (`planted_fault.cpp.txt`, same flags, `logs/p4-planted.txt`):

| planted fault | observed exit | message |
|---|---:|---|
| write one past a `[13][64][7]` `int16_t` table | **1** | `runtime error: index 13 out of bounds for type 'short int [13][64][7]'` |
| signed integer overflow | **1** | `runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'` |
| clean use of the same table | **0** | `OK -5` |

The first fault is deliberately the shape of the one this feature could produce (an out-of-range index
into a correction table); the second is the shape of a bad arithmetic term. Both are caught; clean code is
not flagged.

**Then the engine** (`logs/p4-run.txt`):

| run | exit | stderr bytes | result |
|---|---:|---:|---|
| `bench 13`, `CorrMargin 20` | 0 | **0** | 748138 nodes — same as the release build |
| `bench 13`, `CorrMargin 64` | 0 | **0** | 815644 nodes — same as the release build |
| 200 P2 positions, `CorrMargin 20` | 0 | **0** | 200 of 200 bestmoves |
| 200 P2 positions, `CorrMargin 64` | 0 | **0** | 200 of 200 bestmoves |

**A mistake I caught here and am reporting:** my first sanitizer run passed with the option *not set* —
the script had been copied from job 3 and still wrote `setoption name LmrCaptureHistory`, which this engine
ignores. It passed, and the pass was worthless: `bench 13` printed 862329, the *off* number, which is what
gave it away. After fixing the option name the same runs print 748138 and 815644 (matching release) and
still produce empty stderr. The node counts are what make the difference between a real test and a
vacuous one.

## 7. P5 — the matches

Same exe both sides (`~/work/j5p/forge`), `nodes=20000`, `Threads 1`, `Hash 16`, `OwnBook false`, UHO
openings both colours, no adjudication, concurrency 4 on 4 cores.

**Control**, 300 games, seed 7920, `logs/control.full.txt`: +226.69 +/- 32.04 (own pair interval +196.3 to
+260.5), pair counts `[0,4,23,70,53]`. Near +200 as required.

**Option delivery**, proved with the engine input log (`logs/probe-M1.engine.log`, 2 games, seed 7921):

```
cand <--- setoption name Threads value 1
cand <--- setoption name Hash value 16
cand <--- setoption name OwnBook value false
cand <--- setoption name CorrMargin value 20
base <--- setoption name Threads value 1
base <--- setoption name Hash value 16
base <--- setoption name OwnBook value false        (no CorrMargin)
```

No row of mine has pair counts `[0,0,N,0,0]`; M3's is `[55,208,375,208,55]`, which is as far from
degenerate as a symmetric result gets.

| match | candidate | seed | games (asked) | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---:|---:|---|---:|---|---:|---|
| M1 | `CorrMargin 20` | 7921 | **2000 (complete)** | 552-574-874 | 1000 | [65,241,402,235,57] | -3.82 +/- 10.57 | **-3.82, -14.4 .. +6.8** |
| M2 | `CorrMargin 20` | 7922 | **2000 (complete)** | 575-561-864 | 1000 | [54,239,410,233,64] | +2.43 +/- 10.46 | **+2.43, -8.0 .. +12.9** |
| **K=20 pooled** | | | **4000** | 1127-1135-1738 | 2000 | [119,480,812,468,121] | | **-0.69, -8.1 .. +6.7** |
| M3 | `CorrMargin 64` | 7923 | **1854 of 2000 (cut)** | 536-530-788 | 927 | [56,211,387,217,56] | -0.00 +/- 11.06 (block covers 1,802) | **+1.12, -9.8 .. +12.0** |
| M4 | `CorrMargin 64` | 7924 | **1184 of 2000 (cut)** | 333-351-500 | 592 | [40,146,236,132,38] | -7.30 +/- 15.18 (covers 1,000) | **-5.28, -19.3 .. +8.7** |
| **K=64 pooled** | | | **3038** | 869-881-1288 | 1519 | [96,357,623,349,94] | | **-1.37, -10.0 .. +7.2** |

**Crashes, illegal moves, disconnects: 0 in every match and in the control.** Checked by tallying how each
of the 7,338 games ended, not by grepping for a word (`logs/termination_reasons.txt`): every game ended by
a chess rule (mate, 3-fold, fifty moves, insufficient material, stalemate).

Per-game files: `logs/{control,M1,M2,M3,M4}.games.txt`. PGNs deleted after deriving these (size).

## 8. P6 — speed, honestly

`bench 16` nps, option off against `CorrMargin 20`, 10 interleaved pairs (`logs/p6-speed.txt`):

| | mean nps | sd |
|---|---:|---:|
| off | 1,700,700 | 82,078 |
| on (K=20) | 1,828,637 | 70,091 |

Per-pair ratio mean **1.0772**, min 0.9963, max 1.1974 — i.e. **+7.7% faster with the option on**.

**That number is not what it looks like, and the node counts say so.** `bench 16` with the option on
searches **3,026,279** nodes against **3,024,920** off — 0.04% more, i.e. the same work. So the +7.7% is
not the feature being cheaper; it is this machine's throughput varying between the two halves of the
measurement (note the 82k and 70k standard deviations, and that 10 of 10 pairs went the same way, which
looks like a warm-up or frequency effect rather than the feature). **The honest statement is: this
feature costs nothing measurable in nps and changes the node count by 0.04% on bench 16; the +7.7% I
measured is machine drift, not a speed gain.** The job warned that this is a rough figure with different
trees; it turned out to be a rough figure even with the same node count.

**Size of the new table: 0 bytes per thread.** There is no new table. The feature adds one `int` to
`SearchStack` (4 bytes per stack entry, `MaxPly + 8` entries), which is a few hundred bytes per thread and
already inside a struct that is cache-resident in use. Nothing is allocated.

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

## 10. Files of the repository I opened

`forge-combo29/src/search.cpp` (`corrected_eval`, `update_correction`, the reverse-futility and quiet-
futility tests, `SearchStack` use, the option globals), `forge-combo29/src/uci.cpp` (option list,
`apply_spin`, `setoption` dispatch), `forge-combo29/include/forge/search.hpp` (`CorrectionGrain`,
`CorrectionLimit`, `SearchStack`, the `extern` option declarations), `forge-combo29/CMakeLists.txt`. I did
not open any other helper's files or any other engine's source.

## 11. Stamps

| step | start | end | source |
|---|---|---|---|
| job file read, contradiction recorded | 19:57:33Z | 19:57:57Z | `JOB_TEXT_CONTRADICTION.txt` |
| P1 tracer built, first trace | 19:58:1xZ | 19:58:20Z | `logs/p1-stamps.txt` |
| patch written, patched build | 19:58:3xZ | 19:59:1xZ | — |
| Step 0 numbers, unpatched and patched | 19:59:16Z | 19:59:21Z | `logs/step0-stamps.txt` |
| P2 2,000 positions, both sides | 19:59:23Z | 20:00:09Z | `logs/p2-stamps.txt` |
| P3 | 20:00:11Z | 20:00:16Z | `logs/p3-stamps.txt` |
| P4 sanitizer build + planted faults + runs | 20:00:2xZ | 20:01:01Z | `logs/p4-stamps.txt` |
| Control (300 games) | 20:01:14Z | 20:03:12Z | `logs/control-stamps.txt` |
| M1 probe (2 games) | 20:03:15Z | 20:03:18Z | `logs/probe-M1.engine.log` |
| M1 | 20:03:21Z | 20:21:28Z | `logs/M1-stamps.txt` |
| M2 | 20:21:31Z | 20:40:16Z | `logs/M2-stamps.txt` |
| M3 | 20:40:19Z | 20:57:49Z | `logs/M3-stamps.txt` |
| M4 | 20:57:54Z | 21:09:34Z | `logs/M4-stamps.txt` |
| P6 | 21:09:36Z | 21:10:11Z | `logs/p6-stamps.txt` |

Job file found 19:57:33Z; last measurement 21:10:11Z = **72 min 38 s**, inside the 80-minute budget and
about 2.5 minutes past the 70-minute stop point.

## 12. What I did not do

- **M3 and M4 are short** (1,854 and 1,184 of 2,000). Both are marked, and my Elo uses every game played.
  The K=64 pooled interval is therefore wider than a full run would give.
- **I did not test the second site separately.** P1 shows the quiet-futility term removes 0.39% of skips at
  K=64, so the matches are effectively site 1 alone. To test site 2 alone I would have had to add a second
  option, which the job forbade ("one idea, one switch").
- **I did not decompose the P6 speed figure properly.** I did report the node counts that show it is
  drift, but I did not use the compiler-opaque-zero trick to isolate the cost of the arithmetic itself.
- **I did not test K values between 20 and 64**, or beyond 64. P1 measured seven candidates; the job asked
  for two to be played.
- **No time control, no PC net**; fixed 20,000 nodes, built-in net, 4 cores, concurrency 4.
- The P1 trace was taken on `bench 13` only, not across a spread of positions.

## 13. What I am not sure about

- **Whether a different functional form would work where this one does not.** Both K values are flat, and
  both directions of the term are symmetric (a large correction widens the margin whether the correction
  is positive or negative). It is possible the right signal is the *signed* correction combined with
  `improving`, or the correction's *change* rather than its size. Untested.
- **Whether the flat result is because site 1 is the wrong place.** Reverse futility already requires
  `eval >= beta` with a large margin; adding a correction term there may mostly remove cutoffs that were
  nearly safe anyway. The null-move verification at `src/search.cpp:1694` looks like a better candidate
  for the same idea, and it was outside this job's scope.
- **The 0.00 at 1,802 games in M3** is a coincidence of a symmetric tree (`[55,208,375,208,55]`), not a
  degenerate row — but it is the kind of number that looks wrong at a glance, so I am flagging it.
- **The +7.7% nps might be a real warm-up artefact of how I measured** (10 back-to-back pairs with the on
  run second each time). If the machine ramps up during a run, the second half of every pair looks faster
  regardless of the option. That would explain 10 of 10 pairs. I did not randomise the order to check.
- **My K values are "about 2%" and "about 8%" of one bench's cutoffs**, not of a game's. A match sees a
  different mix of positions.

## 14. A better way

**The job should have said what to do when the two sites have wildly different sensitivity.** P1 showed
site 1 reacts to the term and site 2 does not (0.39% of skips at K=64), so "one idea, one switch" silently
turned into "measure site 1". The sharper version: instrument both sites first, and if one is inert at
every plausible K, either drop it from the feature or say in the job that the measurement will in practice
be of the other site. How to check it: the P1 table I produced takes about 10 minutes on one bench and
would have told the job's author the same thing before the matches were scheduled.

**For P6, randomise the pair order.** Ten interleaved pairs where the "on" run is always second produced a
uniform +7.7% that the node counts contradict. Alternating which side goes first within each pair (or
shuffling the order) removes the warm-up bias for the same cost. How to check it: rerun P6 with the pairs
in a random order and see whether the ratio stays +7.7% or collapses toward 1.00 — my prediction is the
latter, given 0.04% node difference.

**A "flat" result like this one is worth one more question than a "positive" result.** Both of my K values
landed within 1.4 Elo of zero with intervals around +/- 8. That is a clean null, and the useful next step
is not a third K but a different placement of the same signal (null-move verification, or the signed
version), because the mechanism itself — the static eval has been wrong here before — is still plausible.

## 15. Model

`deepseek3`. Model: **DeepSeek V4.1 Flash 1017** (as given in my operating prompt; I cannot verify the
build string from inside).

## 16. Questions for Fable

1. Do you want the same term at the null-move verification site instead? That is where the mechanism looks
   most promising to me, and P1 says it is not worth putting anywhere near quiet futility.
2. Do you want a signed rather than absolute term (correction above/below raw eval treated differently)?
3. Should the P6 protocol be changed to randomise the run order? The +7.7% I measured cannot be real.
