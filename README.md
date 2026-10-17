# Chess Engine Forge

Chess Engine Forge 6.2.0 is a C++20 UCI chess engine. Version 6.0.0 rewrote
the move generator, search, and evaluation from the ground up for playing
strength, replacing the conservative 5.x search. Version 6.1.0 added
multi-threaded search (`Threads` option, Lazy SMP), a broader evaluation
correction history, capture futility pruning, and a faster default build and
move picker. Version 6.2.0 adds quiet checks in quiescence search, a
pawn-structure move-ordering history, history-aware futility pruning and
capture reductions, and thread voting for the multi-threaded search.

## Strength

Measured on this project's reference ladder: Stockfish 19 with
`UCI_LimitStrength=true UCI_Elo=2800`, 8moves_v3 openings, one thread each,
Hash 64 MB, fastchess. See `validation/release-6.0.0/` and
`validation/release-6.1.0/` for the match records.

| Engine | TC | Games | Score vs SF 19 @ 2800 |
| --- | --- | --- | --- |
| Forge 5.31.0 | 10+0.1 | 20 | 10.0 % (1W 17L 2D) |
| Forge 6.0.0 | 10+0.1 | 200 | 69.0 % (118W 42L 40D) |
| Forge 6.0.0, same machine as the 6.1.0 row | 10+0.1 | 100 | 70.5 % (63W 22L 15D) |
| Forge 6.1.0, one thread | 10+0.1 | 100 | 71.0 % (67W 25L 8D) |

Stockfish's `UCI_Elo` scale is anchored to CCRL blitz ratings, so a score above
50 % against this opponent corresponds to a rating above 2800 on that scale.
The ladder saturates at this level and does not separate 6.0.0 from 6.1.0;
the direct comparisons are in `validation/release-6.1.0/README.md`:
`Threads=2` beats `Threads=1` by +81 +/- 40 Elo at 5+0.05, and the
single-thread changes are positive per node (correction history +12 to +24
Elo at 100k nodes, capture futility +11 Elo at 25k nodes) and neutral to
slightly positive at blitz time controls. The 6.2.0 search changes were
each measured in 1000-game fixed-node self-play against 6.1.0 and then
confirmed together at 3+0.03: **6.2.0 beats 6.1.0 by +17 +/- 22 Elo**
(300 games, one thread, LOS 94 %). The records are in
`validation/release-6.2.0/README.md`.

## Features

Board and move generation

- Magic bitboard sliding attacks, bitboard pawn/knight/king generation
- Pseudo-legal generation with cheap per-move legality filtering, incremental
  checkers, pseudo-legality verification for hash moves
- Incremental Zobrist and pawn-structure keys, FEN-level en-passant legality
- Static exchange evaluation (`see_ge`) with x-ray attackers
- Repetition detection that distinguishes game history from search-tree repetitions
- Strict FEN validation, perft

Search

- Iterative deepening principal-variation search with aspiration windows
- Lazy SMP: `Threads` worker threads share the transposition table; odd
  helpers skip the first iteration so the trees diverge; the best move is
  chosen by thread voting (score- and depth-weighted support per move)
- Bucketed transposition table (16-byte entries, 4-way clusters, aging,
  stored static evaluation, prefetch)
- Staged move picker: hash move, SEE-filtered captures with capture history,
  killers, countermove, history-ordered quiets (checks first), losing captures
- Butterfly, continuation (1/2/4 ply), capture and pawn-structure histories
- Evaluation correction histories keyed by pawn structure, each side's
  non-pawn placement, minor and major piece configurations, and the last two
  moves
- Late move reductions with quiet- and capture-history, PV, cut-node, check,
  and improving terms
- Late move pruning, history-aware futility pruning for quiets, futility
  pruning for captures, reverse futility pruning, razoring,
  SEE pruning for quiets and captures, history pruning
- Null move pruning with adaptive reduction and high-depth verification
- ProbCut, internal iterative reductions, singular extensions with double and
  negative extensions and multi-cut
- Quiescence search with transposition table, futility and SEE pruning,
  quiet checks at the first ply, and full evasion generation when in check
- Mate distance pruning, 50-move and insufficient-material detection
- Time management with soft/hard limits, best-move stability and effort scaling

Evaluation (tapered, parametrized)

- PeSTO piece-square tables with material folded in
- Mobility per piece type with pawn-restricted mobility areas
- Pawn structure (isolated, doubled, backward, connected, phalanx) in a pawn hash
- Passed pawns: rank, blockade, free/safe path, king proximity
- King safety: pawn shelter and storm, attack units with safe-check bonuses
- Threats: pawn threats and pushes, minor/rook/king threats, hanging pieces
- Bishop pair, rook on open/semi-open file and seventh rank, outposts
- Endgame scaling for opposite-coloured bishops and drawn material imbalances
- Every term is an entry in `src/eval_params_table.inc`, which the included
  Texel tuner can regenerate from self-play data

UCI

- `go` with `depth`, `nodes`, `movetime`, `wtime/btime/winc/binc`, `movestogo`,
  `mate`, `searchmoves`, `infinite`, `ponder`
- `Hash`, `Threads`, `Move Overhead`, `Ponder`, `Clear Hash` options
- `go perft N` diagnostic extension

## Build

Requirements: CMake 3.16 or newer and a C++20 compiler (GCC 11+, Clang 14+, or MSVC).

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_NATIVE=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

`FORGE_NATIVE=ON` adds `-march=native`. Without it the x86-64 build still
enables the POPCNT instruction (available on every x86-64 CPU since 2008),
which is worth about 10 % of search speed; `FORGE_PORTABLE=ON` produces a
baseline-ISA binary for older hardware. For an
AddressSanitizer/UndefinedBehaviorSanitizer build:

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
go depth 20
quit
```

`setoption name Hash value 256` sets the transposition table size in MiB.
`setoption name Threads value 4` searches with four threads (Lazy SMP; the
transposition table is shared, everything else is per thread).
`setoption name Ponder value true` enables `bestmove ... ponder ...` output and
`go ponder`/`ponderhit` handling.

## Tuning the evaluation

The evaluation is linear in its parameters, so it can be refitted to game data.

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_BUILD_TUNING_TOOLS=ON
cmake --build build --parallel
# self-play games with fastchess, UCI notation:
fastchess -engine cmd=build/forge name=A -engine cmd=build/forge name=B \
  -each nodes=10000 tc=inf -openings file=book.pgn format=pgn order=random plies=16 \
  -rounds 10000 -games 2 -repeat -concurrency 4 -pgnout file=games.pgn notation=uci
build/forge_extract games.pgn > positions.txt
build/forge_texel positions.txt --epochs 500 --out src/eval_params_table.inc
```

`forge_extract` keeps quiet, non-book positions with the engine's search score;
`forge_texel` fits all parameters with Adam against a blend of game result and
search score and rewrites the parameter table.

## Testing

- `tests/tests.cpp`: FEN validation, perft, make/unmake and hash consistency,
  pseudo-legality, SEE, evaluation symmetry, transposition table, tactical
  search cases, searchmoves and terminal-root behaviour
- `tools/uci_regression.py`: UCI protocol behaviour against the real binary
- `tools/ponder_regression.py`: pondering protocol
- `bench/benchmark.cpp`: perft and fixed-depth search workload (`build/forge_bench`)
- `tools/match/run_match.py`: reproducible fastchess match runner

## Architecture

- `include/forge/bitboard.hpp`, `src/bitboard.cpp`: bitboard utilities, magic attack tables
- `include/forge/board.hpp`, `src/board.cpp`: position, FEN, move generation, legality, SEE
- `include/forge/eval.hpp`, `include/forge/eval_params.hpp`, `src/eval.cpp`,
  `src/eval_params.cpp`, `src/eval_params_table.inc`: evaluation and its parameters
- `include/forge/search.hpp`, `src/search.cpp`: transposition table, move picker,
  search, time management
- `src/uci.cpp`: UCI loop and asynchronous search control
- `tools/tune/`: position extractor and Texel tuner

## License

MIT. The engine has no third-party runtime dependencies. Fastchess and
Stockfish are external testing tools and are not bundled.
