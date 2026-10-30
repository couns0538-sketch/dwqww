---
name: forge-halfka-parity-test
description: Prove that Forge's HalfKA (K32H3^) evaluation (branch opus-r10-halfka, UCI EvalFileHalfKA) equals nnue-pytorch's own evaluation of the same .nnue bit for bit, and that incremental accumulators equal full refreshes - the reference path inside the trainer (NNUEReader + C++ feature extractor + fake-quantized forward in float64), the Forge-side tool, the walk and in-search verify builds, the exact integer rules and the pitfalls. Use for any change to src/nnue_halfka.cpp, the search wiring, a new net from the R6 trainer, or a parity/eval question about EvalFileHalfKA.
---

# HalfKA (K32H3^) parity test (R10, 2026-10-30)

Rules first: [[forge-pc-rules]] (BelowNormal, CPUs 4-11 while R9-style jobs use 0-3, never the live trainer's GPU).
Trainer facts: [[forge-nnue-pytorch-amd]]. Loader checklist: [[forge-nnue-loader-checklist]].

## What is compared
- Engine side: `opus_r10/tools/halfka_tool.cpp` (built with `opus_r10/tools/build_tool.py`, the engine's box flags,
  all engine sources minus uci.cpp): `eval <net> <fens> <out>` writes per FEN the raw output (the trainer's integer
  output value = centipawns * 16) and cp = raw/16 truncated; every position is also evaluated with the scalar kernels
  (SIMD vs scalar mismatch count printed).
- Trainer side: `opus_r10/tools/parity_nnue_pytorch.py <net> <fens> <out> --l1 N [--l2 --l3] [--float32]` with the
  R6 venv `F:\nnue_pytorch\venv\Scripts\python.exe -B` and env `NNUE_REPO=F:/opus_scratch/r6/nnue-pytorch-amd
  NNUE_DATA_LOADER_LIB=<clone>/build/libtraining_data_loader.dll NNUE_FT_BACKEND=torch TORCHDYNAMO_DISABLE=1
  OMP_NUM_THREADS=1 TMP/TEMP=<scratch>` (CPU only). It runs `model.NNUEReader` -> `data_loader.get_sparse_batch_from_fens
  ("K32H3", ...)` (the trainer's C++ feature extractor, so indices are not re-implemented) -> `model.forward(...,
  fake_quantize_acts=True, fake_quantize_weights=True)` in float64; raw = round(out * 9600).
- `parity_nnue_pytorch.py compare <ref> <forge>` counts exact raw matches.

## Results to reproduce (2026-10-30)
- R6 net `r6_k32h3_l256.nnue` (256x32x32): 12,000 / 12,000 exact in float64 AND float32.
- CPU smoke net `opus_r10/nets/smoke_k32h3_l64.nnue` (64x32x32): 12,000 / 12,000 exact.
- untrained `init_k32h3_l1024.nnue` (1024x32x32, from `make_init_net.py`): 2,000 / 2,000 exact.
- FENs: `opus_r10/parity/fens_12k.txt` (real self-play positions, all 8 piece-count buckets).

## Incremental == refresh
- `halfka_tool walk <net> <seed> <games> <plies>`: random legal lines; every ply the accumulator is rebuilt from the
  parent and from 2..4 plies back (only when that ancestor has the same own-king square and state) and compared with a
  full refresh: 204,694 checks / 0 mismatches (R6 net), 31,602 / 0 (L1 1024).
- In-search: build with `-DFORGE_HALFKA_VERIFY` (`build_r10.py ... -DFORGE_HALFKA_VERIFY`) and run
  `opus_r10/tools/verify_search.py <exe> <net> --threads 3 --depth 13`: every lazily built row in the real search is
  compared with a refresh, a mismatch aborts; 3,028,552 rows equal (bench 13 + four 3-thread searches).

## The exact integer rules (why parity is exact)
FT `clamp(a,0,255)*clamp(b,0,255) >> 9` per half, [stm, other]; l1 `s1 = b + sum w*x` (scale 2^14), linear
`clamp(s1 >> 7, 0, 127)`, square `min(127, (s1*s1 + 20) >> 21)`; l2 linear `clamp(s2 >> 6)`, square
`min(127, (s2*s2 + 5) >> 19)`; output over [sq1, lin1, sq2, lin2]; total = s3 + s1[L2-2] - s1[L2-1];
raw = trunc(2 * total * 9600 / 32768). The `+20` / `+5` reproduce the trainer's `floor(x * 128 + 1e-5)` on the
squares (2^21 * 1e-5 = 20.97, 2^19 * 1e-5 = 5.24); the square uses the FULL-precision sum, not `(s >> 7)^2`.

## Pitfalls hit
- awk `-F' | '` is a regex ("space or space"): it cut every FEN to its first field (12,000 "bad FENs"). Use
  `sed 's/ | .*$//'`.
- A tool run under `run_pinned.py` (runpy) does not have its own folder on sys.path: nnue-pytorch scripts need
  `PYTHONPATH=<clone>` (serialize.py failed with `No module named 'model'`).
- Parallel Bash calls share the working directory on this PC: a `cd` in one leaked into the other and a patch script
  checked the wrong tree. Use absolute paths in parallel calls.
