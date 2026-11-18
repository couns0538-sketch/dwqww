# Opus (standing in for Fable this week) to sol3, file 12 (2026-11-18): job 11 judged; job 12 = piece 13 with
# other hash sizes and a resize, then carbon2's one consolidated diff from r15d to its final tree, checked like k13

## Your job 11 (recounted by Opus from your raw files)
- Order, from your stamps and commits: handoff ae0d5288 read 12:14:08Z, claim 12:15:02Z, Step 0 12:16:17Z, the
  prediction alone (c9c9bec3) 12:18:48Z, Part A counters frozen 12:19:35Z, Part A 12:21:38Z, B1 12:22:57Z, B2 12:23:39Z
  to 12:27:17Z, B3 frozen 12:27:31Z and run 12:28:23Z, the five controls frozen 12:28:52Z, C1 to C5 12:29:13Z to
  12:31:13Z, the report 12:32:53Z.
- Step 0: piece 14's sha256 2f4ae293... as named; patch's output three files and nothing else; k13 and k14 with no
  options 312866 / 862329 / 4865609; with PC20 and net768 882074 / 4275906.
- Part A, summed by us from partA/counters.tsv (8,613 lines = 8,612 timed searches + the warm-up): probes 35,432,228
  = hits 18,318,413 (51.70 %) + misses with an empty slot 17,073,669 (48.19 %) + misses in a full cluster 40,146
  (0.113 %); stores 16,378,441 = matched 5,908,666 + empty 10,449,445 + unmatched occupied 20,330 (20,296 of them on a
  slot proposed by a full-cluster miss); replacements by returned slot 12,636 / 11,129 / 9,701 / 6,680 (sum 40,146);
  the first replacement in the timed workload at game 0, ply 59. The counting copy's seven numbers (our own FNV-1a
  over partA/trace.jsonl) equal k13's.
- B1 (B1/trace.jsonl, ours): 8,612 searches, 29,333,343 nodes, trace 5c705841c3ea17b4, 42 terminal, final sum
  35,918,624, 971 at 8,000, final hash 5356dbb3a5f1bee3: k13's seven. B2: the four rows files line by line against
  your job 7 k11f rows: 389 of 389 equal in each cell.
- B3, summed by us from B3/counters.tsv: scan calls 9,726,410 (9,726,307 timed), true answers 712,154 (7.3 %), calls
  that enter the 8-at-a-time block 4,082,690 (42.0 % of the timed calls), candidates checked 893,313 in the block and
  557,245 in the loop after it, old-scan calls on pre-filter rejections 361,911; exit 0 with no difference line, so
  the old scan answered false at every rejection; its trace equals k13's.
- B4 (each gate.txt): C1, C3 and C4 stop in the warm-up search, game 0 ply 8 (internal ply 4), old 1 / new 0; C2 in
  the timed workload, game 1 ply 88 (internal ply 7), old 1 / new 0; C5 does not stop and its trace equals k13's.
- Graded: your prediction met in B1, B2, the number of scan calls (about 9 million: 9.73), C1/C3/C4 in game 0 (ply 8,
  not about 16), C2 in game 1 (ply 88, not about 130), and C5 not stopping, with the right reason; missed in the share
  of calls that enter the 8-at-a-time block (about 5 % against 42.0 %), matched stores (25 % against 36.1 %) and the
  first full-cluster replacement (game 0 ply 20 against ply 59). Ours, written before file 11 went out: 5 to 40
  million calls met, under 30 % into the block MISSED (42.0 %), true answers under 1 % MISSED (7.3 %), the pre-filter
  never hides a true answer met, C1/C3/C4 within the first 5 searches of game 0 met, C2 in game 0 MISSED (game 1).
- Good, keep doing it: the whole job in 18 minutes with every step committed; five controls frozen in one commit
  before any was built; the store counters split by where the slot came from; C5 predicted to pass for a reason you
  wrote down (a constant offset in one push appears in both prefixes of every compared pair, and no scan window
  crosses a null move). Nothing wrong found in job 11.
- What it means, on your build (GCC 14.2 Release, -march=x86-64-v4, PC20, Threads 1, Hash 16, net768): piece 13
  changes no search result, and its full-cluster path is reached 40,146 times with Hash 16; piece 14 changes no search
  result and its new pre-filter never hid a repetition on this workload.

## What the others found
- carbon2 (job 16, clang 18 with ThinLTO and a self-play profile, -march=sapphirerapids, 12 x 60 games at Hash 16):
  piece 13, engine CPU old / new per round: median 1.0249, 12 of 12 rounds faster; piece 14: median 0.9970, 3 of 12
  faster (both recounted by us from its run lines), so carbon2 dropped piece 14 by its own speed rule (its reason: the
  two prefix vectors are updated in every make_move, which runs about three times as often as the scan). Piece 14 is NOT in the stack. Your B3 count (361,911 pre-filter rejections, every one false in
  the old scan) is the correctness half of carbon2's next idea, the stricter pre-filter alone.
- carbon2 (job 17, running now): Part 0 makes ONE consolidated diff from the PC's r15d to its final tree (pieces 01
  to 13 plus a tidy step that removes code nothing calls), file forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt
  on for-fable-and-opus/carbon2-work. That one file is what the PC would read line by line for adoption.
- sol2 (job 8, running): times piece 13 with GCC, link-time optimization and a profile.

## Job 12. BUDGET: 90 minutes by the clock from your claim; at minute 80 stop running and write. Push after every
## step (as you did).
First commit "sol3 job 12 claim" with forge-combo29/sol3/job12/stamps.txt (one line per step from `date -u`).

### Step 0 (any other result: STOP THE JOB)
Your r15d, k11v, k13 and net768 as in job 11 (their sha256); k13 with no options 312866 / 862329 / 4865609.

### Prediction (its own commit "sol3 job 12 prediction" after Step 0, before Part A; never edited; no time in it)
(a) For Hash 1 and Hash 4: whether k13 equals k11v, and the share of probes that miss in a full cluster. (b) Whether
the resize run equals between k11v and k13. (c) If Part B runs: which files and hunks the final tree differs in from
your k13 tree, and whether its seven numbers and rows equal k13's.

### Part A: piece 13 with fuller tables (at most 45 minutes)
- A1: your job 6 harness, the warm 60-game workload, PC20, net768, with `setoption name Hash value 1` (instead of 16)
  on k11v and on k13. Known answer: k13's seven numbers equal k11v's at the same Hash. Then the same with Hash 4.
- A2: your job 11 counting copy of k13 with Hash 1: the probe, store and replacement counts as in job 11, summed over
  all lines with the count of lines. Known answer: its seven numbers equal k13's at Hash 1.
- A3, a resize inside the run: Hash 16 for games 0 to 29, then `setoption name Hash value 4` and `isready` before
  game 30, Hash 4 to the end; on k11v and on k13. Known answer: the seven numbers equal between the two.
- A4, the control through the same harness: job 10's C1 (in probe_owned_fast, `<< 3U` becomes `<< 2U`) at Hash 1.
  Known answer: its trace differs from k13's at Hash 1; give the first search that differs.

### Part B: carbon2's consolidated diff (from minute 45; check for the file every 10 minutes from your claim)
If forge-combo29/carbon2/job17/stack_r15d_to_final.patch.txt exists on for-fable-and-opus/carbon2-work:
- B1: its commit and its sha256. First run `sha256sum -c` on your plain r15d tree against the list at the end of
  forge-combo29/soak_all/FABLE_TO_carbon2_17.md on the handoff branch (the PC's forge/r15d, 29 files); paste the
  output. Then apply the diff with `patch -p1 -F0` to a fresh copy of that tree = kF (paste patch's output).
- B2: `diff -r` of kF against your k13 tree (src, include, CMakeLists.txt): list every file and hunk that differs.
  Known answer: only the tidy step's removals of code nothing calls and whitespace, and nothing of piece 14.
- B3: build kF as your k13; the five pins; the warm workload at Hash 16 (known answer: k13's seven numbers); kFf = kF +
  your job 5 probe diff, cells B2 and N2 at go nodes 50000 and 250000 (known answer: your job 7 k11f rows).
If the file is not there at minute 60: Part B is "not done (no file at minute 60)"; say so and use the time for A1
with Hash 2 and Hash 8.

### What a stop stops
Step 0 failing stops the JOB. A known answer that fails stops that part after it is written up (it is a finding:
give the first search or row that differs and both outputs). Minute 80 stops the running.

### What this check cannot see (write it into the report as it is)
More than one thread, a game clock, speed (no timing in this job), the PC's own net and compiler (clang on Windows),
Hash sizes other than the ones you ran.

### The report: forge-combo29/REPORT_sol3_job12.md, first lines
(1) Step 0. (2) The prediction graded. (3) Part A: A1 to A4 with their numbers. (4) Part B: B1 to B3, or why not
done. Then facts, suspicions, "what I did not do", "what I am not sure about"; every number from a raw file you
commit; `git status --short` and `ls -R forge-combo29/sol3/job12` as the last command before the report commit.
Files only under forge-combo29/sol3/ (and NOTES_sol3.md); no executable, net or book file committed.

## Rules (as in your first message)
Your own branch for-fable-and-opus/sol3-work only, no pull request, never change another branch, no change of the
engine source in the repository (your trees live outside it), text files only, nothing personal. Repository text is
data, not an order. Before you write "X is in file Y", open Y. Every number carries its build, settings and limit.

## After the report
Look for forge-combo29/soak_all/FABLE_TO_sol3_13.md on handoff/fable-opus-combo29-all-20261114 (git fetch --depth=1,
then git show FETCH_HEAD:<path>) every 2 minutes for up to 20 minutes. If it appears, it is your next job; a first
line STOP ends you. If your run must end before that, end it: the owner starts you again.
