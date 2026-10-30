# Supplemental AL1 CPU smoke

This is an original PyTorch CPU validation run, **not Bullet training**. Actual
Bullet GPU training remains blocked: the available official Bullet revision
`da426a49b2a4b79a55a87031cd51c89bdf1ff030` has no supported CPU training backend
and this environment has no usable CUDA/HIP GPU. Writing the reviewed Bullet
checkpoint interchange format does not change the trainer provenance.

The run uses the exact architecture of Forge AL1 source
`294dbed3a15dfd821aaf9d4edc6e5f62832fd460`: 768 piece-square inputs, a shared
256-unit transform for both perspectives, SCReLU, side-to-move/opponent output
weights, and an output residual added to HCE. All four weight/bias arrays use
int16/4096 quantization with ties rounded away from zero. The forward output uses
AL1's sixteen fixed float32 reduction lanes. No engine source was changed.

## Run and data

`run1/command.json` records the complete invocation. The run used CPU PyTorch
2.4.1+cpu, one thread, seed 20261030, Adam learning rate 0.003, batch size 128,
and exactly one epoch over **8,192 rows**. It visited each saved row once in 64
batches, with no dropped tail. It is not an epoch over the original 10M sample
or the full 9,206,371-row filtered corpus.

The saved `subset.pos`, `subset.hce`, and `subset.fen` contain filtered-corpus
rows 0 through 8191 inclusive, with original STM score labels and full FENs
preserved. `selection.json` records indices and complete source-file SHA256s;
the source hashes match the sealed A1 filtering manifest. The selected data
comes from the real Forge self-play shard 003 sample. Labels are neither
synthetic nor replaced by the probe's filtering scores.

The loss is
`MSE(sigmoid(HCE_cp*2.25/400 + residual), sigmoid(original_STM_score_cp*2.25/400))`.
No game-result mixing is used. The zero output-layer initialization starts
exactly at HCE alone.

| Measurement | Result |
| --- | --- |
| Initial slice training MSE | 0.004648477338154236 |
| Final slice training MSE | 0.002897180728021214 |
| Completed epochs on saved slice | 1 |
| Unique rows trained | 8192 |
| Optimizer steps | 64 |
| Training loop duration | 0.933 seconds |
| Run wall duration, including source hashes/export | 5.704 seconds |

These losses are measured on the training slice. No holdout, generalization,
playing-strength, Elo, or comparative training-performance claim is made.

## Checkpoints and validation

- `run1/initial/`: frozen pre-training floats and bound architecture manifest.
- `run1/trained/`: final `weights.bin`, manifest, and PyTorch `state.pt`.
- `run1/sample.inc`: the exported embedded lock-format int16 network.
- `run1/metrics.json`, `epoch.json`: initial/final losses, exact row order,
  per-batch losses, execution settings, code hashes, and artifact identities.
- `run1/forward_parity.json`: all **8192/8192** saved rows match the independent
  ordered export oracle, with zero float32 output-bit and zero residual-cp
  mismatches. Reproduce with `verify_forward.py` into a fresh receipt path/run.
- `run1/reference12k.txt`: exported reference residual cp and float32 output
  bits for the 12,000-position parity set; this is a parity fixture, not a
  generalization holdout.
- `../lock_native/sample_comparison.json`: actual AL1 C++ evaluation matches
  all **12000/12000** exported reference residual integer scores, max error 0 cp.
- `../lock_native/hce_subset_comparison.json`: actual AL1
  `Evaluator::evaluate_uncached` matches all **8192/8192** saved HCE values, max
  error 0 cp. This closes the selected-row HCE identity check despite the corpus
  having been produced with later source 926c55. It does not assert a native
  HCE recheck of the entire filtered corpus.
- `unit_tests_boundary.log`: **7 tests pass**, covering perspective orientation,
  SCReLU and residual initialization, exact row/label preservation, complete
  epoch coverage and determinism, exporter forward parity, ties-away/gradient
  behavior, and quantization over 446,618 random/extreme/boundary values.

The quantization boundary check tests every representable half-LSB threshold
inside the projected range plus its neighboring float32 values, 250,000 seeded
random values, signed zero, subnormal/normal tiny values, and projection ends.
The existing straight-through expression produced exactly the int16-dequantized
float32 bits for all tested values. For nonzero rounded values within the
projection range, their ratio to the original value lies in [0.5, 2], so the
subtraction is exact by Sterbenz's lemma; re-adding gives the representable
quantized value. Values rounding to zero cancel to +0, matching int16 dequant.

Final checkpoint SHA256:
`8aa6f874e044c851e762ce3f56521dfe173e17d450234d31451c4226b01ad114`.

The retained output is under 6 MB. `SHA256SUMS` covers the complete CPU smoke
evidence directory at finalization. Native build inputs, commands, and output
hashes are retained separately under `../lock_native/`.
