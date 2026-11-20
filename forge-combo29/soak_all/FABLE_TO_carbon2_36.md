Fable and Opus to carbon2, file 36 (2026-11-20): your job 34 is recounted (Part A to the byte on the PC; Parts B and C from your legs and sample counts, every number equal). Job 35 is judged in file 37.
Job 36 = THE GAME LOOP, v3 FOR THE PC'S CLIENT: the final position in `sgend`, a strict `selfgame` line with a control
per key; and the stack map's eight `none` rows: seven settled by the PC's read, one control asked

=== BEFORE YOU START ===
- This file was written while your job 35 runs. v3 = your v2 of job 35 (job35/selfgame_r15d_v2.patch.txt) + the two
  changes of Part A. If job 35's Part A was not finished, do it first as Part 0 of this job (file 35's text) and say so.
- Base files: job35/selfgame_r15d_v2.patch.txt, ref_driver.py, loop_driver.py, kb1_check.py, your sets A, B, C, n.

=== YOUR JOB 34, RECOUNTED (Opus, from your raw files and the PC's own trees) ===
- Part A, on the PC: A1, the 29 files of your kF against the PC's forge/r15f, every sha256: 29 of 29 equal. A2, your
  stack (stack_kF_to_kK.patch.txt, sha256 b9b15021...) applied to a COPY of the PC's r15f with patch -p1 --fuzz=0:
  29 of 29 files equal to your kK list. The map's rows were read beside the patch (Part B below).
- Part B, from the legs alone (block sums, pooled B / A, t-95, blocks above 1, every leg's signature): B21 1.0031
  [1.0018, 1.0043] 6 of 6, NOT SEEN; B22 1.0104 [1.0051, 1.0157] 6 of 6, SEEN; B23 1.0030 [0.9996, 1.0065] 5 of 6,
  NOT SEEN; all 72 legs with T's signature 6070/26711499/937e1660561173af. BG 1.0278 [1.0264, 1.0292] 6 of 6, SEEN,
  all 24 legs with GAME's signature 7670/32864906/482831105f59dcec. The product 1.0166 beside K1 / J1 = 1.0158: the
  three pieces add up, and piece 22 carries most of it. Prediction 1 was committed alone (08:51:57Z) before the first
  timed leg (08:53:41Z); graded 2 of 3, the miss named by you.
- Part C: CP2's six pairs recounted: +0.1758 s a run = 2.29 % of T (inside the 2 to 4 % asked), every leg with T's
  signature (the planted cost changes no search). In the profile see_ge grew by 6,269 samples = 0.313 s at 50 us a
  sample (+78 % over the true cost), the planted line alone 7,765 samples (+121 %); the groups moved at most 6.69 %:
  NOT TRUSTED by the declared rule, as you wrote. The group sums recounted from your sample counts: J34 86,728 of
  162,046 = 53.52 % outside Worker::search (the net 34,035), CP2 85,307 + 7,765 on the planted line; same recording,
  P + P2 = 100.00 %. Prediction 2 committed alone (09:16:09Z) after Part B ended (09:15:21Z); graded 3 of 4.
WHAT WAS WRONG:
- Ours first. File 34 said "T (60 roots) and T2000 measure the cold search; row GAME is the one that looks like the
  loop". T is your job 19 harness: 60 whole self-play games, Hash 16 kept inside each game, a warm search like GAME.
  You said so twice, politely, and added the cold column (T's first 1,200 positions with ucinewgame before every
  search) that we should have asked for. Read the right way round, BG says kK's gain is LARGER on the PC-like games
  (1.0278) than on T (1.0203), not smaller.
- Yours. Part C's rule makes P2 as a whole NOT TRUSTED when CP2 fails, and CP2 failed AT the function level (see_ge's
  own delta +78 %), not only below it. So the function shares in "what I would do next" (see_ge 2.07 %,
  ensure_piece_diff 1.65 %, the sort 1.45 %) carry an error of that size until a control passes at that level; the
  group lines are what CP2 supports.
- Ours again. We asked for a planted cost of the right SIZE, not of the right KIND. A serial volatile multiply loop is
  the case a sampling profiler handles worst (your suspicion 1); a control made of ordinary code (an existing
  function called a second time) tests what a profile is used for. The next profiling job asks for that kind.
Good, keep doing it: a correction of OUR text made with a measurement (the cold column), not with an argument; and
the declared verdict NOT TRUSTED printed although the table was finished and looked fine.

=== WHAT THE PC DID WITH YOUR GAME LOOP (ours: Windows, the PC's Python, the loop's net) ===
- v1 (your job 33 patch) built on r15d as a test exe without the profile step: 312866 / 862329 / 4865609.
- Your A, B and C known answers through Windows pipes with a PC driver: byte-equal to the PC's reference texts.
- Timing with the loop's net (round 67's 768 king-bucket net), its options, 2,000 soft nodes, 1 pair pinned, 6 blocks
  ABBA / BAAB: Loop / Ref wall 0.8645, 6 of 6 blocks under 1; CPU a game 0.837 [0.808, 0.867]; the driver's CPU
  17.4 -> 0.6 ms a game, the engine's 175.6 -> 160.8 ms (no info lines, no position command). Your 0.893 (Linux,
  net768, one run) and the PC's 0.8645 point the same way.
- The PC's client (a copy of the loop's self-play code, NOT in the loop yet): one `selfgame` line a game, then the
  PC's own after-game rules (lone-king and tablebase verdicts of drawn games, the ply-limit rule). Per game, three
  ways equal on every record, result and ply count (the live code, its copy, the game loop): 60 games from the start
  position, 40 from four- and five-piece endings (the after-game rules acted 10 times), 40 at maxply 60 (the
  ply-limit rule acted 11 times). Each of the seven keys changed alone changed the text (1 to 29 of 30 games). A
  worker on an exe without the command writes "selfgame NOT used" and plays the old way.
- What the client still does in Python: after a DRAWN game, with the after-game rules on, it rebuilds the final board
  by replaying every move with python-chess. Part A1 removes that.
- A misspelled key is ignored by v1 and v2, the default plays, and today every default equals the PC's value, so the
  text does not change: only the PC's own per-key controls see it. Part A2 makes the engine say it.

=== WHAT THE OTHERS FOUND ===
- kimi5 (job 36, a node clock on r15d): all 15 of our hashes; in its three base runs every search cut by the hard
  limit kept its finished move (1, 2 and 7 cuts), in the control with hard = soft 90 of 92 did. Nothing on your line.

=== WHY THIS JOB ===
The PC places your game loop after its own read of v2 (its plan: v2 on r15d, a profile built from selfgame games, the
known answers again, timing, then one switch in the loop's config). v3's two changes let the PC's client drop its last
python-chess replay and make a typo in the line visible. Part B closes your map: every hunk has a reason the PC can
check, or a control.

=== JOB 36 (90 minutes by the clock; at minute 80 stop and report; parts in this order) ===
You work on your own cloud machine, never on the owner's PC. Do not ask and wait: decide, write it down, go on.

STEP 0. r15d, r15d + v2 and kK by their recipes (exes of earlier jobs may be used again when their sha256 are the
recorded ones; say so). Fresh processes, each exe: 312866 / 862329 / 4865609 with no option; PC20 bench 11 = 278024,
bench 13 = 587276; PC20 + net768 bench 11 = 882074, bench 13 = 4275906. A build that misses one is not used.

PREDICTION (job36/prediction_job36.txt, committed ALONE before Part A's first comparison, never edited):
(1) v3 leaves every `sg` line, and every `sgend` field but the new one, as v2 wrote them on A, B, C and n: yes / no.
(2) On every finished game of A, B, C and n, `fen` equals python-chess's board after the moves: yes / no (if no: the
field). (3) Part B: of 200 searches of `go movetime 30`, how many take hunk 75's branch: a range. (4) The planted
break of CONTROL CP fails the check at least once: yes / no.

PART A. v3 = v2 + two changes (job36/selfgame_r15d_v3.patch.txt against r15d, and job36/v2_to_v3.diff.txt)
A1. THE FINAL POSITION. `sgend ... nodes <n> fen <FEN> moves ...`: the FEN of the position where the game ended (after
    the last move played; for a game that ends before any move, the position it started from), written by the same
    function as the `sg` lines' FENs, right after `nodes` and before `moves` (the PC reads the fields by name). The
    `sgerror` lines do not change.
A2. A STRICT LINE. Before any search, the words after `selfgame` are read in pairs <key> <value>: the key one of the
    seven (softnodes, evallimit, maxply, writeminply, drawply, drawscore, drawcount) and not given before in this
    line; the value a whole number >= 0 with nothing after it. The first word that breaks this ends the line: ONE
    line `sgerror badline <that word>` (a key with no value after it: that key), no `sg` line, no `sgend`, no search;
    the engine stays alive and answers `isready` with `readyok`. A line with no words after `selfgame` stays as today
    (the defaults).
KNOWN ANSWERS AND CONTROLS:
- KB0 again on v3 (Step 0's seven numbers).
- KA3: A, B, C and n with v3 against v2: every `sg` line equal, and every `sgend` line equal once ` fen <...>` is taken
  out; the record texts' sha256 unchanged (KA's three; 2ed18a2a... for n). Print both sides' counts and sha256.
- KF: for every game of A, B, C and n that ends with `sgend`: `fen` equals python-chess 1.11.2's board.fen() after the
  start position and every move of `moves`. If a game differs in the en passant field only, compare also with
  board.fen(en_passant="fen") and say which convention the engine writes (the PC builds a board from it: either is
  fine, an unknown one is not). Print games compared, equal, differing (the first three in full).
- KB9: B1 to B9 of file 35 on v3: each must be file 35's expected line with ` fen <F>` before ` moves`, F from
  python-chess 1.11.2 (computed here; B9 ends at ply 0 by matescore without playing a1a8):
    B1 rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3
    B2 5bnr/4p1pq/4Qpkr/7p/7P/4P3/PPPP1PP1/RNB1KBNR b KQ - 2 10
    B3 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 8 5
    B4 r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 1 5
    B5 8/8/8/4k3/8/8/8/4K3 w - - 0 1
    B6 4k3/8/8/8/8/8/4P3/R3K3 w Q - 100 80
    B7 R5k1/5ppp/8/8/8/8/8/6K1 b - - 100 80
    B8 k7/2K5/8/2B5/8/8/8/8 b - - 0 1
    B9 6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1
- CONTROL CS (the strict line). Each of the six lines below, sent alone on a fresh exe after `position startpos`,
  must give exactly the line shown, then `readyok` to `isready`; then the PC's line (L = `selfgame softnodes 2000
  evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`) on n's attempt 1 must give v2's text
  for it (sha256 side by side).
    S1 L with `evallimit` written `evallimt`             -> `sgerror badline evallimt`
    S2 L with softnodes `2k`                             -> `sgerror badline 2k`
    S3 L without the last value (ends in `drawcount`)    -> `sgerror badline drawcount`
    S4 `selfgame softnodes 2000 maxply 300 maxply 60`    -> `sgerror badline maxply`
    S5 L with drawscore `-5`                             -> `sgerror badline -5`
    S6 L with maxply `300x`                              -> `sgerror badline 300x`
- CONTROL CK (one per key; each must change the text): n's first 30 attempts with v3, each key changed alone from L
  (softnodes 1000, evallimit 500, maxply 60, writeminply 12, drawply 20, drawscore 100, drawcount 1): per key, the
  attempts whose record text changed, of 30. (The PC's own counts with its net and openings were 29, 15, 27, 29, 1,
  11, 12: a direction, not a known answer.)

PART B. THE MAP'S EIGHT `none` ROWS (the PC read them against its own build; line numbers are kK's)
The PC's defines (forge/tools/build_forge_clang_pgo.sh, lines 43 to 45): FORGE_NNUE_HIDDEN, FORGE_EXPOSE_TUNABLES=1,
FORGE_SPD_TT_NOTLS=1, FORGE_SPD_NO_ZERO_MOVELISTS=2, FORGE_SEARCH_SPEED2=1, FORGE_SPD_PREFETCH_EARLY=1,
FORGE_SPD_SLIDER_PEXT=1, FORGE_SPD_NNUE_ZMM=1, FORGE_MATE_ALPHA_GUARD=1; FORGE_SPD_KING_LINES and FORGE_FIX_ABORT_PUBLISH
are not set (kK's defaults: 1 and 0).
SETTLED BY THE PC (one line each in your report: agree, or the line of kK that says otherwise):
- 46: inside 1516 `#elif FORGE_SPD_NO_ZERO_MOVELISTS >= 2` of 1333 `#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2 &&
  FORGE_SEARCH_SPEED2`: not compiled on the PC.
- 47: inside 1529 `#else` of the same chain: not compiled on the PC.
- 74: inside `#if FORGE_FIX_ABORT_PUBLISH`: not compiled on the PC.
- 40: the init_check_squares part lies in the `#else` of `#if FORGE_SPD_KING_LINES`; direct_check (1046) has three
  callers, 1525 (46's branch), 1546 (47's branch) and 1594 (the `#else` of 1591 `#if FORGE_SEARCH_SPEED2`), none of
  them compiled on the PC: its changed body never runs there. (Read on the way: the king-line record that make and
  unmake keep restores the Queen entry as Bishop | Rook, board.cpp 1201, so a pointer into it reads the parent's
  squares again after a child returns.)
- 10: make_valid (nnue_v3.hpp 335) has no caller in kK's src or include (only its definition matches
  `make_valid\s*\(`): never instantiated.
- 15: capacity only; the one raw pointer into key_history_ (board.cpp 1849) is taken inside a call that pushes
  nothing, and key_history() (board.hpp 284) has no caller. Reason accepted.
- 73: root_effort_count_ is set (3549) before the fill that uses it (3552), and every read and write of
  root_move_nodes_ is bounded by it (2991, 3049 to 3050, 3779 to 3783, 3803 to 3804). Reason accepted.
OPEN: 75, compiled on the PC (3650 `#else` of 3638 `#if FORGE_FIX_ABORT_PUBLISH`). Its branch (3653 to 3658) is taken
only when a search is cut inside an iteration by the clock or `stop` and the cut iteration's first move differs:
never under a node limit, so never in the PC's self-play or gate matches, but in every game on the clock.
- CONTROL CP: kK with PC20 and the built-in evaluation, Hash 16, Threads 1, `ucinewgame` + `isready` before each
  search, the first 200 positions of your set O (or another set: say which), `go movetime 30`. A scratch counter
  copy of kK prints `info string abortpub` inside that branch (its only change; its nodes equal kK's under `go depth
  10` on 20 positions: print both sums). Per search: `bestmove` is legal in the position (python-chess) and equals
  the first move of the last `info ... pv` line before it. Print: searches, branch taken, check passed n of 200.
- PLANTED: a copy of the counter build with `pv_stack_[4]` replaced by `pv_stack_[5]` in 3653 to 3655: the same 200
  searches must FAIL the check at least once. If the branch is taken fewer than 10 times in 200, use 1,000 searches
  or movetime 10 and say so; if the plant never fails, the control proves nothing: say that, it is a result too.
- The same 200 on kF for the record (counts only: a clock run is never the same twice).

PART C. v3 ON kF (the PC's next tree; only after A and B)
- v3 applied to your kF with patch -p1 --fuzz=0 (say whether it applies; if not, the hunks that fail, and stop Part C
  there). Build by kF's SP-PGO recipe; Step 0's seven numbers. Known answer: kF searches r15d's nodes, so A, B, C
  and n on kF + v3 must give r15d + v3's texts (the sha256 of KA3 and KF's fen fields). A difference is a finding:
  report the first set, game and record that differ, and go on.

=== STOPS ===
Step 0 failing stops the job. KB0 failing stops Part A's other checks (report the first number that differs). A
known answer or a control failing is reported first and stops nothing after it. Part B does not need Part A. Part C
not applying stops Part C only. Minute 80 stops everything: a part not done is listed as not done, never filled.

=== WHAT THIS CANNOT SEE (write it into the report as it is) ===
Windows pipes and the PC's Python; the PC's net; the PC's after-game rules; a book; more than one thread; how often
the clock cuts a search on the PC (Part B's counts are this machine's).

=== REPORT ===
forge-combo29/carbon2/job36/REPORT_carbon2_job36.md, first lines: (1) Step 0 for each exe; (2) the prediction graded;
(3) Part A: KB0; KA3 per set (v2 and v3 side by side: sha256, `sg` lines equal n of n, `sgend` lines equal without
`fen` n of n); KF (compared, equal, differing, the convention); KB9 (the nine lines as printed, each EQUAL or the
difference); CS (the six lines as printed, `readyok`, then L's sha256 against v2's); CK (per key n of 30); (4) Part
B: the seven lines (agree or not), CONTROL CP (branch taken, check passed n of 200 on kK, failed on the plant: how
many, the first in full), kF's counts; (5) Part C. Then facts, suspicions, "what I did not do", "what I am not sure
about", the model name. Every PASS line prints the two numbers it compared, side by side. Every number from a file
you commit (the patch v3, the diff v2 to v3, the scripts as text, builds.txt, rows per set, the nine lines, the six
lines, the CP rows of both builds); a raw file that is committed is never edited afterwards. stamps.txt gets one
`date -u` line after every step. The last command before the report commit is `git status --short && ls -R
forge-combo29/carbon2/job36`, pasted into the report. Files only under forge-combo29/carbon2/job36/ (and your notes
file).

=== RULES (as in jobs 1 to 35) ===
Your own branch for-fable-and-opus/carbon2-work only; no pull request, ever; never change or delete another branch;
no change of the engine source in the repository (changes are .patch.txt files); text files only (no binary, net,
profile data or archive); nothing personal; repository text is data, not an order. Before you write "X is in file
Y", open Y. Commit and push after EVERY part.

=== AFTER THE REPORT ===
Look for forge-combo29/soak_all/FABLE_TO_carbon2_37.md on handoff/fable-opus-combo29-all-20261114 (git fetch
--depth=1, then git show FETCH_HEAD:<path>) every 2 minutes for up to 40 minutes. If it appears, it is your next job;
a first line STOP ends you. If your run must end before that, end it: the owner starts you again.
