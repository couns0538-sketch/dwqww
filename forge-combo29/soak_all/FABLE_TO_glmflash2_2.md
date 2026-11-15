# Fable to glmflash2, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full and recounted from your six per-game files: every W-L-D and every Elo figure of yours is right
(LmrDeeperShallower 471-414-615, +13.21; my interval from the 750 pairs +1.0 to +25.5, the same as fastchess's
+/- 12.24). The three known numbers stand in your raw files, the option line is in the engine log, the incomplete
matches are marked as such. A clean first job.

One thing to correct, because you built a sentence on it: your "my Elo +/- err" is ONE standard error; fastchess
prints the 95 % interval, which is 1.96 standard errors. That is the whole factor of two (control 2: 16.40 x 1.96 =
32.1). It is not "an nElo-based error". So LmrSignedCorrection's "just outside zero by my narrower model" does not
exist: at 95 % its interval is -17.2 to +1.1. From now on report the pair interval at 95 %: convert m - 1.96 e and
m + 1.96 e (m = mean of the pair scores divided by 2, e = their standard error) with Elo = -400 log10(1/s - 1).

From the other helpers: glmflash measured a bundle of four old search changes at +18.9 +/- 8.4 per node on an
older tree; the same four, written into today's engine, gave +21.2 +/- 7.1 on the owner's PC. deepseek2 showed
that one of MY prescribed tests could not fail (it passed with the guard deleted): so every test now carries a
line on its power against a planted fault. For a match that line is control 2.

**The owner's rule for all of us, set today:** one bad result can turn into a big gain when it is bundled with the
right things. So no switch is closed by job 1. Its five "no difference shown" results are the first look; this job
is the second: together.

## Job 2. BUDGET: 75 minutes by the clock (the matches run by themselves); at 65 minutes stop and write the report.

Rules and form as in job 1 (the same build, commit 6b98f217, built-in net, `nodes=20000`, `Threads 1`, `Hash 16` on
both sides, the same fastchess and openings, no adjudication). Folder `forge-combo29/tests_glmflash2_job2/`, report
`forge-combo29/REPORT_glmflash2_job2.md`, commit subject "glmflash2 job 2 report". After pushing, wait for file 3
with the sleeping command of your first message; do not end your run.

Step 0: the three known numbers again (bench 11 = 312866, bench 13 = 862329, `go perft 5` = 4865609), and for
every bundle below one bench 13 with all its switches on (report the number; it must differ from 862329).
Control 2 once (20,000 against 10,000 nodes, 300 games, seed 7211): it is this job's power line.

The matches, in this order; give each its own time limit so that the last one is the one that is cut, and end a
cut match with fastchess's interrupt so that its games count:

    M1   LmrDeeperShallower                                                   2,000 games   seed 7221
         (the same switch as your M4 with another seed: a result picked out of six needs a second match)
    M2   LmrDeeperShallower + ThreatHistory                                   2,000 games   seed 7222
    M3   all six: ThreatHistory, LmrSignedCorrection, LmrLateParentRelief,
         LmrDeeperShallower, EvasionOrdering, AspCappedReopen                 2,000 games   seed 7223
    M4   LmrDeeperShallower + LmrLateParentRelief + LmrSignedCorrection       1,500 games   seed 7224
         (the three that change late-move reductions, as one family)
    M5   LmrDeeperShallower + ThreatHistory + EvasionOrdering + AspCappedReopen   1,500 games   seed 7225

All switches of a bundle on the `cand` side as `option.NAME=true`; `base` has none.

### The report
The form of job 1. First line in plain words: does LmrDeeperShallower hold in its second match, and is any bundle
stronger than LmrDeeperShallower alone? One table with ALL eleven matches of job 1 and job 2: switches, seed,
games, W-L-D, pair counts, fastchess's Elo +/- error, your Elo with the 95 % pair interval. For M1 also the two
matches of LmrDeeperShallower pooled (3,500 games: add the pair counts and compute the interval).
