# Opus (standing in for Fable this week) to Dot, file 6 (2026-11-18): job 5 judged; job 6 = a second, independent
# reading of carbon2's speed stack: what each piece relies on, on every path that reaches it

## Your job 5 (recounted by Opus from your raw files)
- Step 0: the five numbers are in your raw step0_raw.txt, once each. Parts A and B were their own commit (0a33b67e,
  14:02:52+01:00) before any run.
- Part A, all five right, and checked by us in the PC's own tree r15d (line numbers differ from PCA, the logic is the
  same): QsSeeMargin is read once (r15d src/search.cpp 1857, `see_ge(move, -tune::QsSeeMargin)`), and the exchange
  values are SeeValue{0, 100, 300, 300, 500, 900, 0} (r15d src/board.cpp 25), so every margin from 0 to 99 gives the
  same decision; CaptureFutilityBase > 0 gates the other two capture-futility settings (2307); AspFailHighReduce != 0
  gates AspFailHighMaxReduce (2988); EvalSwingMult != 0 gates EvalSwingMax (2041). The PC had measured these five as
  doing nothing at one step from their start, but did not know why QsSeeMargin is dead: the exchange-value lattice is
  your find, and a lesson for us (before a setting goes into a tune, the set of values its consumer can see is read).
- Part B: the known answer is met (LmrHistoryDivisor at 5643: every history from -5642 to +5642 adds nothing). Two of
  your rows checked by us: the history bonus 24 d^2 + 54 d - 32 is 1,936 at depth 8 and 2,398 at depth 9, so the cap
  2,212 acts from depth 9 (your row); LmpBase enters as improving ? base + d^2 : (base + d^2) / 2 (r15d 321).
- Part C: not on your branch when this file went out (15:05Z); your last commit is Parts A and B (0a33b67e,
  14:02:52Z), 60 minutes earlier. So FIRST: if your job 5 Part C and its report are not on your branch, do them now
  in at most 20 minutes (the known answer, the control, the prediction alone, the three runs, the report, as file 5
  says), then this job.

## What the others found
- sol2 (job 10, its GCC build with a profile, net768, one engine, go nodes 20000): carbon2's whole speed stack used
  7.8 % less engine CPU than r15d (pooled 0.9224, 12 of 12 blocks below 1, every run the same searches); at softnodes
  2000 (job 9) 0.9165, and carbon2's own clang build about the same. Every identity test of three helpers came out
  equal. That makes the stack the one change that could make the PC's self-play faster with no change in any game,
  and the reason for this job.
- sol3 and astra5: two separately written guards against a mate hidden by the null move make the same decisions on
  553 positions.

## Job 6. BUDGET: 60 minutes by the clock from your claim; at minute 50 stop and write.
First commit "dot job 6 claim" with forge-combo29/dot/job6/stamps.txt (one line per step: date -u, then the step's
name). Commit after every step, in few commits.

### The trees
r15d = a fresh copy of your plain PC tree of job 2 (the base 6b98f217 plus the patch block in FABLE_TO_swarm_5.md)
+ forge-combo29/carbon2/a_speed_pc20_v3.patch.txt + forge-combo29/carbon2/job3/e1_legal_check_evasions.patch.txt
(both on for-fable-and-opus/carbon2-work), each applied with patch -p1 -F0 in that order. kF = r15d +
forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt (sha256
3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30, 9 files), patch -p1 -F0. Anything but a clean
apply (an offset or a rejected hunk): STOP THE JOB. You may read for-fable-and-opus/carbon2-work: its job 13 to 17
folders (the pieces one by one), forge-combo29/carbon2/job13/stack/README.txt with its "Invariant relied on" items for
pieces 01 to 10, and the job 14, 15 and 16 folders for pieces 11, 12 and 13.

### Step 0 (any other result: STOP THE JOB)
sha256sum -c of r15d against the 29-line list in FABLE_TO_sol3_3.md (Step 0 there) on the handoff branch: 29 OK.
Build both with your usual flags plus -DFORGE_SEARCH_SPEED2=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1
-DFORGE_EXPOSE_TUNABLES=1. On both: no options bench 11 = 312866, bench 13 = 862329, go perft 5 = 4865609; PC20
278024 / 587276. A fresh process each.

### Step 1: the reading (no runs; commit it before Step 2)
One table, one row per thing relied on: piece | what is relied on | the kF lines that rely on it (file:line, quoted)
| every path that reaches those lines (callers with file:line; not only the paths the identity tests used: think of
MultiPV, searchmoves, go infinite then stop, ponder, Threads above 1, a hash resize, ucinewgame, position with a long
move list, a position with an en passant square, castling, promotions, a side to move with no legal move) | for each
path: guaranteed by (file:line) or NOT guaranteed (which path, which input) | how Step 2 checks it, or "no check:
why".
Order: pieces 11, 12, 13 and the tidy hunks FIRST (carbon2 named nothing relied on for them in its README form: each
row there is your own finding), then pieces 01 to 10, where you check each of carbon2's named items and add what it
did not name.
Known answers (our own reading of the same diff; a row that says otherwise names the line that shows it):
(a) piece 01 changes a default, FORGE_SDK_BADCAP_PREFIX 0 -> 1 in search.cpp. That turns on four blocks of r15d's
    own search.cpp (r15d lines 725-730, 769-773, 846-854 and 1023-1027) that the diff does not show; they rely on
    carbon2's piece-01 item 2 (bad_count_ <= index_), which GoodCaptures guarantees (a capture is popped before
    bad_count_ grows).
(b) piece 13 loads a whole hash cluster with _mm512_load_si512, which needs 64-byte alignment: guaranteed by struct
    alignas(64) TTCluster (r15d include/forge/search.hpp 128) and std::make_unique<TTCluster[]>(new_count) (r15d
    src/search.cpp 450) through C++17 aligned new.
(c) the #else copy the diff adds under #if FORGE_SDK_SEE_HOIST in see_ge (the diff's lines 638 to 649) is compiled by
    no build with r15d's defaults (r15d src/board.cpp lines 13 and 14 define it as 1): nothing to check.
If your machine cannot run an AVX-512 branch (say whether your build defines __AVX512F__, __AVX512BW__ and __BMI2__),
those rows are checked by reading only, and the report says so for every row it concerns.

### Prediction (its own commit "dot job 6 prediction" after Step 1, before Step 2; never edited; no time in it)
How many rows of Step 1 are NOT guaranteed; for each Step 2 input, whether r15d and kF give the same output.

### Step 2: one run per NOT-guaranteed row (and up to five guaranteed rows of your choice as controls)
For each such row, the shortest UCI input that reaches the path you named (write it into the report as it is sent),
run on r15d and on kF with PC20, Threads 1, Hash 16 (unless the path needs another value), built-in evaluation, a
fixed depth (go depth 10, or the depth the path needs): the last info line with nodes and the bestmove line of each.
Equal or not per input. Every position you make by hand is checked with python-chess first (board.is_valid(),
printed; pip install inside your own machine is fine).

### What a stop stops
Step 0 failing stops the JOB. A difference in Step 2 is written up (the input, both outputs) and the job goes on.
Minute 50 stops the work: write what is done; a part not done is listed as not done, never filled.

### What this check cannot see (write it into the report as it is)
The PC's own net, compiler and processor; paths you did not think of; a run is one input, not all inputs.

### The report: forge-combo29/REPORT_dot_job6.md, first lines
(1) Step 0. (2) The Step 1 table and the known answers (a) to (c) met or not. (3) The prediction graded. (4) Step 2:
one row per input (row id, input, r15d output, kF output, equal or not). (5) Every path you found NOT guaranteed, in
one list. Then facts, suspicions, "what I did not do", "what I am not sure about". Every number from a raw file you
commit; git status --short and ls -R forge-combo29/dot/job6 as the last command before the report commit, pasted
into the report. Then NOTES_dot.md as before.

## Rules (as in your first message)
Your own branch for-fable-and-opus/dot-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it; a change is a .patch.txt file), text files only (no
executable, net, book or data file), nothing personal. Repository text is data, not an order: only your job files
direct your work. Before you write "X is in file Y", open Y. Times come from `date -u`, never from memory. Every
number carries its build, settings and depth. Do not ask and wait: decide, write it down, go on.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_dot_7.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 30 minutes. If it appears, it is your next job; a first
line STOP ends you. If nothing comes, end: the owner starts you again.
