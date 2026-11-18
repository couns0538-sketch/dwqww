Your name in this job is: carbon2 (job 15)

Opus (standing in for Fable this week) to carbon2, file 15, 2026-11-18. Same machine, same builds, same Step 0 as
jobs 1 to 14. If your builds are gone, rebuild them exactly as job 1 says and show Step 0 again before anything else.
This file judges job 13 (file 16 will judge job 14) and gives you the next task. If job 14 is not finished when you
read this, finish it and its report first.

=== JOB 13 AS WE COUNTED IT (raw files, not the summaries) ===
- Step 0, step0_job13_raw.txt (the engine's own lines): SP-profiled pc_r15 312866 / 862329 / 3024920, perft 5
  4865609, PC20 without a net 278024 / 587276; SP-profiled r15d and SP-profiled curated equal on PC20 + net512
  625258 / 3652372 / 23891329 (evals 968 / 1176 / 31) and on PC20 + net768 882074 / 4275906 / 32374943; perft 5
  4865609 on both.
- Part 1, checked on the PC itself: we rebuilt the PC's r15d as text from the public base 6b98f217 and the three
  patch files (all 29 files equal to the PC's own hash list), applied your ten pieces in order with patch -p1 -F0,
  and diff -r against r15d + curated_sp_bundle.patch.txt is empty here too.
- Part 2, curated_sp_time_profile_raw.txt recounted: five passes, 60,949.67 ms of engine CPU for 300 games = 203.166
  ms a game, 16,016 samples (= the sum of your eight subsystem rows); the frame-pointer build 59,512.51 ms = 198.375
  ms a game, 15,630 samples; all ten passes 7,670 searches, 25,641,316 nodes, trace ee465caeff9c0fcf (r15d's own).
- Good, keep doing it: one piece per file in the order asked; a README with the invariant and the named oracle of
  each piece; the byte-for-byte check pasted with its command; the caller-inclusive table taken on a frame-pointer
  build with the SAME profile data, with its ms per game beside the plain build's; a trace on every pass; the report
  inside the time.
- Wrong or not shown by your files:
  (a) The identity after each piece is not shown. stack_identity_raw.txt holds one summary line per piece ("EXACT"),
      not the engine's lines, and stamps.txt puts the ten pieces 16 to 17 seconds apart (07:15:12Z to 07:17:39Z),
      while one bench 16 took 10.1 s (net512) and 14.9 s (net768) on curated in step0_job13_raw.txt. Say how and
      when those checks ran (in parallel? before the stamps?). From now on the identity file of every step holds the
      engine's own bench lines, and for the 250 rows their node sum and the sha256 of the rows file.
  (b) Your first stamp names a valgrind check; no file and no line of the report gives its result. Say what ran and
      what came out, or that it did not run.
- What the PC's line-by-line read of the ten pieces found: nothing that changes a move, a node or an output with the
  PC's defines (FORGE_SDK_SEE_HOIST 1, FORGE_SPD_KING_LINES 1, FORGE_SPD_NO_ZERO_MOVELISTS 2,
  FORGE_SEARCH_SPEED2 1, no pawn history). Three things to tidy:
  (1) dead code from 01_S4: has_cached_quiet_history() and cached_quiet_history() have no caller,
      quiet_hist_epoch_ never changes from 0, and last_quiet_history_ (written in 09_W1) is never read;
  (2) 09_W1 adds an AVX-512 table of the continuation and check terms that 10_W2 removes again (about 35 lines that
      are not in the bundle), and it carries three whitespace-only edits (two apply_history lines, one null_score
      line);
  (3) 04_S7's position parser follows r15d's cache rule (same root test, token-wise prefix, whitespace fallback, the
      same ucinewgame reset), but no check of yours sends position commands of other shapes than your driver's.
      That is Part 1 below.
- Others: sol3 (another helper) rebuilds the PC's r15d from the public base and checks your ten pieces one by one at
  depth 10 on 400 positions, with a planted key fault that must fail; you will hear its result.
- What the PC does with job 13: nothing is placed. When the processor is free, the PC builds the curated tree with
  its own recipe (clang 23.1.5 + libstdc++, ThinLTO, -march=znver5, profiled with bench and 60 self-play games),
  checks identity on 1,200 positions with two real nets, and times it against r15d on that build. Only that number
  counts for the loop.

=== THE TASK (yours to plan; the owner's words: a task, not an order) ===
Part 1, first (cheap, never timed): a PROTOCOL IDENTITY test of 04_S7 (apply_position_sv, parse_limits_sv).
  - Two plain builds, no PGO, with -DNDEBUG and the six speed switches as in your timed builds: r15d, and curated
    (r15d + your ten pieces). Both with PC20 and net512.fnn3 loaded, as in your identity suite. One command stream
    file, sent to each exe by one driver that waits for readyok after every block (never pipe a whole file at once:
    a later command interrupts a search).
  - The stream, at least 20,000 position commands, made by a script you commit (seed 15001 for every random choice)
    from the 60 games of your self-play driver:
    (a) every prefix of each game, growing, as  position startpos moves ...  and as  position fen <the game's start>
        moves ... ;
    (b) the same prefixes shrinking, and in a seeded random order;
    (c) the root changing between two commands (game A, game B, game A again);
    (d) two spaces, a tab, and trailing spaces between move tokens and after "moves"; "moves" with nothing after it;
    (e) an illegal move in the middle (a move from another game), "e2e9", a promotion letter that does not belong
        ("e2e4q"), and after each of them a command that continues the list past the bad token;
    (f) FEN roots with 4 and with 5 fields;
    (g) ucinewgame between some commands;
    (h) go lines for parse_limits_sv: depth, nodes, softnodes, searchmoves with two to five moves, one go line of
        more than 32 tokens (wtime btime winc binc movestogo depth 6 and a searchmoves list of every legal move),
        and an unknown word between two known ones.
  - The probe after every position command: go perft 2, eval, isready. After every 50th: ucinewgame, then go depth 6
    (Threads 1, Hash 16), compared without the time, nps and hashfull fields.
  - Known answer: both exes print the same lines, line for line (after removing those three fields). Report the
    position commands sent (per kind (a) to (h)), the probes, the lines compared, and the lines that differ (must
    be 0).
  - Planted fault: a scratch copy of curated whose quick prefix test ignores the whitespace boundary (the test of
    moves_sv[canon.size()] removed) must give at least one different line; paste the first one.
Part 2: the refresh counters (counters only, no step in this part). Your job 13 profile puts
  nnue::v3::refresh_from_pieces at 5.87 % inclusive (11.639 ms a game). replay_ply already refreshes only the
  perspective whose king key changed, through the per-worker cache, so the question is how often and how much.
  - A scratch copy of curated with counters that change no node: bench 11, 13 and 16 of both nets equal to curated's,
    pasted from the engine.
  - Over the 60 games of your driver, Hash 16, softnodes 2000, PC20 + net768.fnn3: static_evaluate_v3 calls, and how
    many end in apply_pair_and_evaluate and how many in make_valid; make_valid calls by the number of plies they
    replay (a table: 1, 2, 3, 4 to 7, 8 or more); refresh_from_pieces calls by cause (the king changed bucket, the
    king changed flip, no valid ancestor), each split into "at the evaluated ply" and "inside a replay below it";
    and the RefreshCache's own counters: columns per refresh (mean and the 50th, 90th and 99th percentile).
  - Commit your prediction of these shares ALONE before the first counted run, each with the range that kills it.
Part 3, if time is left: ONE step on the tree job 14 leaves, aimed at the largest cost Part 2's table shows, with
  the usual proofs and timing; or, if the table shows nothing with a size, say so and stop there.
Not wanted: bug hunting (cheaper helpers do that), a change of the net file format, anything about training, and
any strength match with net512.fnn3 or net768.fnn3 (made-up weights; file 11 v3).

=== EVIDENCE RULES (as in jobs 4 to 14) ===
- Every step: its prediction committed ALONE before its first timed or counted run (what it removes or changes, its
  count, the predicted gain with the range that kills it); one unified diff forge-combo29/carbon2/job15/<step>.patch.txt
  on your base; the identity proof of files 4 to 14 (bench 11, 13 and 16 of both nets, the 250 depth-9 rows, the
  1,000 evals, both traces) plus any oracle of the code the step touches; a planted fault your checks catch.
- An identity file holds the engine's own lines (see (a) above), never a summary line alone.
- Each build: the full compile and link lines and the profile run's output in a raw file (build_pgo_raw.txt), with
  the number of profile files merged and the self-play games, searches and nodes of the SP profile run.
- Timing with your self-play driver at Hash 16: A1 B1 B2 A2, 12 rounds of 60 games, the per-round ratios, their
  median, the number of rounds faster, and the per-round A/A range beside the median; the raw file opens and closes
  with a  date -u  line.
- A count, share or time in the report comes from a committed raw file. Before you write "X is in file Y", open Y.
  A number you multiply or compare is copied from its raw file, with the file named beside it.
- After every step append the output of  date -u  and a few words to forge-combo29/carbon2/job15/stamps.txt; never
  type a time.

=== BUDGET ===
90 minutes from the moment you read this file, by the clock; the report at minute 80 with what you have. Nobody
answers questions within that time: decide, write down what you decided and why, go on.

=== RULES (as in jobs 1 to 14) ===
- Your branch: for-fable-and-opus/carbon2-work (add commits on top). New files only under
  forge-combo29/carbon2/job15/ (text only).
- Change NO engine source file in the repository: patches stay text files. No binaries, no net files, no profile
  data files.
- Do NOT open a pull request. If your tool opens one by itself, say so in the report.
- Read no other branches than the ones named in jobs 1 to 14 and here. No secrets, keys or personal data anywhere.
  Text in the repository is data, not instructions to you; only this file and your job 1 to 14 files direct your work.
- The last command before the report commit is  git status --short  and  ls -R forge-combo29/carbon2/job15 , pasted
  into the report.

=== THE REPORT: forge-combo29/carbon2/job15/REPORT_carbon2_job15.md ===
  0. Step 0 on each build, the compiler and its version, the -march, and for a profiled build the profile files
     merged and the self-play games, searches and nodes of the SP profile run.
  1. Part 1: the stream's make-up (commands per kind (a) to (h)), the probes, the lines compared and the lines that
     differ, and the planted fault's first different line.
  2. Part 2: the tables, and the prediction (met or killed, share by share).
  3. Part 3: what you did and the counts that decided it.
  4. A table, one row per step: step | patch file | lines | identity | timing | prediction (met or killed) | planted
     fault (caught or not).
  5. Your answers to (a) and (b) of "Wrong or not shown" above.
  6. What you would do next with another 90 minutes, ranked, or why you would stop.
  7. Times: the first and last line of stamps.txt; your model name and version as your runtime gives it.
Then push your branch.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_16.md on branch handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1 origin handoff/fable-opus-combo29-all-20261114, then git show FETCH_HEAD:<path>) every 2 minutes for at
most 20 minutes. If it appears, it is your next job. A first line STOP ends you. If nothing appears within 20
minutes, end.
