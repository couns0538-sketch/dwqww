# r3-03 LmrSignedCorrection

## Where the idea comes from

The change is the requested quiet-move late-move reduction: add a signed fraction of a ply taken from this engine's own correction history. No formula, constant, or table was taken from another engine.

`Worker::update_correction` in `forge-combo29/src/search.cpp` already stores a signed residual of the search score against the static eval. The pawn-structure table is always updated. The material table is updated when `MaterialCorrectionWeight` is non-zero (the default is 100). The two non-pawn tables are updated only when `NonPawnCorrection` is on (default off). `Worker::corrected_eval` adds that same blend to the uncorrected evaluation. The search keeps both numbers on the stack: `raw_eval` is the uncorrected eval, `static_eval` is the eval after the correction. Their difference is the signed correction in centipawns. A negative difference means results have come back worse than the uncorrected evaluation. A positive difference means they have come back better.

The first draft used one ply per 8 centipawns with no cap. The follow-up below replaces that. The current rule is `correction_cp / 64` rounded toward zero, then limited to -1..+1 ply. It was not tuned for strength, and this report does not claim a strength result.

## Behaviour

One new UCI check option, `LmrSignedCorrection`, default `false`. It is printed in the `uci` answer. With it left off, the new branch is not taken.

With it on, inside the existing late-move reduction of a quiet move (after the history, check, cut-node, and related adjustments already there), the reduction becomes:

```
delta = clamp(correction_cp / 64, -1, +1)   # division rounds toward zero
reduction = max(0, reduction - delta)
```

`correction_cp` is `static_eval - raw_eval`. The node is skipped when either eval is `ValueNone` (in check) or the difference is zero, so a zero correction leaves the reduction value untouched. Noisy late-move reductions are unchanged. `LmrDeeperShallower`, `NonPawnCorrection`, and `ContHist4PlyRead` stay independent and default off.

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

## Follow-up: one-ply fraction

The previous adjustment subtracted `correction_cp / 8` with no cap, so a large correction moved the reduction by several plies. The follow-up rule subtracts `correction_cp / 64`, rounded toward zero, then limits that adjustment to -1..+1. The reduction is still never negative. Positive correction (results better than the raw eval) subtracts a ply. Negative correction adds a ply. A correction inside -63..+63 centipawns changes nothing.

Owner build on this machine: AVX-512F and BMI2 are present, and so are the rest of x86-64-v4, so the binary is the default Release build (`FORGE_PORTABLE` off, `-march=x86-64-v4`, g++ 13.3.0). No CMakeLists edit and no extra `FORGE_*` source define. Option off, Threads 1, Hash 16, OwnBook false:

- bench 11: 312866
- bench 13: 862329
- go perft 5 from the start position: 4865609

bench 13 with `LmrSignedCorrection` on: **862329**. The same count as option off. A one-ply step needs 64 centipawns, and each correction table caps at 32, so the step happens only when the pawn and material corrections are both saturated on the same side. That did not change the depth-13 bench tree.

Screening, not a strength claim. Same binary, option on as the first engine, `nodes=50000`, Threads 1, Hash 16, OwnBook false. Book `UHO_Lichess_4852_v1.epd` (sha256 `7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a`), sequential chunks of 500 openings, two games each (colors swapped), up to 9 chunks or 6 hours. fastchess alpha 1.8.3. Engine id `Chess Engine Forge 6.4.24 candidate`. Implementation commit `01701ba52bfa8b8d9c42cd76c4d5cf2e5d3b3e94`. Engine sha256 `c91a68b5e05822f312df0547d162e551d30c98250201e77452938ece4e41c31a`.

Chunk results are written under `forge-combo29/screen_r3fu_03/` as each chunk finishes. W-L-D counts the option-on engine first.

Chunk 01 (openings 1-500, 1000 games, 00:22:42): W-L-D 259-246-495, Elo 4.52 +/- 11.73 (95%), LOS 77.48%, pentanomial 11, 96, 275, 105, 13. Detail: `forge-combo29/screen_r3fu_03/chunk-01-summary.md`.

Idle bench 13 nps, off then on, five times: 1553745/1534393, 1562190/1579357, 1573593/1556550, 1520862/1489341, 1491918/1442021. Nodes stayed 862329 on every run.

option name LmrSignedCorrection type check default false
bench 13 with LmrSignedCorrection on: 862329
