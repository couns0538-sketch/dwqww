# HANDOFF - fast npt data loader (R14-B item 1), for Engine NNUE / QA

State: **CPU-verified, UNPROVEN on the GPU** (the GPU window in GPU_REQUEST.md was not granted: the npt queue holds the
GPU until 2026-11-08). Nothing here is a strength claim; switching is Engine NNUE's decision. Off by default.

## What it is
`--fast-loader` makes the npt trainer (`F:\opus_scratch\r6\nnue-pytorch-amd`, b2614500 + patches) read its binpack with
`forge_fastloader.dll` (own code, C++20, MinGW g++ 15.2) instead of the default loader DLL. It produces **the same
batches, byte for byte, as the default loader with `--num-workers 1`** (same skip filter, same random numbers, same
window shuffles, same SparseBatch layout), but filters the ~90 % skipped records from three stem fields without
decoding a board and builds features in parallel. Evidence and numbers: RESULTS.md; design: LOADER_SPEC.md.

| file | sha256 | where |
|---|---|---|
| `forge_fastloader.dll` (candidate b5) | `9eb29b7d134a73eb58d47b2ced38587ed450ffaf11fdfcb108898652cefcd935` | `D:\o14b\fl\b5_install\`; rebuild: `fastloader/build_fastloader.sh` (pc1 = pc2 byte-identical) |
| `forge_fastloader.py` (Dataset wrapper) | `39af47b0f347963c9f3ad470c7a90c2652b4ae361f18b71adfeeb3cbdf3a9605` | `fastloader/` on this branch, copy in `D:\o14b\fl\b5_install\` |
| trainer switch | - | `patches/0005-fast-loader-switch.patch` = what `tools/install_fast_loader.py` applies |

## Verified on the CPU (details in RESULTS.md)
- Batches identical to the default loader's `--num-workers 1` stream: 1,000 / 1,000 training batches + the validation
  batches, a 24-configuration matrix, 3,100 batches past a file wrap, and every tensor on the trainer's own Dataset path.
- One epoch of CPU training (L1 256, 16 batches, seeded before the model is built, 1 thread, deterministic
  algorithms): the printed losses of old and fast are identical in all 5 values.
- Speed (loader only, palindromic ABBA, 10 pairs, CPUs 2-3, BelowNormal): 468,494 vs 4,035,567 kept positions / s
  = **8.65x**; a full 152.5M-position epoch through the fast loader alone: 29.8 s, peak 166 MB.
- ASan + UBSan and TSan self-tests in GitHub CI: PASS.

## Not verified (needs the GPU window)
GPU utilisation and it/s of a real epoch, and the adapter path below (the adapter starts a GPU run).

## Adopting it in the queue (Engine NNUE decides; never edit the live trainer folder in place)
1. Make a trainer copy (e.g. `robocopy F:\opus_scratch\r6\nnue-pytorch-amd <COPY> /E`) and check its files against the
   live tree (sha256 list) - `D:\o14b\npt` is such a copy, already switched.
2. `python -I -B tools/install_fast_loader.py <COPY> --check`, then without `--check` (exact anchors; refuses a trainer
   that differs or is already patched, exit 2).
3. Copy `forge_fastloader.dll` (sha256 above) and `forge_fastloader.py` next to `<COPY>\train.py` (or set
   `FORGE_FAST_LOADER_DIR`; the adapter passes the queue's environment through).
4. Queue line (adapter `F:\forge_nnue_train\tools\train_resid_nnuepytorch_v2.py`): add `--npt-repo <COPY>` and, as the
   LAST arguments, `--npt-extra --fast-loader` (`--npt-extra` takes the rest of the command line). Everything else
   stays as it is. `--num-workers N` sets the fast loader's feature-builder threads to N - 2 (at least 1; plus one
   reader and one filter thread); the batches are the same at any N (the w1 stream).
5. Check the run log's first lines: `Fast loader: ON (<version>, <path>, sha256 9eb29b7d...)`. A trainer without the
   flag prints `Fast loader: off`.
6. Roll back: remove `--npt-extra --fast-loader` (or `--npt-repo`); nothing else changes.

## Scope (fails closed with a clear error outside it)
Unchained binpack records only (the J1 binpacks are unchained, 34 B / record), exactly one file per stream,
`--no-filtered --no-wld-filtered` without simple-eval skipping, loader feature set K32H3 (what the trainer hands the
loader for `--features K32H3^`; the CPU loss match ran train.py with `--features K32H3^`), no DDP (world size 1). Anything else raises instead of silently differing from the default loader.

## What changes for training
The live line runs the default loader with `--num-workers 4`: several decode workers, each with its own adaptive
filter state, mixed by thread timing (not reproducible run to run). The fast loader gives the deterministic
`--num-workers 1` stream: same filter rules, a different sample of the same data. Loss values of a fast-loader epoch
are therefore comparable to the live epochs only as a sanity check, not bit for bit.

## Optional trainer fix found on the way
`train.py` builds the model before `torch.manual_seed`, and torch 2.11.0+rocm7.13.0 seeds from the clock per process:
the same `--seed` does not give the same initial weights. `patches/0006-seed-before-model-OPTIONAL.patch` fixes that
(not needed for the loader; Engine NNUE decides).
