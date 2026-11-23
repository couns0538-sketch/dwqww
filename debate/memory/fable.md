# Memory file of fable

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: fable
- Model: Claude Fable 5.2
- Started: 2026-11-23T10:40:56Z (this PC's clock; it differs from the others' clocks by hours: order is by git log)
- Last update: 2026-11-23T12:33:00Z
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
- N8 after astra's counterexample (two openings, one whole FEN): replayed on the PC = 0 rows against 127 rows.
  The engine reads its history in three functions, all bounded by the halfmove clock (board.cpp 1463, 1474,
  1770; callers search.cpp 1592, 1601, 2551 to 2584, 2790, 2797 and uci.cpp 424; `key_history()` has no caller,
  `history_size()` is a length). Key whole FEN + window in order: 113 of 132 copies kept (300,000 draws), the
  ordered moves 3. The PC's driver does send an opening that is already a third occurrence (its rule test runs
  before each random ply only); the engine ends it with 0 searches.

## Proposals and where they stand (see BOARD.md)
- ACCEPTED: A1, A3, A4, A5, A6, N1 (changed), N2, N3, N6, N8 (my first AND my second key shown wrong by astra; the key is
  now astra's candidate: whole FEN plus the positions since the last pawn move or capture, in order; neon is
  asked), N10, N11 (stage 3 of the bundle rule closed at "lower bound above -3", all three), F1 (mine; J10).
  TO MEASURE AFTER THE DEBATE: A2, N4, N5, N7, N9.
- I dropped two drafts (server build, net shape limit) because neon had posted the same points first (N2, N3);
  my additions went into my replies.

## What I still owe
- An answer to every new message, by name, in git order. Nobody owes an answer on the key: it is A7 (astra), accepted by all three. MY SLIP at 12:01Z: I merged five messages (astra 045047Z, 045117Z, 045230Z; neon 045136Z, 045430Z) without reading them, because I listed new files only at the first fetch of a turn; I asked neon a question it had answered. From now on: after EVERY merge, `git diff --name-only <last read commit>..HEAD -- debate/msgs`, and the last read commit is the line at the bottom of this file. W10's advance criterion is "the same lower bound above 0" (I had drafted an SPRT -5 / 0 and took it out before pushing: a level result is no reason to change every self-play game). The en-passant rule of the key: past positions legal, the current position with its target when a pawn stands ready to capture (117 of 132; every raw target: 77). Neon's audit of the draft is in draft 2. Neon reached the same en-passant rule on its own (051000Z: every reader, 40 of 40 replays); astra agreed to it and to every new bar of draft 2 (051450Z, 051512Z) and has NO dissent left; astra's 051545Z qualifies neon's pre-seed note (only when the whole key can be rebuilt): in the plan. Neon voted the same (051650Z): NO dissent on draft 2 from either. My own correction: W4's "4.5 hours" had no measurement behind it (1.8 hours with 12 at once). THE OWNER EXTENDED THE DEBATE at 12:17Z on my clock: up to two more hours from then if all three think the plan can still be improved; it ends when each says more debate no longer improves it. Phase 3 at the latest 13:50Z mine (06:50Z theirs), last stop 14:20Z (07:20Z). I asked both for the item with the weakest test and proposed F2 (W8: the disk trainer's net also judged by games, SPRT -5 / 0 at 250,000 nodes) and F3 (W5 c: closed session, killed allocator, cut link, nothing deleted before the PC confirmed it): astra AGREES with both (052049Z, with sharper kill points) and proposed A8 (W6: compare the UPDATE on the rented card, a zero-learning-rate run must fail): I agree. Neon AGREED on F2, F3, A8 (052702Z) and proposed N12 (persistent-worker game parity against the PC) and N13 (four known tables for the stop rule): astra and I agree. I proposed F4 (the day never depends on the opening table; built last; worth 1.3 to 2.1 % of the day): astra agrees with the fallback, the rest is open. THE OWNER (three messages between 12:27Z and 12:35Z mine; the last one counts): the debate runs for THE TWO HOURS he gave and ends at 14:17Z mine (06:17 PC); neon has enough credit and is waited for however long it takes; astra got two subagents from him, I get none. Final text for the votes at about 13:40Z mine (05:40 PC). My part until then: hold the plan's bars against the PC's earlier declarations (W1's five matches, breadth, TD twin). Astra's part: the paid items (W5, W6, W13). N13's four values recounted by my own program: equal to six digits (debate/evidence/fable_n13_recount.txt). Astra WITHDREW its own stop (052358Z: the owner confirmed the extension to it directly): latest stop 07:17Z theirs = 14:17Z mine = 06:17 PC; the final text goes out when all three have said NOTHING MORE, at the latest 13:50Z mine. Astra traced and controlled the pinned en-passant capture (052306Z, 052319Z): selection swaps at search.cpp 960 to 964 and 989 to 996; in W15. MY SLIP at 12:23Z: a fix-up step failed its assert and the next step ran anyway (only the second was guarded): the pushed text said "2 to 3 times" and "without a word"; corrected one push later. Every step of a chain is guarded, not only the last. The owner: neon sometimes waits 180 s for its shell. Astra corrected two texts of mine after that (N5's lower-tail cell; J10's "level pair" control): both taken over, see BOARD. The DRAFT of `debate/FINAL_PLAN.md` is on the branch since 2026-11-23T12:01:01Z: every objection to an item W1 to W16 is answered and written beside the item.
- The hourly summary for the owner (in BOARD.md's last section).
- Phase 3: `debate/FINAL_PLAN.md` from about 13:10Z on my clock.

## My next step
- Watch both branches; carry astra's commits over; answer replies to my additions and to F1.
- Go through the plan's items nobody has touched yet (P5, P6, P12, the order in section 5) and post what my
  reading supports.

## Last shared commit read
shared 3049ba4 and astra e945b44 (every message up to these two is read and answered).
