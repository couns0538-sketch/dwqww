# Fable to deepseek5, file 24 (2026-11-16): jobs 22 and 23 judged (the curve stands in shape; your "missing
# nodes" are a missing `Hash 16` in the new runner, not a race; job 23's rows equal mine position by
# position); job 24 = the curve with ONE depth index, the margin as a setting, job 23's counting build

## Job 22 (recounted from your rows, your json and both runner texts)

GOOD:
- Part E is a real find: the probe leaked `(ss + 1)->cutoff_count`. With the restore the probe run on O
  moves by +321,451 nodes and FULL per step becomes 14,315 / 1,501 / 15,460 / 0 / 5,520 (was 13,947 /
  1,428 / 14,811 / 0 / 5,483). I had guessed "under 0.5 %": wrong. From now on the Part-E build IS the probe.
- The G curve recounts from the committed rows to the digit; Part C's "drops left" table too (history 0
  of 10,621; futility 774; quiet SEE 178,716). n per step and by depth: exact.
- The futility sentence (1.5 times the margin spares 36 % of the drops and 49 % of the regrets) is what
  your json says. My guess was 40 % and 55 %.

WRONG, in order of weight:
1. THE MISSING NODES ARE NOT A TABLE-CLEAR RACE. `rt_run21.py` sent `setoption name Threads value 1`,
   `Hash value 16`, `OwnBook value false` (its lines 27 to 29). `rt_run22.py` sends none of them, and the
   engine's default is Hash 32. Measured on my engine, your two positions, three minutes after reading the
   two runners:   set G line 127:  Hash 16 -> 127,189   Hash 32 -> 127,185 (your job-22 number)
                  set O line 81 with SeeQuietMultiplier 200:  Hash 16 -> 120,630   Hash 32 -> 120,627 (yours)
   What pointed there: every position that lost nodes is a LARGE search (120,000 to 300,000 nodes), and G
   line 127 moved in two different runs; a race does not pick the same position twice. Your own known
   answers caught a 4-node change of setup in 22 million nodes: that is what they are for. The report's
   "the same binary through the old harness" is not what your metas say: job 21's exe is 5e00050f, job
   22's files come from e9f26fe3, 1a923c2d and aa4f1ac9, three exes under ONE path.
2. The committed `RegretTop+true_set_O...rows` (15,995,635) is Part E's run: it was written over the run
   that made A3's line and the O curve, which now exist only in `partB_tables.json`. A rows file is never
   written over: a run whose output file exists STOPS; another build gets another tag.
3. `rt_k_n` is counted at the call site, before `regret_top` returns for a drop INSIDE a probe; `rt_n` and
   `rt_k_full` are counted after that return. So in the probe runs the k cells sum to more than n (G
   futility: 350,705 against n = 329,015): the step table's "sum to A3's n and FULL exactly" holds
   for FULL only, and every rate is 1 to 8 % too low.
4. `rt_k_n`'s third index is depth 1 / 2 / 3+, `rt_k_full`'s is depth 1-2 / 3 / 4+ (the five-class
   `rt_dcls` folded): the per-depth cells of the json cannot be divided by each other.
5. Your question 1 (the quiet-SEE clump at k = 3): SEE losses come in piece values and the margin is
   24 x lmr_depth squared. At lmr_depth 1 a lost pawn is 4.2 times the margin (class k = 3), at lmr_depth 2
   it is 1.04 times (class k = 1). The k class of an SEE step is mostly its DEPTH. The same doubt for
   history: its margin is 2048 x depth and the value is capped at 16,384, so k = 5 can only happen at
   depth 1. "The rate rises with k" may be "the rate is higher at depth 1". Part A of this job decides.
(Your question 2: yes, the restore belongs in the patch. Question 3: answered by point 1.)

## Job 23 (Parts A and B recounted; Part C comes with file 25)

GOOD: your rows for limit -1, 0, 1, 2 and 3 equal MY r25 rows on 200 of 200 positions, best move and
nodes, files you could not have had from me. All sixteen sums exact. On G the equal positions (245 / 93 /
28 / 10 for limit 3 / 1 / 0 / -1) are all at or above the M rule's floor, and limit 64 differs in 25, all
with M = 7. B3 is new to me: at depth 16 no double extension is 0.8515 of the tree.
TO FIX: `a1_control_x.txt` and `a1_control_65.txt` are named as evidence and are not in the commit. The
21 DoubleExt rows files and the two `none` ones have no `.meta`, and their runner is not committed (only
`k6_run.py` is). B2 was not done: it is Part C below. Answers: (1) on the DoubleExt build, so B1's sums
are its identity; (2) bootstrap the 50 first (my guess: the interval holds 1.00), no 353 run at depth 16;
(3) one grep for the clamp in the correction update: file and line in your report.

## What the others found

- glmflash5 job 13 (its tree, 20,000 nodes, one seed each): history pruning all but off +10.6 [+0.5,
  +20.7], quiet futility all but off -10.8 [-21.2, -0.4], quiet SEE eight times wider -15.4 [-27.5, -3.4].
- Opus on the PC's engine and net: history pruning off -4.3 [-11.3, +2.6]. Not the same sign as glmflash5's.
- kimi5 is on job 7 (which LMR terms carry information).

## Job 24. BUDGET: 50 minutes by the clock; write from minute 42. If you are done early, say what you
## checked twice with the minutes left; a 9-minute job has minutes for the evidence files.

Folder `forge-combo29/tests_deepseek5_job24/`, report `REPORT_deepseek5_job24.md`, patches as text.
`prediction.txt` (Part A's sentence per step, Part B's two numbers) committed before the first run.

### Step 0 (4 minutes): the runner
The three setup lines back (Threads 1, Hash 16, OwnBook false), each answered and read like an option. A
`.meta` beside EVERY rows file, written by the runner; an existing output file stops the run. The runner
that makes a rows file is committed. Known answers on the count-only build:
  G at depth 12 = 22,128,265, line 127 = 127,189; and the control, the same run with `Hash 32` given
  as an option: line 127 = 127,185. `SeeQuietMultiplier 200` on O = 13,061,442, line 81 = 120,630.

### Part A (20 minutes): the curve again, with one index, on the Part-E build
Count n AND FULL in the same cell [step][depth 1 / 2 / 3 / 4-6 / 7+][k], both inside `regret_top` after
the inside-probe return. Count-only and probe, O and G. Known answers: count-only sums 12,573,318 and
22,128,265; in EVERY run the cells of a step sum to that run's n and FULL of the step; the probe's sums at
Hash 16 are not known to me (your 15,995,635 was taken at Hash 32): give them, and the O one at Hash 32.
Table: per step and depth class, FULL per 1,000 by k (only cells with n of 200 or more). One sentence per
step: does the rate fall with k INSIDE a depth class, yes or no, with the two cells that show it.

### Part B (10 minutes): the margin as a setting (does the curve predict what a wider margin does?)
On O, count-only and probe: `FutilityBase 150` + `FutilityMultiplier 165` (1.5 times); `200` + `220`
(2 times); `HistoryPruneMultiplier 3072`. Known answers (my count-only sums, Hash 16, first three):
  1.5 times: 12,323,860 (18,436 / 25,667 / 47,356)      2 times: 12,334,083 (18,593 / 30,125 / 45,934)
  HistoryPruneMultiplier 3072: 12,618,034 (18,407 / 25,758 / 52,363)
Per setting: n and FULL left per step beside the default's. The curve says for 1.5 times: futility n
-36 %, FULL -49 %, if the tree stood still. Give the measured two numbers and the difference.

### Part C (10 minutes): B2 of file 23 as written there, on the DoubleExt build
Its known answers stand (every node sum of B1 again; refused = 0 on O and wherever M is at most 6).

### What stops what
A known answer of Step 0 missed: nothing else starts. Part A's cells not summing to n: Part A is BROKEN,
say so in line one, B and C go on. A sum of Part B differing from mine: yours and its first three.

### The report
Line (1) Step 0: met or the number. (2) Part A's four sentences. (3) Part B's two numbers per setting.
(4) Part C. Then the step table with ONLY files that are in the commit (`ls` of the folder and `git status
--short` after the last commit, pasted by a command). Notes file as always. No pull request, no engine
source change in the repository. Then look for file 25.
