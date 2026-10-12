# Chess Engine Forge

Chess Engine Forge 6.0.0 is a C++20 UCI chess engine. This release replaces the deliberately
unpruned 5.x search with a modern selective search and a position-indexed transposition table.
Legal move generation, UCI handling, pondering and the evaluation function are unchanged.

## Current 6.0.0 release status

Measured with fastchess (pinned commit from `tools/match/README.md`), both sides single-threaded
with Hash 32 MiB on the `tools/openings/forge-10000.epd` corpus, candidate against the unchanged
5.31.0 binary:

| Change (each measured against the previous step) | Time control | Games | Result | Elo |
|---|---|---|---|---|
| Selective search (LMR from depth 3, null move from depth 3, reverse futility, LMP/futility, check extension, SEE ordering, aspiration, soft time limit) vs 5.31.0 | 5+0.05 | 100 | W88 D7 L5 | +413 +/- 111 |
| Position-indexed transposition table, standard repetition rule | 5+0.05 | 120 | W42 D40 L38 | +12 +/- 38 (fixed-depth nodes -4% to -56%) |
| PeSTO piece-square tables | 5+0.05 | 120 | W64 D36 L20 | +134 +/- 56 |
| Attack-unit king safety | 5+0.05 | 200 | W60 D94 L46 | +24 +/- 30 |
| **Final 6.0.0 vs unchanged 5.31.0** | 10+0.1 | 100 | W84 D9 L7 | **+355 +/- 92** |

All games ended by checkmate or threefold repetition; there were no time losses, illegal moves
or crashes in any of the measurement matches.

In a fixed three-second search of the first corpus position, 5.31.0 reached depth 9 and 6.0.0
reaches depth 19. The search is now speculative by design: like every modern alpha-beta engine
it trades exactness at a fixed nominal depth for depth and time, and its quality is measured in
games rather than by zero-window bound reproduction. The pruning-independent properties kept
under test are forced mates, draw handling (repetition, fifty-move rule, stalemate under
zero-window pruning, insufficient material), searchmoves/ponder protocol behaviour, time-limit
semantics and search determinism.

## Historical 5.31.0 release status

On unchanged 5.30.0 (source SHA-256 `fd2f0d249b78bc353bc3a439464be0c4aec7a01eb1664f2c923f985aef74d0d7`), direct interior depth-9 zero-window searches for `rn1qkb1r/p1p1ppp1/1p1pbn2/7p/3P4/2N1PN2/PPP1BPPP/R1BQK2R w KQkq - 0 1` at [53,54] and [54,55] return 53 and 54: false fail-lows compared with no-LMR full-depth references returning 54 and 55. 5.31.0 raises the LMR floor from 9 to 10; both full-depth boundary windows now return 54 and 55. GCC and Clang strict builds, ASan+UBSan, 4/4 CTest suites, extended UCI/ponder and the three reference perfts pass. Windows Zen 4 binary was cross-compiled with LLVM-MinGW from frozen source and PE-verified, but not Windows-runtime-tested. The depth-10+ LMR and depth-6+ null-verification concerns remain separate.

## Historical 5.30.0 release status

5.30.0 is a **correctness release**, not a claimed Elo-strength release. On the unchanged 5.29.0 source (ZIP SHA-256 `8de2079347384e029f8819ed71b98b5aae1fbbb5ac8e870fe1e604c52a330944`), `position fen 4r2k/8/8/8/8/8/8/4K3 w - - 0 1` with `go depth 1 searchmoves a1a8` falsely printed `score mate 0`; White has legal check evasions. The fix distinguishes a genuinely terminal root from a root restriction with no permitted legal moves. In the latter case, it returns a null best move, empty PV, neutral score, a public no-result flag and one explicit UCI diagnostic, without storing a restricted-root TT bound. Genuine mates/stalemates and permitted interrupted fallbacks remain correct.

Fresh strict GCC 14.2, Clang 17, Clang ASan+UBSan, C++/match-tool/UCI/ponder tests and the three reference perfts pass. Three interleaved CPU0-pinned paired search benchmarks preserve all 908,968 shallow and 11,713,955 deep nodes, scores, best moves, and complete PVs. Timing moves in opposite directions across workloads and is not evidence of throughput or Elo improvement. Pinned Fastchess 4-pair A/A calibration completed normally. A/B Elo testing is not required for a pure protocol correctness fix, and no external superhuman-strength calibration exists. Windows Zen 4 PE is cross-compiled and PE-verified, NOT Windows-runtime-tested.

Historical note: 5.29.0 is a **validated pondering feature release**, not a claimed Elo-strength release. Forge 5.28.0 was the immediately preceding correctness release. On unchanged 5.27.0, `rn1qk1nr/ppp2p1p/3pb1p1/4p3/1bPP4/2N1P2N/PP3PPP/R1BQKB1R w KQkq - 0 1` returns +38 full-window at direct depth 8 and falsely fails low at +134 for `[134,135]`; nominal-depth/no-depth-8-LMR search and 5.28.0 return +135 for both. An independent fixture, `rnbqkb1r/p2pp1pp/1p5n/2p2p2/3P1PP1/2P1B2N/PP2P2P/RN1QKB1R w KQkq - 0 1`, changes from -22 / false fail-low -19 to -18 / -18. 5.28.0 therefore raises the ordinary LMR floor from depth 8 to depth 9 while leaving depth-9+ LMR and its existing re-search rules unchanged.

The exact 5.27.0 source archive SHA-256 is `6170b7b2d03eac5372802f4fb02c249ce52abcc316dfd7f0c7a6f66b66982b01`. It was freshly rebuilt under strict GCC/Clang and ASan+UBSan before editing; extended UCI/perft validation passed. Five CPU0-pinned interleaved comparisons show shallow nodes unchanged at 908,968 and deep nodes increasing 8,062,226 -> 11,713,955 (+45.29%); deep median time increases 4,817.760 -> 7,515.447 ms (+55.99%). No speed or Elo claim is made.

## Features

- Strict FEN parsing and serialization with legality-oriented state validation
- Complete legal move generation: checks, pins, castling, en passant, and all promotions
- Make/unmake with castling, en-passant, clocks, and repetition keys
- Incremental Zobrist key updates and lightweight legal-move filtering
- En-passant hash legality uses occupancy/attack bitboards without copying the 64-square mailbox
- Exact incremental piece bitboards plus per-color occupancy bitboards, cross-checked against the mailbox board
- Independent incremental pawn key for pawn-structure reuse
- Pawn-structure cache covering pawn placement, weaknesses, and passers
- Incrementally cached king locations for constant-time check lookup
- Fixed-capacity stack move lists for pseudo-legal/legal generation, eliminating per-node move-list heap allocation
- Iterative-deepening negamax alpha-beta search with progressive aspiration windows
- Principal-variation search with logarithmic late-move reductions from depth 3, adjusted by node type, the improving flag, killer/countermove status and history
- Null-move pruning from depth 3 with an evaluation-aware reduction; a verification search only at depth 10+
- Reverse futility pruning, late-move pruning and futility pruning in non-PV nodes, never on checking moves, never in check or near mate scores, and never without non-pawn material
- Check extension bounded by twice the root depth; internal iterative reduction on hash-move misses
- Exact mate-distance window pruning
- Reply-specific countermove ordering alongside killer and per-colour history heuristics
- Root-to-root history aging so move-ordering feedback adapts throughout a game
- Position-indexed transposition table; the fifty-move clock is part of the entry context only from clock 90 upward
- Repetition detection inside the search: one earlier occurrence after the root, or two anywhere in the known history
- Quiescence search with depth-0 TT bounds, MVV-LVA ordering, delta pruning and static-exchange pruning of clearly losing captures
- Static-exchange evaluation with bitboard attacker enumeration, x-rays, en passant, promotions, and king-safe recapturer selection
- Single-score stable in-place move ordering; losing captures and underpromotions are tried last
- Soft/hard time management: no new iteration after half of the budget, extended when the best move changed
- Transposition-move reuse in quiescence ordering
- Correct checkmate and stalemate scoring at the quiescence horizon
- Correct checkmate precedence over rule-50 and repetition draws
- Native insufficient-material adjudication for dead minor-piece endings
- Tapered middlegame/endgame evaluation with PeSTO material and piece-square tables plus mobility, pawn structure, passed pawns, bishop pair, rook files, king shelter, and tempo
- Exact-key evaluation cache for repeated transpositions
- Occupancy-bit iteration through evaluation hot paths
- Single-pass non-pawn evaluation: piece-square, mobility, and rook-file terms are accumulated together
- Direct per-color/type bitboard iteration for non-pawn evaluation, avoiding repeated mailbox piece decoding
- Precomputed directional ray masks and occupancy bit scans for exact bishop/rook/queen mobility scoring
- Compile-time jump and slider ray masks remove repeated board-edge arithmetic from move generation and attack detection
- Legal filtering tests king safety directly from updated occupancy instead of mutating/restoring the mailbox for every candidate move
- Functional UCI pondering (`Ponder`, `go ponder`, `ponderhit`, `stop`, and legal PV reply publication)
- Restricted-root UCI no-result status distinct from genuine checkmate/stalemate, including no false `score mate`
- Clock, increment, move-time, depth, and node limits
- Validated unsigned 64-bit UCI node limits for long analysis
- Fully validated and range-clamped numeric UCI search limits
- UCI protocol plus a `go perft N` diagnostic extension
- UCI depth, selective-depth, NPS, hash occupancy, score, and PV telemetry
- Legal TT-based principal-variation reconstruction for cold and warm searches, without recursive PV-vector allocation
- Deterministic regression tests, seven synthetic tactical positions, five reference perfts, and a repeatable benchmark

## Build

Requirements: CMake 3.16 or newer and a C++20 compiler (GCC, Clang, or MSVC).

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

For an AddressSanitizer/UndefinedBehaviorSanitizer build on GCC or Clang:

```sh
cmake -S . -B build-san -DCMAKE_BUILD_TYPE=Debug -DFORGE_ENABLE_SANITIZERS=ON
cmake --build build-san --parallel
ctest --test-dir build-san --output-on-failure
```

## Use

Point a UCI-compatible chess GUI at `build/forge`, or interact directly:

```text
$ ./build/forge
uci
isready
position startpos moves e2e4 e7e5
go depth 7
quit
```

Supported `go` limits include `depth`, `nodes`, `movetime`, `mate`, `wtime`, `btime`, `winc`, `binc`, `movestogo`, `searchmoves`, `infinite`, and `ponder`. Explicit `searchmoves` restrictions are strict, including an empty legal intersection. `stop` interrupts a running search. Hash size is configurable with `setoption name Hash value 128`; communication latency can be reserved with `setoption name Move Overhead value 25`; `setoption name Clear Hash` clears search caches. Enable GUI pondering with
`setoption name Ponder value true`; the GUI must then supply `go ponder` while the opponent
thinks and send `ponderhit` if the predicted reply occurs. `stop` safely aborts a miss.
`Ponder` defaults to false, and `bestmove ... ponder ...` is emitted only when enabled and
a legal principal-variation reply is available. There is **no** Threads or OwnBook option.

`position` updates are transactional: an invalid FEN or move anywhere in the command leaves the prior position unchanged and reports an `info string` diagnostic.

`go perft N` supports depths 0 through 10, prints a root divide for positive depths, and reports the total node count.

Run a move-generator diagnostic with `go perft 5`. Run the multi-position performance workload with:

```sh
./build/forge_bench
```

The benchmark covers the starting position, Kiwipete, a middlegame, and an endgame. Timings are machine-dependent; node counts, scores, and best moves are the reproducible comparison fields.

## Architecture

- `include/forge/board.hpp`, `src/board.cpp`: position state, FEN, move generation, legality, hashing, make/unmake, perft
- `include/forge/search.hpp`, `src/search.cpp`: evaluation, iterative deepening, alpha-beta, quiescence, TT, ordering, time control
- `src/uci.cpp`: UCI command loop and asynchronous search control
- `tests/tests.cpp`: regression, special-move, repetition, perft, and mate-search tests
- `bench/benchmark.cpp`: fixed perft and search workloads

## Current scope

This engine has **no opening book**, endgame tablebases, NNUE or multi-threaded search.
Pondering is supported and tested, but has no measured Elo benefit yet. The built-in book
size is **0 bytes** and Forge does not ship a `forge-book.bin` file. Draw detection covers the fifty-move rule, threefold position history, and standard insufficient-material cases.

## License

MIT. The project has no third-party runtime dependencies; CMake and the C++ standard library are build requirements.

## Additional validation tools

`tools/uci_regression.py` tests the actual UCI executable. `tools/search_benchmark.cpp` and
`tools/benchmark_compare.py` supply high-resolution interleaved comparisons; compile the
same driver against each unchanged core. `tools/audit/` contains reproducible diagnostics
for both the fixed SEE defect and explicitly unresolved TT/time-control findings.

Optional Python tools require Python 3.10+. Set `FORGE_BUILD_VALIDATION_TOOLS=ON` to build
the original opening generator. Fastchess and the independent chess.hpp verifier are
external test tools, not engine dependencies, and no external books/weights are bundled.
