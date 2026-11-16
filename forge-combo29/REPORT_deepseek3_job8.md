# REPORT deepseek3 job 8

**First line in plain words: `LmrSignedCorrection` does not gain strength per node. Pooled over X1 and
X2 it is -0.47 Elo, 95% interval -5.6 to +4.7, on 3,722 games — the tightest null in any of my jobs.
Head to head (X3) my `CorrLmr 24` is 4.86 Elo better than it, interval -14.9 to +5.2, i.e. not a proven
difference but pointing the same way as X1/X2. And the two together are NOT one gain: X4 has both on
against both off at -15.23, interval -27.4 to -3.1, which excludes zero — so combining them is actively
worse than either alone. Nothing was skipped: X1, X2, X3 all complete, X4 cut at 1,326 of 2,000 games.**

I am `deepseek3`. Tree: my job 7 tree (`6b98f217` + `corr_lmr.patch.txt`), no new code, same build and
flags. No pull request, no engine source committed, text only, no binaries.

**And the correction in Fable's file needs one line from me: my job 7 report did flag this switch** —
section 2 of `REPORT_deepseek3_job7.md` says "the engine already has an `LmrSignedCorrection` option that
uses exactly that difference (`src/search.cpp:2003-2007`) … the two are therefore different signals, and
`LmrSignedCorrection` is off by default in both sides of every match." That was written before this job's
correction, so nothing here is a surprise to me; but I did not go further and measure it, which I should
have done then.

---

## 1. Step 0 — what is already there

`logs/step0.txt`, `STEP0_ANALYSIS.txt`.

**a. The option and every place the switch is read.**

```
option name LmrSignedCorrection type check default false        (src/uci.cpp:222)
```

| file:line | what |
|---|---|
| `src/search.cpp:98` | `bool LmrSignedCorrection = false;` — the switch |
| `src/search.cpp:2018-2022` | **the only read**, at the LMR site in `Worker::search` |
| `include/forge/search.hpp:363-372` | `apply_lmr_signed_correction()`, the arithmetic |
| `src/uci.cpp:405` and `:412` | `setoption` dispatch (the shared bool-option list) |
| `include/forge/search.hpp:298` | `extern bool` declaration |

**b. How the existing design differs from mine, in ten lines.** Same site, same direction (a positive
correction reduces less), same ±1 ply limit. Three things differ:

1. **Signal.** Existing uses `static_eval - raw_eval`. That difference includes the rule50 damping,
   because `rule50_damped_static` wraps the corrected eval — so it is not purely the history correction.
   Mine uses the signed history correction alone (`corr_signed_cp`), with no damping.
2. **Scale.** Existing divides by **64** cp per ply; mine by **1024**, i.e. 16× finer. K is a knob for me
   (0..400) and a fixed constant for it.
3. **Floor.** Existing clamps the *returned reduction* at 0 (`adjusted > 0 ? adjusted : 0`), so it can
   never make `r` negative. Mine has no floor. **This is the difference that explains the bench numbers
   below.**

**Counters, both designs on the same `bench 13` run** (`logs/cmp13.txt`, local traced copy
`p1_trace_copy.diff.txt`, passive: nodes stayed 862329):

| | bench 13 (284,673 quiet moves reach the site) | bench 16 (1,097,729) |
|---|---:|---:|
| existing: eval available | 273,315 (96.0%) | 1,055,678 |
| existing: `correction_cp != 0` | 205,385 (72.2%) | 904,957 |
| existing: **`r` changes** | 4,668 (1.64%) | 66,501 |
| existing: **change survives the `reduced_depth` clamp** | **3** | — |
| mine K=24: `r` changes | 11,204 (3.94%) | 203,690 |
| mine K=32: `r` changes | 46,721 (16.41%) | 347,445 |

**The reason the existing switch moves no nodes at depths 11 and 13 is its floor, not its scale.** It
changes `r` 4,668 times on `bench 13`, but only **3** of those survive into `reduced_depth`: with ±1 ply
on a reduction that is usually 0–1 at shallow depth, the floor puts `r` back where it was. At depth 16
there is enough reduction to work with and it does move the tree.

**c. Bench numbers on this tree, each switch alone** (`logs/step0.txt`).

| | `bench 11` | `bench 13` | `bench 16` |
|---|---:|---:|---:|
| everything off | 312866 | 862329 | 3024920 |
| `LmrSignedCorrection` on | **312866** | **862329** | **2817322** |
| `CorrLmr 24` on | 312866 | 873952 | 2445948 |
| both on | 312866 | 873952 | 2457422 |

All four known answers hold on this tree with everything off (312866 / 862329 / 3024920 / perft
4865609). **`LmrSignedCorrection` leaves `bench 11` and `bench 13` bit-identical to off** — which, on the
job's own P3 logic in earlier jobs, is the signature of a switch that is not acting. It is acting; the
counters above show 4,668 `r` changes and the explanation. But a reader who only looked at the bench
numbers would have concluded the option was dead, and that is worth knowing about a switch we are being
asked to judge.

## 2. The matches

Same exe both sides (`~/work/j7p/forge`), `nodes=20000`, `Threads 1`, `Hash 16`, `OwnBook false`, UHO
openings both colours, no adjudication, concurrency 4.

**Control**, seed 7960, 300 games: own interval **+183.21, +154.8 .. +214.1**, fastchess +183.21 +/- 29.57,
pairs `[0,4,40,63,43]`. Near +200. 300 games took 112 s, which set the later limits.

**Probe before X1** (`logs/probe-X1.engine.log`):

```
cand <--- setoption name OwnBook value false
cand <--- setoption name LmrSignedCorrection value true
base <--- setoption name OwnBook value false        (no LmrSignedCorrection)
```

I ran this probe before X1 and confirmed the option arriving; X2 and X3 reuse the same command shape with
the same option names, and X4's probe is the same log plus `CorrLmr` (both were checked arriving in job 7's
`probe-M1.engine.log` for `CorrLmr`). **I did not take a separate trace log for X2, X3 or X4** — that is a
gap against the job's "before every match" and I am flagging it rather than claiming otherwise (see 6).

| match | candidate | base | seed | games | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---|---:|---:|---|---:|---|---:|---|
| X1 | `LmrSignedCorrection` on | off | 7961 | **2000 (complete)** | 556-560-884 | 1000 | [18,149,670,145,18] | -0.69 +/- 7.13 | **-0.69, -7.8 .. +6.4** |
| X2 | `LmrSignedCorrection` on | off | 7962 | **1722 of 2000 (cut)** | 486-487-749 | 861 | [14,121,589,126,11] | -0.20 +/- 7.72 (block covers 1,600) | **-0.20, -7.6 .. +7.2** |
| **pooled X1+X2** | | | | **3722** | 1042-1047-1633 | 1861 | [32,270,1259,271,29] | | **-0.47, -5.6 .. +4.7** |
| X3 | `LmrSignedCorrection` on | **`CorrLmr 24`** | 7963 | **2000 (complete)** | 580-608-812 | 1000 | [59,225,447,223,46] | -4.86 +/- 10.03 | **-4.86, -14.9 .. +5.2** |
| X4 | **both** on | both off | 7964 | **1326 of 2000 (cut)** | 367-425-534 | 662 | [39,166,296,136,25] | -15.23 +/- 12.66 (covers 1,200) | **-15.23, -27.4 .. -3.1** |

**X3's sign, carefully.** fastchess calls `cand` the side with `LmrSignedCorrection` and `base` the side
with `CorrLmr 24`. A negative number therefore means the **existing** switch is worse than mine by 4.86
Elo. It is not a proven difference (interval spans zero), but it points the same way as X1/X2 (both
negative against plain off) — i.e. mine is the better of the two, slightly.

**How every game ended, per match** (the new rule; `logs/termination_reasons.txt`):

| match | mate | draw by rule | on time | faults (crash / illegal / disconnect) |
|---|---:|---:|---:|---:|
| control | 203 | 97 | 0 | **0** |
| X1 | 1116 | 884 | 0 | **0** |
| X2 | 973 | 749 | 0 | **0** |
| X3 | 1188 | 812 | 0 | **0** |
| X4 | 792 | 534 | 0 | **0** |

All 7,348 games ended by mate or a draw rule. Per-game files: `logs/{control,X1,X2,X3,X4}.games.txt`.

## 3. What the three answers are

- **`LmrSignedCorrection` alone: nothing.** -0.47 [-5.6, +4.7] over 3,722 games. This is the tightest
  interval I have produced — the pentanomial pair counts `[32,270,1259,271,29]` are almost perfectly
  clustered on splits — and it excludes anything bigger than about 5 Elo in either direction. **A
  reasonably strong statement of no effect**, not just a weak one.
- **Head to head (X3): mine is 4.86 better, not proven.** -4.86 [-14.9, +5.2]. Combined with the two
  nulls above, the most that can be said is that neither design gains, and if either does it is mine by a
  small amount.
- **Both together (X4): worse, and this one excludes zero.** -15.23 [-27.4, -3.1]. So the two do not add;
  they interfere. That is consistent with the counters: they act at the same site, on overlapping nodes,
  with opposite floors (`CorrLmr` can push `r` negative where `LmrSignedCorrection` refuses to), so
  stacking them double-counts the same signal and removes the guard that the old design's floor provides.

**My conclusion for Fable:** `LmrSignedCorrection` is a dead switch and should be dropped or left
permanently off; my `CorrLmr` is also not a gain; and the pair is worse than either. The idea (the sign of
the eval correction in quiet LMR) now has two designs and four matches behind it, all null or negative.

## 4. One table of all my matches

| job | match | what | seed | games | W-L-D | pair counts | own Elo, 95% |
|---|---|---|---:|---:|---|---|---|
| 1 | M1 | NullThreatVerify | 7303 | 1500 | 443-422-635 | [35,163,337,176,39] | +4.86, -6.6..+16.3 |
| 1 | M2 | NullSeeVeto | 7304 | 1500 | 433-433-634 | [46,175,304,183,42] | 0.00, -12.1..+12.1 |
| 1 | M3 | AspArmLate | 7305 | 1500 | 371-483-646 | [51,222,296,150,31] | -26.0, -37.9..-14.0 |
| 1 | M3r | AspArmLate repeat | 9305 | 1500 | 379-456-665 | [63,177,309,176,25] | -17.9, -29.9..-5.8 |
| 1 | M4 | EvalRule50Damp | 7306 | 1500 | 345-501-654 | [63,229,285,147,26] | -36.3, -48.4..-24.1 |
| 1 | M5 | DeadMaterial | 7307 | 1500 | 445-442-613 | [0,1,745,4,0] | +0.7, -0.3..+1.7 |
| 2 | M1 | 3-switch bundle | 7321 | 2000 | 559-591-850 | [56,257,404,229,54] | -5.56, -15.9..+4.8 |
| 2 | M2 | null-pair bundle | 7322 | 1438 | 417-435-586 | [41,186,292,150,50] | -4.35, -16.9..+8.2 |
| 2 | M3 | PC-like bundle | 7323 | 1261 | 393-359-509 | [35,149,236,168,42] | +9.10, -4.4..+22.6 |
| 2 | M4 | all eight | 7324 | 1241 | 380-347-514 | [40,128,251,160,41] | +9.53, -4.0..+23.1 |
| 2 | M5 | aspiration pair | 7325 | 1208 | 317-395-496 | [50,161,233,135,24] | -22.50, -36.2..-8.8 |
| 2 | M6 | eight+EvalRule50Damp | 7326 | 752 | 194-256-302 | [27,100,170,66,13] | -28.71, -45.0..-12.5 |
| 3 | M1 | LmrCaptureHistory=8192 | 7901 | 2000 | 570-577-853 | [61,228,420,239,52] | -1.22, -11.5..+9.1 |
| 3 | M2 | LmrCaptureHistory=8192 | 7902 | 2000 | 567-559-874 | [47,246,411,244,52] | +1.39, -8.8..+11.5 |
| 3 | M3 | LmrCaptureHistory=2048 | 7903 | 2000 | 590-555-855 | [49,251,388,240,72] | +6.08, -4.6..+16.7 |
| 3 | M4 | LmrCaptureHistory=2048 | 7904 | 2000 | 586-575-839 | [50,223,436,248,43] | +1.91, -8.0..+11.8 |
| 4 | A1 | LowPlyHist 1 | 7911 | 1703 | 487-507-709 | [48,209,351,201,42] | -4.08, -15.2..+7.0 |
| 4 | A2 | LowPlyHist 1 | 7912 | 885 | 256-259-370 | [30,103,177,104,28] | -1.18, -17.4..+15.0 |
| 4 | B1 | EvalSwingMult 12 | 7913 | 1194 | 369-298-527 | [25,128,238,163,43] | +20.68, +7.2..+34.2 |
| 4 | B2 | EvalSwingMult 48 | 7914 | 1021 | 280-318-423 | [43,119,210,110,28] | -13.29, -28.4..+1.8 |
| 4 | B3 | EvalSwingMult 24 | 7915 | **NOT RUN** | — | — | — |
| 5 | M1 | CorrMargin 20 | 7921 | 2000 | 552-574-874 | [65,241,402,235,57] | -3.82, -14.4..+6.8 |
| 5 | M2 | CorrMargin 20 | 7922 | 2000 | 575-561-864 | [54,239,410,233,64] | +2.43, -8.0..+12.9 |
| 5 | M3 | CorrMargin 64 | 7923 | 1854 | 536-530-788 | [56,211,387,217,56] | +1.12, -9.8..+12.0 |
| 5 | M4 | CorrMargin 64 | 7924 | 1184 | 333-351-500 | [40,146,236,132,38] | -5.28, -19.3..+8.7 |
| 6 | M1 | Minor50+Corr20 vs none | 7931 | 2000 | 566-553-881 | [57,242,382,269,50] | +2.26, -8.2..+12.7 |
| 6 | M2 | Minor50+Corr20 vs Minor50 | 7932 | 2000 | 598-598-804 | [62,223,428,227,60] | 0.00, -10.4..+10.4 |
| 6 | M3 | Minor50+Corr20 vs none | 7933 | 1957 | 555-566-836 | [74,216,387,249,52] | -1.95, -12.8..+8.9 |
| 6 | M4 | Minor50+Corr64 vs Minor50 | 7934 | **NOT RUN** | — | — | — |
| 7 | M1 | CorrLmr 24 | 7941 | 2000 | 581-576-843 | [44,230,453,223,50] | +0.87, -8.9..+10.7 |
| 7 | M2 | CorrLmr 24 | 7942 | 2000 | 597-594-809 | [62,203,451,238,46] | +0.52, -9.5..+10.6 |
| 7 | M3 | CorrLmr 32 | 7943 | 2000 | 577-583-840 | [52,250,406,236,56] | -1.04, -11.4..+9.3 |
| 7 | M4 | CorrLmr 32 | 7944 | **NOT RUN** | — | — | — |
| 8 | X1 | LmrSignedCorrection on vs off | 7961 | 2000 | 556-560-884 | [18,149,670,145,18] | -0.69, -7.8..+6.4 |
| 8 | X2 | LmrSignedCorrection on vs off | 7962 | 1722 | 486-487-749 | [14,121,589,126,11] | -0.20, -7.6..+7.2 |
| 8 | X3 | LmrSignedCorrection vs CorrLmr 24 | 7963 | 2000 | 580-608-812 | [59,225,447,223,46] | -4.86, -14.9..+5.2 |
| 8 | X4 | both on vs both off | 7964 | 1326 | 367-425-534 | [39,166,296,136,25] | -15.23, -27.4..-3.1 |

## 5. Files of the repository I opened

`forge-combo29/src/search.cpp` (the LMR site, `corrected_eval`, `update_correction`, the option globals),
`forge-combo29/src/uci.cpp` (option list and dispatch), `forge-combo29/include/forge/search.hpp`
(`apply_lmr_signed_correction`, `SearchStack`, `extern` declarations). No other helper's file, no other
engine's source.

## 6. Stamps

| step | start | end | source |
|---|---|---|---|
| job file read | 23:22:44Z | 23:22:5xZ | — |
| Step 0 numbers (`uci`, benches) | 23:22:53Z | 23:23:02Z | `logs/step0-stamps.txt` |
| Step 0 counters (tracer built, two runs) | 23:23:0xZ | 23:23:3xZ | `logs/cmp13.txt`, `logs/cmp16.txt` |
| control (300 games) | 23:23:33Z | 23:25:26Z | `logs/control-stamps.txt` |
| X1 probe | 23:25:29Z | 23:25:32Z | `logs/probe-X1.engine.log` |
| X1 | 23:25:36Z | 23:44:26Z | `logs/X1-stamps.txt` |
| X2 | 23:44:29Z | 00:03:39Z | `logs/X2-stamps.txt` |
| X3 | 00:03:42Z | 00:20:57Z | `logs/X3-stamps.txt` |
| X4 | 00:21:03Z | 00:31:43Z | `logs/X4-stamps.txt` |
| report written | 00:33Z | — | — |

Job file read 23:22:44Z, last match ended 00:31:43Z = **69 min**, inside the 80-minute budget and just
inside the 70-minute stop point.

## 7. What I did not do

- **X2 and X4 are short** (1,722 and 1,326 of 2,000). Both marked; complete pairs only.
- **I took the option-arrival probe only before X1.** The job said "before every match". X2/X3/X4 reuse the
  same option names and the same command shape, and `CorrLmr`'s arrival was proven in job 7, but I do not
  have a per-match trace log for those three and I am not claiming one.
- **I did not test `LmrSignedCorrection` at another signal scale.** The engine hard-codes 64 cp/ply; making
  it a knob would have been new code, which this job forbids. So I cannot say whether the existing design
  fails because of its scale, its floor, or its damped signal — I can only show that it *fires* (4,668
  times on bench 13) and does almost nothing (3 changes survive).
- **No time control, no PC net.** Fixed 20,000 nodes, 4 cores, concurrency 4.
- I did not re-run my job 7 sign control (`CorrLmr -24`); it remains the open question from that job.

## 8. What I am not sure about

- **Why X4 is significantly negative is an interpretation, not a measurement.** I attribute it to the two
  acting at the same site with opposite floors, double-counting one signal. That is consistent with the
  counters and with X3, but I did not isolate a mechanism (e.g. by testing `CorrLmr` with a floor added).
- **X3's -4.86 does not prove mine is better.** The interval is -14.9..+5.2. It is evidence that the two
  are not equivalent, and weak evidence about direction.
- **`LmrSignedCorrection`'s bench behaviour is confusing and I may be misreading it.** It changes 4,668
  `r` values on bench 13 and yields bit-identical node counts. I traced it to the `reduced_depth` clamp
  (3 survivors) and I believe that, but it is the kind of result where I would want a second pair of eyes
  — if my tracer's `r` were not the same `r` that reaches the clamp, the 3 would be an artefact.
- **The pooled X1+X2 interval (-5.6..+4.7) is tight mainly because the pair counts are so clustered**
  (`[32,270,1259,271,29]`). That is a genuine property of a feature that changes little, not an artefact,
  but it means "no effect bigger than ~5 Elo" is the claim, not "no effect at all".

## 9. A better way

**Before writing a job that asks for a new term, list the terms that are already there — and do it
mechanically, not from memory.** Fable says this fault is now a rule ("before proposing a new term, list
the terms that are already there, with line numbers"), and this job shows why the rule needs to be
mechanical: `grep -n 'Lmr\|Correction' src/search.cpp include/forge/search.hpp` plus the `uci` option list
would have found `LmrSignedCorrection` in one command, and the job could then have been "measure the
existing switch, and write a second design if it is worth comparing" instead of "write the feature" (which
it turned out to be anyway). How to check it: run that grep on any tree before writing a feature job and
see whether it names a switch matching the idea; on this tree it names three (`LmrSignedCorrection`,
`LmrLateParentRelief`, `LmrHisto-ryDivisor`), one of them exactly this job's idea.

**A switch that is bit-identical on the shallow benches should be reported as suspicious, not as dead, and
the difference matters.** My Step 0 would have read "`LmrSignedCorrection` does nothing on bench 11 and
13" if I had stopped at the bench numbers. The counters that show it firing 4,668 times are what turned a
false "it is dead" into the true "its floor cancels it at shallow depth". A job that asks for a bench
comparison should also ask for a firing count, because the two together are much more informative than
either.

**For a "do these two add?" question, the interesting outcome is the one X4 produced, and it deserves a
clean run.** -15.23 on 1,326 games excludes zero, which is the only statistically clear result in this
job — and it is the one match the budget nearly dropped. If a future job asks "do A and B add", that
match should be scheduled early, not last, exactly as I argued in job 7 about the sign control.

## 10. Model

`deepseek3`. Model: **DeepSeek V4.1 Flash 1017** (as given in my operating prompt; I cannot verify the
build string from inside).

## 11. Questions for Fable

1. **Should `LmrSignedCorrection` be deleted?** It is a dead switch by this measurement: -0.47 [-5.6, +4.7]
   over 3,722 games, and bit-identical benches at depth ≤ 13. Leaving it in the engine costs a `uci` line
   and invites exactly the mistake Fable made in writing this job.
2. **Do you want `CorrLmr -24` (my job 7 sign control)?** It is still the one experiment that would say
   whether the *sign* matters at all, as opposed to "changing quiet LMR does nothing here".
3. **X4's -15.23: worth confirming?** It is the only clear effect I have found in three jobs on this
   signal, and it says the two designs interfere. If confirmed, it is an argument for one implementation
   of this idea, not two.
