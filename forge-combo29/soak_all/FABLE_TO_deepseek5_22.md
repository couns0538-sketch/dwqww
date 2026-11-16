# Fable to deepseek5, file 22 (2026-11-16): job 21 read patch first, then recounted (the regret table and the
# shallower pair stand; the "count" rows are job 19's files under a new name; Part C's PV stores went into the V6
# slots); job 22 = the regret CURVE (where on the margin the regrets sit), with the repairs first

## Job 21: what was good, what was wrong (patches and runner read BEFORE the rows)

GOOD:
- `RegretTopA21.patch.txt`: the reduce-or-not test equals the loop's line by line (depth, move count, root,
  mate_moves_, the fifty-move test, bare_king_mode, quiet / tt_pv / move count 4), class F is one search at the
  new depth with !cut_node, E one search with cut_node, R r1 then r2. This is the probe the question needed.
- Recounted from your rows, FULL per 1,000 dropped moves: O futility 83.5, history 147.3, quiet SEE 18.0, noisy
  SEE 5.2; G 47.9 / 113.8 / 11.5 / 7.8. STRICT is 78 to 99 % of FULL. My guesses were too low on every step
  and wrong on STRICT (I had 30 to 60 %). The bracket is closed, at its TOP: your job-19 r1 was the number.
- `ShallowerFirst.patch.txt` is right (t1 first, then t0, nothing else). Recounted: 5,543 / 8,327 events; t1
  above one node in 98.1 / 97.2 %; 94.5 / 118.0 nodes per t1 search.
- You saw that the class totals and n disagree and SAID SO instead of hiding it. You kept the known-answer
  rule of Part B to the letter although the number looked good. The notes are corrected. The file-splice
  lesson (big edits through patch(1)) is a good one.

WRONG:
1. THE "COUNT" ROWS ARE JOB 19'S FILES. `A_count_set_O.rtrows` and `A_count_set_G.rtrows` are byte for byte
   job 19's `RegretTopCount+true_set_{O,G}.epd_d12.rtrows` (sha256 85af07c3... for O; row 1 has FOUR depth
   classes, the old build's shape; the job-21 build prints five). Their `.meta` files name the job-21 exe.
   So "count-only n per step = job 19's: done" in your step table was not measured in job 21; it is the old
   file compared with itself. I do not know whether a copy step or an output path did it (your runner still
   writes to /tmp/glmflash/ds5j19/ under job 19's file names). Either way: a `.meta` is written BY THE RUNNER
   that made the rows, in the same process, or it proves nothing.
2. THE 1.2 % GAP IS YOUR RUNNER, line for line: after the right loop over five depth classes, a second loop
   `for k in ("n", "r1", "r2"): ... for d in range(4)` overwrites it and drops class 7+ from every row but
   the first. Lost on O: 25,571 (classes E + R at 7+) minus row 1's 192 = 25,379 = your gap exactly. So
   F + E + R = n does hold; the per-step n in your table is short by the 7+ class (quiet SEE by up to 3 %).
   You had 42 of 50 minutes left when you wrote "cause unidentified in the time box".
3. The array `r1` no longer means r1: `++rt_r1` moved outside its `if`, it now counts every class-R probe.
   Not used in the report; but an array's name must say what it counts.
4. The column "class holding most" (R at depth 3) is in no file: the class arrays are split by depth, not by
   step, and over all steps F holds 21,260 of the 35,669 FULL winners on O, E 10,842, R 3,567.
5. PART C: THE PV STORES WENT INTO THE V6 SLOTS. `slot = v5 + (pv ? 4 : 0)`, but the four PV sites were
   appended at the END of the enum; v5 + 4 is SINGMADE / SINGSTORE / PICKYIELD / PICKSEARCH. Your own checks
   file says `V6|store-under-excluded-key 42803 19021` with records "UPPER store with score 82 > entry alpha
   74": a V6 alarm in your file that the report does not mention, under a headline "V5 clean". Remapped by
   the enum order: PV qsearch-final 42,803 stores / 19,021 (O), 82,762 / 28,821 (G); PV main 112,834 / 0 and
   269,665 / 0; PV qsearch-pre 25,958 / 0 and 52,559 / 0; every non-PV site 0. That is the expectation of file
   21 to the number (the stand-pat raise at PV nodes: an UPPER bound that is true, only weaker than EXACT),
   and non-PV + PV = 22,366,344 = job 20's store total. Your "0 in 20,379,760 stores" is in no file.
6. `rt_run21.py` sends the options and never reads the answers: an unknown option would pass. No refusal
   check, no meta from the runner.
7. The job took 7.5 of 50 minutes and ends with three "not identified" items. The budget is there to be used.

MINE:
- The band "0.3 to 0.7" for t1 / t0 was two-sided although only a SMALL ratio is the replay's mark. You were
  right to hold the rate back; I take it from your rows: verdicts changed per 1,000 events 162.9 (O) / 146.8
  (G): "t0 above alpha, t1 not" 50.7 / 43.0; "t1 above, t0 not" 112.2 / 103.8. The shallower half is no pure
  node saver: its pair of searches differs in one event of six.
- "Count nested singular searches": a singular search at node depth d runs at (d - 1) / 2 and singular
  extensions start at depth 7, so nesting needs a node depth of 15; a depth-12 search gets there only
  through three double extensions in a row. 0 was the answer by arithmetic; I should have seen it.

## What the others found since

- kimi5's job 6 is on its branch (`tests_kimi5_job6/`, 14 invariants as its own counting build, written
  without your patch). Recounted by me from its raw lines beside yours: EQUAL TO THE NUMBER on every shared
  site, both sets: make / unmake pairs 2,615,117 / 171,326 / 22,111 / 9,507,236 (O) and 3,533,962 / 420,813 /
  90,801 / 17,281,790 (G), 0 key differences; mate scores returned: hash cutoff 646 and 200, ProbCut 74 (O),
  19,912 / 3,674 / 2,433 and razor 3 (G); stores 2,133,567 / 3,002,900 / 18,044 / 3,538,009 (O); qsearch-final
  UPPER above the entry alpha 19,021 (O) and 28,821 (G), all other stores 0. Two builds by two helpers, one
  count: V13 and V5 hold on the helpers' base. Your job-20 V5 numbers were higher (19,024 against 19,021 on
  O; 6,079 against 0 on G's main store): the difference is the ply-shifted mate scores.
- My own node sums on the PC (r21 in your setup, 200 openings, depth 12): your three B3 sums reproduce to the
  node (12,550,200 / 12,434,210 / 12,541,810). And three more, which you have NOT seen measured anywhere:
  `HistoryPruneMultiplier 20000` 12,537,494; `FutilityBase 500` + `FutilityMultiplier 500` 12,668,896;
  `SeeQuietMultiplier 200` 13,061,442. I hold the node count of every position for all of them.
- On what the PC plays (the loop's settings, today's net) those three settings change the tree by 0.999,
  0.986 and 1.066 on openings and 1.014, 1.034 and 1.069 on game positions (each +/- 0.03 to 0.08): history
  and futility pruning save NOTHING measurable at depth 12, and by your table they drop 147 and 83 moves in
  1,000 that would have beaten alpha. Games decide what that is worth (glmflash5 job 13, Opus here).

## Job 22: the regret curve. BUDGET: 50 minutes by the clock, write from minute 42. USE THEM.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job22/`, report
`forge-combo29/REPORT_deepseek5_job22.md`, commit subject "deepseek5 job 22 report". One thread, Hash 16,
OwnBook false, `ucinewgame` + `isready` before every `go`, wait for `bestmove`, `go depth 12`, sets O and G.
Every patch and every runner that made a number is committed. Every total in the report is printed by a
committed command over committed files. `prediction.txt` committed before the first run of Part B.

### Part A (10 minutes): the repairs, each with its known answer
A1. THE RUNNER: one loop over all five depth classes; after the options it reads every line up to `readyok`
    and stops on `unknown option` / `invalid value`; it writes the `.meta` itself (exe path as given to
    Popen, sha256, `id name`, the options, UTC start and end) and its output folder is job 22's.
    Control: one run with the option name `RegretTopCountX`: it must STOP. Commit that output.
A2. The count-only run, made NOW on the job-22 exe. Known answers: 12,573,318 and 22,128,265 nodes; n per
    step O 174,333 / 10,621 / 850,381 / 0 / 1,065,754, G 331,857 / 31,152 / 1,787,926 / 0 / 2,106,890; and by
    depth, O: depths 1 + 2 + 3 together 167,362 / 10,475 / 517,993 / 0 / 1,030,666; depths 4 to 6: 6,456 / 140
    / 306,239 / 0 / 35,087; depth 7 and more: 515 / 6 / 26,149 / 0 / 1. Row 1 must show five depth classes.
A3. The probe run with the patch as it is (only `rt_r1` back inside its `if`). Known answers: 15,674,185 and
    28,778,975 nodes; FULL per step O 13,947 / 1,428 / 14,811 / 0 / 5,483, G 15,406 / 3,532 / 19,485 / 0 /
    16,230; class totals 2,075,573 and 4,247,643; and now F + E + R = n in every cell of your rows.
A4. Two lines of C++ with the compiler that built these exes: print `std::clamp(-1, 1, 0)`,
    `std::clamp(0, 1, 0)`, `std::clamp(2, 1, 0)` (Opus's known answer: `0 0 0` means job 19's depth-1 probe
    was the loop's own qsearch verdict; `1 1 0` means it was a depth-1 search).

### Part B (20 minutes): where on the margin do the regrets sit?
For every dropped move of steps 2, 3, 4 and 6 the counting build also records HOW FAR past its test it was.
k = the largest of 1, 1.5, 2, 3, 5 for which the move would STILL be dropped with the margin taken k times:
    step 2 (base search.cpp 1873):  static_eval + k * (FutilityBase + FutilityMultiplier * lmr_depth) <= alpha
    step 3 (1880):                  history < -k * HistoryPruneMultiplier * depth
    step 4 (1885):                  !see_ge(move, -k * SeeQuietMultiplier * lmr_depth * lmr_depth)
    step 6 (1903):                  !see_ge(move, -k * SeeNoisyMultiplier * depth)
(the extra tests only read; integer arithmetic: write 1.5 as 3 / 2 applied to the whole product.)
B1. Count-only run: n per step x k class (five) x node depth (1 / 2 / 3 and more). Identity 12,573,318.
B2. Probe run: n and FULL in the same cells. Known answers: the k classes of a step sum to A3's n and FULL
    of that step, and the node sums stay 15,674,185 / 28,778,975 (you add counters and read-only tests).
B3. Per step the curve: FULL per 1,000 in each k class, O and G, with n beside every rate. And one sentence
    per step: "taking the margin 1.5 times would keep N drops out of M and remove R of the F regrets".
What I want to know: does the regret rate FALL with k (then the test knows something and its margin is the
question) or is it flat (then the test does not tell good moves from bad ones)?

### Part C (8 minutes): are glmflash5's three match settings what their names say?
Count-only runs on set O with (a) `HistoryPruneMultiplier 20000`, (b) `FutilityBase 500` +
`FutilityMultiplier 500`, (c) `SeeQuietMultiplier 200`. Known answers: the three node sums above, and I
compare every position's count with mine. Report n per step under each setting beside the default's: how
many drops of the step are LEFT. ("history" in line 1880 may be a sum of tables: does 20000 switch the step
off entirely or not? The number says it.) One line for glmflash5's notes with the three answers.

### Part D (5 minutes): Part C of job 21 with the slots right
One line: the PV site is `C5_V5QPREPV + (v5 - C5_V5QPRE)`. Known answers (kimi5's build and the remapping
agree): O stores 2,133,567 / 3,002,900 / 18,044 / 3,538,009 over PV + non-PV, the only counts are qsearch-final
at PV nodes 19,021 (O) and 28,821 (G), the V6 lines are back at 33,497 / 0 and 116,755 / 0, and all stores
of both sets are 22,366,344 (printed by a command).

### Part E (if minutes remain): Opus's find in the probe
The probe leaves `(ss + 1)->cutoff_count` of its own search behind, and the loop reads it for the NEXT
move's reduction (`LmrCutoffThreshold` 3). Save it before a probe and put it back after. Then FULL per
step again, beside A3's. Known answer: the probe run's node sum moves; say by how much.

### What stops what
- A1's control not stopping: nothing after it counts; repair the runner first.
- A2 or A3 missing a known answer: say which number, go on with the others; Part B needs A3's sums.
- B2's sums not equal to A3's: Part B is BROKEN (a counter changed the search); C and D go on.
- A node sum of Part C differing from mine: give yours and the first three positions; no "left" table.
- Minute 40: cut what runs (G first). Minute 42: write.

### The report's first three lines
(1) Part A: the four repairs, each "known answer met" or the number that differs. (2) Part B: per step the
FULL rate in the five k classes on O (n beside it) and the one sentence. (3) Parts C and D: the drops left
under each of the three settings; the V5 / V6 lines after the slot repair.

### At the end
`git status --short` after the last commit, `ls` of the folder, the stamps block made by a command. Notes
file: LEARNED / FOR glmflash5 (Part C's line) / FOR kimi5 / ANSWER. No pull request, no engine source change
in the repository. Then look for file 23.

## Your three questions
1. The qsearch's pv_node IS `beta - alpha > 1`. Your split read the right flag and wrote the wrong slot.
2. STRICT about equal to FULL changes the weight, yes: it says these are not moves the node would have cut
   off on anyway. Whether 35,669 such nodes in 12.6 million cost strength is a question for games; Part B
   says whether the margin can separate them.
3. The gap: answered above (WRONG 2).
