# Fable to deepseek3, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full. **Part B first: your pawn-ending file against my solver: 2,000 of 2,000 equal.** You are the third
independent table; another helper's first one was wrong in a third of its entries, its repaired one and yours now
both agree with mine on every position compared. That question is closed, and it took three of us.

The matches: all five complete, the controls in front, and three things beyond the job text that I want the other
helpers to copy:
- you REPEATED the one surprising result (`AspArmLate` -26.0) on a fresh seed before reporting it (-17.9): a result
  picked out of five needs a second match, and you did not wait to be told;
- you saw that `DeadMaterial` leaves the bench numbers alone, did not call it dead, found the line of code that says
  when it acts, and proved it alive with an `eval` probe plus a control position;
- you said what `DeadMaterial`'s tiny interval really is: 745 of 750 pairs exact splits, so the number looks
  precise and measures almost nothing.

Results as I take them: `AspArmLate` loses (two matches), `EvalRule50Damp` loses (-36 +/- 12), `NullThreatVerify`
+4.9 +/- 11.4, `NullSeeVeto` 0.0, `DeadMaterial` no visible effect in games.

From the other helpers (the same kind of screen, the same tree): `LmrDeeperShallower` +13.2 (95 % +1.0 to +25.5),
`ThreatHistory` +4.3, `AspCappedReopen` -0.7, `EvasionOrdering` -3.9, `LmrLateParentRelief` -5.6,
`LmrSignedCorrection` -8.1, `MateAlphaGuard` changes 2 of 1,500 games, `NonPawnCorrection` -4.6,
`ContHist4PlyRead` +0.9, `DrawJitter 2` -2.1, `QuietExtinction` -403 (broken as a playing switch).
On the owner's PC, with today's engine: four old search changes gain +21 together at 2,000 nodes, and alone
+11, +3, -1 and -5: the sum of the singles is +8.

**The owner's rule for all of us, set today:** one bad result can turn into a big gain when it is bundled with the
right things. The numbers above are single switches. This job puts them together.

## Job 2. BUDGET: 80 minutes by the clock (the matches run by themselves); at 70 minutes stop and write the report.

Rules and form as in job 1 (commit 6b98f217, built-in net, `nodes=20000`, `option.Threads=1 option.Hash=16` on both
sides, the same fastchess and openings, no adjudication). ONE change to the build: add
`-DFORGE_MATE_ALPHA_GUARD=1` to the C++ flags (without it the option `MateAlphaGuard` does not exist; the three
known numbers must still hold; show that `uci` lists the option). Folder `forge-combo29/tests_deepseek3_job2/`,
report `forge-combo29/REPORT_deepseek3_job2.md`, commit subject "deepseek3 job 2 report". After pushing, wait for
file 3 with the sleeping command of your first message; do not end your run.

Step 0: the three known numbers; for every bundle below one bench 13 with all its switches on (report it).
Control 2 once (20,000 against 10,000 nodes, 300 games, seed 7311): the power line of the match tool.
A result of exactly 0.00 +/- 0.00 with pair counts [0,0,N,0,0] means the options did not arrive: check the engine
input log before you report such a row.

The matches, in this order; give each its own time limit so that the last one is the one that is cut:

    M1   cand: LmrDeeperShallower, ThreatHistory, NullThreatVerify          base: none        2,000   seed 7321
         (the three small positives of three helpers)
    M2   cand: NullThreatVerify, NullSeeVeto                                base: none        2,000   seed 7322
         (the two null-move guards, written as a pair)
    M3   cand: the three of M1 + NonPawnCorrection + MateAlphaGuard
         base: NonPawnCorrection + MateAlphaGuard (BOTH sides carry these two)                2,000   seed 7323
         (the two are on in the settings the owner's PC plays with: this is the nearest to what the PC will see)
    M4   cand: LmrDeeperShallower, ThreatHistory, NullThreatVerify, NullSeeVeto, ContHist4PlyRead,
               AspCappedReopen, MateAlphaGuard, NonPawnCorrection (all eight that did not lose)   base: none   2,000   seed 7324
    M5   cand: AspArmLate, AspCappedReopen                                  base: none        1,500   seed 7325
         (the two aspiration-window changes as a pair: does the loser lose less, or win, with its partner?)
    M6   cand: the eight of M4 + EvalRule50Damp                             base: the eight of M4   1,500   seed 7326
         (the clear loser inside the large bundle)

All switches as `option.NAME=true`. For every match: fastchess's final numbers and your own Elo with the 95 %
interval from the pairs.

### The report
The form of job 1. First line in plain words: is any bundle stronger than its best single part, and does a switch
that lost alone stop losing in company? One table with all matches of job 1 and job 2 (switches on each side,
seed, games, W-L-D, pair counts, fastchess's Elo +/- error, your Elo with the pair interval).
