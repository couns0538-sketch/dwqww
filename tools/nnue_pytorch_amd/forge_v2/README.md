# Forge v2 net on the fast AMD path (R7 J1)

GPL-3.0 tool code (uses nnue-pytorch's data loader; kernels derived from the R6 Triton port). Never copy any of it
into Forge `src/`, `include/` or `tests/`.

| file | what |
|---|---|
| `forge_v2_kernels.py` | Triton forward/backward for Forge's v2 feature transformer + SCReLU (both perspectives in one kernel, K32H3 -> Forge remap inside the kernel, fp32 atomics in the backward, torch's clamp-gradient rule) |
| `train_forge_v2_fast.py` | trainer + benchmark: Grok Bot's model/loss/Adam/clip/export with `--backend plain|triton`, `--fused-adam`, `--pinned` (+ `--inflight`), `--compile`, `--mode train|loader|synthetic`; hard caps batch <= 8192, loader threads <= 2 |
| `test_forge_v2_kernels.py` | Triton path == plain path (output + every gradient) on real loader batches; 2 planted errors must be caught |
| `bench_matrix.sh` | the guarded A/B matrix (2 interleaved rounds) |
| `parity_forge_v2_fast.py` | trained net vs the engine's own v2 eval (`nnue_v2_tool eval`): keys, output bucket, dequantised <= 1.001 cp, float <= 2 cp |
| `engine_load_check.py` | load the .fnn2 in a Forge exe (shape options, NNUEFile, isready), bench, depth-8 sanity scores |

## Run (Git Bash, from the branch root)
```
source F:/opus_scratch/r7/tools/env_r7.sh          # venv on PATH (Triton), thread caps, caches, R6 guard path
nice -n 10 "$PY" -B "$GUARD" tools/nnue_pytorch_amd/forge_v2/test_forge_v2_kernels.py <data.binpack> 2048 3
nice -n 10 "$PY" -B "$GUARD" tools/nnue_pytorch_amd/forge_v2/train_forge_v2_fast.py --data <data.binpack> \
    --backend triton --fused-adam 1 --pinned 1 --inflight 3 --batch 4096 --threads 1 --steps N --out <prefix>
nnue_v2_tool eval <prefix>.fnn2 pos10k.fen <eng>     # built from the engine tree with the exe's flags
nice -n 10 "$PY" -B "$GUARD" tools/nnue_pytorch_amd/forge_v2/parity_forge_v2_fast.py <prefix>.pt <prefix>.fnn2 pos10k.fen <eng>
python -I -B tools/nnue_pytorch_amd/forge_v2/engine_load_check.py <forge.exe> <prefix>.fnn2 13
```
`env_r7.sh` sets `NNUE_REPO` (the R6 clone that provides `data_loader`), `NNUE_DATA_LOADER_LIB`, `TRITON_CACHE_DIR`,
`TORCHINDUCTOR_CACHE_DIR`, `TMP`, the 1-thread BLAS caps and `R6_MIN_FREE_GB=7`. `FORGE_V2_WRITER` overrides the
path of Forge's writer `tools/nnue/forge_nnue_v2.py` (default: the `opus-r7-nps` worktree).

## Notes
- The K32H3 loader's dummy -1 slots are skipped by the kernel (no padding row); `w1` is exactly `[32*768, H]`.
- `--pinned 1` without the in-flight cap let the host queue hundreds of steps and held ~0.75 GB more pinned host
  memory; `--inflight 3` keeps the speed and the memory of the unpinned run.
- Atomics make the gradients' summation order non-deterministic: two runs agree to ~1e-6 in the loss, not bit for bit.
