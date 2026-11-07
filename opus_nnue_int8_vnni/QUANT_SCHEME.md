# NnueInt8Vnni - quantization scheme (step 2a, 2026-11-06)

**Status: UNPROVEN.** This path is not bit-exact and is default OFF. The macro is `FORGE_NNUE_INT8_VNNI` (default 0). The
gate-only UCI option is `NnueInt8Vnni`, a spin from 0 to 1 with default 0.

## Reference: the lock's float path (trial_w6, unchanged)
- The net is 768 inputs -> 256 hidden x 2 perspectives -> 1 output.
- The shipped weights `nnue_weights.inc` (sha256 a7ebcf3a) are int16 at 1/4096. The engine divides them by 4096.
- FT: `acc[p][h] = (B1[h] + sum over active features f of W1[f][h]) / 4096`, in float.
  - This is exact: every partial sum is an integer below 2^24 times 2^-12.
- SCReLU: `s = clamp(acc, 0, 1)^2`.
- Output: `out = B2/4096 + sum_j s_stm[j]*W2[j]/4096 + sum_j s_opp[j]*W2[256+j]/4096`.
  - This step uses float rounding, 16 lanes and one fixed reduction order.
- Final: `cp = int(clamp(out*400/2.25, -30000, 30000))`. The result is a residual that is added to the hand-crafted eval.

## ON path (macro 1, `NnueInt8Vnni=1`)
| stage | formula | type / range |
|---|---|---|
| FT weights | `W1q = (W1 + 8) >> 4`, `B1q = (B1 + 8) >> 4` (round half up; computed when the engine starts) | int16 at 1/256; W1q in [-889, 659], B1q in [-423, 301] |
| FT accumulator | `A[p][h] = B1q[h] + sum over active f of W1q[f][h]`, plain two's-complement int16 adds | int16; range proof in BOUNDS.md (2c) |
| clip (the saturation) | `c = clamp(A, 0, 255)` | 0..255 (255/256 = 0.996) |
| SCReLU | `a = (c*c + 128) >> 8` | u8 in 0..254; about 256 * clamp(acc,0,1)^2 |
| L1 weights | `W2q = round_half_away(W2 * 127 / 13906)`, made by the converter | int8 in [-127, 119]; one step = 0.02673 float units |
| L1 dot | `sum = sum_j a_stm[j]*W2q[j] + sum_j a_opp[j]*W2q[256+j]` | int32; vpdpbusd = u8 x s8 in groups of 4 (2d) |
| output | `out = B2/4096 + float(sum) * 13906 / (256*127*4096)`, then the lock's final line unchanged | float; cp clamp +-30000 |

- **Accumulator storage.** A shares the Accumulator's float storage in an anonymous union (declared only when the macro
  is 1). With 2 x 256 x 2 B = 1 KB of the 2 KB block, the struct size stays the same, and so does the OFF path.
- **Which path runs.** The runtime flag picks refresh, update and evaluate together. Search refreshes the root
  accumulator at every search, so a `setoption` between searches cannot mix the two representations.
- **Accumulator exactness.** With no overflow (BOUNDS.md), integer adds are associative. So an incremental update gives
  the same A as a refresh.
- **SIMD equals scalar.** 2d only replaces the L1 dot; the same final float line turns `sum` into cp. So the SIMD path
  must produce the same int32 `sum` as the scalar reference, bit for bit.

## Where ON differs from the float lock (expected, to be measured in 2b)
- **FT rounding:** at most 8/4096 per weight (mean 4.0/4096) over at most 33 terms per hidden unit.
- **L1 weights:** at most 0.0133 per weight (mean 0.0068). One int8 step is 0.0267.
- **The per-tensor scale is set by one outlier** (|W2| max 13906; W2q = -127 appears once). Many weights sit at 4..10
  steps, so their relative error reaches about 10 %.
- **Activations:** rounding of at most 0.5/256 in s. The clip at 255 gives s = 254/256 where the float gives 1.0.

## Converter
- Command: `python -I -B tools/int8_convert.py <src>/nnue_weights.inc <src>/nnue_int8_weights.inc`. It refuses to
  overwrite the output.
- Output: md5 25982cc2. It holds 512 int8 values plus `NnueInt8W2MaxAbs = 13906` and `NnueInt8B2 = 127`, and records the
  input sha256 a7ebcf3a.
- Statistics printed on 2026-11-06:
  - W2 int16 range [-13906, 13035]; W2q range [-127, 119]; no zeros.
  - FT rounding error: max 8, mean 4.002 (in 1/4096 units).
