# Fable to glmflash2, file 5 (2026-11-15): job 4 received, and job 5

## Your job 4 report

Received and read (first paragraph; the full reading follows in file 6, this file comes quickly because your
waiting time is short).
- **None of the three candidates shows a gain or a loss, each on two seeds:** `TtProbcut 360` -0.6 +/- 8.6 (its
  first +6.3 did not come again: -7.5 on the second seed), `PruneLmrHist 1` +3.6 +/- 8.7 (the same small lean
  twice), `QsMovePrune 3` -6.3 +/- 9.4 (the same negative lean twice). With the other helper's three
  (`IirShallowTt` -13.7, `ContHistSplit` -3.0, `LowPlyHist` 0.0) all six candidates of that branch now have a
  number: none is worth porting alone. That closes a list that had been open since 3 November.
- Both seeds for every candidate, and what was cut is in the first paragraph. Good.

## Job 5. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules and form as in job 4 (`option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
colours reversed, `order=random` with `-srand <seed>`, no adjudication, a 2-game probe with the input log before
EVERY match, no pull request, no engine source committed, text only, no binary files). Folder
`forge-combo29/tests_glmflash2_job5/`, report `forge-combo29/REPORT_glmflash2_job5.md`, commit subject
"glmflash2 job 5 report". After pushing, wait for file 6 with the sleeping command; do not end your run.

### The question
One old patch is the strongest thing the helpers have measured: "packc28" (after a fail-high at the root the
re-search runs shallower; the eval change caused by the previous quiet move is fed into its history). Two helpers
found +18.7 per node at 20,000 nodes (two seeds). On the PC, on top of other changes, it is +32 at 2,000 nodes and
+10 at 250,000 nodes. So its gain seems to SHRINK with depth, and what matters for real games is the deep end.
You measure the curve on one tree: the same switch set at a shallow, a middle and a deep node count.

### What to build
Commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT of that commit; Release build with g++ and
`-DFORGE_NNUE_HIDDEN=256`) plus `opus_r13/p1/packc28/packc28_port.patch` from branch `opus-r13-p1-nearmiss-ports`
(`patch -p1`). Known answers: no option `bench 11` 312866, `bench 13` 862329, `go perft 5` 4865609; with
`AspFailHighReduce 1`, `AspFailHighMaxReduce 3`, `EvalSwingMult 24`, `EvalSwingMax 200`: `bench 13` 690187.
The four options are NOT in the `uci` answer of this patch, so the match program never sends them: the cand side
runs through a wrapper script that sets them first (the form another helper used: a script that prints the four
`setoption` lines and then passes on everything it receives to the engine), and `bench 13` THROUGH the wrapper
must print 690187 before any match.

### The matches (the same exe on both sides; cand = the four options through the wrapper, base = none)
    C     control at 20,000 against 10,000 nodes, no options, 300 games, seed 7250: near +200
    M1    nodes=5000      3,000 games   seed 7251
    M2    nodes=80000     1,000 games   seed 7252
    M3    nodes=80000     1,000 games   seed 7253   (the second seed of the deep point)
    M4    nodes=5000      3,000 games   seed 7254   (the second seed of the shallow point; only if time is left)
The 20,000-node point exists already (+18.7, two seeds, two helpers): do not replay it.
Deep games are four times as long as yours so far: start M2 right after M1 and give M2 and M3 the largest part
of the budget; if the time does not reach, M3 is cut, not M2.

### The report
First line in plain words: the gain of packc28 per node at 5,000, at 20,000 (the known +18.7) and at 80,000 nodes,
each with its 95 % pair interval, and whether it shrinks with depth. Say in the FIRST paragraph what was cut or
not reached. One table of all matches; the wrapper check; the probes; Step 0; files opened; stamps; what you did
not do; what you are not sure about; a better way; model.
