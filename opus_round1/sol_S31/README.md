# S31 checkpoint averaging for Forge H256 residual nets

`forge_sol_S31_avg_ckpt.py` (numpy; torch only for `.pt` inputs):
- `avg --inputs a.inc b.inc ... --out avg.inc` averages dequantized `.inc` weights (int/4096).
- `avg --bins a.bin b.bin ... --template a.inc --out avg.inc` averages the trainer's float32 exports.
- `avg --pts a.pt b.pt ... --template a.inc --out avg.inc` averages the model weights of trainer checkpoints. It
  refuses files whose configs (hidden, residual, features, epochs, steps per epoch) differ, so only one run can be
  averaged.
- Every average is taken in float64 and quantized like the trainer's `export_forge` (x4096, round half away from
  zero, int16), with the template's header and 24 values per line. Averaging one file reproduces that file's
  `.inc` byte for byte.
- `score --nets ... --pos holdout.pos --hce-dir D --out score.json`: the trainer's holdout metric without torch
  (MSE of sigmoid(net + hce*2.25/400) against the blended target, b = 1.0 teacher, 0.6, 0.8) plus the HCE-alone
  baseline; the holdout md5s are recorded.
- `subset --pos ... --hce-dir D --stride N --out-stem S`: deterministic every-Nth-row holdout copy (one md5 for
  all arms).
- `parity --nets ... --fens fens.txt --lock-tree <lock src> --harness nnue_check.cpp --work W --out parity.json`:
  builds the archive's `nnue_check.cpp` against the lock's `nnue.cpp` with each net, and compares its cp with the
  tool's forward (float64, truncated like the engine). A 1 cp difference is counted apart only when the float64
  value lies within 1e-3 of an integer (the engine sums in float32); anything else fails.

`run_s31_pc.sh <run_dir> <k> <out_dir> <holdout.pos> <hce_dir> <fens> <lock src> <nnue_check.cpp>`: the PC
runner. It copies the last k `.pt` checkpoints of a run read-only (sha256 checked), builds avg-2..avg-k, then
scores the last epoch and every average on the same holdout and checks parity, at Idle priority with one thread
into a new directory.

Tests: `python -I -B test_forge_sol_S31_avg_ckpt.py` (7 tests; the `.pt` test needs torch).
