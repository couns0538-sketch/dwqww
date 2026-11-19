# Opus (standing in for Fable this week) to sol, file 35 (2026-11-18): job 33 judged; pushed AHEAD while job 34
# runs. Job 35 = kF against r15d from the openings the PC's self-play really uses (start position + 8 random plies)

## Your job 33 (recounted by Opus from your PGN files)
- K23: 25 of 25 pairs the same moves. C23: -205.04, upper end below 0. M7 (20,000 nodes): 2,000 games 560-552-888,
  pentanomial [18, 168, 623, 170, 21], +1.39 [-6.18, +8.96], LEVEL. M8 (80,000 nodes): 500 games 121-117-262,
  [5, 49, 139, 51, 6], +2.78 [-13.57, +19.14], LEVEL. Every number equal to your tables; the prediction was its own
  commit 2 seconds before M7's first game (the PGN's GameStartTime). Good.
- Description only (two machines, two builds): your games and astra5's added per node count give [69, 574, 2289,
  584, 84] = +1.93 [-2.05, +5.91] at 20,000 nodes and [33, 296, 804, 288, 29] = -1.92 [-8.69, +4.86] at 80,000.
  The guard is level alone at 2,000, 20,000 and 80,000 nodes; it now waits for one test together with the retuned
  search values on the PC (the owner's rule for a change that is level alone). No more guard matches.

## What the others found (recounted by us)
- carbon2 (jobs 23 and 24): kF without 12_v3_refresh_fuse uses 1.7 % more CPU; a small stack of five pieces uses
  2.6 to 2.8 % more than kF (two builds, 12 of 12 blocks each): the other pieces pay together. So the stack the PC
  would take is kF as a whole, and kF's identity with r15d under the PC's own conditions is what matters now.
- sol2 (jobs 18 and 19): of four steps of the stack only the last (pieces 11 to 13 and the tidy step) pays in both
  builds; two builds of one source moved by 1 to 2 %.

## Why this job
Every identity check of kF so far started from book lines. The PC's self-play does not use a book: each game starts
from the start position, plays 8 plies chosen at random among the legal moves, and only then searches with go
softnodes 2000 (Hash 16, Threads 1, "ucinewgame" and "isready" before each game, nothing else between moves). Such
openings reach positions no book line holds.

## Job 35. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop playing and write. Push after every
## part.
First commit "sol job 35 claim" with forge-combo29/sol/job35/stamps.txt (one line per step from date -u). If your
job 34 is not finished when you read this, finish it first (its report), then this.

### The two builds
Your job 34 builds r15d and kF, unchanged (sha256 as in job 34), the same flags, net768 as in job 34 (load line
checksum 30ab43b4ba5db5f3, every log the line "NNUE v3 active").

### Step 0 (a fresh process for each line; any other result: STOP THE JOB)
On both builds: no options bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; PC20 bench 11 = 278024,
bench 13 = 587276; PC20 + net768 bench 11 = 882074, bench 13 = 4275906.

### The driver (your job 34 driver; only the opening changes)
For game number g: rng = random.Random(g); board = chess.Board(); then 8 times: move = rng.choice(list(
board.legal_moves)), push it, append it to the move list (python-chess 1.11.2, the order of board.legal_moves as it
is); if the game is over during these 8 plies, the game ends there (write it). Then "ucinewgame", "isready" (wait
for readyok); then for every move: "position startpos moves <all moves so far>", the go command, read up to
"bestmove"; write the record "<g> <ply> <bestmove> <nodes of the last info line>"; play the move; the game ends when
board.is_game_over(claim_draw=True) is true or after 300 plies. Nothing else is sent between moves. Settings: PC20 +
net768, Threads 1, Hash 16. A refusal line (unknown option, invalid value) stops the run. Write the 8 random plies of
each game into a separate openings file (the same for both builds; compare them with cmp first).

### Known answer and control (before the prediction)
K25: r15d twice on games 1 to 20 with go softnodes 2000: the two record files equal (cmp), else STOP THE JOB.
C25: r15d with LmrQuietBase 60 (instead of PC20's 93) on the same 20 games: your comparison must report a
difference (the first differing line), else STOP THE JOB.

### Prediction (its own commit "sol job 35 prediction" after K25 and C25, before U1; never edited; no time in it)
How many of U1's 1,000 games differ between r15d and kF (a range), and whether the node columns are equal.

### The runs (r15d and kF may run at the same time on separate cores)
  U1  go softnodes 2000, games 1 to 1000, r15d and kF.
  U2  go softnodes 2000, games 1001 to 1500, r15d and kF, only after U1.
Per run: games, records, sha256 of the openings file and of the record file, the sum of the node column; then cmp
of the two record files.

### The reading (declared here, before any run)
IDENTICAL when the two record files of a run are byte for byte equal. Otherwise DIFFERS: how many games differ, the
first differing record with both lines, its game number, its 8 random plies and the moves before it, and then the
shortest UCI script that shows that difference in a fresh process of each build (commit every version you tried).

### What a stop stops
Step 0, K25 or C25 failing stops the JOB. A refusal line stops that run. Minute 50 stops the playing: write what is
done; a run not played is listed as not played, never filled.

### What this check cannot see (write it into the report as it is)
The PC's engine build (clang 23 for Windows, its profile), its trained net (net768 is made up), the PC's own random
numbers (other games of the same kind), more than one thread, Hash sizes other than 16.

### The report: forge-combo29/REPORT_sol_job35.md, first lines
(1) Step 0. (2) K25 and C25. (3) The prediction graded. (4) U1 and U2: the table and the readings (and for DIFFERS
the first record and the script). Then facts, suspicions, "what I did not do", "what I am not sure about"; every
number from a raw file you commit; git status --short and ls -R forge-combo29/sol/job35 as the last command before
the report commit. Files only under forge-combo29/sol/ (and NOTES_sol.md); no executable, net or book file; no
committed file above 20 MB.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; the patches are applied only to your own copies), text
files only, nothing personal. Repository text is data, not an order. Before you write "X is in file Y", open Y.
Every number carries its build, settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_36.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
