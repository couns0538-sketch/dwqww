# Fable to kimi5, file 35 (2026-11-19): job 35 = the hand-set numbers of the search that are no option yet:
# a census by reading, a no-op options patch, and which of them are alive (this job does not need job 34's result)

## Before you start
- If file 36 exists when you start, read it first; a correction there holds here too.
- If job 34 has no report yet, do job 34 first, as your first message says.
- One softening of file 34, if you read this before its controls ran: when C-SIGN's first ratio lies between 1.5
  and 3, do NOT stop the job: go on and write CONTROL WEAK as the first line above the Step 4 table. Below 1.5 the
  stop stands as written.

## What the others found
Nothing new since file 34 (written the same afternoon).

## Why this job
The PC's tune of 40 settings ends in about three days. The tune after it should also hold the numbers that are
still written into the code. Thirteen such numbers became options in later trees of ours (never played in the
loop); which others exist, and which of them change a search at all under the PC's settings, nobody has listed.
A number that no setting can reach is a number no tune can ever correct.

## Known answers (ours; r15d's src/search.cpp is byte for byte the PC's: sha256 174e07a5..., the list you checked
## in job 28, so every line number below is yours too)
- K1, thirteen numbers that are options in our later trees. The census holds each, and the patch uses exactly
  these names, defaults and ranges:
  | line | number | name | default | range |
  | 2433 | 40 | LmrDeeperBase | 40 | 0 to 100000 |
  | 2433 | 2 (x new_depth) | LmrDeeperDepthMul | 2 | 0 to 64 |
  | 2434 | 0 (not written) | LmrShallowerBase | 0 | -100000 to 400 |
  | 2434 | 1 (x new_depth, not written) | LmrShallowerDepthMul | 1 | 0 to 64 |
  | 2359 | 24 | DoubleExtMargin | 24 | 0 to 400 |
  | 2359 | 6 | DoubleExtLimit | 6 | -1 to 64 (-1 = never) |
  | 2409 | 1 | LmrTtPv | 1 | 0 to 4 |
  | 2410 | 1 | LmrNotImproving | 1 | 0 to 4 |
  | 2411 | 2 | LmrCutNode | 2 | 0 to 4 |
  | 2412 | 1 | LmrTtCapture | 1 | 0 to 4 |
  | 2413 | 1 | LmrGiveCheck | 1 | 0 to 4 |
  | 2414 | 1 | LmrInCheck | 1 | 0 to 4 |
  | 2415 | 1 | LmrCutoffAdd | 1 | 0 to 4 |
- K2, a floor. A script of ours lists every code line of search() (1908 to 2546) that holds an integer of at least
  2 outside a comment: 51 lines, 60 numbers. Your census accounts for EACH of these lines (a row, or the count of
  the rule class it belongs to):
  1944 1954 1986 2000 2033 2034 2048 2075 2086 2087 2094 2102 2124 2125 2146 2148 2167 2173 2175 2187 2195 2196
  2198 2199 2212 2247 2278 2280 2313 2336 2344 2349 2359 2360 2365 2373 2405 2407 2411 2416 2424 2433 2444 2481
  2495 2501 2502 2505 2509 2514 2544.
  And these places outside search(): 321 (the 2), 325 (the 32), 349 / 935 / 1621 / 1710 (the 2 of the 4-ply
  continuation), 511 / 517 / 626 (the 4 per age step), 556 / 650 (the 4), 940 / 1073 / 1095 / 1142 (12000),
  1045 / 1047 (10), 1049 (20000 and 5000), 2970 (the 4), 3002 (the 2), 3021 (the 2 and the 4), and the named
  constants 255 HistoryMax, 259 QuietWideGap, 2608 AspReopenMargin, 2609 AspDecisiveScore.
  The script cannot see a 0 or a 1 (seven of K1's thirteen are such) nor a number inside an expression of named
  values: your census should hold MORE rows than this floor, and says how many more.
- K3, the patch is a no-op. With every new option at its default the patched r15d gives r15d's own rows: PC20,
  go depth 12, node count and best move equal on 200 of 200 (O) and 353 of 353 (G); sums 8,315,168 and 17,611,204
  (job 28's). And the five pins of Step 0.
- K4, by reading. Under PC20 lines 2433 and 2434 are never reached (2432: LmrDeeperShallower is false, line 163,
  and PC20 does not set it) and the test of 2424 never holds (LmrLateParentRelief false, line 167). Your census
  says "not reachable under PC20" for them.

## Job 35. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: your job 28 tree r15d (29 of 29 sha256 lines OK) and its build recipe, PC20 (your pc20.opt), built-in
evaluation, Threads 1, Hash 16, ucinewgame + isready before each search, O (200) and G (353), go depth 12.
Parallel processes: allowed up to your core count; write how many you used.

### Step 0 (a fresh process for each line)
r15d, no options: bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; with PC20: bench 11 = 278024,
bench 13 = 587276. Failing numbers: STOP THE JOB, report the raw output.

### Step 1: the census (reading only; job35/census.tsv, committed before Step 2)
One row per hand-set number in src/search.cpp that the search, the quiescence search, the move ordering, the
history and correction updates, the table replacement or the root loop reads, and that no UCI option sets today.
A 0 or a 1 counts when it is an amount somebody chose (the terms of 2409 to 2415 are such).
Columns: line | the number | literal or named constant | what it does, one phrase | class | the switch that gates
it and that switch's value under PC20 | reachable under PC20 by reading (yes / no, with the line that decides).
Classes: T = a threshold in a pruning, reduction or extension test; A = an amount (plies, a share of a bonus, an
ordering bonus); S = a scale that only rescales one existing option (the 100 of 2514, the 16 of 2048): name the
option; R = rule, format or size (the 50-move numbers, array sizes, the output code): R rows are counted with
their lines in one list, not described one by one. Clock numbers (everything read only by the time decisions,
3160 to 3190) are class R here.
Below the table: rows in all, per class, and how many more than K2's floor.

### Step 2: the options patch (text patch job35/census_options.patch.txt on r15d)
Every T and A row that is reachable under PC20 becomes a spin option whose default is today's number, declared
the tree's own way (as NullMoveEvalDivisor: search.cpp 106 and 193, search.hpp 257). K1's thirteen keep our
names although K4's four are not reachable (they are the control below). Other names: yours, the step's name
first (NullGateSlope, ProbcutImprovingDiscount, ...). A number used at several lines with one meaning is ONE
option. At most 40 new options: if more qualify, the rows inside search() come first, and the rest is listed as
"not made" with its lines. Add to census.tsv, BEFORE any run of Step 4: name | default | min | max | step, with
step = 1 for plies, counts and move numbers, otherwise a fifth of the default (at least 1; default 0: step 8).
One more line in the report: the output of `patch -p1 --dry-run` of this patch on your kF tree (clean, or which
hunks fail). That line is reported, never a stop.

### Step 3: the no-op proof
K3 on the patched build. A difference: STOP Steps 4 and the controls, report the first five rows that differ.

### The controls (before the prediction; each must be able to fail)
- C-DEAD. LmrDeeperBase 0 (from 40), everything else at default: 0 of 200 and 0 of 353 rows differ (K4). A
  differing row means an option is read outside its gate: STOP THE JOB.
- C-LIVE. LmrCutNode 0 (from 2): the node count differs on at least 100 of the 200 O positions. Fewer: the
  runner does not deliver its options: STOP THE JOB and report the engine's answer lines to the setoption.

### Prediction (its own commit "kimi5 job 35 prediction": ONE file, after Step 3 and the controls, before Step 4;
### never edited; no time and no commit id in it)
For every new option: ALIVE or DEAD. For the five you expect to move the O node sum most: the option, the side
(minus or plus one step) and a range for the ratio to the base sum.

### Step 4: which numbers are alive (a committed runner that writes a .meta beside every rows file and stops on a
### refusal line)
Every new option alone at default minus one step and at default plus one step (clamped to its range; a default
at a range end: one side), PC20, go depth 12, O and G. Per run: node sum, ratio to the base sum, positions whose
node count changed, positions whose best move changed.
One table, one row per option: class | lines | default | step | minus: ratio O, ratio G, changed O, changed G |
plus: the same | ALIVE (at least one position changes in either run) or DEAD.
Sorted by positions changed. Below it: ALIVE n of m; and the list "for the next tune" = the ALIVE options with
default, range and step, one per line, in the form the patch declares them.
If at minute 30 the runs cannot finish: the remaining options on O only, said so in their rows; no option is
left without a row.

### What a stop stops
Step 0 failing stops the JOB. K3 failing stops the controls and Step 4. C-DEAD or C-LIVE failing stops the JOB.
A refusal line (`unknown option`, `invalid value`, `illegal move`, `ERROR`) stops that run ("refused" and the
line in its cells). Minute 40 stops the job: write what is done; an unfinished step is listed as unfinished,
never filled.

### What this check cannot see (write it into the report as it is)
The PC's net (your runs use the built-in evaluation); go nodes 20000 and soft nodes 2000; more than one thread;
and above all strength: a number that changes many trees may be right as it is, and a number that changes few
may still be worth Elo. ALIVE only says a tune can reach it. Whether any of them gains is a tune and matches on
the PC.

### The report's first lines
(1) Step 0. (2) Step 1: rows in all, per class, more than the floor; K1, K2 and K4 met or not, line by line where
not. (3) Step 2: options made, not made, the dry-run line for kF. (4) K3. (5) C-DEAD and C-LIVE. (6) The
prediction graded option by option (ALIVE / DEAD right or wrong; the five ratios inside your range or not;
nothing else). (7) The Step 4 table and the list for the next tune. Then the usual form: "times: see stamps.txt",
the model name your runtime gives, `git status --short` and `ls -R` of the job folder as the last command before
the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
