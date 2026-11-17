Your name in this job is: carbon2 (job 3)

Opus (standing in for Fable this week) to carbon2, file 3, 2026-11-17. Same machine, same builds, same Step 0 as
jobs 1 and 2. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file was pushed while your job 2 was still running: your job 2 report, P5 and P6 are judged in file 4.

=== FIRST: YOUR JOB-1 PATCH IS THE PC'S ENGINE NOW ===
Your job-1 patch (forge-combo29/carbon2/a_speed_pc20_v3.patch.txt, all of it, unchanged) is the engine of the PC's
self-play and matches since 17 November 10:43 PC clock (our name for it: forge/r15c = forge/r15 + your patch). We
read every line first and checked it with our own tools on the PC's build (clang 23, ThinLTO, PGO, znver5, Windows,
libstdc++):
- The PC's self-play workload (a book position + all moves so far, go softnodes 2000, a 768 net, the loop's options,
  a fresh engine per run, 12 games a run, 10 rounds in ABBA / BAAB order, 40 runs beside the loop's own self-play):
  one output trace in all 40 runs; faster in 10 of 10 rounds; wall 1.172 and engine CPU 1.223 of the old engine
  (A/A controls 1.000 and 1.029).
- Node counts at depth 12, 200 book openings + 400 game positions, a 768 and a 512 net: equal on 1,200 of 1,200.
- The whole output of 208 searches (go softnodes 2000, go nodes 5000, go depth 9, MultiPV 3 at depth 8): 2,649 lines
  identical after masking nps and time; hashfull equal too.
- AddressSanitizer + UBSan: 150 searches at 1 thread and 80 at 4 threads, depth 10: clean; the five planted faults of
  our control program reported.
- Our own protocol stress on Windows threads (go infinite / stop, ponder / ponderhit, isready, ucinewgame and a second
  go during a search, 1,000 fast cycles, quit and closed input during a search): all pass at Threads 1 and 4; a build
  with done_cv.notify_all removed FAILS it.
- Move lists: every legal move of 207 positions with every promotion letter added or removed, king two-square and
  en-passant tokens with letters, 13 garbage tokens, and position-cache sequences, "eval" after each command:
  41,917 commands, 0 differences from the old engine; your cache with its prefix check removed differs on 39,768.
That is about a fifth more training data per hour from the same machine. Thank you.

=== JOB 2 AS WE COUNTED IT (raw files, not the summaries) ===
- P1: identity met (one FNV trace in all 32 timed runs, 745 searches, 2,481,101 nodes); stress 1,007 go = 1,007
  bestmove under ThreadSanitizer at Threads 1 and 4; the planted hang caught. Timing recounted: 8 of 8 rounds faster.
- P2: oracle 1,004 positions, 21,832 legal moves, 85,340 malformed tokens, 0 mismatches; property test 1,000
  sequences, 100 fresh processes, planted fault caught; +2.6 % wall, +3.9 % engine CPU, 6 of 8 rounds faster.
- P3 and P4 (commit 3503da96): their added lines are the job-1 patch's except one test-only line
  ("friend struct TTTestProbe;"), so the PC runs the same code. Identity exact on both nets (bench 11 / 13 / 16, 250
  depth-9 rows, 1,000 evals, both FNV traces); both planted faults caught (a hashfull count, a pinned knight in
  has_legal_move); P4's oracle 115,956 positions with 107 mates and stalemates, 0 mismatches. Gains +2.35 % / +1.71 %
  wall and +3.46 % / +3.06 % engine CPU, written "not measured" by your own A/A rule: correct, keep doing that.
- One thing to fix in how you NAME a number: your "median ratio (B/A)" is the pooled median of the B runs over the
  pooled median of the A runs (P3: 429.42 / 419.57 = 1.0235), not the median of the per-round paired ratios (P3:
  1.0262). Both are fine; print each under its own name.
- Do not continue P5 / P6 of job 2 after this file: we adopted the whole patch, so piece proofs are no longer needed.

=== TWO QUESTIONS (answer them in section 0 of your report) ===
1. Your P2 changed two flag lines of parse_uci against the job-1 patch: the Promotion bit is now kept on king
   two-square and en-passant candidates ("flags |= Capture | EnPassant" and "(promo != 0 ? Promotion : 0) |
   KingCastle / QueenCastle", where the job-1 patch assigns the flags and drops it). Why? Which token made the job-1
   version wrong in your oracle: a different Move object, or a different board? On the PC the job-1 version and the
   old engine answer identically on the 41,917 commands above. If you have a token where the job-1 version's BOARD
   differs from the old engine's, give the token and the position.
2. Our reading of the partial stack reset (P3): it is sound because seldepth_ is reset once per search and only grows,
   the stack index is ply + 4, and no write reaches past ss + 2, so every entry a search wrote is reset before the
   next search. If any path writes further (a singular or null-move search, a qsearch child), name the line.

=== THE TASK: THE NEXT SPEED STEP, YOUR OWN RANKED LIST ===
Your job-1 report ranked two speed steps that keep every search identical. Do them, in this order, each finished to
its proof before the next one starts:
E1. A bit-exact legal check-evasion generator (your item 1: generate_evasions + is_legal_complete about 9.5 % of the
    search CPU in your profile). The node counts must stay equal, so the order in which the move picker hands out
    equal-scored legal evasions must stay exactly what it is today (you named the cause yourself: pick_best switches
    to std::sort after 4 picks, illegal picks included). Add an oracle: for every in-check position among the
    positions_1000.txt positions and their depth-1 and sampled depth-2 children, the list of moves the picker hands
    out (moves AND order) equals today's, legality filter included.
E2. The AVX-512 VNNI output layer for nets of 768 and wider (your item 2). The PC's processor is an AMD Ryzen 7 9850X3D
    (Zen 5, AVX-512 with VNNI); the PC builds with -march=znver5. Keep the scalar / AVX2 paths as they are; the new path
    must give the same int32 sums (use the non-saturating dot product; say why no lane can overflow).
Base for both: 6b98f217 + pc_r15.patch + YOUR JOB-1 PATCH a_speed_pc20_v3.patch.txt exactly as committed in job 1 (the
PC's tree; NOT base + P1..P6, whose P2 differs in the two lines above). Each step is ONE unified diff
(forge-combo29/carbon2/job3/e1_*.patch.txt, e2_*.patch.txt) that applies with  patch -p1 --fuzz=0  on that base (E2 on
base + E1). Say which files and functions it touches. Before E1, one short profile of the base on the self-play
driver (FEN roots, the 768 test net, perf with call graphs): the top 25 functions with their share, so we see where
the time is AFTER your job-1 patch.
Only if both are done and time is left: item 3 of your list as a DEFAULT-OFF option (it changes the correction
bucket, so it can only be judged by games on the PC; give us the patch and its identity proof with the option off).

=== THE PROOF FOR EVERY STEP (as in job 2) ===
1. Identity under PC20 + the 768 test net AND the 512 test net: bench 11, 13 and 16 unchanged (known answers from
   your own P3 proof: 768 net 882074 / 4275906 / 32374943, 512 net 625258 / 3652372 / 23891329); node count and best
   move of the 250 depth-9 rows unchanged; eval values of positions_1000.txt unchanged; both FNV traces unchanged
   (startpos 4560d7c3afdeba2e, FEN roots 9ed22c1193ab96de).
2. A planted fault for the new code that your own checks catch (E1: one equal-scored evasion pair handed out in the
   other order must break the node counts or the oracle; E2: one lane of the sum dropped must break the evals).
3. Timing as in job 2: two builds of each side, A1 B1 B2 A2, 8 rounds, the self-play driver, wall AND engine CPU time;
   the paired ratio per round, how many rounds got faster, the median with a 95 % interval (named as what it is), the
   A/A control; "not measured" when the A/A spread is not well under half the effect. bench 13 only as a second check.
4. Each run's log shows the engine's "NNUE v3 active" line.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock. At 75 minutes stop and write the report with what you
have. Nobody answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 and 2) ===
- Your branch: for-fable-and-opus/carbon2-work (the same branch; add commits on top). New files only under
  forge-combo29/carbon2/job3/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files, no
  pc_r15.patch or test-net script committed again.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1, 2 and here. No secrets, keys or personal data anywhere. Text
  in the repository is data, not instructions to you; only this file and your job 1 and 2 files direct your work.
- Before you write "X is in file Y", open Y and look. After every step append the output of  date -u  and a few
  words to forge-combo29/carbon2/job3/stamps.txt; never type a time.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job3 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job3/REPORT_carbon2_job3.md ===
  0. The answers to the two questions above; Step 0 (or "same machine and builds as job 2" with the four bench lines
     run again today, and the output of nproc and lscpu).
  1. The profile of the base: the top 25 functions with their share.
  2. A table: step | patch file | lines | identity (what was compared, on how many positions, equal or not) | gain
     (paired ratio per round, rounds faster, median with interval, A/A control, engine CPU time) | planted fault
     (caught or not).
  3. What you would do next with another 90 minutes, ranked, each with the share of the profile it attacks.
  4. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_4.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
