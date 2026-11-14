# Search plumbing, round 3 agent 20

The search is unchanged. Bench 11, bench 13, and perft 5 from the start position are the same numbers as the base at `e04556dd`. Two disjoint sets of 10,000 positions, each searched at depth 8 with Threads 1, Hash 16, and OwnBook false, returned the same best move, score, and node count.

This is a timing measurement on one machine. It is not a strength result.

## Pins

Printed on the unmodified binary before any edit, and again on the final binary:

| check | before | after |
| --- | ---: | ---: |
| bench 11 nodes | 312866 | 312866 |
| bench 13 nodes | 862329 | 862329 |
| perft 5 from the start position | 4865609 | 4865609 |

bench 16 nodes stayed 3024920. Perft 4 on the eight bench positions matched the base as well (197281, 4085603, 3269539, 43238, 1635300, 3813973, 24244, 2433324).

## Where the time was

`perf` task-clock on bench 16, one process, the unmodified binary, 3129 samples. Evaluation is listed only so the rest of the ranking is clear. It was not changed.

| share | samples | function |
| ---: | ---: | --- |
| 17.03% | 533 | evaluate_position |
| 11.79% | 369 | nnue::update |
| 10.10% | 316 | Worker::search |
| 7.93% | 248 | MovePicker::pick_best |
| 5.98% | 187 | nnue::evaluate |
| 5.15% | 161 | generate_pseudo_legal |
| 5.11% | 160 | MovePicker::next |
| 3.74% | 117 | see_ge |
| 3.48% | 109 | corrected_eval |
| 2.78% | 87 | is_legal |
| 2.56% | 80 | init_magics |
| 2.36% | 74 | attackers_to |
| 1.79% | 56 | TT probe |
| 1.66% | 52 | refresh_king_lines |
| 1.57% | 49 | introsort (inside pick_best) |
| 1.41% | 44 | unmake_move |
| 1.05% | 33 | make_move |
| 0.93% | 29 | gives_check |
| 0.93% | 29 | key_after |

Outside evaluation, the three hottest areas were:

1. Move picker. `pick_best` 7.93%, `next` 5.11%, and the sort it calls 1.57%. `see_ge` (3.74%) is the capture filter inside the picker and is also called from the search.
2. Move generation. `generate_pseudo_legal` 5.15%, `is_legal` 2.78%, king-line refresh 1.66%, `gives_check` 0.93%, and the magic-number search at startup 2.56%.
3. Make and unmake. `make_move` 1.05%, `unmake_move` 1.41%, and `attackers_to` 2.36%, which make_move used to find checkers.

The hash probe was next, at 1.79% plus `key_after` at 0.93%.

The same sample of the final binary (3005 samples) still spends most of its time in evaluation. `pick_best` fell from 248 samples to 178. The magic search is gone. `attackers_to` dropped out of the list above 0.7%. `next` rose, because the best score is now recorded while the moves are scored, so that work sits in `next` instead of in a later scan.

## What changed, and where the idea came from

Every change is local to this engine. Nothing was taken from another engine's source, constants, or tables. The profile above is the reason each spot was touched.

Move picker. The first move handed out is the lowest-index move with the strictly highest score. That index is known as soon as the moves are scored, so the first pick no longer walks the list. Later picks still walk, four scores at a time, and a tie still keeps the earlier index. The tail is still `std::sort` with `score >`. A stable insertion sort was tried in its place. Bench 11 moved from 312866 nodes to 292627, so the insertion sort was removed and `std::sort` stayed.

Move generation. Captures, quiets, and the full list are separate compilations of one generator, so the capture-or-quiet flag is fixed in each one. The order of moves is the order the old generator emitted. Slider attacks use the BMI2 indexer that was already in `bitboard.cpp` when the compiler target defines `__BMI2__`. The required build is `-march=x86-64-v3`, which has BMI2. That indexer returns the same attack sets as the multiply magics and does not search for magic numbers at startup. A CPU without BMI2 still gets the multiply indexer. Empty-board rook and bishop rays are constant per square, so they are stored once at startup and read back. They are the same bitboards `rook(square, 0)` and `bishop(square, 0)` already produced, and they are what king-line refresh and the exchange pin test were computing.

Make and unmake. After a move, the checkers are the mover's attacks on the opponent king. The other side's pieces cannot be checkers, so they are not gathered. The bitboard is the one `attackers_to` was masked down to.

Legality and discovered check. The usual question is a pin test or a check-square test on lines that were already built for the position. Those two tests are inlined at the call. Check, en passant, king moves, castling, and promotions still use the full test.

Hash table. The owned probe does not build a stripe lock. The four-entry scan stays a short loop: a matching occupied entry is a hit, the first empty entry is the replacement, and a full cluster keeps the lowest depth-minus-age entry, ties keeping the earlier slot. An earlier fully unrolled form of that choice spilled registers and was slower, so the loop was kept.

No UCI option was added.

## Depth 8

Threads 1, Hash 16, OwnBook false, every other option left at its default. Each position was `ucinewgame`, then `position fen`, then `go depth 8`, and the engine was allowed to finish before the next position.

The positions are random legal walks of 12 to 39 plies from the start position, produced with this engine's own move list. Two seeds, no shared position.

| set | positions | best move, depth, score, nodes |
| --- | ---: | --- |
| seed 0x20c0ffee | 10000 | all equal to the base |
| seed 0xB16B00B5 | 10000 | all equal to the base |

The first set searched 58715778 nodes in total, on both binaries.

## Bench 16 timing

Five fresh processes each, base then the new binary, on this machine (4-thread Intel Xeon, x86-64-v3). The number is the `time` field from `bench 16`, in milliseconds. Nodes were 3024920 on every run.

| run | base | new |
| ---: | ---: | ---: |
| 1 | 1520 | 1478 |
| 2 | 1515 | 1496 |
| 3 | 1517 | 1481 |
| 4 | 1609 | 1480 |
| 5 | 1509 | 1565 |
| mean | 1534 | 1500 |

The mean gap is 34 ms. Run 5 went the other way, and run 4's base time is high, so one bench 16 is too noisy to read on its own. An earlier five on the same two binaries, taken the same way, averaged 1524 ms and 1464 ms, and every pair was faster. A second bench inside the same process was also lower for the new binary on the quiet pairs, so the gap is not only the missing magic search at startup.

## Not verified

No games were played, so this says nothing about strength. Only Threads 1 was searched. Time-control, ponder, and MultiPV were not compared. The multiply-magic slider path was not timed, because this CPU has BMI2. Depths other than the pins, perft 4 on the bench set, and depth 8 were not compared.
