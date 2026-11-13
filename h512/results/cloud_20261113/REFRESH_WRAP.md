# NNUE v3 refresh may wrap an intermediate int16 sum

Date: 2026-11-13. No accumulator order was changed. This is not an Elo result.

## What was checked

`refresh_from_pieces` updates one piece type at a time, white pawns first. A legal placement of 32 pieces can still pass through 33 columns: the early type gains a square before a later type loses one.

The position pair is legal for `Board::set_fen` (one extra white knight, one fewer white pawn):

- `rnbqkbnr/pppppppp/8/8/8/8/NPPPPPPP/RNBQKBNR w KQkq - 0 1`
- the standard start position

With every `w1` column equal to 1000 and `b1` equal to 700, the true sum of 32 columns is 32700. The pawn-then-knight update reaches 33700 while both the new pawn and the old knight are present, which does not fit in int16. `add_epi16` / `sub_epi16` and the scalar `int16` cast wrap modulo 65536, and the stored lanes come back to 32700.

The header used to say the loader bound keeps every partial sum inside int16. That sentence was stronger than the bound. The bound keeps the final sum of the bias and at most 32 columns inside int16. Saturating adds would keep 31767 after the same update. The kernels were left as wrapping adds.

## Result

`h512/tools/nnue_v3_tests.cpp` now loads that net, refreshes the knight position and then the start position through the cache, and requires every lane to equal `700 + 1000 * pieces`. It also requires the cache to match the scalar square-order refresh. Both builds passed that check, including a second pass back to the start position after a two-king position.

The same run is the existing 100000-ply walk. Totals match `h512/results/step3/nnue_v3_tests_combo29.log`: 100000 plies, 64987 evaluations, 0 mismatches. v4: 101066 checks, 0 failures, kernels `scalar, avx2, avx512`, `kernel_checks 129974`. AVX-512 VNNI build: 101115 checks, 0 failures, kernels `scalar, avx2, avx512, avx512-vnni`, `kernel_checks 194961`. `apply_changes` and the column add/sub loop now call the VNNI kernel when it is compiled in; that path uses the same AVX-512 add and sub as the AVX-512 kernel.

g++ 13.3.0, `-std=c++20 -O3 -ffp-contract=off -fno-fast-math -DNDEBUG`, the `FORGE_*` defines in `REFRESH_BIAS.md`, `-march=x86-64-v4` and the same plus `-mavx512vnni`. Scratch directories `/tmp/forge-nnue-v4-scratch` and `/tmp/forge-nnue-vnni-scratch`. Test exes stayed in `/tmp/forge-nnue-build` and are not in git. v4 sha256 `4af3fcf851ad8007dad684a62158f7bfc3f849b7d2afbff8d475782c07737af8`. VNNI sha256 `915f2be840e2fbd33afd03b4377a5a605ff0cdb49e112250e52fbc5f16b6d8b1`. The linked `nnue_v3.o` objects are the ones named in `VNNI.md`; this change does not alter that translation unit.

## Incremental hand-crafted eval

`Evaluator::update_runtime_psqt` was compared with `refresh_runtime_psqt` and with `evaluate_uncached` over 8000 positions, and `evaluate` (pawn cache) was compared with `evaluate_uncached` on the same positions. Seed 20261113. Counts: 40 castlings, 7 en passant, 71 promotions, 261 null moves, 0 mismatches, on both builds. That is a sample, not every legal position. No PSQT code was changed. The three incremental methods are callable from the test; search is still the production caller.

## Trainer `b2`

`Model.clip` clamped `w1`, `wf`, `b1`, and `w2`, and left `b2` alone. The module text says parameters are clipped to exportable ranges. `round(b2 * 255 * 64)` has to fit in int32. `131586 * 16320 = 2147483520` does; `131587 * 16320` does not. `clip` now clamps `b2` to `±131586 / (QA * QB)`. `export_net` still rejects an out-of-range value instead of wrapping it.

`h512/train/test_scorer_parity.py` checks that limit in int64 and in float32. Torch is not installed on this machine, so `clip()` itself was not executed. The rest of that file passed: 520 scorer rows, 0 mismatches, 253 negative.

## Not changed

Piece-type order was not reordered. Any order of wrapping adds and subs of the same columns stores the in-range final sum. A fused both-perspective update and a VNNI retune were not repeated.
