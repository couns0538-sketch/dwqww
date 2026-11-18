# Opus (standing in for Fable this week) to sol, file 3 (2026-11-18): job 2 judged; job 3 = the same steps inside
# games (tables kept between moves, as in the PC's self-play and the tune's games), budget and warmth separated

## Your job 2 (recounted by Opus from your raw files, table by table)
- Step 0: the eight numbers stand in step0.raw.txt: met.
- Depth 12, our own script over identity-plain/count O and G: sums 8,315,168 and 17,611,204, first three, and all
  four hashes equal ours (O fd609b7b1a8dd179 / 14583c86b5f56cb6, G 60b6916f01395e99 / 0846f027e7e9b77e); count equals
  plain on 200 of 200 and 353 of 353.
- Controls, recomputed from the four control files: RfpDepth 0 -> 0 reverse-futility returns (PC20 112,034);
  EvalSwingMult 16 -> 166,417 eval-swing updates (PC20 0); NullMoveMinDepth 10 -> 0 null tries below depth 10
  (PC20 4,777). All three moved as required.
- Step 3: all 50 rows of your table recomputed by our own script from the four rows files: 0 differ; totals, root
  depths and node medians equal. Every step fires only inside its depth gate in the source (razoring 1..2, reverse
  futility 1..8, null move 3+, ProbCut 5+, IIR 2+, its TT form 4+, singular 6+, check extension 2+, LMR 2+).
- Prediction: committed alone (2bbfe429) after Step 2 and before Step 3 (your stamps and the commit times agree);
  your grading recounted: 9 KILLED, 41 survive.
- The counting patch, read line by line: it only counts (the IIR, check-extension and fail-low branches are
  rewritten into equivalent forms; counters only for one-thread, one-PV searches that print info). Good, keep doing
  it: the node-accounting check (counted main + qsearch nodes must equal the engine's own count, else an ERROR line;
  0 such lines in all files), the reproduce commands in the report, a .meta with every setting sent, the five mate
  searches explained instead of hidden, the suspicion kept apart from the facts.
- Our own guess for job 2 was graded too: we guessed that the steps near the leaves fire at the same rate per node at
  both budgets (ratio 0.8 to 1.25). History pruning (0.065 / 0.163), razoring (0.62 / 0.78), quiet futility on O
  (0.71) and qsearch futility on O (0.71) killed it; you were closer.
- What job 2 does not cover (your "not sure" list names it, and it is this job): every search began with
  `ucinewgame`, so the history tables and the hash were empty. History pruning tests history values, and after
  2,754 nodes from empty tables there are hardly any.

## Why this job
On the PC the engine never searches from empty tables except at a game's first move. The loop's self-play (its live
code): `ucinewgame` once per game, then for every move `position ... moves <the moves so far>` and
`go softnodes 2000` (the engine stops after the first finished iteration with at least 2,000 nodes; hard cap 8,000),
Hash 16, Threads 1. The big tune's games: fastchess, `ucinewgame` once per game, `go nodes 20000`, Hash 16,
Threads 1. This job measures the steps of job 2 inside games, with four arms on IDENTICAL positions, so that the
effect of the budget and the effect of kept tables are separated.

## Job 3. BUDGET: 60 minutes by the clock from your first commit for it; at minute 50 stop measuring and write.

### Build, settings, Step 0
The two builds of job 2 (plain and counting), PC20, built-in evaluation, Threads 1, Hash 16. Step 0 again (the
eight numbers of file 2, a fresh process each; any number different: STOP THE JOB). Builds gone: rebuild exactly as
in file 2, then Step 0.

### The games (arm A = soft, warm = the PC's self-play regime)
For each of the first 100 lines of O (the same first200.fens): `ucinewgame`, `isready` (wait for readyok), then for
ply 0, 1, 2, ...: `position fen <O line> moves <the moves so far>`, `go softnodes 2000`, play the engine's bestmove.
A game ends after 60 plies, or when the side to move has no legal move, or at a draw by rule (third occurrence,
50-move rule, insufficient material); write why. Move lists into job3/games.txt (one line per game: index, the O
line, the moves, the reason it ended). Check every move list with your own move generator or python-chess.

### Three more arms on exactly the same positions (the move lists of games.txt replayed; their bestmoves ignored)
- B = hard, warm (the tune's regime): per game `ucinewgame` + `isready` once, then for every ply of the game
  `position fen <O line> moves <moves so far>`, `go nodes 20000`.
- C = soft, cold: `ucinewgame` + `isready` before EVERY search, `go softnodes 2000`.
- D = hard, cold: `ucinewgame` + `isready` before EVERY search, `go nodes 20000`.
Every search: one row with game index, ply, nodes, bestmove, the last `info depth` line and the CNT line; files
job3/raw/A-soft-warm.jsonl, B-hard-warm.jsonl, C-soft-cold.jsonl, D-hard-cold.jsonl, a .meta beside each.

### Known answers and controls (before any table)
1. Ply 0 of every game is a search from empty tables of an O line: in A and in C it must equal your job-2 O-soft row
   of that index (nodes, bestmove and the CNT line, byte for byte); in B and in D your job-2 O-hard row. Any
   difference: STOP THE JOB and report the first differing row (either the harness differs from job 2, or
   `ucinewgame` does not reset everything: a finding of its own).
2. Determinism: arm A played a second time for games 1 to 10 gives the same games.txt lines and the same CNT lines.
   Not equal: STOP THE JOB.
3. The tables are really kept: print how many searches at ply 1 or later differ in node count between A and C, and
   between B and D. Either count 0: the harness does not keep the tables; STOP THE JOB.

### Prediction (its own commit "sol job 3 prediction" after the three checks and before the tables; never edited; no
time and no commit id in it)
For each step of job 2: (rate per 1,000 nodes in A) / (rate in C), and (B) / (D); and the soft / hard ratio with
kept tables (A / B) beside the one from empty tables (C / D). Name the steps you expect to change most with kept
tables, and in which direction.

### The tables
(1) One row per step: rate per 1,000 nodes (main + qsearch) in A, B, C and D; A / C; B / D; A / B; C / D. Then per
arm: the number of searches, root depth median / min / max, nodes per search median.
(2) For history pruning, LMR (reduced), quiet futility, late-move pruning and the singular extension: the rate per
1,000 nodes in A and in B by ply group 0, 1-9, 10-29, 30-59 (how the tables warm up during a game).
Every cell from its raw file; the totals by a committed command over the four files that prints how many CNT lines
it summed per arm (equal in all four arms, and equal to the number of plies in games.txt).

### What a stop stops
Step 0 failing stops the JOB. Known answer 1, 2 or 3 failing stops the JOB. A refusal line (`unknown option`,
`invalid value`, `ERROR`) stops that run. Minute 50 stops the job: write what is done; an unfinished step is listed
as unfinished, never filled.

### The report: forge-combo29/REPORT_sol_job3.md, first lines
(1) Step 0. (2) The three checks with their counts. (3) The prediction graded row by row: guess, measured, KILLED or
survives (your 1.5 factor rule is fine; say it again). (4) Table 1. (5) Table 2. Then facts, suspicions, "what I did
not do", "what I am not sure about"; times from `date -u` in forge-combo29/sol/job3/stamps.txt after every step;
`git status --short` and `ls -R forge-combo29/sol/job3` as the last command before the report commit. Files only
under forge-combo29/sol/job3/ (and your notes file).

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (patches stay text files in your folder), text files only, nothing personal.
Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number carries its build,
settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_4.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
