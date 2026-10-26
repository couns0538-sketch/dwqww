# S09 CPU RAM-loader preparation, 2026-10-26

The actual archive/load probe has **not run**. Root must explicitly authorize a
fresh f022 BUILD window before the real command is invoked. Its CLI window
argument records that authorization and does not grant it. The frozen S09 source
packet in the sibling S09 folder was left unchanged.

The one authorized ordinary-import baseline did run in f021 BUILD: private
venv/bin/python -B -c 'import torch', CPU1/nice19, BLAS/MKL/OMP1 and empty
CUDA_VISIBLE_DEVICES. It failed with actual return code1, no timeout under its
15-second watchdog, and ImportError: libtorch_cpu.so missing. Raw stdout/stderr,
library-presence before/after and metadata are retained in
forge_sol_S09_ordinary_import_RED_20261026.*. This is genuine import evidence;
the earlier toy RED logs are separately labelled and are not import evidence.

Restore-map entry60 is preserved as metadata only. Its recorded source is
488851697 raw bytes, SHA256
`0aae29741806982c5778f7863e53711edc5c4afb829595d7296f729ac176cfe3`;
gzip129931554 bytes, SHA256
`a889e666c7922e02fc51569518a2742b5f74556840c45266fb2245fd78d81b9b`.
Archive contents have not been read or hashed during this preparation. Existing
libgomp, libc10 and libtorch_python files were listed/stat'ed; the CPU library
remains absent from the ordinary environment.

Eight toy-only tests pass: exact gzip-to-memfd bytes, offset reset, all four
immutable seals, EPERM on write/grow/shrink/reseal, compressed/raw hash and size
negatives, corrupt gzip, failure FD cleanup, existing-output refusal and exact
deterministic reversible evidence archives. The public Python build lacks the
fcntl seal names; Linux UAPI constants were verified against local headers and
actual kernel behavior. The loader uses F_ADD_SEALS1033, F_GET_SEALS1034 and
SEAL/SHRINK/GROW/WRITE bits1/2/4/8. Tests used only small owned fixtures and no
real library bytes, imports or ctypes preloads.

The prepared real path, only after authorization, is one owning CPU process:

1. Require the exact private interpreter and an absent ordinary CPU library;
   check dependencies and enough available RAM.
2. Verify the full compressed size/hash, stream-decompress into an anonymous
   memfd while verifying full raw size/hash, then seal write/grow/shrink/seal.
3. Preload existing libgomp and libc10, then the verified memfd with RTLD_GLOBAL.
   Import Torch with empty CUDA visibility and one CPU thread.
4. Run three tiny CPU arithmetic/autograd steps, then actual frozen S09 checks:
   bucket1 initialization/forward/export identity; replicated8 float tolerance;
   three CPU Adam smoke steps on192 t000 rows; before/after MSE on512 h000 rows.
5. Preserve actual parity exports as deterministic lossless .inc.gz/.bin.gz,
   plus independently checked before/after float-state NPZ and full hashes.
   Remove only owned temporary raw exports after preserving their exact bytes.
6. Close the memfd and exit. Normal private-environment import remains unready;
   no disk library restoration, installation, package edits or GPU operations.

The planned command is NOT permission to run it now:

```sh
OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' \
  taskset -c 1 nice -n19 /workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python -B \
  forge_sol_S09_torchram_probe_20261026.py --authorized-build-window f022-BUILD \
  --out new_f022_runtime_output
```

Root should apply a bounded watchdog to that single child within its actual
BUILD lease. A failure is an honest FAILED_UNVERIFIED packet, with completed
stages preserved. No ordinary-import success or SONAME satisfaction is assumed.

The smoke uses a seeded small untrained model with deliberately nonzero output
weights for meaningful parity. It is not a trained f006 checkpoint. CPU Adam
smoke does not qualify the default DirectML optimizer. The holdout is a synthetic
512-row subset; no full50k, real013/014, native1M, Std/null-pruning or strength
claim follows. The .so exists only in sealed RAM during the owning process.

Source version322a1c73788d5f5cf222f6091cf5fd56231914a6928c98380f83f10eac025aa1
was preserved before root requested reversible evidence and baseline hash checks.
The current receipt pins the revised source. Independent read-only review found
no remaining blockers, and did not execute the real path. Actual status remains
UNVERIFIED until root's fresh-window run.
