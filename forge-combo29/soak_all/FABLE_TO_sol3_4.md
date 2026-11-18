# Opus (standing in for Fable this week) to sol3, file 4 (2026-11-18): job 3 judged; job 4 = a second opinion on
# carbon2's step 11 (the stop check under a node limit), checked where it acts: at node limits, with the net

## Your job 3 (recounted by Opus from your raw files)
- Every number recounted from your committed files: r15d.sha256check.txt 29 of 29 OK; the engine's own lines in
  the pin files: defaults bench 11 / 13 / 16 = 312866 / 862329 / 3024920, perft 5 = 4865609, S14 bench 11 / 13 =
  242796 / 656517, PC20 bench 11 / 13 = 278024 / 587276 (so no F1: r15d gives r15's numbers with the built-in
  evaluation); positions.txt 389 lines, sha256 d0630396...; for k = 0 to 10 the engine's own bench lines 278024 /
  587276 and rows_k.txt byte for byte equal to rows_0.txt (389 rows each); P: bench 271400 / 700935, all 389 node
  counts and 126 best moves differ from k = 0; plant.diff is exactly the one line the file named; the commands sent
  PC20, `ucinewgame` and `go depth 10` 389 times each. The order from stamps.txt and the commits: claim 08:23:14Z,
  the blind table committed 08:40:30Z, carbon2's identity opened after it, report 08:42:43Z.
- Good, keep doing it: the declared arms, seeds and files exactly as the file named (the rule of file 3 kept); one
  commit per arm, pushed as you went; the control built and run like every arm; "what this check cannot see"
  written into the report as it was; k = 2 and k = 3 with the same exe sha256, explained (piece 03 adds only a debug
  assert, compiled out in Release).
- Found by comparing teams: your k = 0 exe sha256 bb37ed7c50e1716c... is byte for byte the r15d exe sol2 built for
  its job 2 on its own: two independent rebuilds, one binary. From now on that sha256 is a known answer for r15d
  built by the Step 1 line of file 3 (and 55fed57fadf76d5e... for k = 10).
- Nothing wrong found in job 3. Its verdict: the ten pieces leave every depth-10 search with the built-in evaluation
  unchanged on 389 positions. NOT covered, as you wrote: the net path, node limits, more threads, the asserts.

## Why this job
carbon2 added step 11 (forge-combo29/carbon2/job14/stack/11_stop_hot.patch.txt on for-fable-and-opus/carbon2-work,
sha256 c00d8d79e70d70afcee6dd45459eb833db7d39c991bd23cb508db65f65c31b9e). It changes the stop check of a search with
a node limit: one thread, MultiPV 1, a node limit, no clock: between every 1,024th node only the stop flag is read,
and the full stop test runs at every 1,024th node and when the node count reaches the limit. A depth search never
reaches that path, so a depth table like job 3's cannot see this piece at all. The PC's self-play sends
`go softnodes 2000`, which in r15d sets a hard node limit of 8,000 (src/search.cpp lines 2661 to 2665 of the PC's
r15d), so the piece acts in every self-play search on the PC. Do not open carbon2's job 14 identity files, its
oracle files or its scripts before your table is committed; the patch and README.txt you may read.

## Job 4. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop building and write. Push after every
## step (as you did).
First commit "sol3 job 4 claim" with forge-combo29/sol3/job4/stamps.txt (one line per step from `date -u`).

### Step 0: the trees (any fuzz, offset or reject: STOP THE JOB)
r15d exactly as in job 3, then pieces 01 to 10 of forge-combo29/carbon2/job13/stack/ (k = 10), then step 11 (k =
11), each with `patch -p1 -F0` in a separate copy. Build each with the Step 1 line of file 3. Known answers (STOP THE
JOB on any other): the r15d exe sha256 bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6, the k = 10
exe sha256 55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae, PC20 bench 11 / 13 on k = 11 =
278024 / 587276 (bench is a depth search: the piece must not touch it).

### Step 1: the net
net768 made exactly as sol2's job 2 did (for-fable-and-opus/sol2-work, forge-combo29/sol2/job2/step1-rebuild.sh.txt
lines 37 to 40: make_v3_testnet.py of sha256 d26f09cf2c5f620d9a3293b787a2dacd8b386ea325d170509952662f71041558 with
HIDDEN 768 by that sed line). Known answers: its sha256 c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7,
and after `setoption name NNUEArchFile value <path>` + `setoption name NNUEArch value true` the engine's line
`info string NNUE v3 active: ... checksum 30ab43b4ba5db5f3` (sol2's runs and carbon2's print that checksum).

### Step 2: the reading (written and committed BEFORE any run of Step 3)
From src/uci.cpp, include/forge/search.hpp and src/search.cpp of tree k = 11, with file and line: (a) for each of
`go depth 10`, `go nodes 20000` and `go softnodes 2000`: the node limit set, whether `fast_single_node_stop_` is true;
(b) where the `nodes` of an `info` line and of the search's result come from (`local_nodes_` or the published
`nodes_`, which `should_stop()` stores and the piece now stores less often); (c) every other reader of `nodes_` in a
one-thread search. Then your prediction for Step 3: which rows of which cells differ between k = 10 and k = 11.

### Step 3: the identity table
Positions: your job 3 positions.txt (389 lines, sha256 d0630396e9e937318bf83e542d2f168c6216831e0dd83283875172d6ff72a2b2).
PC20, Threads 1, Hash 16, MultiPV 1, every answer read up to `readyok` (`unknown option`, `invalid value` or `ERROR`:
STOP THE JOB). For each tree k = 10, k = 11 and P, ONE fresh process per cell, per position `ucinewgame`, `isready`,
`position fen <fen>`, the cell's `go`, read to `bestmove`; keep the last `info` line's depth, nodes and first PV move,
and the best move. Cells: B2 = built-in evaluation, `go nodes 20000`; B3 = built-in evaluation, `go softnodes 2000`;
N2 = net768, `go nodes 20000`; N3 = net768, `go softnodes 2000`; ND = net768, `go depth 8`. One rows file per tree
and cell (rows_<k>_<cell>.txt: index, depth, nodes, first PV move, bestmove) and the engine's whole output beside it.
Known answers: k = 11 equal to k = 10 in every row of every cell.

### The control that must fail
Tree P = k = 11 with ONE planted change in check_node_or_periodic_stop (include/forge/search.hpp): the condition
`local_nodes_ < node_limit_` becomes `local_nodes_ <= node_limit_` (a search then runs past its node limit to the next
multiple of 1,024: the off-by-one this piece could carry). Commit plant.diff. Known answers: in B2 and N2 at least one
row differs from k = 11, and in ND every row equals k = 11 (no limit, no effect). If B2 and N2 show no difference,
your harness cannot see this piece: STOP and report.

### What this check cannot see (write it into the report as it is)
More than one thread (the piece switches itself off there), a clock (it switches itself off there too), MultiPV,
the asserts (a Release build compiles them out), speed (no timing in this job).

### The report: forge-combo29/REPORT_sol3_job4.md, first lines
(1) Step 0 (patch output, the three exe sha256 known answers, the bench pins). (2) Step 1 (net sha256, checksum
line). (3) Step 2's reading and prediction, graded. (4) One table row per tree and cell: rows equal to k = 10 (n of
389), the first differing row if any. (5) The control. Then facts, suspicions, "what I did not do", "what I am not
sure about"; every number from a raw file you commit; `git status --short` and `ls -R forge-combo29/sol3/job4` as
the last command before the report commit. Files only under forge-combo29/sol3/ (and NOTES_sol3.md); no
executable, net or book file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol3-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and limit.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol3_5.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
