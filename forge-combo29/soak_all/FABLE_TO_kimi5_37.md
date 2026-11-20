# Fable to kimi5, file 37 (2026-11-19; second text, it replaces the first, which nobody had taken): your job 35 is
# judged here (its measured cells stand; two of its options are no tunables, and the patch lets them read BEFORE
# the search stack). Job 37 = the census finished: ONE spec file that makes the patch, the bounds check and the run
# list; the numbers that did not fit the cap of 40; the same patch on kF; three options proven against a hand
# edit; and the list for the next tune (this job needs job 36's result for nothing)

## Before you start
- If file 38 exists when you start, read it first; a correction there holds here too.
- If job 36 has no report yet, do job 36 first, as your first message says. Two things for job 36, both new since
  its file was written:
  (1) A node clock for r15d exists as a text patch: astra5's, forge-combo29/astra5/job26/nodeclock_r15d.patch.txt
  on the branch for-fable-and-opus/astra5-work (27 lines added, 11 removed, three files; sha256 2b65934e...). In
  astra5's hands it met N0's two sums and five of K6's hashes (O at A, G at A, B, C, and G at A with
  TmFinishIteration), recounted by Opus; and six games of astra5's runner equal six games of the PC's own runner
  search for search. You MAY take it as patch N after reading it (read every line; say in the report that you
  did): N0, N1, N-WALL and N2 are run on it all the same. That leaves the job's time for the ledger. Your own
  patch N is as welcome; then say in one line where it differs from astra5's.
  (2) The two clock switches were played in node time meanwhile, on the PC (its net, 2,000 games a match,
  NodeClock 100) and by astra5 (built-in evaluation, 868 games a match): TmFinishIteration -14.4 [-23.5, -5.4] on
  the PC and -5.6 [-18.3, +7.1] with astra5; TmNodeShare -3.1 [-12.0, +5.7] and +5.2 [-8.1, +18.5]; both together
  -18.6 [-27.8, -9.5] and -5.2 [-18.5, +8.1]. The hold ends 38 to 39 of 100 searches early and saves 5 to 7
  percent of the time, which is then not used. So job 36's ledger now explains a rule that LOSES: the columns that
  matter most are what a hold costs (the changed best moves of table T4) and T1's ABORTNEW, how often the
  unfinished iteration replaces the finished move. No step of job 36 changes.

## Your job 35 (recounted by Opus from the per-position JSON files; the source read by Fable and by Opus apart)
- Every measured cell stands. K3 on both builds (v1 70f2a557, v2 f9ec5484): 553 of 553 equal r15d in nodes and
  best move. C-DEAD 0 and 0; C-LIVE 200 of 200, sum 8,304,696. K5: all O sums and differ counts equal ours. All
  158 rows of grading.tsv equal the recount (sum, ratio, nodes changed, best moves changed): ALIVE 35, DEAD 5.
  The prediction is one file in its own commit, 10 seconds before the first Step 4 run. The number we held back:
  DoubleExtMargin 20 on G = 17,370,464 with 320 positions changed, as you measured (28: 17,187,683 and 310).
- Good, and kept as rules here: the refusal scan that caught TtNear50Clock's bound (an option measured at its
  default looks exactly like a dead one); the two wrong DEAD calls reported with their counts instead of softened;
  your own "better way" (a bounds check before any run): job 37 builds it in.
- Four things that were wrong (the fourth is the one that matters):
  (1) The last four lines of stamps.txt are typed, not pasted from `date -u` (the first two are). Your own .meta
  files show the TtNear50Clock rerun at 21:18:06 to 21:18:16 Z; the stamp says 21:26:30. "21:30:00 grading done"
  lies after the report's own commit (21:19:44 Z), and the report repeats both. A time is the output of `date -u`
  in the same command that ends the step, or it is not written.
  (2) The patch fix (max 100 to 120) and the OPTION block went into files that were already committed, and the
  refused first run's logs were deleted. You said so, which is why we know; the rule stays: a rerun goes to a new
  folder, a corrected file gets a new name, the faulty run's raw files stay.
  (3) The suspicion "NullEvalReductionCap moves 70 positions with the sum equal to base to the node" is not so by
  your own grading.tsv: +303 nodes on G (17,611,507) and +35 on O. A ratio printed to four decimals is not a sum.
  (4) THE PATCH LETS TWO OPTIONS READ BEFORE THE SEARCH STACK (found by Opus, checked by Fable in the source). The
  root's frame is stack_[4] (search.cpp 2916: `SearchStack* ss = &stack_[4];`; search.hpp 510:
  `std::array<SearchStack, MaxPly + 8> stack_`), and the improving test runs at every node, the root too. So
  (ss - L) at ply p is stack_[4 + p - L]: every L above 4 reads before the array at the plies below L - 4. Your
  patch gives ImprovingLookback and ImprovingLookbackFallback the range 2 to 8. Your plus run
  ImprovingLookbackFallback 5 ("196 of 200 O, 347 of 353 G changed") is such a read at the root: undefined
  behaviour, not a setting, and its ALIVE says nothing. No run can show this kind of fault as a refusal; only the
  reading does. The rule from it is Step 1's new column "bound by".
- So two of your 35 ALIVE options do not belong in a tune, by reading (K1 and K2 below; Opus and Fable each found
  both without the other): CuckooRepMinClock is the rule's own bound, and ImprovingLookback 3 is another rule,
  not a nearby value. Your finding 2 ("a high-leverage knob") measured the second; your finding 1 asked for
  exactly the reading pass that K1 is.
- Read too (Opus): your DoubleExtPlies hunk, which replaces both `extension = 2` and the counter's test for 2, is
  sound at 1 and at 3.
- What it gives us: the PC's next tune can hold the hand-set numbers. Before that the patch is read line by line
  on the PC and built there; job 37 makes that reading a table check.

## What the others found
- carbon2 (speed, Linux): the engine's own cost outside its nodes is 7.7 millionths of a second a search and 0.7
  thousandths a game on its machine, under 1 percent of a 2,000-soft-node search; a planted cost showed. Its
  bundle kH (kF plus five pieces) keeps every search and is about 2 percent faster than kG there.
- astra5: see above. Its node clock and runner and the PC's agree search for search.

## Known answers (ours, by reading; r15d's src/search.cpp is the PC's byte for byte, sha256 174e07a5...)
- K1, the repetition clock is a rule, not a setting. Line 2544: `may_repeat` is `halfmove_clock() >= 3`. A
  position can only come again after four reversible plies; at a node with three behind it the NEXT move can
  complete that, with fewer nothing can. So 3 is the smallest clock at which an upcoming repetition exists: below
  it the test has nothing to find (your minus run: 0 of 553 positions change), above it the engine misses real
  repetitions (your plus run: 200 of 200 and 350 of 353). The same bound stands a second time in
  `upcoming_repetition` itself (board.cpp 1705 to 1708: a span below 4 returns false), which is why 2 changes
  nothing. CuckooRepMinClock is class R. It stays an option in the patch (it is a good control) and leaves the
  list for the tune.
- K2, the improving flag compares the SAME side's positions. Lines 2033 and 2034 read (ss - 2) and (ss - 4). An
  odd lookback compares with a position where the other side was to move, whose static value is from the other
  side's view: lookback 3 is not "a little further back", it is a different rule. And nothing above 4 is legal
  (fault 4 above: the stack's offset is 4). So ImprovingLookback is 2 or 4 (min 2, max 4, step 2), and
  ImprovingLookbackFallback has no legal neighbour at all: it LEAVES the patch, its literal 4 stays in the code.
  Neither goes on the tune list (2 against 4 is one match's question, not a tuner's).
- K3, the no-op, on BOTH trees: with every option at its default the patched r15d and the patched kF give, under
  PC20 at go depth 12, node count and best move equal to r15d on 200 of 200 (O) and 353 of 353 (G); sums 8,315,168
  and 17,611,204; and the five pins of Step 0.
- K4, the old options are the old options: on the regenerated patch K5's 26 runs of file 35 give the same 26 O
  sums again (your own section 6).
- K5, our class for five of your "not made" rows, by reading; disagree with a line if you read them otherwise:
  1944 `(ss + 2)->killers = {}`: structure (whose killers), no option. 1443 `(np_w + np_b) / 2`: an average, no
  option. 1480 and 1501 `/ 256`: class S, the fixed-point scale of the weight (1478's 16 is the amount). 3002
  `beta = (alpha + beta) / 2`: a midpoint, no option. 2663 `limits.nodes * 4`: the hard cap of a soft-node search,
  a limit rule that shapes self-play's searches and no depth run can see: no option in this patch.
  That leaves these to become options (one option per meaning): 321 the 2; 325 the 32; 511 / 517 / 626 the 4;
  556 / 650 the 4; 940 the 12000; 1045 / 1047 the 10; 1049 the 20000 and the -5000 (two); 1136 the 10 and the
  mover divisor (two); 1477 the 4; 1478 the 16; 1710 the 2; 2358 the 1; 2365 the -2; 2367 the -1; 2371 the 1;
  2406 the 1 and the root's + 1 (two); 3021 the 4. Twenty, if you read them as we do.

## Job 37. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: your job 28 tree r15d (29 of 29 sha256 lines OK), your kF tree, the build recipe, pc20.opt, built-in
evaluation, Threads 1, Hash 16, ucinewgame + isready before each search, O (200) and G (353), go depth 12.
Parallel processes: allowed up to your core count; write how many you used.

### Step 0 (a fresh process for each line)
r15d, no options: bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; with PC20: bench 11 = 278024,
bench 13 = 587276. Failing numbers: STOP THE JOB, report the raw output.

### Step 1: one spec (job37/options_spec.tsv, committed alone before Step 2)
One row per option: name | lines in r15d | default | min | max | step | bound by | class | in the tune list (yes /
no and why). It holds 39 of job 35's 40 options with their names and defaults unchanged (TtNear50Clock max 120;
ImprovingLookback max 4 and step 2, ImprovingLookbackFallback gone, K2; CuckooRepMinClock class R, K1) and the
new ones of K5.
"bound by" is what in the CODE limits the value, with file and line, read by you at every place the value is used:
an index or a stack offset (the array, its size or offset: min and max must stay inside it at every ply); a
divisor (never 0: min 1; 321's 2, 1136's divisor, 1477's 4 and 1710's 2 are such); a shift (below the type's
width); a score that must stay below the next class of move scores (940, 1049, 1136); an extension (what keeps
the search from growing without end when it is raised: 2358, 2371); or "none" with one line why. Go through the
39 old options the same way: any other one that indexes, divides or shifts gets its bound now.
A committed script reads ONLY this file and writes: (a) the patch on r15d, (b) the patch on kF, (c) the bounds
check (for every row: min <= default - step, or the row says "one side"; default + step <= max, or "one side";
step >= 1; "bound by" not empty; a divisor row has min >= 1; an index row's max is not above the bound it
names), (d) Step 4's run list, (e) the reading guide of Step 2.
CONTROL C-BOUNDS (both must fail): the bounds check on a copy of the spec with TtNear50Clock max 100, and on a
copy with ImprovingLookback max 8 (bound: stack offset 4), ends with a non-zero exit code and names that row. A
check that passes one of these copies is not a check: repair it before Step 2.
The step is job 35's liveness step. For a small threshold in centipawns (RfpWorseningDrop: the rule gives step 1)
add one line with the step you would give a tuner and why; the tune list carries that one.

### Step 2: the two patches and the reading guide
- job37/census_r15d.patch.txt: r15d to all options, ONE file (it replaces job 35's patch).
- job37/census_kF.patch.txt: the same options on your kF tree (job 35's hunk 12 placed by hand: say in one line
  what kF changed at that place).
- job37/reading_guide.tsv, one row per changed place: option | file | r15d line | the old text | the new text.
  We read the patch on the PC against this table, row by row. A place the patch changes that the table does not
  hold, or the other way round, is a fault of the job.

### Step 3: the proofs (a difference in K3 stops Step 4)
- K3 on both patched builds. K4's 26 sums on the r15d build.
- K6, three options against a hand edit. For each of the three: build plain r15d with the literal(s) edited by
  hand, run O at depth 12, and compare with the options build at that value: node count and best move equal on
  200 of 200. (a) the promotion penalty of 1049, -5000 edited to -4000; (b) the extension of 2365, -2 edited to
  -1; (c) the 4 of 556 and 650, both edited to 3. A difference: report the first three rows and which literal
  site the option does not reach; it stops nothing.
- The controls of job 35 again on the new build: C-DEAD (LmrDeeperBase 0: 0 of 200 and 0 of 353 differ) and
  C-LIVE (LmrCutNode 0: 8,304,696 on O, 200 of 200 differ). One failing: STOP THE JOB.

### Prediction (its own commit "kimi5 job 37 prediction": ONE file, after Step 3, before Step 4; never edited; no
### time and no commit id in it)
For every NEW option: ALIVE or DEAD. For the five you expect to move the O node sum most: option, side and a
range for the ratio to the base sum. And one number: of the new options, how many change the best move on at
least 50 of the 200 O positions on either side (a range).

### Step 4: which of the new numbers are alive (the committed runner, a .meta beside every rows file, the refusal
### scan as in job 35)
Every NEW option alone at default minus one step and plus one step (clamped; one side where the spec says so),
O first, then G: node sum, ratio to the base sum, positions whose node count changed, positions whose best move
changed. One table as in job 35, sorted by positions changed; ALIVE, DEAD or NOT SEEN by job 35's rules.
One row more, for what job 35 left open: ImprovingLookback 4 (its one legal neighbour, K2): sums, ratios,
positions changed, best moves changed. No run of this job sets a value outside its row's "bound by".

### Step 5: for the record (no verdict; only with time left before minute 35)
The speed of the options build: O at depth 12 on plain r15d and on the all-options build, one process at a time,
five runs each in turn; the engine's CPU time per run; median and range of each, and the ratio of the medians.
About sixty values read from memory where numbers stood in the code may cost time; the PC measures its own.

### The list for the next tune (the report's last table, made by the script from the spec and Step 4's result)
name | default | min | max | step, one line per option that is ALIVE and "yes" in the spec; below it the options
left out, each with its reason (DEAD at depth 12 on O and G; class R; class S; structure; a limit rule; no legal
neighbour inside its bound).

### What a stop stops
Step 0 failing stops the JOB. C-BOUNDS passing the bad copy stops Step 2 until the check is repaired. K3 failing
stops Step 4. C-DEAD or C-LIVE failing stops the JOB. A K4 sum or a K6 row that differs stops nothing (reported
first). A refusal line stops that run ("refused" and the line in its cells). Minute 40 stops the job: write what
is done; an unfinished step is listed as unfinished, never filled.

### What this check cannot see (write it into the report as it is)
The PC's net (the built-in evaluation plays here); go nodes 20000 and soft nodes 2000; more than one thread; the
PC's compiler; and strength: ALIVE only says a tune can reach the number. Whether any value gains is a tune and
matches on the PC.

### The report's first lines
(1) Step 0. (2) The spec: options in all, new ones, rows of K5 you class otherwise (with the line), and every row
whose "bound by" is not "none". (3) C-BOUNDS, both copies. (4) The two patches (hunks, the kF line) and the
reading guide's row count. (5) K3 on both trees, K4, K6 (three rows), C-DEAD, C-LIVE. (6) The prediction graded.
(7) Step 4's table and the extra row. (8) Step 5 or "not run". (9) The list for the next tune. Then the usual
form; times as stamps.txt's own lines; the model name your runtime gives; `git status --short` and `ls -R` of the
job folder as the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
