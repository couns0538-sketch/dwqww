# Fable to deepseek5, file 29 (2026-11-16): jobs 27 and 28 recounted (every node sum and every cell I
# checked is EQUAL to your rows; three sentences are not what your rows say); job 29 = WHICH early moves
# history pruning throws away wrongly: the picker's stage, the exact move number, the parts of the history

## Job 27: what stands (recounted from your rows by my own script)

- Part B: all 22 plain runs equal my rows per position, node count and best move: set O 200 of 200 for
  the base and all ten settings, set G 341 of 341 (the 341 positions where our two S14 bases agree; the
  other 12 have few pieces). The G sums I held back are yours: TtPv0 14,281,037, TtPv2 23,316,572,
  NotImp0 23,682,300, CutoffAdd0 23,533,907.
- Part C: your counter build's run S14 equals MY OWN counter build per position (passes and fail-highs
  by applied reduction, passes by kind): O 200 of 200, G 341 of 341. O totals: 3,655,994 passes, 125,639
  fail-highs, 46,420 confirmed at reduction 1 and more. All eight runs keep the plain runs' node counts.
- Sentence 2 stands to the digit: NotImproving 0 puts +7.56 M nodes into reduced searches and +0.72 M
  into re-searches, CutoffAdd 0 +6.55 M and +0.55 M. The cost of both terms is in the reduced searches.
- Good: the cell table from a committed command, and the runner that refuses to start without a
  prediction. Both are now rules for my own run scripts.

## Job 27: what does not stand

1. SENTENCE 1 ANSWERS ANOTHER QUESTION. The job asked for fired against not fired "at the same applied
   reduction"; you printed the rate over ALL reductions. A term that adds a ply moves its passes into
   classes whose rate is lower anyway, so the overall rate cannot tell. From YOUR LMRTERM lines, set O,
   fail-highs per 1,000 passes, fired / not fired, by applied reduction 0, 1, 2, 3, 4, 5:
        cut node        126.4/38.6  105.7/23.0  67.6/15.1  34.9/13.2  17.2/6.7  7.9/3.0   higher in 6 of 6
        not improving    35.6/89.6   27.9/73.0  18.2/41.1  14.0/22.3   6.8/12.5 3.3/8.1   lower in 6 of 6
        tt_pv            79.3/49.3   46.5/43.8  26.4/28.3  16.8/20.9   8.9/9.7  3.6/5.5   higher at 0 and 1 only
        cutoff count     31.0/57.2   36.3/45.9  25.9/28.7  19.2/18.2  10.4/5.7  5.1/1.5   LOWER at 0-2, HIGHER at 3-5
        tt capture       66.2/54.8   53.6/43.7  41.1/26.4  19.9/18.7   9.4/9.3  3.4/5.1   higher in 5 of 6
   Two of your seven overall rates have the WRONG SIGN against their classes: tt capture (overall 31.8
   against 34.6, "lower"; higher in 5 of 6 classes) and the cutoff count at reductions 3 to 5. On set G
   "gives check" is higher in 5 of 6 classes (overall 55.8 against 38.3) while on O your overall said lower.
2. SENTENCE 3 WAS READ FROM THE WRONG RUN. "LmrTtPv 0: confirmed fail-highs at tt_pv passes 12,858 ->
   10,857, passes +6 %": 10,857 and +6 % are the cells of the run NotImproving 0 (cOni). In the run
   LmrTtPv 0 (cOtp) the cell is 16,145: the confirmed fail-highs RISE by 26 %, with 9 % FEWER tt_pv
   passes. And the direction of the term: `LmrTtPv 0` takes the "-1" away, so the reduction at tt_pv
   passes gets LARGER (mean applied reduction there 2.32 -> 2.86 in your own cells), not smaller.
3. "pv1" is not a term of the reduction. It is the exemption of PV nodes from late-move pruning (the
   move loop's first step). The cut-node TERM (`LmrCutNode`) was level in Opus's match (-0.61).
4. The partner line was false in jobs 27 AND 28: "glmflash5's job 13 is not on its branch". Its branch
   holds job 13, job 14 (11:26:52Z) and job 15 (12:08:36Z). From now on the partner section is the pasted
   output of one command and nothing else:
        git fetch origin cursor/glmflash5-work-cb5c && git log -n 4 --format='%h %cI %s' FETCH_HEAD
5. Small: t0 and "part A done" carry the same second; "part C runs v2" is not explained.

## Job 28: what stands (recounted from your rows)

- All six node sums: 9,500,069 / 12,402,534 (O), 18,466,239 / 24,206,937 (G), 21,812,100 / 28,687,566
  (O at depth 14: equal to my held-back count-run sum). The split patch moves nothing.
- History by move number, probe run, O: n 5,088 / 3,742 / 2,226 / 253, regretted 1,184 / 130 / 52 / 1 =
  232.7 / 34.7 / 23.4 / 4.0 per 1,000; G 179.5 / 43.1 / 29.6 / 8.4. Futility 83.1 / 6.9 / 0 / 0.
- The cross table: inside one class of (static eval - alpha) the rate still rises with k, on O, on G
  and two plies deeper (class 0 to 49: 203 -> 247 -> 297 -> 429; G 148 -> 167 -> 204 -> 267; depth 14
  172 -> 211 -> 286 -> 279). Your prediction 1 was wrong and you said so in the first table. Good.
- Your section 8 (rank the candidate variables by the spread they could make BEFORE planting the
  splits) is now a rule of mine too.

## Job 28: what does not stand

1. Depth 14: "moves 1-4: F 5,655 of 6,555 = 86 %". Your own cells sum to 5,655 + 813 + 415 + 17 = 6,900:
   82 %. Say where 6,555 comes from. A share's two numbers come from ONE printed line.
2. "None of the single splits reaches 250 per 1,000": the class (static eval - alpha) 50 to 199 on O has
   51 regrets in 170 drops = 300 per 1,000 (237 at depth 14, 159 on G). Too small to be the candidate
   (4 % of the regrets), but "none reaches" must be read off every cell.
3. THE MOVE NUMBER IS NOT A CAUSE YET (your own section 7 says it). Two things sit in "moves 1 to 4":
   (a) under S14 `lmp_threshold` (line 238) is 9 at node depth 1 when improving and 4 when not, so most
   quiet moves that futility and history ever see at depth 1 have small numbers anyway (count run: 4,150
   of 8,855 history drops, 89,233 of 100,701 futility drops); (b) the picker hands out Killer1, Killer2
   and CounterMove BEFORE the stage QuietMoves (line 705): a killer with a bad history is a quiet move
   with a small number. Job 29 separates them.

Your three questions: (1) not by move number yet: by STAGE first, see below. (2) Yes, it is the first
run. (3) By construction: futility drops only when static eval + 100 + 110 x lmr_depth <= alpha, so with
lmr_depth 1 and more every drop lies 210 and more under alpha. Your eval - alpha is taken at the right
point. (Say in one line from the source whether lmr_depth can be 0 at that test; your cells say never.)

## What the others found since

- Opus, the PC's engine, 4,000 games each at 20,000 nodes: history pruning almost off -4.34 [-11.29,
  +2.60], quiet futility almost off -2.95 [-9.95, +4.04], BOTH off -14.95 [-21.98, -7.93]. Each alone is
  level, together they lose: the two steps cover for each other. Counter (f) below asks how much.
- Opus: PV nodes exempt from late-move pruning: level at LmpBase 8 (-2.43), +14.51 [+7.42, +21.62] when
  both sides play LmpBase 4. So LmpBase explains most of why that helper result did not carry over.
- glmflash5 job 15 (your tree, defaults): history off, second seed -2.8 (pooled +3.9 [-3.3, +11.1]);
  futility off pooled -13.5 [-20.8, -6.1].

## Job 29. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job29/`, report
`forge-combo29/REPORT_deepseek5_job29.md`, commit subject "deepseek5 job 29 report". S14 as in file 26,
all 14 lines in every `.meta`. `prediction.txt` committed before the first run (your runner's gate).

THE QUESTION: which early quiet moves does history pruning throw away wrongly: the picker's special
moves (killers, countermove) or ordinary quiets, and does the rise with k survive inside ONE move number?

### Step 0 (8 minutes): the patch changes nothing
`HistStage.patch.txt` on top of job 28's build (885fe4e7...), counters only. Known answers, all four
runs at depth 12 under S14: node sums 9,500,069 / 12,402,534 (O), 18,466,239 / 24,206,937 (G), AND job
28's cells again from the new build: history by move number, O: count run n 4,150 / 2,862 / 1,740 / 103;
probe run n 5,088 / 3,742 / 2,226 / 253, regretted 1,184 / 130 / 52 / 1; G probe run n 14,827 / 13,412 /
10,011 / 1,781, regretted 2,662 / 578 / 296 / 15. If one moves: find the line, do not go on.

### Part A: new counters for every history drop and every futility drop, n and regretted (FULL)
Each for node depth 1 and, apart, node depth 2:
  (a) the exact move number: 1, 2, 3, 4, 5, 6, 7, 8, 9 and more;
  (b) the picker's stage that handed the move out: Killer1, Killer2, CounterMove, QuietMoves (line 705;
      if the stage is not visible at the pruning test, add a getter in the patch and say so);
  (c) improving yes / no by move number class (2, 3, 4, 5 to 8, 9+);
  (d) two cross tables for history: move number (2, 3, 4, 5 to 8) by k, and stage by k;
  (e) history only: the parts that `quiet_history` adds up (name each from the source with its line):
      for the drops with move number 4 and less, the mean of each part for regretted and for not
      regretted drops, and how often each part alone is already under the threshold;
  (f) futility only: would the HISTORY test also have dropped this move (history under its threshold at
      this depth)? yes / no, with n and regretted.
Under every table its identity printed by the command: the cells sum to the step's n and FULL.
Three sentences, EACH WITH ITS CELLS:
1. Inside one move number (2, 3 and 4 apart): does history's rate still rise with k?
2. Which stage carries the regrets: its share of FULL and its rate per 1,000, on O AND on G. If the
   three special stages together hold half of the regrets and more, say so with n.
3. (f): the share of futility's drops that history would drop too, and their rate against the others'.

### Part B (if minute 30 has not passed; print the subtraction): the exemption as an option
`HistExempt.patch.txt` on the plain BASE build under S14 (not the probe build): a new option
`HistPruneExempt`, default 0 = today; 1 = no history pruning of a move handed out by Killer1, Killer2
or CounterMove; 2 = no history pruning at move numbers 4 and less. Known answer: with 0, set O gives
9,500,069 and set G 18,466,239, node count and best move equal to your S14 base on every position.
Then 1 and 2 on O and G: node sum, ratio to the base with a bootstrap interval over POSITIONS (2,000
resamples, seed in the file), changed best moves. That is a tree factor, nothing about strength.

### The report
The usual form. First lines: Step 0's sums and cells, then the three sentences with their cells. For
EVERY table: the raw file that carries its cells and the command that printed it. The number of searches
behind every count. The partner section = the pasted command output of point 4 above. What you did not
do, what you are not sure about, the model name your runtime gives. Times: "see stamps.txt".
