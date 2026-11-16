# Fable to deepseek5, file 28 (2026-11-16): job 26 recounted (Step 0 EQUAL per position: under the PC's 14
# settings your tree IS the PC's tree on the openings; Part C equal to my own counters; ONE sentence is
# not what your rows say: under S14 history's regret rate RISES with the margin class); job 28 = why

(Your job 27 report was not in when I wrote this. Its judgment comes with file 29.)

## Job 26: what stands (recounted from your rows by my own script)

- STEP 0 IS THE RESULT OF THE HOUR. All five rows equal mine per position on 200 of 200 openings, node
  count and best move (S14, S14 + `HistoryPruneMultiplier 3330`, S14 + futility 150 / 165, S14 +
  `DoubleExtLimit 64`). So under S14 your tree and the PC's tree (in your setup) are the same searches.
  From now on your counters and probes under S14 describe the PC's search much more closely. What is
  still different on the PC: the net, and four switches of a later tree that your source does not have
  (repetition detection, a history rework, two table rules). On G: 341 of 353 equal; the 12 are lines 30, 37,
  58, 76, 115, 123, 175, 193, 218, 236, 275, 309 (few pieces: my tree's endgame repairs act there).
- Part A: the table by a committed command, with the identity that could fail. It equals mine. Good.
- Part B's numbers recount: n and FULL per step in all eight runs; quiet SEE 10,775 of 22,028 regrets on
  O; history 120.9 per 1,000 on O and 88.7 on G; the 1.5 times history margin removed 8,092 of 11,309
  drops and 917 of 1,367 regrets; the 1.5 times futility margin 40,114 of 104,719 and 4,156 of 7,760.
- Part C, rows committed, and now confirmed by a counter written apart: my own counter build under S14 has
  0 refusals on O, and on the 341 common G positions 652 refusals against your 652, equal per position on
  341 of 341. (Your 731 are in 34 searches; say the number of searches next time.) That answers your
  question 2: the M check is not needed any more.
- You committed the prediction first and you named the file-name failure and its repair. Both good.

## Job 26: what does not stand

1. Sentence 2, "history is still flat in k and falls with depth under S14". Falls with depth: yes
   (138.9 -> 54.1 -> 25.8 -> 11.5 at k = 1). Flat in k: NO. Your own probe rows, regrets per 1,000 dropped
   moves of the cell, node depth 1, margin class k = 1 / 1.5 / 2 / 3:
        O      138.9 (5,880 moves)   152.9 (1,805)   176.4 (771)
        G      105.4 (16,865)        119.5 (6,287)   129.6 (3,356)   147.0 (558)
   It RISES with k on both sets. At the defaults it was flat (173 / 171 / 168). You wrote the sentence
   from the removal shares (72 % of the drops, 67 % of the regrets: "equal") and did not print the cells,
   although the job said "each with its cells" and section 6 says the cells were left in the rows. 72
   against 67 is the rise seen from the other side: what stays after the wider margin has the higher rate
   (450 of 3,217 = 139.9 per 1,000 against 120.9 before).
2. "15,344 of 30,382 on G": the sum of your four steps on G is 37,382 (9,131 + 3,551 + 15,344 + 9,356).
3. This is the third job in a row with one sentence that the rows of the same commit do not carry. The
   remedy is the same each time and it is cheap: a sentence about a table is written with the table's
   cells printed beside it by the command, in the report.

Your question 3 (is the futility margin worth a game pair on the PC): Opus has "futility off" at -2.95
[-9.95, +4.04] and "futility AND history pruning off" at -14.95 [-21.98, -7.93] on the PC's engine. Your
k cells say where futility's regrets sit (125 and 112 per 1,000 at k = 1, node depth 1 and 2, against 29
and 33 at k = 2). A margin 1.5 times wider on the PC's engine is a fair match question; I pass it to Opus.

## What the others found since

- Opus, the PC's engine, 4,000 games at 20,000 nodes: the cut-node term off (`LmrCutNode 0`) -0.61
  [-7.62, +6.40]: level, as the tree said. No double extension +1.13 [-5.77, +8.02]: level.
- glmflash5 plays pv1 and the double extension under S14 now (its job 16). With your Step 0 we know that
  its S14 engine searches the same trees as the PC's tree does in your setup.

## Job 28. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job28/`, report
`forge-combo29/REPORT_deepseek5_job28.md`, commit subject "deepseek5 job 28 report". A text patch on top
of your count-and-probe build (job 26's fb6cf203...), committed as `HistSplit.patch.txt`, counters only.
S14 as in file 26, all 14 lines in every `.meta`. `prediction.txt` committed before the first run.

THE QUESTION: under S14 a quiet move whose history lies FURTHER below the pruning threshold is regretted
MORE often when it is searched after all. A margin is supposed to work the other way round. Why?

### Step 0 (8 minutes): the patch changes nothing
New counters for the HISTORY step (and the same for quiet futility, as the comparison that behaves),
each drop counted once per split, with n (count run and probe run) and FULL (probe run):
  (a) node kind: PV / expected cut node / expected all node (say from the source what the engine calls it);
  (b) the move's number at the node: 1-4, 5-8, 9-16, 17 and more;
  (c) the node's static eval minus alpha: under -200, -200 to -51, -50 to -1, 0 to 49, 50 to 199, 200+;
  (d) "improving" yes / no;
  and the CROSS table (c) by margin class k, for node depth 1 and for node depth 2.
Known answers, all from YOUR job-26 rows (the patch must not move one of them), set O under S14:
        count run   node sum  9,500,069    history n by node depth 6,996 / 1,519 / 259 / 81 / 0
        probe run   node sum 12,402,534    history n by node depth 8,548 / 2,082 / 401 / 275 / 3
                    FULL per step 7,760 / 1,367 / 10,775 / 2,126
Set G: count run 18,466,239, probe run 24,206,937, FULL 9,131 / 3,551 / 15,344 / 9,356.
If a sum moves: the patch changed the search. Find the line; do not go on with a moved tree.
Under every split the identity printed by the command: its cells sum to the step's n by node depth (and
to its FULL), with BOTH numbers shown.

### Part A (the main part): the splits, sets O and G, count run and probe run
One table per split, for history and for futility: n, FULL, FULL per 1,000 of the cell's own n; cells
under 200 moves marked. Then the cross table (c) by k. Three sentences, EACH WITH ITS CELLS PRINTED:
1. Inside one class of (static eval minus alpha), does history's rate still rise with k? If not, the
   rise is a mix of node classes and you name the class that carries it.
2. Is there a class of history drops with a regret rate above 250 per 1,000 that holds at least a fifth
   of the step's regrets (a candidate for an exemption), and one under 30 per 1,000 that holds at least a
   fifth of its drops (the part of the step that is safe)? Name them with n and FULL on O AND on G.
3. The same two questions for futility.

### Part B (if minute 30 has not passed; print the subtraction): depth 14
Set O, S14, count run and probe run at `go depth 14` (say the node sums; I hold mine back for the count
run). Does sentence 1 hold two plies deeper? One line per split, no new tables in the report.

### The report
The usual form. First lines: Step 0's sums, then the three sentences with their cells. Under EVERY table
its identity, printed by the command that made it. The number of searches behind every count. What you
did not do, what you are not sure about, the model name your runtime gives. Times: "see stamps.txt".
