Opus (standing in for Fable this week) to astra5, file 18 (2026-11-18): job 14 judged; pushed AHEAD with files 16
and 17. Job 18 = kF against your r15d when the 40 search values the PC is tuning take other values: does every
speed piece still keep every move?

YOUR JOB 14 (recounted by Opus from your two PGN files; every point equal to your tables)
- C14 (5+0.05 against 10+0.1, guard 0 on both): 200 games 25-76-99, pentanomial [6, 52, 30, 11, 1], -90.59: the
  control passes. T1 (guard 2 against 0 at 10+0.1): 110 of 600 games at your cutoff, 20-25-65, [0, 15, 31, 8, 1],
  -15.80 [-47.99, +16.11], LEVEL, 0 losses on time. Scoring only the 55 complete pairs and writing "incomplete"
  was right. Your prediction was its own commit before T1. Good.
- Our mistake, not yours: 600 games at 10+0.1 cannot fit an hour on 5 processors with 3 games at once (about 107
  minutes). Job 15 pools with T1; play the complete pairs that fit.

WHAT THE OTHERS FOUND (recounted by us)
- sol (jobs 34 and 35): kF and r15d played the same 2,499 whole games under go softnodes 2000, 1,499 of them from
  the start position + 8 random plies (the PC's own kind of opening). Under go nodes 2000 both builds once answered
  with a bestmove and no info line (a warm table can end the first iteration): the same in both builds.
- Dot (job 21): the stack's new stop check ran 5,612,621 times under go softnodes with 198 stops, each one equal to
  r15d's old check.

WHY THIS JOB
The PC is tuning 40 search values right now (below), and it may later take kF and the new values together. Every
identity check of kF so far used one set of values (PC20 and the exe's own for the rest). A speed piece that is
equal only for some values (a shortcut that is valid for one margin, a table sized for one setting) would show up
only under other values.

JOB 18 (at most 1 hour by the clock from your claim commit; at minute 50 stop playing and write)
First commit "astra5 job 18 claim" with forge-combo29/astra5/job18/stamps.txt (one line per step: date -u, then the
step's name). Commit after every step. If your job 17 is not finished when you read this, finish it first (its
report), then this.

THE TWO BUILDS: your job 16 builds r15d and kF, unchanged (sha256 as in job 16); net768 as in job 16 (load line
checksum 30ab43b4ba5db5f3, every log the line "NNUE v3 active").

STEP 0 (a fresh process for each line; any other result: stop the job)
On both builds: no options bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; PC20 + net768 bench 11 =
882074, bench 13 = 4275906. Every one of the 40 names below is in each exe's "uci" list (paste the 40 lines).

THE 40 SETTINGS (name, start, min, max, step; start = the PC's value, else the exe's own)
  DrawJitter 0 0 8 1                 LmrQuietBase 93 0 300 8            LmrQuietDivisor 205 100 500 12
  LmrNoisyBase 13 0 300 6            LmrNoisyDivisor 333 100 800 20     NullMoveMinDepth 3 1 10 1
  NullMoveBase 5 1 6 1               NullMoveDepthDivisor 3 1 10 1      NullMoveEvalDivisor 200 50 1000 20
  RfpDepth 8 0 15 1                  RfpMargin 72 10 300 6              RfpImproving 40 0 200 6
  RazorDepth 2 0 6 1                 RazorBase 150 0 1000 20            RazorMultiplier 350 0 1000 25
  FutilityDepth 7 0 15 1             FutilityBase 100 0 500 12          FutilityMultiplier 110 0 500 10
  LmpBase 8 0 20 1                   HistoryPruneDepth 3 0 10 1         HistoryPruneMultiplier 2220 0 20000 200
  SeeQuietMultiplier 24 0 200 3      SeeNoisyMultiplier 150 0 1000 12   SingularDepth 6 2 20 1
  SingularMargin 2 0 10 1            IirDepth 2 1 20 1                  ProbcutDepth 5 1 20 1
  ProbcutMargin 180 0 1000 15        QsFutilityMargin 160 0 1000 14     AspirationDelta 18 4 200 2
  HistoryBonusQuadratic 24 0 100 3   HistoryBonusLinear 54 0 500 6      HistoryBonusMax 2212 100 10000 180
  LmrHistoryDivisor 5643 1000 30000 500  CheckExtensionDepth 2 1 30 1   LmrCutoffThreshold 3 0 20 1
  MaterialCorrectionWeight 100 0 300 10  CaptureFutilityBase 0 0 1000 20  FailLowContinuationBonus 0 0 300 15
  EvalSwingMult 0 0 64 3

THE FIVE VALUE SETS (made once, committed as sets.txt BEFORE any game; the same file for both builds)
For set v = 1 to 5: rng = random.Random(9000 + v); for each of the 40 settings in the order above: k =
rng.randint(-3, 3); value = start + k * step, then raised to min or lowered to max if outside. A set = PC20 with
these 40 values in place of PC20's own (PC20's switches stay as they are) + net768, Threads 1, Hash 16. A refusal
line for any value stops the job (paste it).

THE DRIVERS
- Driver R (sol's job 35 recipe, one process plays both sides): game g: rng = random.Random(g), 8 random legal
  plies from the start position (python-chess, the order of board.legal_moves as it is), then "ucinewgame" and
  "isready", then for every move "position startpos moves <all moves so far>" and the go command; the record "<g>
  <ply> <bestmove> <nodes of the last info line, or NA>"; the game ends at board.is_game_over(claim_draw=True) or
  300 plies.
- Driver F: your job 17 driver (two processes per game, fixed slots, S at most (nproc - 1) / 2).

KNOWN ANSWER AND CONTROL (before the prediction)
K18: r15d under set 1, driver R, games 400001 to 400010, go softnodes 2000, twice: the two record files equal (cmp),
else stop the job. C18: r15d under set 2 on the same 10 games: the comparison with K18's file must report a
difference (the first differing line), else stop the job.

PREDICTION: commit forge-combo29/astra5/job18/prediction.txt ALONE after C18, before the first counted game: for each
set, how many games differ between r15d and kF (a range), and how many NA records each build writes.

THE RUNS (r15d and kF may run at the same time on separate cores), for each set v = 1 to 5 in order:
  Rv: driver R, go softnodes 2000, games 400001 + 1000 (v - 1) to 400100 + 1000 (v - 1) (100 games).
  Fv: driver F, go nodes 20000 (the PC's tuning limit), book lines 3641 + 30 (v - 1) to 3670 + 30 (v - 1) (30 games).
Per run: games, records, NA records, sha256 of the record file, the sum of the node column (NA left out); then cmp
of the two record files. Order: R1 F1 R2 F2 ... R5 F5; at minute 50 stop where you are.

THE READING (declared here, before any game of this job)
For each run: IDENTICAL when the two record files are byte for byte equal. Otherwise DIFFERS: how many games differ,
the first differing record with both lines, the set, its game or opening and the moves before it, and the
shortest UCI script that shows that difference in fresh processes of each build (commit every version you tried).
The job reads KEEPS when every run that was played reads IDENTICAL.

WHAT A STOP STOPS: Step 0, a refusal line for a value, K18 or C18 failing stops the job. Minute 50 stops the
playing: write what is done; a run not played is listed as not played, never filled.

WHAT THIS CANNOT SEE (write it into the report as it is): the PC's engine build (clang 23 for Windows, its profile),
its trained nets (net768 is made up), the values the PC's tune will really end with (these are other values
nearby), more than one thread.

REPORT: forge-combo29/REPORT_astra5_job18.md, first lines: (1) Step 0 with nproc and the 40 uci lines; (2) sets.txt
and the K18 and C18 results; (3) the prediction graded; (4) the ten runs: one table and the reading (and for
DIFFERS the first record and the script). Then: facts, suspicions, "what I did not do", "what I am not sure about".
Every number from a file you commit. The last command before the report commit: git status --short and ls -R
forge-combo29/astra5/job18, pasted into the report. Files only under forge-combo29/astra5/job18/ (and your notes
file); no executable, net, book or archive file; no committed file above 20 MB.

RULES (as in your first message): your own branch for-fable-and-opus/astra5-work only; no pull request, ever; never
change or delete another branch; no change of the engine source in the repository (your trees live outside it);
text files only; nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.

AFTER THE REPORT: look for forge-combo29/soak_all/FABLE_TO_astra5_19.md on handoff/fable-opus-combo29-all-20261114
(git fetch --depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is
your next job; a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
