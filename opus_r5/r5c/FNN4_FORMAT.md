# FNN4: Forge NNUE v4 network file (R5C)

A v4 net is the v3 feature transformer (king-bucketed HalfKA, int16 accumulators, SCReLU; `fable-nnue-arch`
`FORGENN3`, used here as the format reference only) followed by the J7 second layer: a clipped-ReLU layer of `L2`
units (J7 trains `--l2 16`) and a per-output-bucket linear output. Engine path: `include/forge/nnue_v4.hpp`,
`src/nnue_v4.cpp`, UCI `NNUEv4` (check, default false) + `NNUEv4File` (string, default empty). Exporter:
`tools/nnue/export_fnn4.py`.

## Layout (little-endian, no padding)

| offset | type | field | value / rule |
|---|---|---|---|
| 0 | char[8] | magic | `FORGENN4` |
| 8 | u32 | version | 1 |
| 12 | u32 | header_bytes | 256 |
| 16 | u32 | inputs | 768 (12 piece kinds x 64 squares per king bucket) |
| 20 | u32 | hidden H | 64..1024, multiple of 64 (the AVX2 kernel adds 64 lanes per pass) |
| 24 | u32 | king_buckets KB | 1..32 |
| 28 | u32 | output_buckets OB | 1..16 |
| 32 | u32 | l2 | 1..64 (J7: 16) |
| 36 | u32 | flags | bit 0 residual (cp is added to the hand-crafted eval), bit 1 mirror; other bits 0 |
| 40 | i32 | eval_scale | 1..10000 (cp per output unit; J7: 400) |
| 44 | u32 | qa | 255 (accumulator unit 1/qa) |
| 48 | u32 | s_shift | 6 (SCReLU input of layer 2 = clamp(a, 0, qa)^2 >> s_shift, at most 1016) |
| 52 | u32 | qw | 1024 (layer-2 weight unit 1/qw) |
| 56 | u32 | qo | 256 (output weight unit 1/qo) |
| 60 | u8[64] | king_map | bucket of the own-king square in the perspective frame (values < KB) |
| 124 | u8[33] | output_map | output bucket by total piece count 0..32, kings included (values < OB) |
| 157 | u8[99] | reserved | 0 |
| 256 | i16[KB][768][H] | w1 | feature columns (unit 1/qa) |
| | i16[H] | b1 | accumulator bias (unit 1/qa) |
| | i16[L2][2H] | l2w | row j: H weights on the side to move's SCReLU, then H on the opponent's (unit 1/qw) |
| | i32[L2] | l2b | unit 1/ONE, ONE = qa^2 * qw >> s_shift = 1,040,400 |
| | i16[OB][L2] | l2o | unit 1/qo |
| | i64[OB] | b_out | unit 1/(ONE * qo) = 1/266,342,400 |
| | u64 | checksum | FNV-1a 64 (offset basis 0xcbf29ce484222325, prime 0x100000001b3) of every preceding byte |

File size = 256 + 2*KB*768*H + 2*H + 4*L2*H + 4*L2 + 2*OB*L2 + 8*OB + 8 bytes (KB 8, H 512, L2 16, OB 8:
6,325,896 bytes).

## Features (identical to v3 / v2)
Perspective p, own king on `ksq`: `kr = p == White ? ksq : ksq ^ 56`, `flip = (mirror && file(kr) >= 4) ? 7 : 0`,
`bucket = king_map[kr]`; a piece `pc` on `sq` is feature
`bucket*768 + ((colour(pc) == p ? 0 : 1)*6 + type(pc) - 1)*64 + ((p == White ? sq : sq ^ 56) ^ flip)`.
Output bucket: `output_map[min(pieces, 32)]`.

## Integer forward (exact; the order of additions does not matter)
1. `a = b1 + sum of w1 columns` per perspective (int16). Loader bound: `max|b1| + 32*max|w1| <= 32767`, so no
   accumulator can overflow (at most 32 pieces).
2. `s = (clamp(a, 0, 255)^2) >> 6` (0..1016) for the side to move (`us`) and the opponent (`them`).
3. `z_j = l2b[j] + sum_i s_us[i]*l2w[j][i] + sum_i s_them[i]*l2w[j][H+i]` (int32). Loader bound per unit j:
   `|l2b[j]| + 1016 * sum_i |l2w[j][i]| <= 2^31 - 1`, so every partial sum fits int32 in any order (scalar and AVX2
   `madd` give the same value).
4. `h_j = clamp(z_j, 0, ONE)`.
5. `out = b_out[ob] + sum_j h_j * l2o[ob][j]` (int64).
6. `cp = trunc(out * eval_scale / (ONE * qo))` (C++ integer division, toward zero), clamped to +-30000; with the
   residual flag the engine returns `hce + cp`, otherwise `cp`.
Float view (what the J7 trainer computes): `s = clamp(a/qa, 0, 1)^2`, `hidden = clamp(s @ l2w^T + l2b, 0, 1)`,
`out = hidden . l2o[ob] + b2[ob]`, `cp = out * eval_scale`. Quantisation (exporter): `w1, b1` as v3 (x qa), `l2w` x qw,
`l2b` x ONE, `l2o` x qo, `b_out = b2 * ONE * qo` (exact for the trainer's b2 grid 1/(qa*64): ONE*qo/(255*64) = 16320).
Only `l2w`, `l2b`, `l2o` lose precision (the J7 trainer does not fake-quantise them); M4 reports that error.

## Loader rules (refuse loudly, keep the default net)
Header fields exactly as above; file size equal to the formula BEFORE any weight is read; checksum; the two bounds;
map values in range. On any failure the engine prints `info string ERROR NNUE v4: <reason>` and keeps (or returns
to) the default net; nothing of a failed file stays loaded.
