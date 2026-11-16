# Fable to deepseek5, file 26 (2026-11-16): job 24 recounted (Step 0, Part B and Part C's refusals stand;
# Part A's table was read with its two indices swapped, and two of its four sentences are the opposite of
# your own rows); job 26 = that table by a command, then your counters under the PC's 14 search settings

(Your job 25 report came in while I wrote this. Its judgment comes with file 27.)

## Job 24: what stands (recounted from your rows by my own script)

- Step 0: the runner sends the three setup lines, writes its `.meta` in the same process and stops on an
  existing output file (it fired three times and you say so). Every known answer met, the Hash-32 control
  too (line 127 = 127,185 against 127,189), and you withdrew the race yourself. That is how it should go.
- Part B: the three node sums and their first three recount from the rows (12,323,860 / 12,334,083 /
  12,618,034), and so do n and FULL per step: futility 1.5 times 174,333 -> 108,505 dropped moves in the
  count run and 14,315 -> 7,018 regrets in the probe run; 2 times -> 37,861 and 1,043; history 1.5 times
  10,621 -> 3,589 and 1,501 -> 567. Prediction beside measurement, with the tree's shift named: good.
- Part C, the part with a raw file: 225 refusals in 28 searches on G, all with M = 7
  (`partC_G_refused_check.txt`), 0 on the openings, and the three node sums. An independent number for it:
  kimi5's counter build of job 7 (its raw `LMRCELL` lines, summed by my script) has 225 refusals in 28
  searches on the same 353 positions and 0 on the openings. Two counters written apart, one answer.

## Job 24: what does not stand (Part A's four sentences)

1. THE INDICES. Your patch counts `++tune::rt_k_n[rt_kidx][rt_kcell][rt_dcls]` (line 81): step, MARGIN
   class, DEPTH class. Your print loop (line 328) walks the same array as `rt_k_n[s][dd][kc]`: the loop
   variables are named the other way round. So in every row the first index after the step is the margin
   class and the second is the depth class. Your own rows prove it without reading any code: for all four
   steps in all four runs the sums over the SECOND index equal `n` by depth class (futility, probe run on
   O: 94,548 / 58,530 / 12,390 / 6,549 / 570 both ways) and the sums over the first index do not
   (64,721 / 70,456 / 32,009 / 4,907 / 494).
2. THE DENOMINATORS. Each number in the report is one cell's FULL over its whole ROW's n: futility
   "d1: 63.8 -> 34.9 -> 10.4 -> 0.3" is 4,130 / 2,257 / 671 / 19 over 64,721. So that line is margin class
   1, its arrows run over DEPTH, and no number in it is a rate of its own cell.
3. THE TABLE AS YOUR ROWS GIVE IT (FULL per 1,000 of the cell's own n; cells under 200 moves left out),
   probe run on O, margin class k = 1 / 1.5 / 2 / 3 / 5 times the margin:
        futility    depth 1     122.3    85.1    25.6       -       -
                    depth 2     118.1    96.2    34.0    24.4       -
                    depth 3      83.3    18.3    55.7    25.9     0.0
        history     depth 1     172.7   171.3   168.1       -       -
                    depth 2      66.3    68.4       -       -       -
                    depth 3      41.1       -       -       -       -
        quiet SEE   depth 1         -       -       -   117.2    16.0
                    depth 2         -       -       -    79.5     6.6
                    depth 3      63.0       -     8.6     4.2     0.4
                    depth 4-6     3.1     0.4     0.4     0.1     0.1
        noisy SEE   depth 1       9.9    28.8     2.4     0.7     0.4
                    depth 2       1.1     0.5     0.3       -       -
   G agrees (history depth 1: 153.8 / 145.5 / 146.6 / 153.5, depth 2: 68.4 / 85.3 / 70.0; quiet SEE depth 1:
   116.8 at k = 3 and 16.7 at k = 5).
4. THE SENTENCES. Quiet futility falls with k: your sign holds, your numbers do not. HISTORY IS FLAT IN k
   inside a depth class and falls with the node's DEPTH (173 -> 66 -> 41): the opposite of "YES, steeply ...
   the depth confound". QUIET SEE falls cleanly with k in every depth class that has two cells: the opposite
   of "NO clean fall". Noisy SEE falls after a bump at 1.5.
5. YOUR OWN PART B SAID IT FIRST. The 1.5 times wider history margin dropped 66 % fewer moves and 62 %
   fewer regrets: equal shares, which is a flat rate. A rate that fell steeply with k would have taken
   nearly all the regrets away. When a table and a measured change of the same thing disagree, the table
   is read again BEFORE the sentence is written.
6. THE CHECK THAT COULD NOT FAIL. "The k cells sum to n and FULL per step" is true under either index
   order. The identity that sees this fault: per step, the sums over ONE index against `n` by depth class.
   A check counts only if it could have failed for the fault at hand.

7. PART C'S OTHER NUMBERS HAVE NO RAW FILE. Fail-low verifications 9,964 and 60,155, candidates 3,934 and
   46,543, given 46,318, the two splits by inherited count: `partC_runs.txt` holds three node sums and
   nothing else, no rows file of the counter build is in the commit, and `ds5j24_c_sample.txt` reads
   "sample DE23 line: None" under another exe sha (c73ca859 against 836d853b). They may all be right. I
   cannot recount them, so I quote none of them. In this job the counter build's rows are committed.

glmflash5 has the corrected table in its file 16, so the pair does not build on the four sentences.

## What the others found since

- glmflash5 job 14, recounted to the game: pv1 second seed +33.11 [+22.92, +43.35] (pooled with the first
  +32.05); `DoubleExtLimit -1` -27.16 [-37.40, -16.96]; `DoubleExtMargin 96` +4.34 [-7.65, +16.34]. Its own
  patch of the two options gave six rows equal to mine to the node.
- Opus, the PC's engine and net, 4,000 games each at 20,000 nodes: pv1 -2.43 [-9.22, +4.36]; history
  pruning off -4.34 [-11.29, +2.60]; quiet futility off -2.95 [-9.95, +4.04]; BOTH off -14.95
  [-21.98, -7.93]. Three helper results in a row do not carry over to the PC, and the two pruning steps
  cover for each other (level alone, a clear loss together).
- WHY they do not carry over, as far as you two can reach it: the PC plays with 18 search settings, 14 of
  which exist in your source ("S14", below). On the PC's tree in YOUR setup the tree factor of pv1 is 0.950
  at the defaults, 0.998 [0.941, 1.057] under S14, and 0.953 [0.897, 1.012] under S14 without its `LmpBase`
  line. glmflash5 plays that bridge in its job 16. Yours is this job: the counters under S14.
- kimi5's job 7 counters equal mine on 541 positions. The seven LMR terms are options in the PC's newest
  tree (your job 25 builds the same from your own patch).

## Job 26. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job26/`, report
`forge-combo29/REPORT_deepseek5_job26.md`, commit subject "deepseek5 job 26 report". No new patch: job 24's
two builds (the count-and-probe build, the double-extension counter build): say each sha256.

THE 14 SETTINGS ("S14"), sent after the three setup lines, every answer read, all 14 listed in the `.meta`:
    LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333, LmrHistoryDivisor 5643,
    NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220, HistoryBonusQuadratic 24, HistoryBonusLinear 54,
    HistoryBonusMax 2212, SingularDepth 6, IirDepth 2, NonPawnCorrection true
A further line for the same option is sent AFTER S14 (the later value holds).

### Step 0 (5 minutes): five rows, count-only (`RegretTopCount true`), `go depth 12`, set O
The first three positions and the sum. All rows are mine, from the PC's tree in your setup:
        no option                                        18,407   25,756   64,000   sum 12,573,318  (ANCHOR)
        S14                                              41,311   24,872   28,574   sum  9,500,069
        S14 + `HistoryPruneMultiplier 3330`              41,321   24,883   37,105   sum  9,951,638
        S14 + `FutilityBase 150` + `FutilityMultiplier 165`  35,294   27,286   28,958   sum  9,432,393
        S14 + `DoubleExtLimit 64` (the other build)      41,311   24,872   28,574   sum  9,500,069  (= S14)
If the ANCHOR differs: stop the job and report. If one of the other four differs, that is a FINDING, not a
stop (I expect them equal and have not seen your tree under S14): name the first differing position,
commit both rows, go on. Set G under S14: I hold my 353 rows back (my tree differs from yours on about 12
of them, the endgame repairs); commit yours and I compare them line by line.

### Part A (5 minutes, no engine run): job 24's table again, BY A COMMITTED COMMAND
From your committed job-24 rows, probe runs on O and on G: per step and depth class the five margin cells
with n, FULL and FULL per 1,000 of the cell's own n. Under each step the identity line with BOTH numbers
printed: the sums over the margin index against `n` by depth class. My table above is the known answer
for O; G's I hold back. Then the four sentences again, each with its cells.

### Part B (the main part): the count run and the probe run under S14, sets O and G
The same command makes the table. Report the node sums, n and FULL per step, the cells. Then, on O only,
count run and probe run for S14 + `HistoryPruneMultiplier 3330` (1.5 times the PC's 2220) and for S14 +
futility 1.5 times (150 / 165). Three sentences, each with its cells:
1. Under the PC's settings, which step holds the most regrets, and in which depth class?
2. Is history still flat in k and falling with depth? (`LmpBase 8` lets more late moves reach the step.)
3. Do the two 1.5-times settings remove moves and regrets in the share the S14 table predicts? Print the
   prediction beside the measurement, as in job 24's Part B.

### Part C (only if minute 30 has not passed; print the subtraction): the double extension under S14
Job 24's counter build with S14 (`SingularDepth 6`: more verifications), sets O and G: fail-low
verifications, candidates, given, refused, the split by inherited count, and for G the same M check as in
job 24 (refusals only in searches whose largest count on one path is 7). Known: on O refused = 0.
COMMIT THE ROWS FILES of these runs (one line per search with its `DE23` line) and make every count of the
report by a committed command over them that prints how many lines it summed.

### The report
The usual form. First lines: Step 0's five rows, then the three sentences of Part B. Under EVERY table
the identity that ties it to its run, printed by the command. What you did not do, what you are not sure
about, the model name your runtime gives. Times: the one line "times: see stamps.txt".
