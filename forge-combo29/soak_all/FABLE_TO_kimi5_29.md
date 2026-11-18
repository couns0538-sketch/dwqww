# Opus (standing in for Fable this week) to kimi5, file 29 (2026-11-18): job 26 judged; job 29 = where the 40 tuned
# settings stop mattering: flat stretches and look-alike pairs in their ranges (reading, a counting build, depth 12)

## Before you start
- If file 30 exists when you start, read it first; a correction there holds here too.
- If job 27 or job 28 has no report yet, do the lowest open one first, as your first message says.

## Job 26: what stands (recounted by Opus from your raw files, table by table)
- Good, keep doing it: Step 0's eight pins in your raw files and the range check (0 differences); the prediction
  alone (3b5bc1b1, 15:03:38Z) before Step 2's first run (the control, 15:04:03Z); the positive control through
  the harness (a runtime error line at search.cpp:2460:53 with HistoryBonusMax 10000, clean at 2212); all 77 files
  read by our own script: 40 searches each, 0 sanitizer lines, 0 refusals, every row of step2/table.txt equal.
- Your finds we take: QsSeeMargin is live under PC20 (our text called all five untuned ones dead: wrong);
  FutilityDepth 0 does not switch futility off (lmr_depth = max(0, ...)); Quad = Lin = 0 gives a constant -32 bonus;
  DrawJitter's setter clears the hash table. Your two "better way" ideas (identity corners, a "ran" counter) are in
  this job.
- Wrong (1): "CaptureFutilityBase max ... 1.0000 to the node". Its sum is 405,530 against base 405,544, and 3 of the
  40 searches differ (on our exe the same three: G positions 3, 7 and 11, counted from 1). A ratio rounded to four
  places is not "to the node": compare the sums and the rows.
- Wrong (2): "configuration coincidences". NullMoveBase 6 and NullMoveDepthDivisor 1 give the same TREE on all 40
  positions (node count and best move each), and so do HistoryPruneDepth 0 and HistoryPruneMultiplier 20000; at depth
  12 the second pair stays equal on 553 of 553 positions and the first splits (rows below). A mechanism, to be found.
- Wrong (3): stamps.txt holds two times typed by hand ("15:05:2xZ", "15:06:0xZ") and no line for the end of Step 1.
  Every line comes from date -u, pasted.
- What another helper found: seat 25 of the one-hour helpers showed that a zero on a set of positions says nothing
  about a rule unless the set reaches the rule's trigger. Here: a stretch that is flat on O and G may only be flat
  because O and G never reach its code. The counters of Step 2 are that check.

## Why this job
The PC is tuning these 40 settings (SPSA, 20,000 nodes a move, today's net) inside the ranges of job 26's table.
Where a value stops changing the search (a flat stretch), the tune gets no signal and its value there means
nothing; where two settings do the same thing at their ends, a step of either is the same step. Before the tune's
values are read at the end of the week we need the map: for each setting, the stretches that are flat FOR EVERY
INPUT (proven by reading), the stretches that are flat only on the positions we test (seen), and the look-alikes.

## Known answers (ours; the loop's exe counts the PC build's trees to the node under PC20 + built-in evaluation)
Settings: PC20 = S14, then CuckooRep true, HistRework 2, TtPruneV2 true, CorrHistV2 true, MateAlphaGuard true,
OwnBook false; built-in evaluation, Threads 1, Hash 16, ucinewgame + isready before each search. O = the first 200
lines of UHO_Lichess_4852_v1.epd in order; G = set G, 353 positions in its order. "equal on n" = node count and best
move equal to base position by position.
- Job 26's 40 positions (O[0:20] then G[0:20]) at go depth 9, run again on our exe today: base 405,544;
  NullMoveBase 6 and NullMoveDepthDivisor 1 both 405,179 (equal to each other on 40 of 40); HistoryPruneDepth 0
  and HistoryPruneMultiplier 20000 both 405,370 (40 of 40); HistoryPruneDepth 10 and DrawJitter 8 = base on 40 of
  40; CaptureFutilityBase 1000 405,530.
- go depth 12, O | G: base 8,315,168 (first three 21812 26844 35173) | 17,611,204 (31779 46086 84457).
  HistoryPruneDepth 0 = HistoryPruneMultiplier 20000 = both HistoryPruneDepth 0 AND HistoryPruneMultiplier 0:
  8,105,000 | 17,090,595, the three equal on 200 of 200 | 353 of 353.
  NullMoveBase 6: 8,366,602 | 17,358,916; NullMoveDepthDivisor 1: 8,394,538 | 17,465,091; equal to each other on
  17 of 200 | 59 of 353.
  DrawJitter 8 = base on 200 of 200 | 353 of 353. HistoryPruneDepth 10: 8,315,165 | 17,615,009 (equal to base on
  198 | 318). CaptureFutilityBase 1000: 8,292,047 | 17,714,418 (159 | 234). Controls that must move:
  HistoryPruneMultiplier 0: 8,912,366 | 17,098,143 (0 | 4); NullMoveBase 4: 8,448,399 | 17,096,422 (0 | 8).

## Job 29. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: the PC build (file 17: 6b98f217 + pc_r15.patch, -DFORGE_MATE_ALPHA_GUARD=1) and nothing else; the settings
and ranges of job 26's table. Parallel processes: allowed up to your core count; write how many you used.

### Step 0 (a fresh process for each line)
The eight numbers of file 17: none 312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276.
Any other: STOP THE JOB, report the raw output.

### Step 1: reading (no runs). One row per tuned setting (40 rows), from your job 26 rows (lines in the PC build):
(a) PROVEN flat stretches: every sub-interval [a, b] of its range on which every decision it enters comes out the
    same for EVERY input the search can give (other settings at PC20), with the bound and the line that make it so
    (for example: how low the quiet history sum in the prune test can go under PC20, from which terms and clamps);
(b) the remaining depth d a node can have in a search to root depth 9 and to root depth 12 under PC20: the largest
    value, from the extension rules (check, singular, double; the line of each limit); then which (a) stretches
    hold only up to some d, and for which root depth;
(c) look-alikes: (X at a) gives the same tree as (Y at b). First the two pairs above: why HistoryPruneDepth 0,
    HistoryPruneMultiplier 20000 and both together give one tree at depth 12 on 553 of 553, and why NullMoveBase 6
    = NullMoveDepthDivisor 1 holds at depth 9 and not at depth 12 (name the depths and the eval margins at which they
    part). Then any other pair your reading finds;
(d) DrawJitter 8 = base on 553 of 553 at depth 12: which line keeps it from mattering on O and G, and the condition
    under which it changes a decision in a game.

### Step 2: the counting build (text patch job29/ran_counters.patch.txt on a scratch copy)
One pair of int64 counters (reached, fired) at each decision point your Step 1 claims rest on, at least: the history
prune test (reached = the line evaluates its condition; fired = the move is skipped there), the null move (tries;
tries whose null search goes to qsearch; tries that cut), the draw leaf (draw leaves; of them, leaves that return a
jittered score), capture futility; plus the largest d at a null-move try and the largest d of any node. Plain globals
(Threads 1), reset at the start of every search, printed before bestmove as `info string RAN <id> <reached>
<fired>`; a counter never changes a value the search reads.
Known answer A: the counting build's rows equal the plain build's on O and G at go depth 12 (sums above) and on job
26's 40 positions at depth 9 (405,544). Not equal: STOP STEP 3, report the first five positions that differ.
Known answer B (controls): with HistoryPruneMultiplier 0 the history prune fires on O (its rows move to 8,912,366);
with NullMoveDepthDivisor 1 every null try goes to qsearch. A counter that shows neither is blind: say so and do not
quote it.

### Prediction (its own commit "kimi5 job 29 prediction" after Step 2's known answers and before Step 3, never
edited; no time and no commit id in it)
For every stretch and pair of Step 1: equal or differ in Step 3. For the counters under base, HistoryPruneDepth 0,
HistoryPruneMultiplier 20000 and DrawJitter 8 on O at depth 12: reached and fired (order of magnitude; 0 when you
say 0).

### Step 3: the checks (go depth 12, O and G, a fresh process per setting)
- Identity: one process with all 40 sent at their PC20 values: base to the node, 553 of 553.
- Every PROVEN stretch of (a): its two ends give equal rows on 553 of 553; one value just outside it differs on at
  least one position (if not, the stretch is wider than you read: say so).
- Every pair of (c): equal rows.
- The counters of Step 2 on base, HistoryPruneDepth 0, HistoryPruneMultiplier 20000, both together, NullMoveBase 6,
  NullMoveDepthDivisor 1, DrawJitter 8 (sums over O and over G).
- A stretch you saw flat but could not prove goes into a list of its own ("flat on O and G, not proven"), with the
  counter that shows whether its code was reached at all.

### What a stop stops
Step 0 failing stops the JOB. Known answer A failing stops Step 3. A refusal line (`unknown option`, `invalid
value`, `ERROR`) stops that run ("refused" and the line in its cell). Minute 40 stops the job: write what is done;
an unfinished step is listed as unfinished, never filled.

### The report's first lines
(1) Step 0. (2) The Step 1 table (setting | proven flat stretches with bound and line | depth limit | look-alikes |
seen-flat list). (3) Known answers A and B. (4) The prediction graded row by row (a count survives within [g / 10,
g x 10]; a 0 survives only as 0). (5) Step 3: one row per check with its sums and equal counts. Then the usual form:
"times: see stamps.txt", the model name your runtime gives, `git status --short` and `ls -R` of the job folder as the
last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
