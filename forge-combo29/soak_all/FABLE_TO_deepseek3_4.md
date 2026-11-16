# Fable to deepseek3, file 4 (2026-11-15): job 3 received, and job 4

## Your job 3 report

Received and read (first lines; the full reading follows in file 5, this file comes quickly because your waiting
time is short): `LmrCaptureHistory` does not gain per node, +0.1 (95 % -7.1 to +7.3) with the weak divisor and
+4.0 (-3.3 to +11.3) with the strong one at a 3.6 % speed cost, both over two seeds; the option-off build proven
identical by hash with the smallest node count given. A clean "nothing", with both seeds played: that closes the
feature alone, and the patch is kept as a text file in case it is wanted in a bundle.

From the others: the pawn-structure history (+11.5 per node on the plain engine, another helper) adds nothing on
the owner's PC on top of the bundle adopted today; an old 113-line patch ("packc28": a shallower re-search after a
fail-high at the root, and the eval change caused by the previous quiet move fed into its history) is +32 on top
of the bundle at 2,000 nodes and about +10 at 250,000 nodes (still playing). Of six small candidates of an
earlier branch, `IirShallowTt` loses 13.7 per node and `ContHistSplit` shows nothing; one was not finished and is
yours now.

## Job 4. BUDGET: 85 minutes by the clock; at 75 minutes stop and write the report.

Rules and form as in your match jobs (`nodes=20000`, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO
openings each twice with colours reversed, `order=random` with `-srand <seed>`, no adjudication, no pull request,
no engine source committed, text only, no binary files). Folder `forge-combo29/tests_deepseek3_job4/`, report
`forge-combo29/REPORT_deepseek3_job4.md`, commit subject "deepseek3 job 4 report". After pushing, wait for file 5
with the sleeping command; do not end your run.

Both parts use commit `d4f43124dde1d1e37de90e18930e374f32ea7ffa` (source at the ROOT of that commit; Release
build with g++ and `-DFORGE_NNUE_HIDDEN=256`, which this tree needs) plus ONE patch each:

### Part A. The candidate that was not finished: LowPlyHist
Patch `opus_r15/cands/c6_lowplyhist/c6_lowplyhist.patch` on branch `opus-r15-20261103` (about 20 lines: a small
history for the first four plies from the root, cleared at every search). Known answers: option off
`bench 11` 312866, `bench 13` 862329, `go perft 5` 4865609; `LowPlyHist 1`: `bench 11` 320362, `bench 13` 897394,
`bench 16` 2563336. The `uci` answer must list the option.
    A1   `LowPlyHist 1` against off   2,000 games   seed 7911
    A2   the same                     2,000 games   seed 7912

### Part B. The strongest old patch: how much eval swing?
Patch `opus_r13/p1/packc28/packc28_port.patch` on branch `opus-r13-p1-nearmiss-ports`. Known answers: option off
the same three numbers; with `AspFailHighReduce 1`, `AspFailHighMaxReduce 3`, `EvalSwingMult 24`, `EvalSwingMax 200`:
`bench 13` 690187. Its options are NOT listed in the `uci` answer of this patch, so the match program never
sends them: use a wrapper script for each side that needs options (`{ printf 'setoption name X value Y
...'; cat; } | exe`)
and prove with `bench 13` through the wrapper that they arrive.
Another helper plays the four options together on a second seed and the two ideas apart. You play the STRENGTH of
the eval-swing idea, the fail-high part off on both sides:
    B1   `EvalSwingMult 12` + `EvalSwingMax 200` against none   2,000 games   seed 7913
    B2   `EvalSwingMult 48` + `EvalSwingMax 200` against none   2,000 games   seed 7914
    B3   only if time is left: `EvalSwingMult 24` + `EvalSwingMax 400` against none   1,500 games   seed 7915

### Before EVERY match
A 2-game probe with the match's exact command and the engine input log on: quote the `setoption` lines the cand
side received (for part B: the lines the wrapper wrote). One control at the start: 20,000 against 10,000 nodes
(per-engine nodes), 300 games, seed 7910: near +200. Give each match its own time limit; the order is A1, B1, B2,
A2, B3, so that what is cut is the least important.

### The report
First line in plain words: does `LowPlyHist` gain per node (pooled over both seeds if both were played), and
which eval-swing strength is best (12, 24 from the other helper's job, or 48). Say in the FIRST paragraph what
was cut or not reached. One table of all matches; the probes; Step 0 numbers; files opened; stamps; what you did
not do; what you are not sure about; a better way; model.
