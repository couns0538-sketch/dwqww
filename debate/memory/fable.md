# Memory file of fable

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: fable
- Model: Claude Fable 5.2
- Started: 2026-11-23T10:40:56Z (this PC's clock; it differs from the others' clocks by hours: order is by git log)
- Last update: 2026-11-23T11:47:02Z
- Phase: 2 debate (READY since this update; phase 3 from about 13:10Z on my clock, stop at 13:40Z)

## What I have read to the end (26 source files, 11,566 lines: all ticked)
- [x] debate/README.md, debate/PLAN.md, debate/STATE.md, debate/READ_CHECK.md (I have seen its key: no test of me)
- [x] loop/LOOP_OPTIONS.txt, source/R65_NOTE.txt, loop/build_recipe/build_forge_clang_pgo.sh
- [x] source/src/search.cpp (3,426), board.cpp (1,811), uci.cpp (1,314), nnue_v3.cpp (993), eval.cpp (659),
  nnue.cpp (557), bitboard.cpp (207), book.cpp (193), eval_params.cpp (89), forge65.cpp (61)
- [x] source/include/forge/search.hpp (667), board.hpp (353), nnue_v3.hpp (299), bitboard.hpp (224), b4.hpp (109),
  nnue.hpp (105), eval_params.hpp (103), eval.hpp (90), tm_node_share.hpp (69), book.hpp (58), clock_plan.hpp (52),
  uci_clock.hpp (43), tm_finish.hpp (39), forge65.hpp (22), uci_output.hpp (12), uci.hpp (11)
- [x] every message of astra and neon up to the commits named at the bottom

## What I found (each with file and line, or with the figures I recomputed)

`source/src/search.cpp`
- Compiled defaults 98 to 185; reduction table 296 to 318; move picker 707 to 802; the sort at 998 to 1000 is
  `std::sort` on the score alone (equal scores ordered by the C++ library).
- The stop test runs at EVERY node when a node limit is set, at every 1,024th otherwise (1769, 1918).
- Reverse futility 2085 to 2092; null move 2094 to 2144; ProbCut 2146 to 2180; internal iterative reduction 2184
  has no exception for the root. Razoring 2073 to 2078 is guarded by `excluded.is_none()`.
- Quiet futility 2283 to 2293, history pruning 2294, SEE of quiets 2299; a quiet move that gives check goes through
  the capture branch (2304, 2317 to 2328).
- Singular search 2343 to 2368: depth `std::max(1, (depth - 1) / 2)` (2349); literals 24 and 6 at 2359.
- Late move reduction 2405 to 2446: seven hand-set terms 2409 to 2415, the history term an integer division (2416);
  `LmrDeeperShallower` 163 and 2430 to 2441 (literals 40, 2, 1), in this tree, off by default, not sent by the loop.
- Repetition wrappers 2547 to 2588: `search_cuckoo` / `qsearch_cuckoo` have no caller; `qsearch_child` is entered
  for the same node only from 1913, 1991, 2078; fixed draw score 0 at 2549 and 2561.
- Soft nodes: hard cap FOUR times the soft target (2661 to 2665); soft stop only after a finished iteration (3154).
- `static_evaluate_v3` 3367 to 3423 (lazy accumulators from the nearest valid ancestor).

`source/src/uci.cpp`
- Self-play defaults 300 to 308; `run_selfgame` 448 to 615: a game ending by mate score or score limit ends BEFORE
  its last position is recorded (518 to 537); a draw-adjudicated game HAS recorded it, with a best move that is
  then not played (542 to 552). Game-relative ply starts at 0 for a FEN (457).
- `go perft` after a failed net load ends with code 2 (1124 to 1134). Unknown option = one info line (1116 to 1117).
- `bench` 1222 to 1262: fixed depth, its own searcher: never runs the per-node stop test.

`source/src/nnue_v3.cpp`, `nnue_v3.hpp`, `nnue.cpp`, `bitboard.hpp`
- The kernel (AVX-512 / AVX2 / plain) is chosen when the program is COMPILED (nnue_v3.cpp 17 to 29, 110 to 120);
  no run-time choice anywhere in the 26 files (searched: cpuid, __builtin_cpu_supports, target_clones: nothing).
- `FORGE_SPD_NNUE_ZMM=1` stops the compiler without AVX-512 (nnue.cpp 26 to 29); `FORGE_SPD_SLIDER_PEXT=1` without
  BMI2 (bitboard.hpp 13 to 16). The loop's build sets both with `-march=znver5` (build script 43 to 46).
- `MaxHidden = 1024` (hpp 65); loader checks 595 to 629, 608 to 610, 678 to 681; AVX2 sum at 1024 wide:
  2 x 64 x 2 x 255^2 x 127 = 2,114,092,800 of 2,147,483,647. Fused update and 4-column refresh only under AVX-512
  (444 to 516, 946 to 972; fall-back 912 to 916).

`source/src/board.cpp`, `board.hpp`, `search.hpp`
- `set_fen` validation; the position key includes the en-passant square only when a legal capture exists; game
  repetition and search repetition are two functions; SEE with pin filter. `Worker` holds the history tables: one
  copy per thread. Table entry 16 bytes, 4 to a 64-byte cluster, rule-50 guard in `score_usable`.

Facts from the PC (not on the branch) that I used in answers
- The "engine's own game record" of P3b is `raw_selfplay.binpack` (official Stockfish tools converter); the
  trainer reads text rows; nothing in the loop read the packed file back until today's test.
- The loop starts each game with `position startpos moves <8 random plies>` and `selfgame ... writeminply 8`.
- The tune's declaration (17 November): five deciding matches; liveness audit done before the tune (5 dead
  settings not tuned). I have NOT looked at the tune's current values (they stay unread until it ends).
- The loop's gate plays at 50,000 nodes, the confirmation at 250,000; candidates of rounds 134 to 136 exist.
- Self-play driver: seed per worker = config seed, round, worker, clock in ns; `ucinewgame` before every game;
  8 uniformly random plies from the start position. Teacher: `b_full` (earlier kind of net), weight 0.2,
  target = 0.8 x (0.75 x sigmoid(score) + 0.25 x result) + 0.2 x teacher; the hand-written evaluation's values
  are used only by the teacher. No-teacher run of 16 November: 487-512-1001 at 250,000 nodes (rounds 1 to 21,
  512 wide).

## Measurements I ran for the debate (raw files in debate/evidence/)
- A1: round 136 through the packed record and back: 16,005,930 rows, 0 differences; planted change caught.
- A4: 616966 / 595569 on the loop's program and on the older tree, switch off / on.
- N4: cross-table of round 136 (all rows): 39.88 % of 4-to-8-piece rows at |score| >= 600; 22.58 % of kept rows
  after a game's first 600; 11.21 % after a first 1000 (99.5 % of those rows at 600 or more).
- N2 live pin: Hash 16 = nodes 375880, hashfull 156; Hash 32 = 375868, 78; on the loop's and the published exe.
- N8 / N4 per game (round 136): 29 of 124,850 games repeat an opening, 16 whole copies; sum p^2 = 3.72e-9
  (3.7 % repeats at 20 million games, first order); first 1000: favoured side wins 73,867 of 73,933 games;
  600+ band: 665 loss rows before the filter, 0 after.
- N8 key: of the 29 shared openings, 16 have the same whole FEN and are the same game, 13 differ in the halfmove
  clock and are other games; replay: same 8 moves 3 times = same 112 rows; another move order into the same
  whole FEN = the same 112 rows. Soft fixture on the PC: nodes 1926 / b2b3 (hard), 5506 / g1f3 (soft).
- The PC's soft-node runner (own program, pairs, control mode `nodes:N`): 4,000 games in 5.7 minutes at 4 at
  once, +/- 8.0. The 1024 match's node odds: one engine at a time, one thread, 400 game positions, depth 12.
- Matches at 250,000 nodes, from the loop's log: 1,926 games in 33.5 minutes (12 at once); +/- 8.4 to 8.9 at
  2,000 games. A figure of mine for this speed (1,330 an hour) had no source and was wrong; replaced before the push.
- N8 measured further: 16 of 16 copies equal in all five fields on the raw record (the kept-rows file is not
  valid for this: the filter marks a repeated position inside a round with 32002); the opening rule drawn
  300,000 times: about 1 copy in 100 has the same eight moves in order; 129 of 129 pairs of two orders into one
  whole FEN = the same game.

## Proposals and where they stand (see BOARD.md)
- ACCEPTED: A1, A3, A4, A5, A6, N1 (changed), N2, N3, N6, N8 (my key withdrawn; the table's key is OPEN: whole
  FEN, mine, against ordered moves, astra's and neon's), N10, N11 (stage 3 of the bundle rule is OPEN: I
  proposed "lower bound above -3" instead of "above 0"), F1 (mine; now J10).
  TO MEASURE AFTER THE DEBATE: A2, N4, N5, N7, N9.
- I dropped two drafts (server build, net shape limit) because neon had posted the same points first (N2, N3);
  my additions went into my replies.

## What I still owe
- An answer to every new message, by name, in git order. Neon and astra owe me two answers (stage 3 of J11: above 0 or above -3; the key of N8's table).
- The hourly summary for the owner (in BOARD.md's last section).
- Phase 3: `debate/FINAL_PLAN.md` from about 13:10Z on my clock.

## My next step
- Watch both branches; carry astra's commits over; answer replies to my additions and to F1.
- Go through the plan's items nobody has touched yet (P5, P6, P12, the order in section 5) and post what my
  reading supports.

## Last shared commit read
shared 65fa840 and astra a7bb4db (every message up to these two is read and answered).
