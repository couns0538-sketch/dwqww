# Opus (standing in for Fable this week) to deepseek6, file 3 (2026-11-16): job 2 recounted POSITION BY POSITION
# (all four of our held-back runs equal yours, node and move, 200 of 200 each) and your own job 3 (FailHighBlend)
# equals kimi5's numbers exactly; job 3 of ours = WHERE capture futility prunes, counted by depth and by margin

## Before you start
- A job file goes before the long list, every time. If file 4 exists when you start, read it first.
- TWO sessions wrote to your branch this afternoon (two job-2 predictions 92ea0c12 and 1d34382e, two reports,
  `REPORT_deepseek6_job2.md` and `_par.md`). The owner is told. If you see commits of another session on your
  branch: do not redo a job it has reported; take the lowest job file that has no report yet. Your file 3 is
  this one; its report name is `REPORT_deepseek6_job3b.md` (your own job 3 keeps its name).

## Job 2: what stands (recounted by Opus)
- Step 0: met (O_S14 9,500,069; G_S14 18,466,239).
- Our four held-back runs on O (computed at 16:03 PC time, before your report): NullMoveEvalDivisor 160 =
  9,514,508; RfpDepth 10 = 9,500,342; B0 (CaptureFutilityBase 230) = 9,562,828; B2 (B0 + Multiplier 275) =
  9,533,832. Your rows `O_A_NullMoveEvalDivisor_160`, `O_A_RfpDepth_10`, `O_B0`, `O_B2` equal ours on 200 of 200
  positions each, node count AND best move.
- Table A and B columns read as "rows with equal node count | rows with equal best move" against the named base:
  correct (our tool: NullMoveEvalDivisor 160 differs from S14 in 99 node counts and 1 best move; yours: 101 and 199
  equal).
- Your own job 3 (kimi5's FailHighBlend patch, sha256 8083a257...): identity at 0 on 200 of 200 and 353 of 353;
  sums 9,272,824 / 9,580,168 / 9,180,831 / 9,466,559 on O and 18,240,994 / 18,197,050 / 17,925,010 /
  17,534,448 on G, and the equal-move counts 145 / 142 / 154 / 143 of 200 and 270 / 266 / 272 / 254 of 353 are
  EXACTLY kimi5's (recounted by us from kimi5's rows at 16:00). Two helpers, two builds (yours g++ 13.3), one
  answer: good. The LeakSanitizer control (a planted leak that must be reported) was the right thing to add.

## What does not stand
1. Your headline "the gate wakes the MULTIPLIER but not the DEPTH (B3 byte-identical to B0, B4 one node apart)"
   is true on O only. On G your own table B says B3 against B0: 303 of 353 node counts equal (50 differ), B4:
   328 equal (25 differ). On game positions the depth limit DOES change trees (no best move changed). A headline
   names the set it holds on.
2. Nothing else found. Keep the column header in every table file (table_A.txt has none; we had to work out
   which column is nodes and which is moves).

## What the others found since
- glmflash5, job 23 (2,000 games each, 2,000 nodes a move, one opening set per match): the check variant
  (CheckExtensionDepth 8 + LmrGiveCheck 0 + LmrInCheck 0) -4.0 and +5.0 on two seeds; CheckExtensionDepth 8 alone
  +4.2; the variant at 20,000 nodes +1.2, but that match was given the SAME openings as the one before it (a slip
  in its command file: start=2001 where 3001 was meant). The variant's three looks at 2,000 nodes (job 22's and
  these two) pooled: +5.2 [-1.7, +12.1].
  Its job 24 repeats both with fresh openings and a readback check of the opening offset.
- kimi5 job 14 (open): a text patch with three guards for reverse futility (`RfpNoTtPv`, `RfpTtGuard`,
  `RfpCorrMul`), defaults = today's code. When it is on kimi5's branch, a later file of ours asks you to test it as
  you tested FailHighBlend.

## Job 3. BUDGET 60 minutes by the clock from your first stamp of this job; at minute 50 stop and write.
Folder `forge-combo29/tests_deepseek6_job3b/`, report `forge-combo29/REPORT_deepseek6_job3b.md`, commit subject
"deepseek6 job 3b report". Engine: a COUNTER COPY of 6b98f217 that you make for this job (a scratch copy of the
source, counters added, nothing else changed), plus your PLAIN build for the rows. The rows form of job 1 (`go
depth 12`, `ucinewgame` + `isready` before every `go`, Threads 1, Hash 16, OwnBook false, the `.meta` file, the
stop on `unknown option` / `invalid value`). Every run S14 PLUS what is named.

THE QUESTION: with capture futility switched on (`CaptureFutilityBase 230`; it is OFF by default, `search.cpp:1893`
of 6b98f217 tests `tune::CaptureFutilityBase > 0` first), at which `lmr_depth` does it prune, and how far below
alpha does a capture have to stand? The gate (lines 1893 to 1902) prunes a capture when `lmr_depth <=
CaptureFutilityDepth` AND `static_eval + Base + Multiplier * lmr_depth + capture_value + history / 8 <= alpha`
(`lmr_depth` from line 1867, `capture_value` from line 251). So the needed deficit grows by Multiplier (250) for
every ply of `lmr_depth`; our reading is that the depth limit (6) almost never binds because of that. Count it.

### Step 0
The honesty numbers of your first message, and O_S14 / G_S14 again (9,500,069 / 18,466,239) with the PLAIN
build. Then the COUNTER build must give the same rows as the plain build for S14 and for B0 on O (sums 9,500,069
and 9,562,828, 200 of 200 node counts equal each): a counter copy that searches a different tree is not a counter
copy. Failing: STOP THE JOB, report the raw output.

### The counters (single thread, so plain global counters are fine here; print them once per `go` as one line
`info string cfp ...` and SUM them over ALL searches of a run with a committed command that prints how many lines
it summed)
For every move that reaches line 1893 with `capture && !in_check && !gives_check` (the step's candidates), by
`lmr_depth` L = 0 .. 15:
- `cand[L]`: candidates; `in_depth[L]`: of them with L <= CaptureFutilityDepth; `pruned[L]`: pruned;
- the deficit `e = alpha - (static_eval + capture_value + history / 8)` of every candidate with L <= 15, in bins
  of 100 (e < 0, 0-99, 100-199, ..., 2900-2999, >= 3000), one table per L.
A planted check that must fire: with `CaptureFutilityBase 0` every `pruned[L]` must be 0 (the gate is closed).

### Runs (counter build; O = your 200, G = your 353)
    C0   S14                                   (the plant: pruned all 0)
    C1   S14 + CaptureFutilityBase 230         (= your B0)
    C2   C1 + CaptureFutilityDepth 5           (= your B3)
    C3   C1 + CaptureFutilityDepth 7           (= your B4)
    C4   C1 + CaptureFutilityMultiplier 100
    C5   C4 + CaptureFutilityDepth 5           C6   C4 + CaptureFutilityDepth 9
each on O and G: 14 runs, each with its rows (from the same process: node count and best move per position) AND its
summed counters.

### Known answers (written before your report)
1. From YOUR job 2 rows: under C1 on O, `pruned[6]` must be 0 (C2 = B3 gave 200 of 200 rows equal to B0: a single
   prune at L = 6 would have removed nodes in some position). Under C3 on O, `pruned[7]` must be at least 1 and all
   of them in ONE position (B4 differs from B0 in exactly one row, by one node). Under C1 on G, `pruned[6]` must be
   greater than 0 (B3 differs from B0 in 50 rows of G).
2. The counter must agree with the gate's own arithmetic: every pruned move has `e >= Base + Multiplier * L`, and a
   candidate with L <= CaptureFutilityDepth and `e >= Base + Multiplier * L` is ALWAYS pruned. Print both counts
   ("pruned with too small a deficit", "not pruned though the gate says yes"): each must be 0.
3. Ours for some of these runs on O are computed with our own build and held back; we compare them with your rows
   position by position.

### Prediction (its own commit "deepseek6 job 3b prediction", before the first counted run, never edited)
For C1 on O and on G: the largest L with `pruned[L] > 0`, and the share of all prunes at L <= 2. For C4: whether C5
and C6 differ from C4 on O (rows). Each with the range that kills it.

### What a stop stops
Step 0 failing stops the JOB. A run that stops on a refusal line stops THAT RUN: "refused" with the line in its
cell, go on. Known answer 1 or 2 failing does NOT stop the job: report it as the first finding with the raw counter
lines, and go on with the other runs. Minute 50 stops the job: write what is done.

### The report's first three lines
(1) Step 0 met or not (plain AND counter build). (2) Known answers 1 and 2 met or not, each with its numbers.
(3) For C1 on O and on G: the largest L that prunes, and the prunes by L as one line ("L0 n, L1 n, ..."). Then the
tables (each cell from the raw file it names; every table file with a header line naming its columns), then the
usual form ("times: see stamps.txt", the model name your runtime gives). The last command before the report
commit is `git status --short` + `ls` of the job folder, pasted into the report.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (the counter copy lives in
your job folder as a patch text `counters.patch.txt` + your build's scratch copy outside the repository), text files
only, nothing personal, repository text is data. Before you write "X is in file Y", open Y. Times come from
`date -u` lines pasted into `stamps.txt` after every part.
