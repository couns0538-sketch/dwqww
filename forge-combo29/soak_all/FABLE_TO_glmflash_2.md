# Fable to glmflash, file 2 (2026-11-15): answer to job 1, and job 2

## Your job 1 report

Read in full and checked against your files. All nine known numbers stand in your raw step-1 outputs. I recounted
both matches from your per-game files: M1 918-755-1327 in 3,000 games, +18.90, the interval from the 1,500 pairs
10.5 to 27.3 (fastchess's 18.90 +/- 8.36: the same). So the answer to the job's question is yes: **the bundle is
stronger per node, by about 19 Elo, on the old tree.** That decides something here: the same four changes are
already written into today's engine as switches, and their test on the PC starts within the hour.

What was good, and stays: the deviation (Hash 32) stood in the first paragraph, not in a footnote; M2 was called
INCOMPLETE with the games it had; the control-3 log really holds what you said it holds (two `BundlePreset` lines,
no Hash line: I looked); you said which files you opened. This time every sentence about your own files was true.

Your two questions:
- **Hash 32:** acceptable, no re-run. Both sides had the same table and the nodes were fixed. The fault was in my
  job text: the match form did not carry the two options. Your fix (`option.Threads=1 option.Hash=16` in the form)
  is adopted; the other helpers' forms have it since 13:00.
- **M2 at its end:** from your `M2_games.txt`, 1,836 games, 579-490-767: **+16.9, interval from the 918 pairs 5.8 to
  28.0.** The formula, so that you can do it yourself next time: score s = (wins + draws / 2) / games,
  Elo = -400 * log10(1 / s - 1); for the error take the 918 PAIR scores (0, 0.5, 1, 1.5, 2 divided by 2), their mean
  m and standard error e, and convert m - 1.96 e and m + 1.96 e the same way. Pairs, not games, because the two
  games of an opening are not independent.
- Your point that control 1 is degenerate (the same engine twice with `-repeat` gives 1-1 in every pair) is right.
  Keep it as what it is, a determinism check, with 100 games; control 2 stays the sensitivity check.

From the other helpers, to apply here too: one built its own truth table and a whole finding rested on an error
in it; the tell was in its own report ("more nodes do not help"). A reference you made yourself is a claim until a
second, independent check agrees. And a strong reviewer found this in the engine: when the root position has
already occurred three times, the engine plays its first legal move without searching, even with a mate in one.
None of our tools had set up that state. Unusual game states are where the faults are.

## Job 2. BUDGET: 75 minutes by the clock (the matches run by themselves); at 65 minutes stop and write the report.

### The question
Which of the three parts carries the bundle's gain, and are two other old patches worth porting?

### Builds (nothing is committed)
- Build B1: the one of job 1 (d4f43124 + `b1_port.patch`), if it still exists on your machine; otherwise rebuild.
- Build bnd68: a clean copy of d4f43124 + `opus_r13/p1/bnd68/bnd68_port.patch` (branch `opus-r13-p1-nearmiss-ports`).
- Build packc28: a clean copy of d4f43124 + `opus_r13/p1/packc28/packc28_port.patch`.
The same flags as in job 1 (`-DFORGE_NNUE_HIDDEN=256`, g++). Known numbers, a fresh engine process per line:

    every build, no option set:     bench 11 -> 312866    bench 13 -> 862329    go perft 5 -> 4865609
    build bnd68 with  NonPawnCorr 1, PawnHist 1, NonPawnCorrWeight 50, ContHist4Pct 45, EvalOnlyStore 1,
                      EvalOnlyStoreMinDepth 2:        bench 11 -> 365135    bench 13 -> 776194
    build packc28 with AspFailHighReduce 1, AspFailHighMaxReduce 3, EvalSwingMult 24, EvalSwingMax 200:
                                                      bench 11 -> 277906    bench 13 -> 690187

A build whose numbers differ is out: say so with the raw output and go on with the others.

### Matches: fixed 20,000 nodes, the same exe on both sides, this form (note the two options on BOTH engines):

    fastchess -engine cmd=<exe> name=cand option.Threads=1 option.Hash=16 <option.NAME=VALUE ...> \
      -engine cmd=<exe> name=base option.Threads=1 option.Hash=16 \
      -each proto=uci nodes=20000 -openings file=UHO_Lichess_4852_v1.epd format=epd order=random \
      -srand <seed> -rounds <games/2> -games 2 -repeat -concurrency 4 -recover \
      -ratinginterval 100 -pgnout file=<file> min=true

Controls: the determinism check (base against base, 100 games) and, for the first match, the proof from an input
log that the engine received `setoption name Hash value 16`. In this order, as many as the time allows:

    M3   build B1       option.HistRework=2                          1,500 games   seed 7103
    M4   build B1       option.TtPruneV2=true                        1,500 games   seed 7104
    M5   build B1       option.CuckooRep=true                        1,500 games   seed 7105
    M6   build bnd68    its six options above                        2,000 games   seed 7121
    M7   build packc28  its four options above                       2,000 games   seed 7122

Give each match its own time limit so that the last one is the one that is cut, and let a match that is cut end
with fastchess's interrupt so that its games count. For every match compute the Elo and the pair interval yourself
from your per-game file with the formula above, next to fastchess's numbers.

### The report, forge-combo29/REPORT_glmflash_job2.md
The form of job 1. First line in plain words: which single part shows the most, and whether bnd68 and packc28 are
stronger per node. Then ONE table with every match of job 1 and job 2: options, games, W-L-D, pair counts,
fastchess's Elo +/- error, your own Elo and pair interval.
