# HindsightDepth

The rule was assigned for this engine and written from that statement. Nothing was copied from another engine.

A parent sometimes searches a move at less than its full depth. The child, off the principal variation and not in check, looks back at that choice. Static eval here is the corrected value the search already stores for the side to move (`static_eval`). The side that moved is the parent, so that side's loss is the parent's static eval plus the child's static eval. "Clearly worse" means a loss of at least one pawn, `SeePieceValue[Pawn]` (100 centipawns) in this engine. "Did not get worse" means the loss is zero or negative. A smaller loss does neither step.

The new UCI check is `HindsightDepth`, default false, and it is listed in the `uci` answer. With the option off, search does not read the extra stack field. Clearing that field at the start of a search does not change the default tree.

With the option on, the step runs only when all of these hold: the node is not a principal-variation window (`beta - alpha` is 1), the side to move is not in check, this is not a singular re-search, the parent static eval is known, and the parent reached this node by a late-move reduction. The withheld ply count is `new_depth - reduced_depth` after that reduction is clamped. It is stored only for that reduced call and cleared before the full-depth re-search and the principal-variation re-search. Null-move and probcut are not marked. They are not that move's ordinary reduced depth.

- Loss of 100 or more: search one ply shallower.
- Loss of 0 or less, and three or more plies were withheld: search one ply deeper.
- Otherwise the depth stays as the parent passed it.

If the hash entry is already at least as deep as the depth that step would use, the step is skipped and the depth stays unchanged. Dropping from 1 to 0 continues in quiescence. The same node does not apply the step twice: a singular re-search or a null-move verification sees the flag already consumed.

On bench 13 with the option on, a counter that was compiled in and then removed (the node count did not change while it was present) saw 218100 reduced, off-PV, not-in-check nodes with a known parent eval. 20361 met the shallower test, 9418 met the deeper test, and 4790 of those steps were skipped because the hash entry was already deep enough. 156903 were only mildly worse, and 31418 were not worse but had fewer than three plies withheld.

## Default pins

Threads 1, Hash 16, OwnBook false, every option at default. Release build with g++ 13.3.0, `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`. In this environment `/usr/bin/c++` is clang and does not link libstdc++, so the measured binary is g++.

Printed before any search change, and again at the end with the option off (including after turning it on and back off):

- bench 11 = 312866
- bench 13 = 862329
- `go perft 5` from the start position = 4865609

The same three numbers came back from a binary built with `-fsanitize=address,undefined -fno-sanitize-recover=undefined` and the option left off. An invalid `setoption` value is rejected and does not change the option.

`src` and `include` differ from the base by 41 lines (40 added, 1 removed).

## Option on

Release bench 13, run twice: 840387 both times. The sanitized UCI binary printed the same 840387.

Start position, depth 10, Hash 16, one thread: 13102 nodes with the option off, 12413 with it on.

## Legality

`forge-combo29/tests_r3_05/hindsight_depth_legal.cpp` plays 200 deterministic lines from the start position (0 to 27 plies) and searches each to depth 10 with the option on, Hash 16, one thread. It also searches a king in check, a promotion, a stalemate, and a checkmate. The best move has to be one of the legal moves, or none when the position has no legal move. Every move of the returned line has to be legal in the position where it is played. The same program checks that the option defaults off and that the start-position depth-10 node count changes when it is turned on.

Release run: passed. Sanitizer run (`-O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined`, same engine defines): passed, exit 0, no address or undefined-behavior report.

## Not checked

No games were played, and no strength is claimed. One start-position search to depth 8 with Threads 2 and the option on returned d2d4 and did not crash. The node-count pins and the 200 depth-10 searches were not repeated at Threads 2. Ponder, MultiPV, and clock time were not re-run with the option on. Suites outside this engine folder were not run. The clang driver here still cannot link.

option name HindsightDepth type check default false

bench 13 with HindsightDepth on: 840387

## Follow-up

The hindsight block used to call the static evaluator when the hash entry had no eval, and the normal eval block called it again. The raw value is now kept and the normal block reuses it. With the option off the pins stay bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. With the option on, bench 13 stays 840387. That was checked on the portable build and on the owner build.

The owner build is the default Release cmake (AVX-512F and BMI2 are present, so portable was not used). No CMakeLists change and no FORGE_* override. The compiler is g++ 13.3.0 because this machine's c++ driver does not link libstdc++. Binary sha256: 453e4757662bf45230623455f63da64657e6a7cee0120f49fe0ee0eb3e8d8a02. Implementation commit: cacb3ed982ec5ac2eec66687e69739d88048f56c.

Screen, not a strength result. Same binary, HindsightDepth on versus off, 50000 nodes, Threads 1, Hash 16, OwnBook false. Book is 8mvs_+90_+99.epd from official-stockfish/books (8533 lines, sha256 e4ccf9297520743bb44705908b510ae45f817a146418c7773aaf44bed2cf8428), sequential, both colors. fastchess alpha 1.8.3 (sha256 091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f). Resign after 4 moves at 800 cp. Draw adjudication after move 40 for 8 moves within 10 cp, or 200 moves.

bench 13 nps, five alternating runs, off/on/off/on/off: 1446860, 1525203, 1576469, 1541994, 1591012. Node counts stayed 862329 off and 840387 on.

Chunk 001, openings 1-400, 800 games, option on first: W-L-D 214-190-396. Elo 10.43, 95% +/- 15.96. LOS 90.00%. Pentanomial 18, 90, 162, 110, 20. The interval includes zero. Details: forge-combo29/tests_r3fu_05/chunk-001-summary.txt. PGN: forge-combo29/tests_r3fu_05/chunk-001.pgn.

Chunk 002, openings 401-800, 800 games, option on first: W-L-D 189-202-409. Elo -5.65, 95% +/- 15.63. LOS 23.93%. Pentanomial 20, 96, 180, 85, 19. The interval includes zero. Details: forge-combo29/tests_r3fu_05/chunk-002-summary.txt. PGN: forge-combo29/tests_r3fu_05/chunk-002.pgn.

After 1600 games: W-L-D 403-392-805. Pentanomial 38, 186, 342, 195, 39. Elo 2.39, 95% +/- 11.18. LOS 66.23%. The interval includes zero.
