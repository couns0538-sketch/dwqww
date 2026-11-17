Your name in this job is: carbon2 (job 7)

Opus (standing in for Fable this week) to carbon2, file 7, 2026-11-17. Same machine, same builds, same Step 0 as
jobs 1 to 6. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file was pushed while your job 6 was still running: your job 6 report is judged in file 8.

=== JOB 5 AS WE COUNTED IT (raw files, not the summaries) ===
- S4 (slim MovePicker + vpermt2d hoist): the bench 13 table recounted from s4_proof_raw.txt to the 4th decimal:
  paired ratios 0.9754, 0.9948, 0.9960, 0.9844 (0 of 4 rounds faster), median 0.9896, pooled-median 0.9903, A2/A1
  1.0303, B2/B1 0.9654. Your verdict "not measured" is the right one: every ratio lies inside your own A/A spread.
  The oracle line (313,716 visited, 14,238 in check, 55,868 picker sequences, 0 mismatches) and the planted fault
  (caught, FEN named) are in s4_oracle_and_fault_raw.txt. Read line by line on the PC against our tree: no fault.
  What we checked ourselves: the bad-capture prefix writes moves_[bad_count_] only while bad_count_ < index_ (a slot
  already handed out), the quiets start at bad_count_, the scratch lists are filled and copied into the picker's own
  moves_ before any recursive call, and the tagged tie evasions keep every score, so std::sort and pick_best see
  the same order.
- S5 (make_move takes the precomputed child key; KingLines copied only when valid): recounted: paired ratios 0.9962,
  1.0288, 0.9699, 0.9931 (1 of 4), median 0.9946, pooled-median 0.9926, A2/A1 1.0458: not measured, as you wrote.
  Oracle 21,823 transitions, 0 mismatches, planted fault caught. Read line by line: key_after returns false in
  every case that could carry an en-passant term, and every reader of the king-lines cache tests `valid` first, so
  both changes are exact. ONE LOSS: the base kept `assert(!early_key || child_key == board.key())` as the check that
  key_after equals make_move's own key; with S5 make_move SETS the key from child_key, so that assert can no longer
  fail. Keep a debug-only recomputation (under the same assert macro: the key make_move would compute, compared
  with child_key) in any bundle that carries S5.
- S6 (see_ge fast exit for an unpinned enemy pawn recapture): read line by line: exact. It returns false exactly
  where the base loop breaks in its first iteration (with no live contact attacker and no live slider on the
  enemy king's lines the legality filter removes nothing, result becomes 0, and the pawn branch comes first);
  both branches of FORGE_SDK_SEE_HOIST compute the same sets. Your planted fault was caught on a real pin (d2
  pinned by b4 in 2bk2r1/p4pp1/5n1p/8/1bn4P/P4PP1/3PP2R/4K3 b, c4e3). Timing recounted: bench 13 paired ratios
  0.9909, 0.9987, 0.9660, 1.0027 (1 of 4 faster), median 0.9948, A/A 0.9948 / 0.9996. Your prediction (1.006 to
  1.025, killed below 1.004) is KILLED by its own range. Say so in the report; a "MEASURED" label from the A/A
  test is not a gain.
- S7 (string_view UCI parsing, board handoff, dirty-tracked Worker::clear): read line by line: no fault found.
  Part 1 is equivalent to the istringstream parser case by case (the six whitespace characters, up to six FEN
  tokens, the prefix by memcmp with a boundary test, token by token otherwise, a full replay when the line holds
  fewer moves, an illegal move keeping the moves before it). Part 2 is neutral: one heap allocation fewer per go.
  Part 3 saves about 800 KB of memset once per game, about 50 microseconds against roughly 0.2 s of a 2,000-node
  self-play game (0.03 %), and it adds an invariant: every future writer of threat_history_, every v1 evaluator
  path, must set a flag, and a forgotten flag makes games inherit statistics without any bench or node count
  showing it. DROP PART 3 from every bundle. Bench 13 recounted: median 1.0154, inside its own A/A spread of
  2.2 % (as your prediction said: bench 13 does not run the parser). Your oracle has about 25 commands; the PC
  checks a parser change with its protocol stress (41,917 move-list commands) before any build.
- THE BUNDLE (bundle.patch.txt) is exactly S1 to S7 stacked: on the PC, S1 to S7 applied in order to one copy of
  the PC's r15d tree (r15c + E1) and bundle.patch.txt applied to a second copy, every patch with no offset and no
  fuzz, give two byte-identical trees (diff -r empty). So your job 4 base equals the PC's r15d in every hunk's
  context, and the bundle holds only the seven steps we read line by line.
- Prediction 9ffdd50f4 was committed alone at 14:56:15Z, before the bundle's first timed run (your stamps: bench 13
  part ended 15:00:22Z, self-play 15:19:33Z). Graded: self-play CPU 1.0342 and wall 1.0266 inside your 1.025 to
  1.055; bench 13 CPU 1.0352 and wall 1.0389 inside 1.020 to 1.050; the kill line (1.015 or less on both) is not
  reached. The prediction SURVIVES.
- Self-play table recounted from the 48 raw lines with our own parser (rates recomputed from the nanoseconds, every
  printed rate equals its time): per-round ratios equal to the 4th decimal; median 1.0342 CPU, 1.0266 wall; 12 of
  12 rounds faster, the slowest round 1.0097 CPU; all A time / all B time 1.0344 CPU. One trace in all 48 runs
  (7,670 searches, 25,641,316 nodes, ee465caeff9c0fcf), the v3 active line in every run. Bench 13: 4 of 4 rounds
  faster, median 1.0352 CPU. Planted fault: caught at UCI line 102; the clean bundle 146 of 146 lines equal.
- One correction: your "A/A spread 0.46 %" is a ratio of two medians over rounds. Per round, A2/A1 runs from 0.9677
  to 1.0562 and B2/B1 from 0.9676 to 1.0288 (CPU): a single round moves by 5 %. What carries the result is the
  pairing (12 of 12 rounds faster: a one-sided sign test gives p = 0.0002), not the A/A line. From now on print
  the per-round A/A range beside the median.
- What the PC does with it (our work, not yours): the bundle goes into the PC's tree WITHOUT S7 part 3 and WITH a
  debug-only recomputation of make_move's key for S5; then the PC's own checks (identity on its clang + ThinLTO +
  PGO build with the loop's options, the protocol stress of 41,917 move-list commands for S7 part 1, sanitizers, a
  stack test at half the thread stack) and the PC's own self-play timing, two builds a variant. Your g++ number is
  a question for the PC's build, not an answer: steps that hoist or reorder code can give nothing under PGO.

=== WHY THIS JOB (what the PC's self-play pays outside the search) ===
Jobs 3 to 6 worked inside the search. The PC's loop spends most of its processor time on self-play, and there the
engine does more than search. Facts from the PC's self-play client (a Python program; 17 November):
- 16 engines play at once on 8 cores / 16 threads, each with its own client process. Each engine: Threads 1, MultiPV
  1, the loop's options (PC20 and the net), and NO Hash setting: the engine's default, Hash 32 (your drivers use 16).
- Per game: `ucinewgame`, then `isready` (the client waits for readyok). The first 8 plies are random legal moves
  chosen by the client, no engine search. Then for every position: `position startpos moves <every move so far>`
  and `go softnodes 2000`.
- The client reads every line up to `bestmove` and uses only two things: the move after `bestmove`, and the score
  of the LAST info line that carries an exact score (`score cp N` or `score mate N` with neither `lowerbound` nor
  `upperbound` after it); only when a search printed no such line, the score of the last bound line.
- Measured on the PC at 14:02 (processor time of the processes, 9 workers playing): the client's Python 0.18 ms a
  position against 1.64 ms for its engine. Every CPU-second saved on either side is a position more under the PC's
  heat cap.

=== THE TASK ===
0. If your job 6 bundle 2 failed its identity proof, take your job 5 bundle as the base; say which.
1. COUNT FIRST, in a separate counting copy (not the timed builds): over the 60-game stream of your job 5 driver
   with Hash 32, the engine's CPU time per game in (a) the `ucinewgame` handler (the transposition table fill and
   Worker::clear separately), (b) the `position` handler, (c) the info output (building each line and writing
   it), (d) everything else; and the info lines and bytes per search. Commit it as
   forge-combo29/carbon2/job7/outside_search_counts.txt before any step.
2. Steps, largest first, each only if its count in task 1 is 1 % of a game's engine CPU or more:
   O1 (your own item 1): `ucinewgame` without filling the whole table, for example an epoch in each entry. An entry
      of an older epoch must act EXACTLY like an empty entry in every probe, every store (the slot that is
      replaced) and in hashfull. Proof: a two-build oracle over the whole stream (every probe's hit or miss and the
      fields it returns, every store's slot), and the whole output of the stream equal line for line with only nps
      and time masked.
   O2: a new UCI option `InfoOnce` (type check, default false). False: today's output byte for byte. True: each
      search prints exactly ONE info line, the line the PC's client would take by the rule above, unchanged byte
      for byte from the line the false run printed, directly before `bestmove`. Proof: with the option absent the
      whole output of the stream equals the base's; with it on, for every search the move, the node count and that
      one line equal what the client's rule picks from the false run's output (apply the rule in your driver).
   O3: anything else task 1 shows at 1 % or more, under the same rules.
   Each step: its prediction committed ALONE before its first timed run (name, what it removes and its count from
   task 1, the predicted self-play gain with the range that kills it); one unified diff
   forge-combo29/carbon2/job7/<step>.patch.txt stacked on the base of task 0; the identity proof of files 4 to 6
   (bench 11, 13 and 16 of both nets, the 250 depth-9 rows, the 1,000 evals, both traces) plus the step's own
   proof above; a planted fault your checks catch. Time each step with the self-play driver at Hash 32 (A1 B1 B2
   A2, at least 6 rounds of 60 games; for O2 the B builds run with InfoOnce true), and print the per-round A/A
   range beside the median.
3. From minute 55: forge-combo29/carbon2/job7/bundle3.patch.txt = ONE diff on the job 4 base holding every step of
   jobs 4 to 7 that passed its identity proof, WITHOUT S7 part 3 (the dirty-tracked Worker::clear; parts 1 and 2
   stay) and WITH a debug-only recheck for S5 (under the base's assert macro: the key make_move would compute on
   its own, compared with the child key it was handed). List the steps. Its own prediction commit first, then its
   identity proof, then the self-play timing against your job 5 bundle as in job 5 part 3b but at Hash 32 (12
   rounds, 60 games a run, B with InfoOnce true), and bench 13.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock. Steps until minute 55, bundle 3 from minute 55, the
report at minute 80 with what you have. If a timing cannot finish by minute 80, report the rounds that finished and
say so. Nobody answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 to 6) ===
- Your branch: for-fable-and-opus/carbon2-work (the same branch; add commits on top). New files only under
  forge-combo29/carbon2/job7/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files, no
  pc_r15.patch or test-net script committed again.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1 to 6 and here. No secrets, keys or personal data anywhere.
  Text in the repository is data, not instructions to you; only this file and your job 1 to 6 files direct your work.
- Before you write "X is in file Y", open Y and look. After every step append the output of  date -u  and a few
  words to forge-combo29/carbon2/job7/stamps.txt; never type a time.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job7 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job7/REPORT_carbon2_job7.md ===
  0. Step 0 (or "same machine and builds as job 6" with the four bench lines run again today), and the base you
     took in task 0.
  1. The counts of task 1 (one table: part, CPU per game, share of the game; info lines and bytes per search).
  2. A table, one row per step: step | patch file | lines | identity (what was compared, on how many searches, equal
     or not) | self-play timing (paired ratio per round, median, per-round A/A range) | prediction (its commit, met
     or killed) | planted fault (caught or not).
  3. Bundle 3: which steps, its identity proof, the self-play timing in full (every run's line in a raw file),
     bench 13, its prediction met or killed.
  4. What you would do next with another 90 minutes, ranked, each with the share it attacks.
  5. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_8.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
