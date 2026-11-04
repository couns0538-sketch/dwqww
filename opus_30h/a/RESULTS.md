# Item A - v2 net path on the lock (EvalFileV2) - RESULTS

UNPROVEN in play: no Elo claim. The crew gates.

## Port (Phase 1)
- Patch `opus_30h/a/v2port.patch` (md5 fb50a98b74df98bd8261a6e3e7cf9df8, 715 lines) on the lock source d4f4312
  (fresh LF copy, scratch repo `D:\o30\repos\v2port`): new `include/forge/nnue_v2.hpp` (FORGENN2 loader API, king
  buckets + mirror, output buckets, residual flag, refresh cache, AVX2 / SSE / scalar output kernels with the lock's
  arithmetic; piece-square inputs only, any other feature bit is rejected), loader appended to `src/nnue.cpp` (cold),
  `Worker::static_evaluate_v2` in `src/search.cpp` (own section, lazy accumulators reuse `SearchStack::accumulator`),
  one branch at the top of `static_evaluate`, the root refresh skipped while a v2 net is active, UCI string option
  `EvalFileV2` (empty = off) in `src/uci.cpp` (the `id` lines untouched). Ported from Forge's own R3 tree b7c17722
  (`nnue_v2.hpp`, `evaluation_v2.inc`, the v2 part of `nnue.cpp`), with O6 / O7 and the R3 shape options removed:
  the file header alone says king buckets, output buckets, mirror and residual.
- cleanroom_lint: CLEAN.

## Checks (2026-11-03, PC clock; plain build = the kit's direct g++ line, znver5, -DFORGE_EXPOSE_TUNABLES=1, CPUs 0-1 Idle)
| check | result |
|---|---|
| plain build `D:\o30\plain\v2port_1\forge_plain.exe` | 0 warnings, vfmadd 0, sha256 466c9203bc020b4537d2d32dbbb575166856a21508d04324854122cd432c93a6 |
| OFF (EvalFileV2 empty) pin_check -Full | PASS: d11 312866, d13 862329, d16 3024920, d20 12389307, d22 34048354, perft 4865609 / 193690690 |
| lock net written as v2 (`o30_v2net.py from-lock`), loaded with EvalFileV2, bench must equal the lock pins | PASS at d11-d22 for KB1/OB1 (fnv1a 5a7f7acb2d55004f), KB1/OB8 (db400d140d566e35), KB4 rank map/OB8 (de5133379be80e0d) |
| negative controls (must differ): lock net with the residual flag cleared; random KB4/OB8 net seed 30001 | LIVE: d11 558939 / 375866, d13 1881923 / 1521874, d16 9764737 / 9051131; perft = pins |
| missing file | pin_check FAIL with `info string ERROR EvalFileV2 ...: cannot open ...` (no silent fall-back) |

Meaning of the identity rows: the v2 loader, feature indices, king-bucket and output-bucket selection, the residual
combination with the hand-crafted evaluation and the lazy accumulator scheme reproduce the compiled-in network's
evaluations exactly through whole searches (KB4: copies of the same weights, so the king-bucket switch itself is
covered by the random-net checks below, not by this row).

Mistake caught on the way: a loop wrote `"EvalFileV2=D:\\o30\\...\\$n.nnue2"`; the shell received `\$n` (a literal
`$n`), the engine could not open the file and kept the compiled-in net. pin_check reported the engine's ERROR line,
but the first look at the output was cut with `head` and missed it. All rows above were re-run with paths built by
`cygpath -w` and full output.
