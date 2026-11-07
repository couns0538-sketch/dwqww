# NnueInt8Vnni - overflow bounds (step 2c, 2026-11-06)

`python -I -B tools/int8_bounds.py <trial_w6 src>/nnue_weights.inc gen/nnue_int8_weights.inc` prints the result,
`logs/bounds_2c.txt`: **ALL BOUNDS HOLD**. The bounds are proven from the weights alone. No positions are sampled.

| # | quantity | bound | limit | result |
|---|---|---|---|---|
| 1 | FT accumulator \|A\| (int16, 1/256 units) | 21,236 (worst hidden unit 100) | 32,767 | holds, headroom x1.54 |
| 2 | SCReLU `c*c + 128`, c in 0..255 | 65,153 | 65,535 (u16 lanes) | holds |
| 2 | activation `a = (c*c + 128) >> 8` | 254 | 255 (u8) | holds |
| 3 | L1 int32 sum, \|sum\| <= 254 * sum\|W2q\| (sum\|W2q\| = 6,333) | 1,608,582 | 2^24 = 16,777,216 (float exact) | holds, also < 2^31 |
| 3 | one vpdpbusd int32 lane (8 steps x 4 products, a <= 254, \|W2q\| <= 127) | 1,032,256 | 2^31 | holds |
| 4 | AVX2 `pmaddubsw` pair (2 x 254 x 127) | 64,516 | 32,767 (signed 16-bit saturation) | **can saturate**: no AVX2 fallback in this job |

## Why bound 1 covers every reachable accumulator
- **What the bound sums.** For one perspective, a position activates at most one own-king feature, one their-king
  feature and at most 30 other features (a legal position has at most 32 pieces). Each feature (colour, type, square)
  is active at most once.
  - Per hidden unit, the bound adds four terms: the bias, the most extreme king square of each side (or no king), and
    the 30 most extreme non-king features of one sign.
  - It does not use pawn ranks or piece counts, so FENs that are not reachable from the start position are covered too,
    as long as each side has at most one king and there are at most 30 other pieces.
- **Order of the steps.** `refresh_int8` and `update_int8` add and subtract in two's-complement int16; the C++20
  `int -> int16_t` conversion is modular.
  - When the exact final sum fits int16, the wrapped result is that sum, whatever order the steps ran in and whatever
    the intermediate values were.
  - So incremental == refresh exactly. Measured in 2b: 31,977 / 31,977 walk positions.
- **Saturation.** It is never needed, so the FT does not use saturating adds. Saturating adds would make
  incremental != refresh if they ever fired. The only clip is the activation clamp to 0..255.
- **Measured headroom.** The largest |A| seen in 2b is 6,293, 3.4x under the proven bound.
  - A finer FT scale (shift 3, 1/512 units) would double both numbers: proven bound 42,472 (fails), measured ~12.6k.
  - So shift 3 would need a tighter, combinatorial proof. That is not part of this job.

## Kernel consequences (step 2d)
- **Activations in 16-bit lanes.** c^2 + 128 fits u16, so `mullo_epi16(c, c)`, `+128` and a logical `>> 8` are exact in
  16-bit lanes. `packus_epi16` then sees values 0..254, which never saturate.
- **The L1 dot.** No lane overflows, so the non-saturating vpdpbusd and the scalar int32 sum give the same `sum`.
- **The final float line.** |sum| < 2^24, so `float(sum)` is exact. The SIMD and scalar paths share this line, so
  equal sums give equal cp.
