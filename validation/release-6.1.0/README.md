# Release 6.1.0 strength validation

All matches: fastchess (commit 60d7a7a), `-repeat` colour-swapped pairs,
`-recover`, openings `tools/openings/forge-10000.epd` in random order, Hash
32 MB (16 MB for fixed-node games), one thread unless stated, 4-core Intel
Xeon VM, three games at a time. Both sides of every match were built from
this tree with the same compiler (GCC 13.3, Release, `-mpopcnt`), so none of
the differences below is a build-flag artefact. The 6.0.0 reference ("base")
is commit 68f0112.

Fixed-node self-play (`-each nodes=N tc=inf`) isolates search changes: it is
deterministic per node budget and unaffected by machine load, but it does not
reward speed. 25,000 nodes is roughly depth 9-10 for this engine, 100,000
nodes roughly depth 12-13; at 3+0.03 and 5+0.05 on this machine the engines
average depth 16-18. "Adjudicated" games used draw adjudication from move 40
(8 moves inside +/-15 cp) and resignation after 4 moves beyond 600 cp.

## Multi-threading

| Match | TC | Games | W / L / D | Score | Elo |
| --- | --- | --- | --- | --- | --- |
| 6.1.0 `Threads=2` vs 6.1.0 `Threads=1` | 5+0.05, one game at a time | 100 | 41 / 18 / 41 | 61.5 % | **+81 +/- 40** (LOS 100 %) |

## Single-thread component results

| Change under test | Opponent | Budget | Games | Score | Elo |
| --- | --- | --- | --- | --- | --- |
| Selection move picker (speed only; commit c3bdc35) | 6.0.0 | 3+0.03 | 300 | 51.2 % | +8 +/- 20 (LOS 78 %) |
| Extended correction history | same tree without it | 25k nodes, adjudicated | 1000 | 49.8 % | -2 +/- 14 |
| Extended correction history | same tree without it | 100k nodes, adjudicated | 400 | 53.5 % | **+24 +/- 22** (LOS 98.7 %) |
| Extended correction history | same tree without it | 100k nodes, no adjudication | 300 | 51.7 % | **+12 +/- 17** (LOS 91 %) |
| Capture futility pruning | same tree without it | 25k nodes, adjudicated | 1000 | 51.6 % | **+11 +/- 14** (LOS 94 %) |
| Fail-low bonus for the refuting move (dropped) | same tree without it | 25k nodes, adjudicated | 1000 | 49.7 % | -2 +/- 15 |
| Correction update clamp +/-32 cp instead of +/-8 cp (not adopted) | current clamp | 25k nodes, adjudicated | 1000 | 50.7 % | +5 +/- 14 |
| Falling-score time factor (dropped) | 6.0.0 | 5+0.05 | 97 | 47.4 % | tracked the version with it exactly; identical time usage |

The correction-history gain grows with depth, as expected for a term that
learns from search results; the 25,000-node test is too shallow to show it.

## Single-thread aggregate results

| Match | TC | Games | W / L / D | Score | Elo |
| --- | --- | --- | --- | --- | --- |
| All changes, first key implementation (8 % slower) | 5+0.05 | 300 | 92 / 108 / 100 | 47.3 % | -18 +/- 19 |
| All changes, final key implementation | 3+0.03 | 300 | 100 / 98 / 102 | 50.3 % | +2 +/- 19 |
| All changes plus the dropped fail-low bonus | 5+0.05 | 237 | 76 / 71 / 90 | 51.1 % | +7 +/- 25 |
| All changes plus the dropped fail-low bonus | 25k nodes, adjudicated | 400 | 161 / 147 / 92 | 51.8 % | +12 +/- 21 |

The first row is what prompted the speed investigation: maintaining the new
piece-class keys inside `put_piece`/`remove_piece`/`move_piece` cost about
8 % of nodes per second (`piece_type`'s modulo, branches, and dependent
read-modify-write chains on every placement). Moving the update into
`make_move` registers with `Undo` restore recovered about half of that; the
remaining cost is the price of the correction tables. Time-control matches
between near-equal versions of this engine draw 55-65 % of games, so 300
games only resolve differences of about 20 Elo; the per-node component
results above are the evidence that the single-thread changes are positive,
and the time-control rows show they are not negative.

## Speed (bench, same machine, single thread, measured back to back)

| Build | bench 13 nodes | Mnps |
| --- | --- | --- |
| 6.0.0 portable default (libgcc popcount) | 1,209,020 | 1.84 |
| 6.0.0 with `-mpopcnt` (new default flags) | 1,209,020 | 2.03 |
| 6.0.0 with `-march=native` | 1,209,020 | 2.09 |
| 6.1.0 picker commit only | 989,778 | about 1.12x 6.0.0 per node |
| 6.1.0 final | 1,188,868 | about 1.05x 6.0.0 per node |

Node counts differ between versions because move ordering changed; the
per-node ratios come from interleaved `bench 12` runs under identical load.

## Context: choice of base

Two 6.0.0 candidates existed as open pull requests when this work started.
Head-to-head at 5+0.05 (60 games, identical portable builds), the bitboard
rewrite (PR #2, this tree's base) beat the selective-search branch (PR #1)
49 / 2 / 9, +366 +/- 108 Elo, so 6.1.0 builds on PR #2.

## Reference ladder

See `stockfish-ladder.md` in this directory (added when the matches finish)
for Stockfish 19 `UCI_Elo 2800` results measured on this machine for both
6.0.0 and 6.1.0.

## Sanity

- `ctest`: 4/4 suites (C++ tests, match-tool tests, UCI regression, ponder
  regression) with GCC Release `-Wall -Wextra -Wpedantic -Wconversion -Wshadow
  -Werror`, and with ASan+UBSan (`-O1`).
- ASan+UBSan binary exercised with `Threads=4`/`3` through `go movetime`,
  `go depth`, `go infinite` + `stop`, `go nodes`, `ucinewgame`: clean.
- Single-thread `bench` node signature is identical before and after the
  Lazy SMP change and before and after the key-maintenance rewrite
  (1,188,868 at depth 13).
