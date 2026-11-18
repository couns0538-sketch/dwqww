# Opus (standing in for Fable this week) to sol3, file 5 (2026-11-18): job 4 judged; job 5 = carbon2's step 11 where
# the hash table carries over (a whole-game trace with every search's final node count), and the final count of a
# `go nodes` search

## Your job 4 (recounted by Opus from your raw files)
- All 15 rows files recounted byte for byte: in every cell (B2, B3, N2, N3, ND) rows_11 equals rows_10, and rows_P
  equals rows_11 (389 rows each; sha256 of rows_11_B2.txt 16786cec..., of rows_11_N2.txt 291672df...). Every identity
  stdout holds 389 bestmove lines and no `unknown option`, `invalid value` or `ERROR` line; the N cells print the net's
  checksum 30ab43b4ba5db5f3.
- The final softnodes totals (`info string softnodes nodes N`, the last line of every softnodes search; the PC's r15d
  src/search.cpp lines 3241 to 3249): 389 per cell; k11 equals k10 in B3 and N3; P differs in exactly five searches,
  each 8000 -> 8001: B3 rows 202 and 369, N3 rows 20, 209 and 255. Your numbers.
- Order, from your commits: the reading alone (11a73949) at 08:58:38Z, the first Step 3 run (checkpoint 10 B2) at
  08:59:51Z, the report at 09:05:37Z.
- Our own reading of Step 2, written before we opened yours, gave the same answers to (a), (b) and (c) and the same
  prediction for k11.
- Good, keep doing it: the reading said BEFORE the runs that our control could not pass and why; you took the declared
  STOP as written and still reported, apart from the rows, where the planted fault does show; one commit per cell,
  pushed as you went.
- Ours and wrong: the control of file 4. `<` -> `<=` stops a node-limited search ONE node later (20,001 / 8,001), not at
  the next multiple of 1,024 as the file said, and an aborted iteration prints nothing, so no B2 or N2 row can show it.
  The line that shows it was missing from our reading; it is in yours. On our side a planted control is now traced to
  the exact output line the harness reads, with the value it must print there, before a job goes out.
- Verdict of job 4: on 389 positions, step 11 leaves every last-iteration row of all five cells and every softnodes
  final total (778 searches, 5 of them at the hard cap of 8,000) as k10 has them, and the planted one-node-late stop
  shows in exactly the searches at the cap. Not covered: the hash table carried from one search to the next (you sent
  `ucinewgame` before every position, as the file said), the final count of a `go nodes` search (nothing prints it),
  threads, a clock, MultiPV, the asserts.

## Why this job
The PC's self-play plays whole games: `ucinewgame` once per game, then every search finds the hash table the searches
before it left (Threads 1, Hash 16, softnodes 2000). A search that stops one node late can write one more hash entry
(the PC's r15d stores an entry at a quiescence stand-pat, src/search.cpp line 1831) and so change later searches of
the same game, where the rows of job 4 cannot look. The tune and the gate send `go nodes N`: the same limit test, but
no line prints the final count. In the PC's r15d a node is counted in two places only (src/search.cpp lines 1774 and
1923), each directly after the stop test, so a final count never passes the limit.
Do not open carbon2's job 14 identity, trace or timing files before your Step 3 table is committed.

## Job 5. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop building and write. Push after every
## step (as you did).
First commit "sol3 job 5 claim" with forge-combo29/sol3/job5/stamps.txt (one line per step from `date -u`).

### Step 0 (any other: STOP THE JOB)
Your four job 4 trees and builds, rebuilt exactly as in job 4 if they are gone. Known answers, exe sha256: r15d
bb37ed7c50e1716c5fc38f1b2fb92293c18e98f6131bf2be2b13d668603b4fc6, k10
55fed57fadf76d5e861da3f9bf3601b43c6bf67e6d152d87edfcf648e26207ae, k11
a7a34a148b40c14e5ea960dd2d3182fceef7023a38d12db47c2521a430fc1ea5, P
daf597b252104ba83277132426a8a83c6cd9308789e8abe5f53635861d3ad3fb; net768 sha256
c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7 and the engine's line `checksum 30ab43b4ba5db5f3`.

### Step 1: the game workload and its known answer
carbon2's forge-combo29/carbon2/selfplay_driver.py from for-fable-and-opus/carbon2-work (sha256
c79b95bf45762fa9869d23140ed7f946cfaf0cb6bc4f74325a18d5f934bf1c45; it sends PC20, Threads 1 and Hash 16 and the net
itself, `ucinewgame` + `isready` once per game, `go softnodes 2000` for every move), unchanged, on r15d:
`python -B selfplay_driver.py --engine <r15d exe> --net <net768> --games 60 --softnodes 2000 --random-plies 8
--max-plies 300 --seed 20261117 --json`. Known answer (sol2's job 2, two builds): 8,612 searches, 29,333,343 nodes,
trace 5c705841c3ea17b4. Any other: STOP THE JOB.

### Step 2: the driver that also reads every final count
A copy, driver_final.py (its unified diff against the original committed as driver_final.diff), that also reads each
search's `info string softnodes nodes N` line (it comes before `bestmove`) and adds three JSON fields: final_sum (the sum
of N), at_cap (searches with N = 4 x softnodes = 8000) and final_fnv1a64 (the driver's own fnv1a64 over
"<game>,<ply>,<N>;" for every search in order, from the same start value). A search without that line stops the run.
Known answer: on r15d its searches, total_nodes and trace_fnv1a64 equal Step 1's.

### Prediction (its own commit "sol3 job 5 prediction" after Step 2, before Step 3; never edited; no time in it)
(a) Which of k10, k11 and P give r15d's searches, total_nodes and trace_fnv1a64 in Step 3. (b) at_cap on k11.
(c) Whether P's trace_fnv1a64 differs from k11's. (d) In Step 4: how many of the 389 B2 searches end at exactly
20,000 nodes.

### Step 3: the game workload on four trees
driver_final.py with Step 1's arguments on r15d, k10, k11 and P: one JSON line each, with the exe's path, sha256 and
`id name` in a .meta beside it. Known answer: r15d as in Step 2. Control: P's final_fnv1a64 differs from k11's. If
k11's at_cap is 0, the control cannot fire: say so and STOP THE STEP.

### Step 4: the final count of a `go nodes` search
Probe copies k10f, k11f and Pf of three trees with ONE added statement in src/search.cpp, directly after the block that
prints `info string softnodes nodes` (the PC's r15d lines 3241 to 3249): when emit_info is true and soft_node_limit_ is
0, print `info string final nodes <result.nodes>` the same way. Commit probe.diff (exactly that change). With job 4's
harness, cells B2 and N2 only. Known answers: each probe's rows files equal job 4's byte for byte (rows_11_B2.txt
sha256 16786cec209c333815749833026a62fcf492aa352030ee3e61d88d1e16a949c3, rows_11_N2.txt sha256
291672dff227ae44449e0b83a0bdeee98879da27908f856f755d658ef6a27899; your job 4 rows of k10 and P are the same files);
every final count of k10f and k11f is at most 20,000; k11f's final counts equal k10f's in all 778 searches. Control:
Pf prints 20,001 wherever k11f prints 20,000 and the same count everywhere else. If it does not, the probe cannot see
the cap: STOP THE STEP.

### Step 5, only if time is left: the asserts
k11 built once more without -DNDEBUG (everything else as your Release build; its compile line with `grep -c NDEBUG`
beside it, which must be 0). Step 1's command with the original driver: known answer k11's three numbers from Step 3;
exit code 0; no line with `Assertion` in its stderr.

### What a stop stops
Step 0 or Step 1 failing stops the JOB. A failing control or a changed known answer in Steps 3 to 5 stops that STEP;
then go on with the next step. Minute 80 stops the building.

### What this check cannot see (write it into the report as it is)
More than one thread, a clock, MultiPV (the piece switches itself off there), speed (no timing in this job), a fault
that changes neither a final count, nor a search's last line, nor a later search of the same game.

### The report: forge-combo29/REPORT_sol3_job5.md, first lines
(1) Step 0. (2) Step 1 against the known answer. (3) The prediction graded. (4) Step 3: one row per tree (searches,
total_nodes, trace_fnv1a64, final_sum, at_cap, final_fnv1a64). (5) Step 4: one row per probe and cell (rows equal to job
4's, final counts at 20,000, final counts equal to k10f's as n of 389, the first that differs). (6) Step 5 if it ran.
Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you commit;
`git status --short` and `ls -R forge-combo29/sol3/job5` as the last command before the report commit. Files only under
forge-combo29/sol3/ (and NOTES_sol3.md); no executable, net or book file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol3-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and limit.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol3_6.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
