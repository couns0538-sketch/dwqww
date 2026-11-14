# Hand-written evaluation speed (r3 19)

Branch `grok47/r3-19-faster-hce`. Search and the evaluation numbers are unchanged. This is a timing measurement on one machine, not a strength claim.

## Where the idea came from

`bench 16` was timed with `rdtsc` around each section of `evaluate_position` before any rewrite. On that run the hand-written evaluation was the large part of static evaluation, ahead of the network. Inside it, the three heaviest sections were piece evaluation, king evaluation, and threats. Pawn structure, the final taper, attack setup, passed pawns, and the piece-square term were smaller. The changes below are only those three sections, plus eval-only slider tables that those sections call. Nothing was taken from another engine. The attack sets are the ones this file already computed with `sliding_attack`.

## What changed

Piece evaluation walks knights, bishops, rooks, and queens in separate loops and keeps the running attack masks in locals. A queen's bishop ray and rook ray are computed once and reused for the weak-queen term. A rook that stands on a file with passed pawns in both directions does one real-occupancy lookup, not two. Same-color bishop pawn counts and the home-minor count are computed once per side.

King shelter loads each term once and keeps the middlegame half of that load. King danger issues the rook and bishop indexes, then the two loads.

Threats count each enemy piece type with `popcount` and add that term once with that count, instead of walking every target square.

`FORGE_PORTABLE` still leaves movegen on multiply magics (`FORGE_SPD_SLIDER_PEXT=0`). Evaluation uses a second pair of tables, filled from the same masks, indexed with `PEXT`. Empty-board and full-board attacks were checked against the multiply tables at init. The 1,000,000-position compare is the check that the values match in real positions.

## Identity

Threads 1, Hash 16, OwnBook false, every other option left at its default. Printed before any edit and again on the final binary:

| check | nodes |
| --- | ---: |
| bench 11 | 312866 |
| bench 13 | 862329 |
| go perft 5 from the start position | 4865609 |

Every `bench 16` in the table below was 3024920 nodes.

1,000,000 positions came from a deterministic legal-move walk (`tests_r3_19/identity_walk.cpp`, fixed xorshift seed). For each position the record is uncached hand-written eval, cached hand-written eval, the network term, the total, and the in-check flag. The base and new records are byte-identical (`EVAL_1M_MATCH`).

10,000 positions from the same walk were searched at depth 8 with `Searcher(16, 1)`, exclusive transposition table, info output off. That is the search `go` calls. Each record is the best move, the score, and the node count. The base and new records are byte-identical (`SEARCH_10K_MATCH`).

## bench 16

Pinned to CPU 1, base binary then new binary, five times. Release build, `g++` 13.3, `-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3`, `FORGE_PORTABLE=ON`. Times are milliseconds. Nodes were 3024920 on every run.

| pair | base ms | new ms |
| ---: | ---: | ---: |
| 1 | 1531 | 1498 |
| 2 | 1508 | 1486 |
| 3 | 1502 | 1500 |
| 4 | 1598 | 1488 |
| 5 | 1580 | 1491 |
| mean | 1543.8 | 1492.6 |

A separate loop evaluated 20,000 cached positions 21 times with no search. Three pairs, same CPU, seconds:

| pair | base | new |
| ---: | ---: | ---: |
| 1 | 0.141 | 0.135 |
| 2 | 0.138 | 0.135 |
| 3 | 0.138 | 0.134 |

The checksum of that loop matched (`hot_sum -671370`).

## Repeat on the same commit

Same binaries, still `758df95ba`, CPU 1, base then new. Every run was 3024920 nodes. Three more five-pair tables. Several pairs are only a few milliseconds apart, and both sides move by tens of milliseconds between runs.

Table A:

| pair | base ms | new ms |
| ---: | ---: | ---: |
| 1 | 1541 | 1538 |
| 2 | 1572 | 1542 |
| 3 | 1549 | 1511 |
| 4 | 1506 | 1511 |
| 5 | 1543 | 1518 |
| mean | 1542.2 | 1524.0 |

Table B:

| pair | base ms | new ms |
| ---: | ---: | ---: |
| 1 | 1599 | 1665 |
| 2 | 1644 | 1558 |
| 3 | 1617 | 1584 |
| 4 | 1560 | 1555 |
| 5 | 1517 | 1501 |
| mean | 1587.4 | 1572.6 |

Table C:

| pair | base ms | new ms |
| ---: | ---: | ---: |
| 1 | 1496 | 1555 |
| 2 | 1594 | 1534 |
| 3 | 1537 | 1504 |
| 4 | 1513 | 1493 |
| 5 | 1498 | 1590 |
| mean | 1527.6 | 1535.2 |

Fifteen pairs together: base mean 1552.4 ms, new mean 1543.9 ms.

Pins were printed again on both binaries: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609. The same 1,000,000-position eval records were written again and are byte-identical (`EVAL_1M_MATCH`).

## Not verified

Playing strength was not measured.

`/usr/bin/c++` on this machine is Clang and could not link `libstdc++`. The build used `/usr/bin/g++` with the requested CMake flags.

The depth-8 compare did not parse UCI `info` text. It compared `SearchInfo` from `Searcher::search`. Printing was off. A depth limit does not use the clock.

Only one thread was checked. Multi-thread search was not compared.
