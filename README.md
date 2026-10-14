# Chess Engine Forge

Chess Engine Forge 6.2.0 is a C++20 UCI chess engine. The 6.x series is a
strength rewrite: the move generator, search, and evaluation were rebuilt from
the ground up for playing strength, replacing the conservative 5.x search.
6.1.0 added multi-threaded search (`Threads`), tuning options and the NNUE
training tools; 6.2.0 adds a built-in engine-generated opening book with
Polyglot support, cutoff-count LMR, material correction history, new
evaluation terms with a retuned table, a faster move picker and prebuilt Zen 4
(`-march=znver4`) binaries.

## Strength

Measured on this project's reference ladder: Stockfish 19 with
`UCI_LimitStrength=true` at `UCI_Elo` 2800 and 3000, 8moves_v3 openings, one
thread each, Hash 64 MB, fastchess. See `validation/release-6.0.0/` for the
match records.

| Engine | Opponent | TC | Games | Score |
| --- | --- | --- | --- | --- |
| Forge 5.31.0 (previous release) | SF 19 @ 2800 | 10+0.1 | 20 | 10.0 % (1W 17L 2D) |
| Forge 6.0.0 | SF 19 @ 2800 | 10+0.1 | 200 | 69.0 % (118W 42L 40D), +158 Elo |
| Forge 6.0.0 | SF 19 @ 2800 | 30+0.3 | 100 | 82.5 % (79W 14L 7D), +331 Elo |
| Forge 6.1.0 | SF 19 @ 2800 | 10+0.1 | 200 | 75.0 % (134W 34L 32D), +224 Elo |
| Forge 6.2.0 (pre-release build) | SF 19 @ 3000 | 10+0.1 | 200 | 47.75 % (66W 75L 59D), -16 Elo |
| Forge 6.2.0 | SF 19 @ 3000 | 20+0.2 | 100 | 51.5 % (35W 32L 33D), +10 +/- 60 Elo |

With `Threads=4` on a four-core machine the engine scores 75 % (26W 1L 23D over
50 games at 8+0.08) against its own single-threaded build.

Stockfish's `UCI_Elo` scale is anchored to CCRL blitz ratings, so a score above
50 % against the 2800 opponent corresponds to a rating above 2800 on that scale,
and the roughly even result against the 3000 opponent places the single-threaded
engine near 3000 at blitz.

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
- Bucketed transposition table (16-byte entries, 4-way clusters, aging,
  stored static evaluation, prefetch)
- Staged move picker: hash move, SEE-filtered captures with capture history,
  killers, countermove, history-ordered quiets (checks first), losing captures
- Butterfly, continuation (1/2/4 ply), capture, and pawn- and material-keyed
  correction histories
- Late move reductions with history, PV, cut-node, check, improving and
  child-cutoff-count terms
- Late move pruning, futility pruning, reverse futility pruning, razoring,
  SEE pruning for quiets and captures, history pruning
- Null move pruning with adaptive reduction and high-depth verification
- ProbCut, internal iterative reductions, singular extensions with double and
  negative extensions and multi-cut, check extensions for safe checks
- Quiescence search with transposition table, futility and SEE pruning, and
  full evasion generation when in check
- Mate distance pruning, 50-move and insufficient-material detection
- Time management with soft/hard limits, best-move stability, effort scaling and
  falling-evaluation extension
- Lazy SMP: helper threads search the same root sharing the transposition table

Evaluation (tapered, parametrized)

- PeSTO piece-square tables with material folded in
- Mobility per piece type with pawn-restricted mobility areas
- Pawn structure (isolated, doubled, backward, connected, phalanx) in a pawn hash
- Passed pawns: rank, blockade, free/safe path, king proximity
- King safety: pawn shelter and storm, attack units with safe-check bonuses
- Threats: pawn threats and pushes, minor/rook/king threats, hanging pieces
- Bishop pair, rook on open/semi-open file and seventh rank, rook behind a
  passed pawn, outposts, long-diagonal bishops
- Material imbalance, space, weak queen, weak unopposed pawns, king-to-pawn
  distance
- Endgame scaling for opposite-coloured bishops and drawn material imbalances
- Every term is an entry in `src/eval_params_table.inc`, which the included
  Texel tuner can regenerate from self-play data

UCI

- `go` with `depth`, `nodes`, `movetime`, `wtime/btime/winc/binc`, `movestogo`,
  `mate`, `searchmoves`, `infinite`, `ponder`
- `Hash`, `Threads`, `Move Overhead`, `Ponder`, `OwnBook`, `Book File`,
  `Book Depth`, `Book Variety`, `Clear Hash` options
- Opening book: Polyglot `.bin` reader (keys validated against python-chess)
  plus an embedded engine-generated book (`src/book_data.inc`, built with
  `tools/book/bookgen expand`)
- `go perft N` diagnostic extension, `bench` speed/signature command
- Unlisted integer tuning options for every search constant (see
  `forge::tune` in `include/forge/search.hpp`), usable with
  `setoption name <Name> value <int>` for A/B testing

## Build

Requirements: CMake 3.16 or newer and a C++20 compiler (GCC 11+, Clang 14+, or MSVC).

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_NATIVE=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

`FORGE_NATIVE=ON` adds `-march=native`; omit it for a portable binary. For an
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

The engine ships with a built-in opening book generated by its own deep
searches (`OwnBook`, on by default) and can also read any Polyglot `.bin` book
(`setoption name Book File value /path/to/book.bin`). `Book Depth` limits book
use to the first N plies and `Book Variety` (0-100) controls how often a
secondary book move is chosen; set it to 0 for always-best. Book moves are used
for clock and `movetime` searches only, never for analysis (`go depth/nodes/
infinite`), pondering or `searchmoves`.

`setoption name Hash value 256` sets the transposition table size in MiB.
`setoption name Threads value 4` enables Lazy SMP with four search threads
sharing the transposition table. `setoption name Ponder value true` enables
`bestmove ... ponder ...` output and `go ponder`/`ponderhit` handling.
`bench [depth]` prints a node-count signature and speed for the built binary.

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

## Opening book tools

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_BUILD_TUNING_TOOLS=ON
cmake --build build --parallel
# engine-generated book: 3 alternatives for the first four plies, 2 for the next
# two, then the best line to ply 16, each move from a 1.5M-node search
build/forge_bookgen expand --widths 3,3,3,3,2,2 --max-ply 16 --nodes 1500000 \
  --alt-nodes 300000 --threads 4 --out src/book_data.inc
touch src/book.cpp && cmake --build build --parallel
```

`forge_bookgen openings` generates diverse, engine-vetted starting positions for
self-play, and `forge_bookgen build` tallies move statistics from PGN files
(optionally verifying every candidate with the engine) into the same format.

## Experimental NNUE evaluation

`include/forge/nnue.hpp` / `src/nnue.cpp` implement a 768 -> 256x2 SCReLU
network with lazily updated accumulators, and `tools/tune/nnue_train.cpp` trains
one from the same position files:

```sh
build/forge_nnue_train positions.txt --epochs 20 --lambda 0.5 --threads 4 \
  --validate holdout.txt --out src/nnue_weights.inc
touch src/nnue.cpp && cmake --build build --parallel   # compiles the weights in
```

When `src/nnue_weights.inc` exists the engine uses the network (option `UseNNUE`,
default true) instead of the hand-crafted evaluation. No weights are shipped:
nets trained on the few million self-play positions available so far overfit
and lose to the tuned hand-crafted evaluation (validation loss 0.037 vs 0.029).
The tooling is in place for anyone with a larger, more diverse dataset.

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
