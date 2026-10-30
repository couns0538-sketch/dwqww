# Forge lock exporter and checkpoint contract

The primary target is AL1 source `294dbed3a15dfd821aaf9d4edc6e5f62832fd460`:
768 features -> shared 256-unit transform -> two SCReLU perspectives -> one
residual output. The exact lock embeds `src/nnue_weights.inc`; it has **no runtime
`.nnue` loader**. `lock_export.py export` writes that include format, with int16
storage at scale4096 and the lock's unchanged float32 inference. It never edits
engine source, installs a net, or touches a live trainer.

The separate `export_forge.py` and `make_checkpoint_fixture.py` preserve the
initial R10 K32H3 work. Those nets have a different architecture and loader;
R10 output must not be called lock-compatible.

## Exact Bullet interchange

Pinned upstream: MIT Bullet `da426a49b2a4b79a55a87031cd51c89bdf1ff030`.
The x64 `optimiser_state/weights.bin` layout is repeated ASCII tensorID+LF,
uint64 little-endian float count, then float32 little-endian data. It does not
store shapes or architecture. A manifest therefore binds its SHA256, roles,
column-major shapes, architecture, scaling and rounding. Unknown or duplicate
tensors, wrong sizes, nonfinite weights, quantization overflow, unsupported
architectures and overwrite attempts are errors. SHA256 covers the actual parsed
stream, not merely a separate earlier read.

For the original lock graph the tensorIDs are:

| ID | Bullet shape | Physical serialized order |
|---|---|---|
| ftw |256x768|768 feature rows of256 weights|
| ftb |256x1|256 biases|
| outw |1x512|256 STM weights then256 opponent weights|
| outb |1x1|one bias|

All four tensors use scale4096 and nearest ties away from zero (Bullet `.round()`),
with the stored float32 promoted to float64 before scaling. The manifest command
requires those four exact IDs. Manually specified manifests may map other IDs,
with the same explicit shapes and semantics. Export does not deduce or silently
convert an arbitrary Bullet architecture.

```bash
python tools/bullet/lock_export.py manifest \
  --checkpoint CHECKPOINT/optimiser_state/weights.bin --out NEW_MANIFEST.json \
  --provenance 'Actual training run identifier, source SHA and log path'
python tools/bullet/lock_export.py export \
  --checkpoint CHECKPOINT/optimiser_state/weights.bin --manifest NEW_MANIFEST.json \
  --out NEW_nnue_weights.inc
python tools/bullet/lock_export.py reference \
  --checkpoint CHECKPOINT/optimiser_state/weights.bin --manifest NEW_MANIFEST.json \
  --fens fens_12k.txt --out NEW_reference.txt
```

Reference columns are residual centipawns and the pre-cp output's float32 bit
pattern. The oracle recreates ascending-square refresh, each separate float32
multiply/add, the16 independent lanes, ordered lane reduction, cp scaling,
clamp and truncation. It does not use NumPy's dot-product reduction for the lock.
The native unchanged-engine oracle verifies centipawns on every FEN.

## Original Bullet graph and license boundary

`lock_graph/` uses **only Bullet's lower-level MIT compiler/trainer crates**.
The ordinary `bullet_lib` wrapper unconditionally depends on `montyformat`
(AGPL-3.0) and `sfbinpack` (GPL-3.0) at the pinned revision. Its initial typecheck
was rejected after dependency auditing. The original attempted wrapper source
and metadata are retained under validation as rejected evidence; it is not the
active build recipe. No GPL/AGPL source was copied into this project.

The active graph takes sparse STM/opponent inputs and training-only `hce_cp` and
`score_cp` auxiliaries. Its loss is:

```
(sigmoid(hce_cp *2.25/400 + residual) - sigmoid(score_cp *2.25/400))²
```

This avoids training full evaluation and then adding HCE again at inference.
The graph's four learned tensors alone are exported. The initializer's seed is
20261030. Run it on CPU to verify graph construction and obtain an actual
Bullet-written checkpoint:

```bash
cargo run --locked --manifest-path tools/bullet/lock_graph/Cargo.toml -- NEW_weights.bin
python tools/bullet/lock_export.py manifest --checkpoint NEW_weights.bin \
  --out NEW_manifest.json --provenance 'Bullet initialization only; NOT TRAINED'
```

**This binary initializes weights and writes a checkpoint; it does not train.**
A custom GPU input mapper/optimizer driver using the lower-level MIT crates is
still required for Bullet training. No GPU smoke or HIP execution is claimed.
The separate CPU PyTorch smoke is explicitly labelled PyTorch, never Bullet.

## Fixture status and safety

`lock_export.py include-fixture` creates a synthetic checkpoint from an existing
include. It is useful for validating layout and native parity, and is not a new
training run. The R10 fixture bridge similarly labels its provenance synthetic.
The R10 planted-corruption command changes one active output weight and verifies
both changed arithmetic and safe bounds. `.nnue`'s format has no weight checksum,
so successful native loading is expected; the original reference comparison must
fail. No engine strength or training-gain conclusion follows from any fixture.

NumPy is required. Tests are under `tests/bullet/`; native oracle tests also
require their explicit binary environment variable. Use the saved validation
logs to distinguish an executed test from a conditional skip.
