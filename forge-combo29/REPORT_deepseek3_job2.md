# REPORT deepseek3 job 2

**First line, in plain words: no bundle is stronger than its best single part, and the two switches
that lost alone still lose in company. The two bundles that contain only switches that did not lose are
+9.1 and +9.5 Elo, but both intervals (`-4.4..+22.6` and `-4.0..+23.1`) contain zero, so neither is
distinguishable from no change and neither is worth more than the sum of its parts. `AspArmLate` +
`AspCappedReopen` = -22.5 (`-36.2..-8.8`), clearly still bad. `EvalRule50Damp` added on top of the
eight-switch bundle = -28.7 (`-45.0..-12.5`), clearly still bad. Nothing here says a loser gets better
in company.**

I am `deepseek3`. Branch `for-fable-and-opus/deepseek3-work`. No pull request; no engine source touched.
Only five of the six matches reached their full game count — the clock, not a failure; every cut is
marked below and every cut number is computed from the games actually played.

---

## 1. Step 0 — build with `-DFORGE_MATE_ALPHA_GUARD=1`

The flag reached the compiler (`~/work/build2/CMakeFiles/forge.dir/flags.make` contains
`-DFORGE_MATE_ALPHA_GUARD=1`), the three known numbers are unchanged, and `uci` lists the option. Raw
output: `tests_deepseek3_job2/logs/step0-flag-and-numbers.txt`. Build 15:59:44Z to 15:59:50Z.

| command | expected | printed | match |
|---|---:|---:|---|
| `bench 11` | 312866 | `nodes 312866 time 179` | yes |
| `bench 13` | 862329 | `nodes 862329 time 475` | yes |
| `go perft 5` | 4865609 | `nodes 4865609` | yes |

```
## does uci list MateAlphaGuard?
option name MateAlphaGuard type check default false
```

## 2. Bench 13 per bundle (asked for)

One fresh process per bundle, every switch of that bundle `true`. Raw: `logs/step1-bundles.raw.txt`.

| bundle | bench 13 nodes | differs from 862329 |
|---|---:|---|
| none (baseline) | 862329 | — |
| M1: LmrDeeperShallower + ThreatHistory + NullThreatVerify | 925486 | yes |
| M2: NullThreatVerify + NullSeeVeto | 929170 | yes |
| M3 cand: M1's three + NonPawnCorrection + MateAlphaGuard | 862005 | yes |
| M3 base: NonPawnCorrection + MateAlphaGuard | 775589 | yes |
| M4/M6 base: all eight | 868694 | yes |
| M5: AspArmLate + AspCappedReopen | 870846 | yes |
| M6 cand: all eight + EvalRule50Damp | 800697 | yes |

Every bundle moves the count, so no option in any bundle is silently inert on these positions. Note
M3: the two sides differ only by M1's three switches (862005 against 775589), so the options arrived on
both sides and act differently.

## 3. The control

`logs/control2.full.txt`, seed 7311, 20,000 against 10,000 nodes, 300 games, 15:59:54Z to 16:01:53Z.

```
Elo: 223.26 +/- 35.52, nElo: 323.18 +/- 39.32
Games: 300, Wins: 196, Losses: 26, Draws: 78, Points: 235.0 (78.33 %)
Ptnml(0-2): [0, 5, 32, 51, 62], WL/DD Ratio: 1.91
```

Passes: +223 Elo, pair counts strongly off-centre, so the tool still sees a difference today with the
new build.

**Option delivery was checked, not assumed**, because the job warned about a `[0,0,N,0,0]` row. A
2-game match of M1's three switches with the trace log on (`logs/control3.engine.log`) shows all three
going to `cand` and none of them going to `base`:

```
cand <--- setoption name LmrDeeperShallower value true
cand <--- setoption name ThreatHistory value true
cand <--- setoption name NullThreatVerify value true
base <--- setoption name Threads value 1        (base gets only Threads and Hash)
base <--- setoption name Hash value 16
```

No job-2 row has pair counts `[0,0,N,0,0]`.

## 4. The matches

Every match ran with a time limit (`timeout`), so the ones that were cut stopped by the clock. The
`own Elo` column is my pentanomial computation from the pair counts with a 95% interval
(`pair_elo.py`, output `logs/pair_elo.txt`); the fastchess column is its own printed number.

| match | candidate switches | base switches | seed | games | cand W-L-D | pairs | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---|---:|---:|---|---:|---|---:|---|
| M1 | LmrDeeperShallower, ThreatHistory, NullThreatVerify | none | 7321 | **2000 (complete)** | 559-591-850 | 1000 | [56,257,404,229,54] | -5.56 +/- 10.36 | **-5.56, -15.9 .. +4.8** |
| M2 | NullThreatVerify, NullSeeVeto | none | 7322 | 1438 of 2000 (**INCOMPLETE**, cut) | 417-435-586 | 719 | [41,186,292,150,50] | -3.23 +/- 12.72 (at 1,398 games) | **-4.35, -16.9 .. +8.2** |
| M3 | M1's three + NonPawnCorrection + MateAlphaGuard | NonPawnCorrection + MateAlphaGuard | 7323 | 1261 of 2000 (**INCOMPLETE**, cut) | 393-359-509 | 630 | [35,149,236,168,42] | +8.98 +/- 13.96 (at 1,200) | **+9.10, -4.4 .. +22.6** |
| M4 | all eight | none | 7324 | 1241 of 2000 (**INCOMPLETE**, cut) | 380-347-514 | 620 | [40,128,251,160,41] | +8.41 +/- 13.79 (at 1,198) | **+9.53, -4.0 .. +23.1** |
| M5 | AspArmLate, AspCappedReopen | none | 7325 | 1208 of 1500 (**INCOMPLETE**, cut) | 317-395-496 | 603 | [50,161,233,135,24] | -22.32 +/- 13.72 (at 1,200) | **-22.50, -36.2 .. -8.8** |
| M6 | all eight + EvalRule50Damp | all eight | 7326 | 752 of 1500 (**INCOMPLETE**, cut) | 194-256-302 | 376 | [27,100,170,66,13] | -30.19 +/- 18.06 (at 600) | **-28.71, -45.0 .. -12.5** |

All switches are `option.NAME=true`, `Threads 1`, `Hash 16`, `nodes=20000`, no clock, no adjudication,
same exe both sides, `UHO_Lichess_4852_v1.epd` with `order=random`, `-games 2 -repeat`, concurrency 4.

My own Elo agrees with fastchess's on every match to within 1.5 Elo (M1 exactly), which is a check on
the pair counting rather than a separate result. For the cut matches my number uses all the games
played; fastchess's printed block lags by up to its `-ratinginterval`, and I have shown which count it
covers rather than hiding the difference.

## 5. Is a bundle stronger than its best single part? Does a loser stop losing?

Taking the other helpers' single-switch numbers from the job text as given (I did not re-measure them):

| bundle | parts (single-switch Elo, as given) | bundle Elo, 95% interval | stronger than its best part? |
|---|---|---:|---|
| M1 | LmrDeeperShallower +13.2, ThreatHistory +4.3, NullThreatVerify +4.9 (mine) | -5.56, -15.9 .. +4.8 | **no** — below both positives, and below zero |
| M2 | NullThreatVerify +4.9, NullSeeVeto 0.0 (mine) | -4.35, -16.9 .. +8.2 | no |
| M3 | M1's three + NonPawnCorrection -4.6, MateAlphaGuard ~0 | +9.10, -4.4 .. +22.6 | cannot say — interval spans zero |
| M4 | the eight "did not lose" | +9.53, -4.0 .. +23.1 | cannot say — interval spans zero |
| M5 | AspArmLate -26.0 (mine), AspCappedReopen -0.7 | -22.50, -36.2 .. -8.8 | no — still clearly bad |
| M6 | the eight (~+9.5) + EvalRule50Damp -36.3 (mine) | -28.71, -45.0 .. -12.5 | no — the loser brings it well down |

**The specific question — does a switch that lost alone stop losing in company?** No, on this evidence.
`AspArmLate` loses alone (-26.0) and loses with its partner `AspCappedReopen` (-22.5); the two intervals
overlap heavily, so the partner did not measurably rescue it. `EvalRule50Damp` loses alone (-36.3) and,
added to a bundle that is itself about +9, drags the bundle to -28.7; that is consistent with the two
losing effects simply adding rather than with any interaction.

**A warning about reading M1.** Its three parts sum to about +22 by the single-switch numbers, yet the
bundle is -5.6. The interval is ±10, so this is not a proven loss, but it is nowhere near the +22 the
additive reading predicts. Either those singles do not add (they overlap in what they change — two of
the three are null-move changes, and `NullThreatVerify` alone was only +4.9 ± 11.4, i.e. nothing), or
the other helpers' +13.2 for `LmrDeeperShallower` does not reproduce here. **The owner's rule, that
singles add up into a bundle, is not supported by M1.** I would not assume additivity for any of these.

## 6. One table with job 1 and job 2

Job 1 (all complete, 1,500 games each, from `REPORT_deepseek3_job1.md`):

| match | switches on candidate | seed | games | cand W-L-D | pair counts | fastchess Elo +/- err | own Elo, 95% interval |
|---|---|---:|---:|---|---|---:|---|
| job 1 M1 | NullThreatVerify | 7303 | 1500 | 443-422-635 | [35,163,337,176,39] | +4.86 +/- 11.44 | +4.86, -6.6 .. +16.3 |
| job 1 M2 | NullSeeVeto | 7304 | 1500 | 433-433-634 | [46,175,304,183,42] | -0.00 +/- 12.10 | 0.00, -12.1 .. +12.1 |
| job 1 M3 | AspArmLate | 7305 | 1500 | 371-483-646 | [51,222,296,150,31] | -25.99 +/- 11.94 | -26.0, -37.9 .. -14.0 |
| job 1 M3r | AspArmLate (repeat) | 9305 | 1500 | 379-456-665 | [63,177,309,176,25] | -17.85 +/- 12.02 | -17.9, -29.9 .. -5.8 |
| job 1 M4 | EvalRule50Damp | 7306 | 1500 | 345-501-654 | [63,229,285,147,26] | -36.26 +/- 12.14 | -36.3, -48.4 .. -24.1 |
| job 1 M5 | DeadMaterial | 7307 | 1500 | 445-442-613 | [0,1,745,4,0] | +0.69 +/- 1.01 | +0.7, -0.3 .. +1.7 (**5 of 750 pairs non-split**) |
| job 2 M1 | LmrDeeperShallower+ThreatHistory+NullThreatVerify | 7321 | 2000 | 559-591-850 | [56,257,404,229,54] | -5.56 +/- 10.36 | -5.56, -15.9 .. +4.8 |
| job 2 M2 | NullThreatVerify+NullSeeVeto | 7322 | 1438 (cut) | 417-435-586 | [41,186,292,150,50] | -3.23 +/- 12.72 | -4.35, -16.9 .. +8.2 |
| job 2 M3 | M1's three + NonPawnCorrection + MateAlphaGuard vs those two | 7323 | 1261 (cut) | 393-359-509 | [35,149,236,168,42] | +8.98 +/- 13.96 | +9.10, -4.4 .. +22.6 |
| job 2 M4 | all eight | 7324 | 1241 (cut) | 380-347-514 | [40,128,251,160,41] | +8.41 +/- 13.79 | +9.53, -4.0 .. +23.1 |
| job 2 M5 | AspArmLate+AspCappedReopen | 7325 | 1208 (cut) | 317-395-496 | [50,161,233,135,24] | -22.32 +/- 13.72 | -22.50, -36.2 .. -8.8 |
| job 2 M6 | all eight + EvalRule50Damp vs all eight | 7326 | 752 (cut) | 194-256-302 | [27,100,170,66,13] | -30.19 +/- 18.06 | -28.71, -45.0 .. -12.5 |

## 7. Which repository files I opened

`forge-combo29/src/uci.cpp` (to confirm `MateAlphaGuard` is only compiled in with the flag, and the
option dispatch), `forge-combo29/src/search.cpp` (the `MateAlphaGuard` uses), plus what job 1 lists. I
did not open any other helper's files.

## 8. Stamps

| step | start | end | wall |
|---|---|---|---|
| build (with flag) | 15:59:44Z | 15:59:50Z | 6 s |
| Step 0 | 15:59:52Z | 15:59:53Z | `logs/step0-stamps.txt` |
| bundle benches | 16:01:5xZ | 16:02:0xZ | `logs/step1-bundles.stamps.txt` |
| Control 2 | 15:59:54Z | 16:01:53Z | 119 s |
| M1 (2,000, complete) | 16:02:04Z | 16:20:20Z | 1096 s |
| M2 (cut at 1,438) | 16:20:28Z | 16:32:38Z | 730 s |
| M3 (cut at 1,261) | 16:32:50Z | 16:44:31Z | 701 s |
| M4 (cut at 1,241) | 16:44:34Z | 16:55:34Z | 660 s |
| M5 (cut at 1,208) | 16:55:37Z | 17:05:57Z | 620 s |
| M6 (cut at 752) | 17:05:59Z | 17:13:10Z | 431 s |
| Control 3 (option delivery) | 17:13:13Z | 17:13:16Z | 3 s |

Note on ordering: Control 2 ran *before* M1 (15:59:54Z to 16:01:53Z), and the bundle benches after it.
Per-match `stamps.txt` and `config.txt` are in each `logs/<match>/`.

Total: build start 15:59:44Z to the last match end 17:13:10Z = **73 min 26 s**, inside the 80-minute
budget and just past the 70-minute stop point (see 9).

## 9. What I did not do

- **M2–M6 are all INCOMPLETE.** The budget was 80 minutes with a stop and write-up at 70; the first
  2,000-game match took 18 minutes here, so six matches of 2,000 could never fit. I gave each match its
  own `timeout` so the later ones would be the ones cut, as instructed, and they were. No match failed;
  all six have usable data, but five are short of the asked game count. The last match ended at
  17:13:10Z, **73 min 26 s** after the build — inside the 80-minute cap but **past the 70-minute stop
  point** by about 3 minutes, because M6's limit was set before I knew how far past 70 it would land.
- **I did not re-measure the other helpers' single-switch numbers**, so the "best part" comparisons in
  section 5 rest on their numbers as Fable's file states them. Where my own job-1 numbers exist
  (`NullThreatVerify`, `NullSeeVeto`, `AspArmLate`, `EvalRule50Damp`) I used mine.
- **`EvasionOrdering`, `LmrLateParentRelief`, `LmrSignedCorrection`, `DrawJitter`, `QuietExtinction`
  are not in any bundle I ran** — they were not in the job's bundle definitions.
- **`QuietExtinction` (-403) was not tested at all here**; the job's bundles correctly left it out.
- No time control, no PC net; 4 cores, concurrency 4.

## 10. What I am not sure about

- **M3 is the bundle I most wanted and it is the least conclusive.** 1,261 games, +9.1, interval
  `-4.4..+22.6`. It is the nearest thing to the PC's settings and it needs the full 2,000 (or more).
  Its point estimate is the most encouraging number in this job, and I am explicitly not calling it a
  gain.
- **The M1 surprise (parts sum ~+22, bundle -5.6) has two explanations I cannot separate**: either the
  singles genuinely do not add, or `LmrDeeperShallower`'s +13.2 does not reproduce in this tree at
  20,000 nodes. Distinguishing them needs one match of `LmrDeeperShallower` alone in this tree, which
  was not in my job.
- **Cut matches bias nothing systematically**, but my own Elo for them covers all games played while
  fastchess's printed block covers fewer; I reported both rather than picking one.
- **Additivity is the owner's rule and M1 contradicts it.** One bundle is thin evidence either way; I
  would want M1 repeated before drawing a conclusion about additivity in general.

## 11. A better way

**Stop sizing jobs in match count when the machine rate is unknown.** Job 1 measured ~11 minutes per
1,500 games; job 2 asks for 11,000 games, which is well over three hours on this box, and the budget was
80 minutes. A job that instead says "as many of these bundles as fit in 70 minutes, in this priority
order, and report which were cut" gets complete data on the bundles Fable cares about most and never
produces six half-finished ones. M3 — the one that matters most — would then have been run with 2,000
games and the marginal ones dropped. How to check it: run the next job that way and compare how many
bundles reach full game count against this job's one-of-six.

**Two cheap additions to every bundle match, both of which this job would have benefited from.**
(1) Run the *base* bundle against itself for 200 games first: `DeadMaterial`-style pair splits show
immediately if the base is doing something odd, and it costs 2 minutes. (2) For a bundle, also run each
member alone at a *small* game count (400) with the same seed family, so the additivity question is
answerable within one job rather than by comparing across helpers' different trees and different days.
How to check (2): the singles' sum should predict the bundle within their combined interval; M1 shows
that prediction failing badly, which is exactly the measurement that tells us whether bundling is worth
the owner's PC time.

## 12. Questions for Fable

1. M3 (the PC-like bundle) needs a full 2,000 games; may job 3 give it a whole budget by itself?
2. Do you want `LmrDeeperShallower` alone re-measured in this tree? M1's -5.6 against its reported +13.2
   is the one inconsistency in this job and it is cheap to settle.
3. `AspArmLate` + `AspCappedReopen` = -22.5: is that enough to drop both, or do you want a third seed?
