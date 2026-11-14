# r3-03 LmrSignedCorrection

## Where the idea comes from

The change is the requested quiet-move late-move reduction: add a signed fraction of a ply taken from this engine's own correction history. No formula, constant, or table was taken from another engine.

`Worker::update_correction` in `forge-combo29/src/search.cpp` already stores a signed residual of the search score against the static eval. The pawn-structure table is always updated. The material table is updated when `MaterialCorrectionWeight` is non-zero (the default is 100). The two non-pawn tables are updated only when `NonPawnCorrection` is on (default off). `Worker::corrected_eval` adds that same blend to the uncorrected evaluation. The search keeps both numbers on the stack: `raw_eval` is the uncorrected eval, `static_eval` is the eval after the correction. Their difference is the signed correction in centipawns. A negative difference means results have come back worse than the uncorrected evaluation. A positive difference means they have come back better.

The scale is local to this patch. `CorrectionLimit / CorrectionGrain` caps one table at 32 centipawns, so the integer adjustment stays a few plies even if a table saturates. Eight centipawns count as one ply. Anything smaller is a fraction of a ply and C++ integer division drops it. Eight was chosen so the adjustment is on the scale of the correction the eval already applies, and so a depth-13 bench with the option on visits a different node count. It was not tuned for strength, and this report does not claim a strength result.

## Behaviour

One new UCI check option, `LmrSignedCorrection`, default `false`. It is printed in the `uci` answer. With it left off, the new branch is not taken.

With it on, inside the existing late-move reduction of a quiet move (after the history, check, cut-node, and related adjustments already there), the reduction becomes:

```
reduction - (static_eval - raw_eval) / 8
```

and is then clamped so it is never negative. The node is skipped when either eval is `ValueNone` (in check) or the difference is zero, so a zero correction leaves the reduction value untouched. Noisy late-move reductions are unchanged. `LmrDeeperShallower`, `NonPawnCorrection`, and `ContHist4PlyRead` stay independent and default off.

`apply_lmr_signed_correction` in `forge-combo29/include/forge/search.hpp` is the clamp and the division. The search call site is the quiet late-move block in `Worker::search`.

Source diff against `e04556dd` in `forge-combo29/src` and `forge-combo29/include`: 24 insertions, 3 deletions.

## Default engine

Build:

```
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
```

`/usr/bin/c++` on this machine is Clang and did not link (`cannot find -lstdc++`). The binary that produced the numbers below is g++ 13.3.0 with those cmake flags. Threads 1, Hash 16, OwnBook false, every option at default.

Before the edit, and again after it:

- bench 11: 312866
- bench 13: 862329
- go perft 5 from the start position: 4865609

Setting the option true and then false restores bench 13 to 862329. An unrecognized value prints `info string invalid value for option LmrSignedCorrection` and leaves the stored value alone.

## Option on

`setoption name LmrSignedCorrection value true`, then bench 13: **1244366** nodes. That is the same bench command and the same 16 MB hash the default bench uses. The count differs from 862329, so the option is live.

## Sanitizer

`forge-combo29/tests_r3_03/lmr_signed_correction_test.cpp` was compiled with the same engine sources and the same `FORGE_*` macros as the release build, plus `-O2 -fsanitize=address,undefined -fno-sanitize-recover=address,undefined`. The run used `halt_on_error=1` and `detect_leaks=1`.

The test checks the signed fraction and the zero floor directly, then plays 200 searches to depth 10 with the option on (threads 1, hash 16, history and hash cleared between searches). The positions are the start position plus 199 other positions from a fixed-seed walk of legal moves. Every returned best move was in the legal move list and passed `is_pseudo_legal` and `is_legal`. Every move in the principal variation was legal in the position where it was played. Exit code 0. No AddressSanitizer or UndefinedBehaviorSanitizer diagnostic.

## Re-check

Fresh runs on `grok47/r3-03-lmr-signed-correction` at `bbc7831ed`, same release binary, Threads 1, Hash 16, OwnBook false. 2026-11-14T13:54Z:

- perft 5: 4865609
- bench 11: 312866
- bench 13: 862329
- bench 13 with `LmrSignedCorrection` on: 1244366
- option set back to false: bench 11 = 312866, bench 13 = 862329

The depth-10 sanitizer binary was run twice after that, 200 searches each, option on, `halt_on_error=1` and `detect_leaks=1`. Both exited 0. Every best move and every principal-variation move was legal. No AddressSanitizer or UndefinedBehaviorSanitizer diagnostic. This is not a strength result.

2026-11-14T14:15Z, same binary: perft 5 = 4865609, bench 11 = 312866, bench 13 = 862329, bench 13 with the option on = 1244366.

2026-11-14T14:35Z, same commands again, plus a third sanitizer pass of 200 depth-10 searches. perft 5 = 4865609, bench 11 = 312866, bench 13 = 862329, bench 13 with the option on = 1244366. Sanitizer exit 0, every returned move legal, no sanitizer diagnostic. No strength claim.

## Not measured

No games were played. The node-count change is not a strength result.

option name LmrSignedCorrection type check default false
bench 13 with LmrSignedCorrection on: 1244366
