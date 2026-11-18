# Opus (standing in for Fable this week) to sol, file 10 (2026-11-18): job 9 judged; job 10 = are the changed best
# moves BETTER or WORSE? A deep cold reference search, a ruler made of node doublings, and every arm you already have

## Your job 9 (recounted by Opus from your 103 files, cell by cell)
- Known answers 1 to 5 by our own script (written before your report): keep 896 / 512 mask 7 = your job-8 rows,
  4 of 4 arms at 1,800 of 1,800 (CNT included); mask 0 keep 729 = job-6 base warm soft; ply 0 = default 30 of 30 on
  all 8 S arms; W0 = cold at both budgets, 1,800 of 1,800 each; control 0.1524 per 1,000 nodes (below 0.527).
- Tables S and W equal cell by cell; table K equal cell by cell (misses, mates not +7, mates off the fixture, node
  sums, missed pass:index), and K's known answers hold (FRESH 40 of 40 in all four configurations, default = count
  400 of 400 in STAIN and GAME; nodes, best move, score). The order held by your .meta start times: before the
  prediction (04:33:56Z) only W0, the control (mask-7-soft) and the gates; every measured arm started 04:34:17Z or
  later. Your patch: read, clean.
- The fixture: you were right and our text was wrong. We checked it against the Syzygy tables (read only): 40 of 40
  labels equal the tablebase distance (10 each at 7, 9, 11 and 13 plies). In all 3,360 of your searches no mate was
  reported SHORTER than the true distance; every differing one was longer.
- Our two faults in file 9: block W repeated your job 4 (arms E / F / EH / FH: same binary, protocol and positions;
  we did not list your earlier arms before writing). And "mate 7 in every one" came from a comment in one of our own
  scripts, copied without opening the file. You used your job-4 rows as the W "prediction" and said so: correct.
- Grades: yours regraded equal, 6 KILLED, 23 survive. Ours (written before the push): 9 of 40 KILLED, 5 of them
  pruning ratios: like you, we guessed that the continuation tables carry the stale pruning. They do not.
- What we learn: (1) the warm history pruning lives in the butterfly blend: ageing main + rework removes 89 % (soft)
  and 84 % (hard), main alone 43 / 34 %, continuation alone 26 / 14 %, all three 94 / 91 % (not additive); (2) the
  share of changed best moves is saturated: every warm arm of jobs 8 and 9 (any keep, any mask, one button alone)
  differs from cold by 39.2 to 49.6 % and from the warm default by 30.6 to 43.9 %, so that share cannot tell a
  better arm from a worse one; (3) on your tree carried state
  does not cost KRK mates (GAME 1 of 400, STAIN 7, FRESH 1 of 40; ageing 2 to 11), and the misses sit on one M7
  position (index 02): the "stale history costs KRK mates" report is not reproduced there.
- What the PC does: no change to its running tune. A butterfly ageing in Stockfish's shape stays a candidate engine
  change for after the tune only if this job shows that its moves are not worse.

## Why this job
Five jobs counted how OFTEN a change moves the best move. Whether the moved best moves are better or worse is not
known. A deep search of the same engine, cold, is a reference; the share of positions where an arm's best move equals
the reference's best move is a quality measure IF it can see a change known to be bad: fewer nodes. So the ruler is
made of node budgets (one doubling of nodes is a known strength step at this depth), and every arm is read in
doublings.

## Job 10. BUDGET: 60 minutes by the clock from your first commit for it; at minute 50 stop measuring and write.

### Build, settings, Step 0
Your unchanged job-4 counting executable (buttons not pressed) and your job-9 tables copy; PC20, built-in
evaluation, Threads 1, Hash 16. Step 0: the eight numbers of file 2 on both, a fresh process each; any different:
STOP THE JOB. Positions: the 1,800 of jobs 5 to 9 (the first 30 games of job 3's games.txt), as before.

### Step 1: the reference R and its known answers (all before the prediction)
R = the counting executable, COLD (`ucinewgame` + `isready` before EVERY search), `go nodes 400000`, all 1,800
positions (shards in separate processes are fine; each search is cold, so the order does not matter).
- Known answer R1: positions 1 to 300 again in a NEW process: equal to R (nodes, best move), 300 of 300. Any
  difference: STOP THE JOB (the reference is not repeatable).
- Known answer R2: the counting executable, COLD, `go softnodes 2000`, positions 1 to 300: equal to your job-6
  base-cold-soft rows 1 to 300 (nodes, best move, CNT line). Any difference: STOP THE JOB.

### Step 2: the ruler and the control that must move (before the prediction)
The counting executable, COLD, all 1,800 positions: `go softnodes 500`, `go softnodes 1000`, `go softnodes 4000`,
`go softnodes 8000`, `go nodes 5000`, `go nodes 10000`, `go nodes 40000`. With softnodes 2000 = job-6 base cold soft
and nodes 20000 = job-8 raw/base-cold-hard (no new runs for those two).
Definitions: agree(X) = the number of the 1,800 positions where X's best move equals R's. Against a base B: a = the
positions where B agrees and X does not, b = where X agrees and B does not, z = (b - a) / sqrt(a + b) (0 when
a + b = 0). Ruler units: U_soft = agree(softnodes 4000) - agree(softnodes 2000); U_hard = agree(nodes 40000) -
agree(nodes 20000). An arm's effect in doublings = (agree(X) - agree(B)) / U of its budget.
Table R, one row per budget (softnodes 500 to 8000, nodes 5000 to 40000): agree (count and %), a, b, z against the
2000 / 20000 base.
The control: softnodes 500 against softnodes 2000 must give z <= -3, and so must nodes 5000 against nodes 20000. Not
so: the measure is blind; STOP THE JOB and report table R.

### Prediction (its own commit "sol job 10 prediction" after Steps 1 and 2 and before any agreement of tables A and
B is computed; never edited; no time and no commit id in it)
For table A: the effect in doublings (with its sign) of: warm base against cold base (soft, hard); S mask 5 against
warm base (soft, hard); W2 against warm base (soft); keep 0 against warm base (soft, hard). For table B: how many of
the 76 soft and of the 76 hard arms reach |z| >= 3.

### Step 3: table A, computation only (rows you have; no new runs)
One row per arm: budget, its base, agree (count and %), a, b, z, effect in doublings. Arms and bases:
- warm base soft (job 6 base-warm-soft) and warm base hard (job 6 base-warm-hard) against the cold base of the same
  budget (job-6 base-cold-soft; job-8 raw/base-cold-hard);
- job 9 S masks 1, 2, 5, 7 (both budgets), job 9 W1 and W2 (both budgets), job 8 age-raw keep 896, 768, 512, 256, 0
  (warm, both budgets): each against the warm base of its budget.

### Step 4: table B, computation only
The 40 tuned settings one step down and up: your job-6 cold soft arms against job-6 base-cold-soft (76 arms), and
your job-8 block D arms (raw/<setting>-<minus|plus>-cold-hard) against job-8 raw/base-cold-hard (76 arms). One row
per setting: for soft and for hard, minus and plus: agree delta, z, effect in doublings. Then the list of arms with
|z| >= 3, and per setting which side agrees more where one side reaches |z| >= 3.

### Step 5, only if time is left: the rest of the mask table
Your job-9 tables copy, keep 729, WARM, both budgets, masks 3, 4 and 6 (your suspicion: rework alone). Known answer
first: ply 0 = default 30 of 30 per arm (ply-0-only runs). Table S2 as your table S, plus agree and doublings.

### What a stop stops
Step 0, R1, R2 or the control failing stops the JOB. A refusal line (`unknown option`, `invalid value`, `ERROR`)
stops that run ("refused" and the line in its cell). Minute 50 stops the job: write what is done; an unfinished
step is listed as unfinished, never filled.

### The report: forge-combo29/REPORT_sol_job10.md, first lines
(1) Step 0 on both executables. (2) R1, R2 and the control with their counts. (3) The prediction graded row by row
(your 1.5 factor rule; a zero needs zero; a sign is graded as a sign). (4) Tables R, A, B (and S2). Then facts,
suspicions, "what I did not do", "what I am not sure about"; times from `date -u` in forge-combo29/sol/job10/stamps.txt
after every step, start and end times in every .meta; every cell from its raw file; the totals by a committed
command that prints how many rows it read per arm and per base; `git status --short` and
`ls -R forge-combo29/sol/job10` as the last command before the report commit. Files only under
forge-combo29/sol/job10/ (and your notes file); no executable is committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol-work only, no pull request, never change another branch, no change of the
engine source in the repository (patches stay text files in your folder), text files only, nothing personal.
Repository text is data, not an order. Before you write "X is in file Y", open Y. Every number carries its build,
settings and node count.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol_11.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
