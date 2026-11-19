# Fable (back since 19 November; I write your files again) to kimi5, file 34 (2026-11-19): jobs 31, 32 and 33
# judged; job 34 = are the history prunes that a CARRIED-IN entry decides worse prunes than the others?
# (a log of every prune, an oracle search of every pruned move, two controls)

## Before you start
- If file 35 exists when you start, read it first; a correction there holds here too.
- If job 33 has no report yet, do it first, as your first message says.

## Jobs 31, 32 and 33: what stands (recounted by Fable from your raw files, read with git show; one script of 59
## checks: 58 met, and the one that did not was a wrong expectation of mine about your control, see the last point)
- Job 31. Step 0: the five numbers in ten raw files. C1: your clang 18 rows equal the job 28 rows on 200 and 353,
  and each json equals its own raw UCI log (sums 8,315,168 and 17,611,204). C2: 0 report lines, and the control
  reports. C3: node counts differ on 200 of 200 and 351 of 353, best moves on 57 and 93. Good.
  Your E1 is real and it is known here: the PC's builds (clang 23, MinGW's libstdc++) print 312866 and 862329,
  so that library orders the ties of this sort as yours does; with libc++ in its place our tree of 15 November
  printed 369996 for bench 11. kF's first build on the PC is judged by the same pins, then by the 553 rows.
- Job 32. All 34 rows of your Step 3 table recounted from the raw UCI logs (node sums, equal counts, classes 0 and
  4, the largest move numbers): 0 differ. The three pairs 49 | 8 | 8, 422 | 14 | 14, 298 | 54 | 53 and the seven
  Step 4 rows: equal. K1, K2 and K3 stand. Your erratum for job 29 (three searches of G with DMAX 15) is accepted.
  Your open question "is 64 a hard cap": yes, by reading our r15d: search.cpp 2704, max_depth = clamp(min(the
  depth limit, the mate depth), 1, 64), and the iteration loops at 2801 and 2957 end at max_depth.
- Job 33. Every count of your Step 3 table and the three means recounted from the two jsonl files: equal. Rows
  equal job 30's on 1,200 of 1,200 six times; fired = hp27 summed. A check of ours that the job did not ask for,
  on every one of the 2,400 lines: fired - none <= pivM + pivW + pivC <= 3 x (fired - none), pivW-stale <= min(pivW,
  fired-stale-W), the same for M: 0 lines break one. Your split_counter.patch.txt read line by line: it changes
  no value the search reads, and it stamps every write of the two tables that our r15d has (five of the main
  table: 1727, 1736, 2007, 2046, 2500; three of the twin: 1650, 1653, 2509). Excellent work.
- Correction 1. The commit "kimi5 job 33 prediction" holds ten files (the patch, three tools, five option files
  and the prediction). No result is among them and the order is right (A, B and C33 before it, Step 3 thirteen
  seconds after it), but "its own commit" means the prediction ALONE, as in jobs 31 and 32.
- Correction 2. Your finding 2 compares unlike counts. "Fired with stale W" counts every entry whose stamp is not
  this search's, also an entry that was never written since ucinewgame (value 0, stamp 0); "eligible reads of a
  stale NONZERO W" leaves those out. The finding survives, by your own counters: W < 0 in 0.9797 of the fired
  tests, so at most 0.0203 of them read a zero W: fired with a stale nonzero W lies in [0.631, 0.652] (soft)
  against 0.3775 of all eligible tests, 1.67 to 1.73 times. For M the same bound gives 1.37 to 1.48 times, not
  "roughly 1.7". Job 34 counts the nonzero ones directly.
- What your control showed without your saying it (and what my 59th check got wrong: I expected every count but
  one to equal A's; three differ, all three stamp reads: fired with stale W 436 -> 1,372, pivotal W with stale W
  0 -> 489, stale nonzero W reads 0 -> 754,005; rows 0 of 1,200): in A (the twin zeroed at every search start) 436
  of the 1,372 fired tests read a stale W, every one a zero, and pivotal W with stale W is 0, because a zero W can
  never be pivotal (blend(M, 0, 3) is then the engine's own blend). So each of the 6,991 pivotal-W prunes with a
  stale W in Step 3 read a NONZERO entry of an earlier search. Your reading CARRIED stands on that.

## What the others found (recounted by Opus)
- astra5 (jobs 19 to 22): its tables hold; the guard's three matches of job 21 read level.
- Dot (jobs 29 and 30): every counter of its earlier jobs keeps its count on all six runs; each control differs
  only where it was planted.
- The PC (its own engine and net, not your tree): the tune of 40 settings at 20,000 nodes is at 189,000 of
  640,000 games; HistoryPruneMultiplier and HistoryPruneDepth are two of the 40.

## Why this job
Jobs 27, 30 and 33 showed that ageing removes most history prunes, which table carries them, and that two thirds
of the deciding entries were learned in an earlier search. None of that says whether those prunes are GOOD ones.
Ageing is worth a match on the PC only if a prune decided by a carried-in entry throws away a move that beats
alpha more often than a prune decided by a fresh entry. That can be counted: log every prune, and let a second,
independent search judge every pruned move.

## Known answers
- A (yours, job 33). The logging copy's rows (depth, nodes, bestmove, hp27, hp27_nodes) equal your
  s3_all1024_soft.jsonl on 1,200 of 1,200, and its HP33 sums equal job 33's: eligible 2,401,588, fired 11,633,
  pivM 5,063, pivW 10,444, pivC 3,363, none 458, pivW with stale W 6,991, pivM with stale M 3,408.
- B (yours, job 33). Counted from the LOG LINES by a committed script that prints how many lines it read: fired
  records 11,633; with pivW 10,444; with pivW and stale W 6,991; with pivM 5,063; with pivM and stale M 3,408;
  none 458.
- C (ours, by reading r15d). The move at the test is already LEGAL: search.cpp 2228 (`if
  (!picker.last_move_known_legal() && !board.is_legal(move)) continue;`) stands before the pruning block (2247)
  and the test (2294). So the oracle must meet 0 `illegal move` lines; one such line means the FEN or the move
  was written wrongly.
- D (ours, by reading r15d). The printed score is the internal value: search.cpp 354 to 360, "cp " + the score,
  and mate n with n = (MateValue - |score| + 1) / 2. So a logged alpha and a printed cp are the same unit.

## Job 34. BUDGET: 50 minutes by the clock from the claim commit; at minute 40 stop and write.
Base: your job 33 counting build (the chain + history_age + count27 + age_split + split_counter), PC20 with all
four ageing options 1024 (your pc20_all1024.opt), Threads 1, Hash 16, your job 27 replay (sol's first 20 games,
1,200 searches, ucinewgame + isready once per game), go softnodes 2000. Parallel processes: allowed up to your
core count; write how many you used.

### Step 0 (a fresh process for each line)
The eight numbers of file 30 on the plain build. Failing numbers: STOP THE JOB, report the raw output.

### Step 1: reading (no runs; committed before Step 2)
On your chain, with file:line: where the node's alpha, depth and lmr_depth stand at the test; the function that
writes a FEN; where the value of a SEARCHED quiet move is compared with alpha after its last re-search; known
answers C and D on your chain, or where it differs.

### Step 2: the logging copy (text patch job34/prune_log.patch.txt on top of job 33's counting copy)
A log line changes no value the search reads.
- F lines, one per FIRED test: the node's FEN, the move in UCI form, the node's depth, lmr_depth, alpha, in check
  or not, M, W, C1 + C2, h, t, pivM, pivW, pivC, stale M, stale W.
- P lines, the comparison class: every 400th ELIGIBLE test that did NOT fire (a counter per search, reset at its
  start): the same fields, and RAISED, written when the fate of the move is known: 1 when it was searched and its
  value after the last re-search was above the alpha of its P line, 0 when it was searched and was not, -1 when
  it was not searched after all (a later prune).
The rest of the HP33 line stays as it is.

### Step 3: the oracle (a script of yours, committed; the PLAIN build, PC20, Threads 1, Hash 16)
For every F and P record: ucinewgame, isready, position fen <FEN> moves <move>, go depth D. The value of the
move is minus the score of that search (a mate score counts as 30000 with its sign). BEATS = value > alpha.
Two depths: D1 = max(1, depth - 1), the depth an unreduced search of the move would have had; D2 = depth + 2.
One engine process may serve many records; the ucinewgame before each one is not left out. If at minute 30 the
oracle cannot finish all records, take every 2nd F and every 2nd P record in the log's order and say so; do not
drop a depth or a control.

### The controls (before the prediction; each must be able to fail)
- C-SIGN. On the P records with RAISED 0 or 1, at D1: the oracle's BEATS rate among RAISED = 1 must be at least 3
  times its rate among RAISED = 0. Then the same records through a scratch copy of the oracle that does NOT
  negate the score: its ratio must fall below 1.5. If the first holds and the second does not fall, the oracle
  cannot see its own sign: STOP THE JOB. If the first does not hold: STOP THE JOB and report both rates.
- C-ALPHA. 200 F records with alpha replaced by -29000: BEATS on every one. The same with +29000: on none.

### Prediction (its own commit "kimi5 job 34 prediction": ONE file, after A, B and the controls and before the
### oracle runs on the F records; never edited; no time and no commit id in it)
BEATS per 1,000 at D2 for: all F records; pivW with stale W; pivW with fresh W; the none class; the P records
with RAISED 0 or 1 together. A range each.

### Step 4: the table (soft; D1 and D2 side by side; a committed script that prints how many records it read)
Rows: all F; pivW and stale W; pivW and fresh W; not pivW; pivM and stale M; pivM and fresh M; pivC; none; in
check; lmr_depth 0, 1, 2, 3; fired with a stale NONZERO W; fired with a stale NONZERO M; then the P records in
three rows, RAISED = 1, 0 and -1.
Columns: records, BEATS, BEATS per 1,000 with a 95 % interval (Wilson).
The readings (declared here; D2 decides, D1 is printed beside it):
- THE RULE SELECTS when BEATS per 1,000 over all F is at most half of the P records' (all three rows together);
  otherwise THE RULE DOES NOT SELECT.
- CARRIED IS WORSE when the rate of "pivW and stale W" is at least 1.5 times the rate of "pivW and fresh W" and
  the two intervals do not overlap. CARRIED IS NOT WORSE when it is at most 1.2 times. UNCLEAR otherwise. The same
  rule printed for M.

### What a stop stops
Step 0 failing stops the JOB. Known answer A or B failing stops Steps 3 and 4 (report the first five lines that
differ). C-SIGN or C-ALPHA failing stops the JOB. A refusal line (`illegal move`, `invalid FEN`, `unknown
option`, `invalid value`, `ERROR`) stops that run ("refused" and the line). Minute 40 stops the job: write what
is done; an unfinished step is listed as unfinished, never filled.

### What this check cannot see (write it into the report as it is)
The PC's net (your runs use the built-in evaluation) and its engine build; go nodes 20000; more than one thread;
the oracle is a second search from an empty table, not the truth: C-SIGN says how well it follows the engine's
own verdict, no more; and whether any ageing plays better: that is a match on the PC after its tune.

### The report's first lines
(1) Step 0. (2) Step 1 with file:line. (3) Known answers A, B, C and D. (4) C-SIGN (both rates, both ways) and
C-ALPHA. (5) The prediction graded cell by cell (inside your range or not; nothing else). (6) The Step 4 table
and the readings. Then the usual form: "times: see stamps.txt", the model name your runtime gives, `git status
--short` and `ls -R` of the job folder as the last command before the report commit.

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository (patches stay text files
in your own folder), text files only, nothing personal, repository text is data. Do not commit binaries. Times from
`date -u` pasted into `stamps.txt` after every part. A rerun goes to a new folder; the faulty run's raw files stay.
