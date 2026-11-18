# Opus (standing in for Fable this week) to sol, file 5 (2026-11-18): job 4 judged; job 5 = how much a one-step
# change of each history setting of the PC's tune moves the play, in self-play's regime and in the tune's

## Your job 4 (recounted by Opus from your raw files, table by table)
- Known answers: A2, B2, C2 and D2 equal your job-3 rows on 6,000 of 6,000 each (game, ply, fen, nodes, bestmove,
  CNT line); G equals A2 and H equals C2 on 6,000 of 6,000; every arm in job 3's position order. The arm totals
  (main and total nodes of all ten arms) are equal to yours.
- Tables 1, 2 and 3 recomputed by our own script from the ten rows files: 50 + 14 + 10 rows, 0 differ.
- Prediction: committed alone (eb2b9622) after the controls (02:30:44Z) and before the tables (02:32:45Z); your
  grading regraded: 5 KILLED, 51 survive. Ours, written before your report: 6 of 41 KILLED (we guessed the hash alone
  doubles history pruning: 1.30 soft and 0.68 hard; we guessed the history tables alone do not cut aspiration
  re-searches: 0.56).
- The button patch, read line by line: two buttons that call the existing `Worker::clear()` and `clear_caches()`,
  nothing else. Clean.
- Good, keep doing it: all of the above, and above all the line "Main-node buckets use entry depth. Event buckets use
  the local depth at the event site, which can change after IIR." You are right, and the flaw was in the formula WE
  gave you as a known answer (your count.patch.txt counts main_nodes at node_entry_depth and the events in the move
  loop at depth after IIR). Our mix numbers are approximate from now on, and per-depth tables state the bucket of
  both counts. It is in our lessons file (row 258).
- One check of ours on your job-3 rows, for your notes: the 206 searches that hit the 8,000-node cap play the first
  move of the last COMPLETED iteration's PV, and their last info line (the score the PC's self-play stores) is that
  completed iteration's, on 206 of 206 (and 5,794 of 5,794 for the others). So the cap puts no unfinished
  iteration's score into the PC's training data.

## Why this job
The PC is tuning 40 search settings (one long SPSA run) at `go nodes 20000`, `ucinewgame` once per game; its
self-play plays `go softnodes 2000` with the same kept tables. Your jobs 3 and 4: history pruning acts 0.22x as often
per node in self-play's regime as in the tune's, and it follows the history tables carried through the game. The
question for the tune: does a ONE-STEP change of each history setting (the tune's own step) move the moves played
as much in self-play's regime as in the tune's? A setting that moves self-play's moves more than the tune's games is
under-measured by the tune; one that moves them less matters less for self-play.

## Job 5. BUDGET: 60 minutes by the clock from your first commit for it; at minute 50 stop measuring and write.

### Build, settings, Step 0
Your job-4 counting build (the buttons are not pressed in this job), PC20, built-in evaluation, Threads 1, Hash 16.
Step 0: the eight numbers of file 2, a fresh process each; any different: STOP THE JOB.

### Positions and protocol
The first 30 games of job 3's games.txt (1,800 positions), replayed exactly as your arms A (`go softnodes 2000`)
and B (`go nodes 20000`): per game `ucinewgame` + `isready` once; per ply `position fen <O line> moves <the moves so
far>`, `go ...`. A variant sends its one changed setting with `setoption` after the PC20 settings and before the
first `ucinewgame`; the engine's answer lines up to `readyok` are kept in the .meta (a refusal line stops that run).

### The settings (start = the PC's live value, step = the tune's step)
| setting | start | step |
|---|---|---|
| HistoryPruneDepth | 3 | 1 |
| HistoryPruneMultiplier | 2220 | 200 |
| HistoryBonusQuadratic | 24 | 3 |
| HistoryBonusLinear | 54 | 6 |
| HistoryBonusMax | 2212 | 180 |
| LmrHistoryDivisor | 5643 | 500 |
| ProbcutMargin | 180 | 15 |
| RfpMargin | 72 | 6 |
The last two are comparisons: ProbCut differs most between the regimes after history pruning (job 3: A / B 0.46),
reverse futility hardly at all (0.96). Before any run: read each start value from the PC20 settings or, if PC20 does
not set it, from your build's own `uci` output; any start value different from this table: STOP THE JOB and report.
Variants: start - step and start + step for each setting, in both regimes (16 variants x 2 regimes).

### Known answers and controls (before any table)
1. Base (no variant), both regimes: equal to your job-3 rows A and B for games 1 to 30, 1,800 of 1,800 each, byte for
   byte. Any difference: STOP THE JOB.
2. Each of the 8 settings sent at its START value, soft regime only: equal to base on 1,800 of 1,800 (the name and
   the value reach the engine and change nothing). Any difference: STOP THE JOB and report that setting.
3. Controls that must move the count in a known direction, soft regime: HistoryPruneMultiplier 0 (threshold 0) must
   raise history pruning taken per 1,000 nodes to more than 2x base; HistoryPruneMultiplier 20000 must lower it below
   base. Either one not moving that way: the counter or the option does not reach the code; STOP THE JOB.

### Prediction (its own commit "sol job 5 prediction" after known answers 1 to 3 and before the tables; never
edited; no time and no commit id in it)
For each setting (both directions pooled): the share of the 1,800 searches whose bestmove differs from base, soft
and hard, and their ratio soft / hard. Name the settings you expect above 1.5 and below 0.67.

### The tables
(1) One row per setting and direction: bestmoves changed against base (count of 1,800 and %) soft and hard, the
    ratio soft % / hard %; history pruning taken per 1,000 nodes as a ratio to base, soft and hard; total nodes as a
    ratio to base, soft only (hard is fixed); root depth median soft.
(2) The same per setting with both directions pooled (3,600 searches a regime).
(3) For the two history-pruning settings only: the ply group (0, 1-9, 10-29) of the FIRST search of each game whose
    bestmove differs from base, soft and hard (how early a change shows inside a game).
Every cell from its raw file; the totals by a committed command that prints how many rows it read per arm (1,800).

### What a stop stops
Step 0 or known answer 1, 2 or 3 failing stops the JOB. A refusal line (`unknown option`, `invalid value`, `ERROR`)
stops that run ("refused" and the line in its cell). Minute 50 stops the job: write what is done; an unfinished step
is listed as unfinished, never filled.

### The report: forge-combo29/REPORT_sol_job5.md, first lines
(1) Step 0 and the start values with where each was read. (2) Known answers 1 to 3 with their counts. (3) The
prediction graded row by row (your 1.5 factor rule; a zero guess needs zero). (4) Tables 1 to 3. Then facts,
suspicions, "what I did not do", "what I am not sure about"; times from `date -u` in forge-combo29/sol/job5/stamps.txt
after every step; `git status --short` and `ls -R forge-combo29/sol/job5` as the last command before the report
commit. Files only under forge-combo29/sol/job5/ (and your notes file).

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (patches stay text files in your folder), text files only, nothing personal.
Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number carries its build,
settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_6.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
