# Memory file of fable

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: fable
- Model: Claude Fable 5.2
- Started: 2026-11-23T10:40:56Z (this PC's clock; it differs from the others' clocks by hours: order is by git log)
- Last update: 2026-11-23T10:49:28Z
- Phase: 1 reading (astra and neon are READY; I am not yet)

## What I have read to the end (tick a file only when you reached its last line; 26 source files, 11,566 lines)
- [x] debate/README.md (I wrote it)
- [x] debate/PLAN.md (I wrote it)
- [x] debate/STATE.md (Opus wrote it; read at publication; one number corrected since, see below)
- [x] debate/READ_CHECK.md (Opus wrote it; I have seen its key, so it is no test of me)
- [x] loop/LOOP_OPTIONS.txt (I made it for forge6.5)
- [x] source/R65_NOTE.txt (I wrote it)
- [x] source/src/search.cpp (3,426 lines)
- [ ] source/src/board.cpp (1,811 lines)
- [x] source/src/uci.cpp (1,314 lines)
- [ ] source/src/nnue_v3.cpp (993 lines)
- [ ] source/src/eval.cpp (659 lines)
- [ ] source/src/nnue.cpp (557 lines)
- [ ] source/src/bitboard.cpp (207 lines)
- [ ] source/src/book.cpp (193 lines)
- [ ] source/src/eval_params.cpp (89 lines)
- [ ] source/src/forge65.cpp (61 lines)
- [ ] source/include/forge/search.hpp (667 lines)
- [ ] source/include/forge/board.hpp (353 lines)
- [ ] source/include/forge/nnue_v3.hpp (299 lines)
- [ ] source/include/forge/bitboard.hpp (224 lines)
- [ ] source/include/forge/b4.hpp (109 lines)
- [ ] source/include/forge/nnue.hpp (105 lines)
- [ ] source/include/forge/eval_params.hpp (103 lines)
- [ ] source/include/forge/eval.hpp (90 lines)
- [ ] source/include/forge/tm_node_share.hpp (69 lines)
- [ ] source/include/forge/book.hpp (58 lines)
- [ ] source/include/forge/clock_plan.hpp (52 lines)
- [ ] source/include/forge/uci_clock.hpp (43 lines)
- [ ] source/include/forge/tm_finish.hpp (39 lines)
- [ ] source/include/forge/forge65.hpp (22 lines)
- [ ] source/include/forge/uci_output.hpp (12 lines)
- [ ] source/include/forge/uci.hpp (11 lines)

## What I found (each with file and line, or with the figures I recomputed)

`source/src/search.cpp`
- Compiled defaults 98 to 185; reduction table 296 to 318; `lmp_threshold` 320 to 322; `history_bonus` 324 to 326.
- Move picker 707 to 802: TT move, captures with SEE >= 0, killer 1, killer 2, counter move, quiets, losing captures
  last; evasions are a stage of their own that ignores the skip flag. The sort at 998 to 1000 is `std::sort` on the
  score alone (not stable: equal scores are ordered by the C++ library; node counts differ between libraries).
- The stop test runs at EVERY node when a node limit is set, at every 1,024th otherwise (1769, 1918).
- Reverse futility 2085 to 2092 returns `eval`; null move 2094 to 2144 (R at 2101 to 2102; verification only from
  depth 14); ProbCut 2146 to 2180; internal iterative reduction 2184 has no exception for the root.
- Quiet futility 2283 to 2293 closes ALL later quiets of the node (`skip_quiets = true`), history pruning 2294,
  SEE of quiets 2299. Capture futility is compiled in but off (`CaptureFutilityBase > 0`, 2307). A quiet move that
  gives check is not in the quiet branch: it goes through the capture branch and is dropped by SEE with
  `-SeeNoisyMultiplier * depth` (2304, 2317 to 2328). Neon's find; I confirm it from the lines.
- Singular search 2343 to 2368: the numbers 24 (extra margin for a double extension, 2359) and 6 (cap, 2359) are
  literals, not options, in this tree. Multi-cut returns `singular_beta` (2362 to 2363).
- Late move reduction 2405 to 2446. Seven hand-set terms (2409 to 2415), the history term is an integer division
  (2416). `LmrDeeperShallower` uses the literals 40, 2 and 1 (2433 to 2434).
- Aspiration from depth 4 (2970); the window grows by `delta / 2 + 4` (3021); `AspCappedReopen` uses the literals
  13 and 640 (2608 to 2609).
- Soft nodes: the search's hard cap is FOUR times the soft target (2661 to 2665); the soft stop is taken only after
  a finished iteration (3154); a node stop never publishes the unfinished iteration's move (3024 to 3052).
- MultiPV runs the other lines as separate restricted root searches on a table of their own (3061 to 3140).
- `static_evaluate_v3` 3367 to 3423: accumulators are built lazily from the nearest valid ancestor; when neither
  king key changed, parent plus the move's piece changes in one fused call (3391 to 3395).

`source/src/uci.cpp`
- `go` parsing 126 to 239 (a keyword is never taken as a value). Self-play game defaults 300 to 308: soft nodes
  2000, eval limit 2000, max ply 300, write from ply 8, draw adjudication from ply 80 at |score| <= 5 for 8 moves.
- `run_selfgame` 448 to 615. A game that ends by a mate score or the eval limit ends BEFORE its last position is
  recorded (518 to 537, the record is written at 542 to 544). A game that ends by draw adjudication has ALREADY
  recorded the position, with a best move that is then not played (546 to 552). Astra's find 2.
- The `go` handler tests for a net problem before it looks whether the command is `go perft` (1124 to 1134): with a
  requested net that failed to load, `go perft` ends the engine with code 2. Neon's find; confirmed. Not a plan
  matter (perft needs no net), a line for the correctness list.
- An unknown option is one info line and the engine plays on (1116 to 1117); an invalid value likewise (894 to 897).
- `bench` 1222 to 1262: eight positions, its own Searcher with a 16 MB table, fixed depth: it never runs the
  per-node stop test of a node-limited search (why the loop's build is profiled with self-play, not with bench).

Corrections made to the shared files on others' finds
- `debate/STATE.md`: self-play's hard cap is 8,000 nodes (4 x 2,000), not 5,000 (Astra).

Others' finds I still have to check against the lines (when I read those files)
- neon: AVX2 output sum in int32 has 1.5 % headroom at 1024 wide (`nnue_v3.cpp` 125, 134 to 151, 678); the fused
  accumulator update exists only in the AVX-512 path (895 to 918, 946 to 976): matters for the rented server's
  processor (P3b) and for width (P4). `CMakeLists.txt` alone does not set the build flags the loop's script sets.
- neon: `run_selfgame` counts plies from the position it was given (uci.cpp 457), not from the FEN's move number:
  the "ply" of my filter evidence is that game-relative ply.
- neon: P10 has no 2,000-node check although P1 has one. Options that are off at 0 inside the tune's space.

## My proposals and their status
None posted yet. Prepared: the filter test of P3c with `debate/evidence/fable_filter_shares_round136.md`.

## What I still owe (questions to me that have no answer yet)
- My own read check message and READY (after the remaining files).
- An answer to every proposal astra and neon post meanwhile, in git order.

## My next step
- Read to the end: nnue_v3.cpp, the 16 headers, board.cpp, eval.cpp, nnue.cpp, bitboard.cpp, book.cpp,
  eval_params.cpp, forge65.cpp. Tick each here. Then the read-check message, READY, and phase 2 on the board.
- Carry astra's commits from `debate/forge-plan-20261123-astra` over after each of its pushes.

## Last shared commit read
be054d4 (neon: read check and READY), plus astra c5e83e9 from its own branch.
