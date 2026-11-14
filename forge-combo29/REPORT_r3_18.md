# Lazy network accumulator

Branch `grok47/r3-18-lazy-net-accumulator`, built from `e04556dd`. No new UCI option. Search options used for every check below: Threads 1, Hash 16, OwnBook false, every other option left at its default. Build:

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
```

This machine is a 4-core Intel Xeon VM, g++ 13.3, `-march=x86-64-v3` with the portable switches (no PEXT, no AVX-512). The numbers are measurements on that machine. They are not a strength result.

## Where the idea comes from

The network state is one vector per colour, each a sum of piece-square columns. A move changes only a few of those columns. This search already applied those columns inside static evaluation rather than inside `make_move`: `record_move` stored a change list, and `static_evaluate` walked back to the last finished vector and called `nnue::update`.

On an instrumented bench 13 (862329 nodes) that list was built 826208 times and the columns were added 655136 times. The gap is moves that never reach an evaluation: transposition cutoffs, positions in check, and stand-pat cutoffs. A null move was 41488 of the updates, and a null move does not change the piece set, so the copy is the same bits as the parent vector.

This change keeps that rule and tightens it. Making a move now stores only the mover, the captured piece, and the side to move. The change list is built from those facts the first time an evaluation reads that ply. A null move does not copy the vector; evaluation reads the parent. Real moves still go through the same `nnue::update` expressions as before. Nothing here is taken from another engine's source.

## Pins

Recorded on the base binary before the edit, and again on this binary after it. All three match.

| check | before | after |
| --- | ---: | ---: |
| bench 11 nodes | 312866 | 312866 |
| bench 13 nodes | 862329 | 862329 |
| startpos perft 5 | 4865609 | 4865609 |

bench 16, which is not a pin, was 3024920 nodes on every timing run of both binaries.

## Evaluation identity

Fixed seed `0x18D15C0DE` (SplitMix). Two comparisons:

1. In-process playouts, 1,000,000 positions, plus 89,232 null moves and 28,698,721 legal-move change lists. Two plies out of every seven were left unevaluated so the next evaluation had to rebuild a gap. The vector at evaluation matched `nnue::update` from the parent with `dirty_pieces`. `nnue::evaluate` matched a from-scratch `refresh` on all 1,000,000 positions (`refresh_net_mismatch 0`). The full static total matched `Evaluator::static_eval_components` on all 1,000,000 (`refresh_total_mismatch 0`). A separate catalog (start, Kiwipete, en passant, promotions, a capture promotion) checked 123 moves, including 1 en passant, 2 castles, and 16 promotions; each updated vector evaluated equal to a refresh.

2. The base binary and this binary, same seed, 1,000,000 positions, UCI `eval` with Threads 1, Hash 16, OwnBook false. All 1,000,000 lines were identical (134 seconds).

## Depth 8

10,000 positions from the same seed. Each search was `ucinewgame` then `go depth 8` on the base binary and on this binary. Best move, score, and node count matched on all 10,000 (81 seconds).

## Bench 16 timing

Five runs each, alternating base then this binary. Same nodes every time: 3024920. Time is the engine's own millisecond timer.

| run | base ms | this binary ms |
| ---: | ---: | ---: |
| 1 | 1516 | 1523 |
| 2 | 1542 | 1555 |
| 3 | 1516 | 1513 |
| 4 | 1492 | 1498 |
| 5 | 1492 | 1497 |

Base mean 1511.6 ms (spread 1492–1542). This binary mean 1517.2 ms (spread 1497–1555). The two sets overlap. This is not evidence of a speed change. Most of bench 16 still adds feature columns, because most visited positions are evaluated; the work that moved is the small change list, and the null-move copy that was removed is a few percent of the updates.

## What was not verified

- No games, so no strength claim.
- Threads other than 1.
- `UseNNUE false`. The early return to the hand-crafted eval is unchanged and was not re-run.
- The AVX-512 build (`FORGE_PORTABLE` off). This binary is the portable x86-64-v3 build.
- Hash sizes other than 16, and MultiPV other than 1.
- The timing is five runs on one shared VM, not a locked benchmark machine.
