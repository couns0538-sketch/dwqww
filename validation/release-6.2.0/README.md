# Release 6.2.0 strength validation

All matches: fastchess (commit 60d7a7a), `-repeat` colour-swapped pairs,
`-recover`, openings `tools/openings/forge-10000.epd` in random order, Hash
32 MB, one thread unless stated, 4-core Intel Xeon VM, three games at a time.
Both sides of every match were built from this tree with the same compiler
(GCC 13.3, Release, `-mpopcnt`). The 6.1.0 reference ("base") is commit
193a91e, the head of the 6.1.0 branch.

Fixed-node self-play (`-each nodes=25000`, no adjudication of any kind)
isolates a search change from machine load and from speed: both sides
search exactly 25,000 nodes per move (roughly depth 9-10 for this engine),
so a positive result means the change makes the tree better per node. A
change that only makes the tree smaller per depth cannot score in this
setting, and a change that is neutral here is neutral in strength at this
budget. Each component was tested on its own against the base, 1000 games
(500 opening pairs), before being combined.

## Single-thread component results (25,000 nodes per move, 1000 games each)

| Change under test | W / L / D | Score | Elo | Verdict |
| --- | --- | --- | --- | --- |
| Quiet checks at the first quiescence ply | 397 / 375 / 228 | 51.1 % | **+7.6 +/- 14.3** (LOS 85 %) | adopted |
| History-aware quiet futility + capture-history LMR | 393 / 371 / 236 | 51.1 % | **+7.6 +/- 14.0** (LOS 86 %) | adopted |
| Pawn-structure history, ordering only | 383 / 376 / 241 | 50.35 % | +2.4 +/- 13.5 (LOS 64 %) | adopted (18 % smaller tree per depth) |
| Pawn-structure history also feeding pruning/reductions | 100 / 122 / 78 (300 games, stopped) | 46.3 % | about -26 (LOS 1.5 %) | abandoned |
| Check extension removed | 387 / 386 / 227 | 50.05 % | +0.4 +/- 14.6 | adopted as a simplification |
| One ply less LMR in PV nodes | 370 / 377 / 253 | 49.65 % | -2.4 +/- 14.4 | dropped (17 % more nodes per depth) |
| Singular extensions from depth 6 instead of 7 | 383 / 381 / 236 | 50.1 % | +0.7 +/- 14.1 | dropped (no gain) |
| Quiescence futility margin 220 instead of 160 | 381 / 381 / 238 | 50.0 % | 0.0 +/- 14.7 | dropped (no gain) |
| Negative extensions -3 / -2 instead of -2 / -1 | 377 / 374 / 249 | 50.15 % | +1.0 +/- 14.0 | dropped (no gain; 28 % fewer nodes per depth) |
| 4-ply continuation history added to the quiet history | 374 / 377 / 249 | 49.85 % | -1.0 +/- 14.1 | dropped |
| Evaluation table refitted (Texel, 251k positions from these matches) | 396 / 388 / 216 | 50.4 % | +2.8 +/- 14.2 | dropped (no gain over the 1.72M-position fit) |

The refit used `forge_extract` on the UCI-notation PGNs of the fixed-node
matches (3,399 games, 251,362 quiet positions) and `forge_texel` with the
default settings (300 epochs, K = 2.9 on this data). The fitted table moved
546 of 614 parameters by 9.6 centipawns on average (middlegame plus endgame
value) and did not play better, so the 6.0.0 table stays.

The four adopted changes together make the depth-13 `bench` tree 1,390,079
nodes against 1,188,868 for 6.1.0 (quiescence checks add nodes per depth;
the pawn history and the removed extension remove them). The check-aware
generator (below) changes only the tie order between equally scored
evasions and moves the signature to 1,234,322.

## Single-thread aggregate results

| Match | TC | Games | W / L / D | Score | Elo |
| --- | --- | --- | --- | --- | --- |
| Adopted search changes, first build (7 % slower than 6.1.0) vs 6.1.0 | 3+0.03 | 300 | 105 / 112 / 83 | 48.8 % | -8 +/- 24 |
| 6.2.0 final (same tree, 3 % faster than 6.1.0) vs 6.1.0 | 3+0.03 | 300 | 108 / 93 / 99 | 52.5 % | **+17 +/- 22** (LOS 94 %) |

The first row is what prompted the speed investigation. Interleaved
`bench 15` medians on the idle machine put the first build at 0.924x the
node rate of 6.1.0; the quiescence checks alone accounted for it (0.942x),
not through their move generation (replacing the full quiet generation by
a direct checking-move generator only moved it to 0.946x) but through the
in-check quiescence nodes they add, which were the most expensive nodes in
the engine because an in-check position generated every pseudo-legal move
and legality-tested each one. The check-aware generator makes those nodes
cheap: the final build runs at 1.026-1.032x the node rate of 6.1.0 (two
measurements) and 1.127x the first build, with the same search tree.

## Multi-threading

Thread voting cannot be measured at fixed nodes (helpers run until the main
thread stops) and a two-thread time-control match occupies the whole
machine, so the evidence is a sanity match, below, plus the design (the
same vote used by Stockfish and others): each thread backs its best move
with `(score - worst score + 10) * depth`, the move with the most support
wins, ties go to the deeper thread, mate scores are compared directly.

| Match | TC | Games | W / L / D | Score | Elo |
| --- | --- | --- | --- | --- | --- |
| 6.2.0 `Threads=2` vs 6.2.0 `Threads=1` | 10+0.1, one game at a time | 24 | 9 / 3 / 12 | 62.5 % | +89 +/- 69 (LOS 99.6 %) |

The figure is consistent with the +81 +/- 40 measured for 6.1.0 at 5+0.05
over 100 games; it shows the voting pool is sound, not how much the vote
itself is worth.

## Speed

Compiler-level options were measured and rejected: `-flto`,
profile-guided optimisation and the quiet-only move generation are all
within the +/-2 % run-to-run noise of this VM (interleaved `bench 15`
medians), so none is advertised as a speed-up. The pawn-structure history
costs under 1 % of nodes per second; the history-aware futility change
measured 0.98x (noise level). The check-aware move generation is the one
real speed change of the release; see the aggregate results above.

## Sanity

- `ctest`: 4/4 suites (C++ tests, match-tool tests, UCI regression, ponder
  regression) with GCC Release `-Wall -Wextra -Wpedantic -Wconversion -Wshadow
  -Werror`.
- ASan+UBSan build (`-O1`): 4/4 CTest suites; the sanitizer binary ran
  `Threads=4` through `go movetime`, `go depth`, `go infinite` + `stop`,
  `go nodes` and `ucinewgame` without a report.
- Single-thread `bench` node signature is identical before and after the
  thread-voting change, the quiet-generation change and the direct
  checking-move generator; perft 4865609 (start position, depth 5) /
  4085603 (Kiwipete, depth 4) / 11030083 (position 3, depth 6) after the
  check-aware generator, and the UCI regression's reference perfts pass.
