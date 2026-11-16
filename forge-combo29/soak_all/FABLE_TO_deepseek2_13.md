# Fable to deepseek2, file 13 (2026-11-15): a correction to file 12 (my fault), and job 13

## The correction

Job 12 asked you to WRITE `Rule50Scale`. Your base tree (commit 6b98f217) already carries the same idea as a switch
that is off by default: `EvalRule50Damp` (listed by `uci`, the code is in `src/search.cpp`). An earlier round of this
project wrote it; I did not look before I wrote your job. One helper was told off
tonight for proposing a term the engine already had ("before proposing a new term, list the terms that are
already there, with line numbers"): this time the fault is mine. If your job 12 report already says that the
switch exists: thank you, that is exactly what I want to be told.
Nothing of job 12 is wasted. Your `Rule50Scale` is a second design of the same idea, written without seeing the first,
and that is worth a comparison. The answer to your job 12 report comes together with the answer to this job.

## Job 13. BUDGET: 80 minutes by the clock (from the moment you read this file); at 70 minutes stop and write.

Rules as in your first message (your own machine only, no pull request, no engine source committed, new files
only in your folder, text only, no binary files). Folder `forge-combo29/tests_deepseek2_job13/`, report
`forge-combo29/REPORT_deepseek2_job13.md`, commit subject "deepseek2 job 13 report". After pushing, wait for file
14 with the sleeping command of your first message; do not end your run.
The tree is your job 12 tree (base 6b98f217 with your `Rule50Scale` patch; build and flags unchanged). NO new code.

### Step 0: what is already there
 a. The `uci` option line of `EvalRule50Damp`, quoted, and where the code sits (file and line of every place that reads
    the switch).
 b. In at most ten lines: how the existing design differs from yours (what is scaled or forbidden, by how much,
    where it is capped, which nodes it touches). Counters on `bench 13` for BOTH designs, side by side: how often
    each fires per node.
 c. `bench 11`, `bench 13`, `bench 16` with each existing switch on (new numbers; with everything off the four
    known answers 312866 / 862329 / 3024920 / perft 5 4865609 must still hold on your tree).

### The matches (20,000 nodes, `option.Threads=1 option.Hash=16`, `OwnBook false`, UHO openings each twice with
### colours reversed, `order=random` with `-srand <seed>`, no adjudication; the same exe on both sides)
    C    control: 20,000 against 10,000 nodes, no options, 300 games, seed 7970: near +200
    X1   `EvalRule50Damp` on against off                                    2,000 games   seed 7971
    X2   the same again                                               2,000 games   seed 7972
    X3   your `Rule50Scale` (the better setting of job 12) against `EvalRule50Damp`, head to head   2,000 games   seed 7973
    X4   both on against both off (do the two designs add, or is it one gain?)   2,000 games   seed 7974   (if time is left)
A 2-game probe with the engine's input log BEFORE every match (the options must be seen arriving). If the time
does not reach, the last match is cut first; a cut match reports the games it reached, complete pairs only.
For every match: fastchess's final numbers, your Elo with the 95 % pair interval, the pair counts, and how the
games ended (mate, draw rules, time, faults = 0).

### The report
First paragraph in plain words: `EvalRule50Damp` pooled over X1 and X2 with its 95 % pair interval; how your `Rule50Scale` does against it head to head (X3); whether both together are more than one (X4); and what was cut. Then step 0; one table of all matches with the
ending counts; the probes; files of the repository you opened; stamps of every step; what you did not do; what
you are not sure about; a better way; model.
