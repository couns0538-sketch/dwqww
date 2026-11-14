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

This change keeps that rule and tightens it. Making a move stores the mover, the captured piece, and the side, and builds the change list then, before the move is played. The feature columns are still added only when an evaluation reads that ply. A null move does not copy the vector; evaluation reads the parent. A quiet move or a capture writes each new hidden unit with the same sum as `nnue::update`, and the output layer consumes that unit from the register that was just stored, in the same lane order as `nnue::evaluate`. Castling and every other shape still call `update` and then `evaluate`. Nothing here is taken from another engine's source.

## Pins

Recorded on the base binary before the edit, and again on this binary after the fused output pass. All three match.

| check | before | after |
| --- | ---: | ---: |
| bench 11 nodes | 312866 | 312866 |
| bench 13 nodes | 862329 | 862329 |
| startpos perft 5 | 4865609 | 4865609 |

bench 16, which is not a pin, was 3024920 nodes on every timing run of both binaries.

## Evaluation identity

Fixed seed `0x18D15C0DE` (SplitMix). Two comparisons:

1. In-process playouts, 1,000,000 positions, plus 89,232 null moves and 28,698,721 legal-move change lists. Two plies out of every seven were left unevaluated so the next evaluation had to rebuild a gap. The vector at evaluation matched `nnue::update` from the parent with `dirty_pieces`. `nnue::evaluate` matched a from-scratch `refresh` on all 1,000,000 positions (`refresh_net_mismatch 0`). The full static total matched `Evaluator::static_eval_components` on all 1,000,000 (`refresh_total_mismatch 0`). A separate catalog (start, Kiwipete, en passant, promotions, a capture promotion) checked 123 moves, including 1 en passant, 2 castles, and 16 promotions; each updated vector evaluated equal to a refresh.

2. The base binary and this binary, same seed, 1,000,000 positions, UCI `eval` with Threads 1, Hash 16, OwnBook false. Re-run after the fused output pass: all 1,000,000 lines were identical.

## Depth 8

10,000 positions from the same seed, re-run after the fused output pass. Each search was `ucinewgame` then `go depth 8` on the base binary and on this binary. Best move, score, and node count matched on all 10,000.

## Bench 16 timing

Fresh alternating runs after the fused output pass, base then this binary. Same nodes every time: 3024920. Time is the engine's own millisecond timer on this VM. This is not a strength result.

| run | base ms | this binary ms |
| ---: | ---: | ---: |
| 1 | 1509 | 1440 |
| 2 | 1493 | 1450 |
| 3 | 1496 | 1441 |
| 4 | 1493 | 1444 |
| 5 | 1496 | 1438 |

Base mean 1497.4 ms (spread 1493–1509). This binary mean 1442.6 ms (spread 1438–1450). On this run the two spreads do not overlap. An earlier build that only deferred the change list, and copied nothing on a null move, was measured at a mean of 1517.2 ms against a base mean of 1511.6 ms; that version did not help. The lower times above are from folding the output layer into the feature update.

## What was not verified

- No games, so no strength claim.
- Threads other than 1.
- `UseNNUE false`. The early return to the hand-crafted eval is unchanged and was not re-run.
- Hash sizes other than 16, and MultiPV other than 1.
- The portable timing above is five runs on one shared VM. The owner build is in the follow-up.

## Follow-up: AVX-512 fused pass

The first fused kernel was compiled only for AVX2 when `FORGE_SPD_NNUE_ZMM` is off. The owner build turns that kernel off and uses the 512-bit evaluate. `apply_and_evaluate` now has a 512-bit path with the same feature sums as `update` and the same output order as that evaluate: one 512-bit sum, lane j accumulating hidden units j, j+16, j+32, …, with a separate multiply and add. No `FORGE_*` macro is defined or undefined in the sources, and `CMakeLists.txt` is unchanged.

This machine has AVX-512F and BMI2, so the owner configuration (portable off, `-march=x86-64-v4`) was built for `e04556dd` and for this branch. Pins on this binary: bench 11 **312866**, bench 13 **862329**, startpos perft 5 **4865609**.

`tests_r3fu_18/fused_identity.cpp` drives `Worker::static_evaluate`, including null moves, promotions, castling, and en passant, and the 2-change and 3-change fused shapes. It prints the mismatch counts and exits non-zero if either is non-zero. One million fixed-seed playouts on the owner build:

```
refresh_net_mismatch 0
refresh_total_mismatch 0
coverage static_evals 836716 fused2 629949 fused3 56788 promo 167 castle 944 ep 123 null 89238
```

UCI `eval` against the owner-build base binary: 1,000,000 / 1,000,000 lines identical. `go depth 8`: 10,000 / 10,000 matched on best move, score, and nodes.

Bench 16, seven alternating runs after those jobs, owner base then this binary. Every run was 3024920 nodes. The millisecond timer on this VM swings by hundreds of milliseconds, and the spreads overlap, so this table is not a speed result.

| run | base ms | this binary ms |
| ---: | ---: | ---: |
| 1 | 2600 | 2352 |
| 2 | 2230 | 1873 |
| 3 | 2773 | 1891 |
| 4 | 1941 | 2714 |
| 5 | 1999 | 2578 |
| 6 | 2612 | 2524 |
| 7 | 2459 | 2008 |

Base mean 2373.4 ms (spread 1941–2773). This binary mean 2277.1 ms (spread 1873–2714).
