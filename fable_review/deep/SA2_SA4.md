# SA2 int16 inference (opus-sol-SA2) and SA4 hidden-512 build (opus-sol-SA4) — line-by-line read, 2026-10-28

SA2 engine diff vs d4f4312: include/forge/nnue.hpp (+17), src/nnue.cpp (+17), src/nnue_int16.inc (new, 184),
src/uci.cpp (+18), CMakeLists.txt (+24). SA4 on top of SA2: src/nnue.cpp (+9: FORGE_NNUE_WEIGHTS include switch),
tests/nnue_gen_net.cpp (63, synthetic H512 net generator), CMakeLists.txt (+29: forge_nnue_h512_tests).

## SA2: the integer path (nnue_int16.inc), checked against the float path's number format

| item | code | check |
|---|---|---|
| weights | w1, b1, w2, b2 copied from the include file (int16, multiples of 1/4096); packed_w2 permuted with {0-3, 8-11, 4-7, 12-15} per 16-lane group | the permutation is exactly how `_mm256_packus_epi32(first, second)` interleaves its 128-bit halves; the scalar path uses the unpermuted w2 |
| accumulator | int32: A = b1 + sum w1(feature); refresh over occupied squares, incremental update over <= 4 dirty changes (AVX2: 8 lanes, cvtepi16_epi32 then add/sub; scalar identical) | feature_index shared with the float path; no overflow: representability requires largest_lane + 4*largest_column < 2^24 (also guarantees the float32 path's accumulator values are exact on the same grid, so both paths hold the same numbers) |
| activation | a = clamp(A, 0, 4096); AVX2: packus (saturates to [0, 65535], so negatives become 0) then min_epu16 4096 | equals the float clamp to [0, 1] at scale 4096 |
| square | scalar (a*a + 1024) / 2048, scale 8192; AVX2 mulhrs(4a, 4a) = (16a^2 + 2^14) >> 15 = (a^2 + 1024) >> 11 | identical to the scalar formula (a >= 0 so >> and / agree); 4a <= 16384 fits int16 |
| output | madd_epi16(q, w2): products <= 8192 * 32767 < 2^28, pairs < 2^29, a + b <= 2^30, widened to int64 per 16-lane group before any cross-group sum; scalar sums int64 directly | no int32 overflow; total_bound 2*H*8192*32768 <= 2^53 keeps the double conversion exact (H=512: 2^38) |
| scale | logit = T / 2^25 + b2 / 4096; cp = logit * 400 / 2.25, clamp +-30000, truncate toward zero | 8192 (square) * 4096 (w2) = 2^25; matches the float path's cp formula |
| mode switch | `selected` atomic, written by setoption between searches, read in refresh(); update() follows the parent's representation, evaluate() the accumulator's; `searcher.clear_hash()` on the option change | a mode change takes effect at the next root refresh; no mixed-representation child; no data race |
| availability | int16_available() false when WeightScale/OutputScale != 4096, HiddenSize % 16 != 0 or the bounds fail; set_int16(true) then keeps float and says so | fail-safe |

The integer square rounds to the 8192 grid where the float path squares exactly, so the two paths are not bit-identical
by construction; the difference per lane is <= 0.5 units of 1/8192 times w2, which is far below one centipawn for the
lock net (Opus measured 10000/10000 equal truncated centipawns; a rare 1 cp boundary difference remains possible and the
option is OFF by default). Not a defect.

## SA4

FORGE_NNUE_WEIGHTS selects another include file (the include file's own static_asserts reject a width different from
FORGE_NNUE_HIDDEN); the H512 test target compiles the NNUE sources with FORGE_NNUE_HIDDEN=512 against a generated
synthetic net (nnue_gen_net 512 20261027) and runs the int16 tests on it. HiddenSize % 16 == 0 holds for 512; all SA2
bounds scale linearly and stay inside the checks. The default build keeps H256 (CI identity ALL OK, run 40518079733).

Verdict: no defect in SA2 or SA4.
