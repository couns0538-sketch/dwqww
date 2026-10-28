# S-A2 — NnueInt16 (int16 weights, int32 accumulators) + trainer `--weight-clip`

Branch `opus-sol-SA2` = AL1 lock `d4f4312` + CI baseline `0d99f02` + this job. Two parts, both OFF by default.

## 1. Engine: UCI option `NnueInt16` (check, default false)
- **ON:** integer inference with the include file's own int16 weights (scale 4096) and **int32 accumulators**:
  `A = b1 + Σ w1`, `a = clamp(A, 0, 4096)`, `q = (a² + 1024) / 2048` (scale 8192), `T = Σ q·w2` (int64),
  `cp = trunc(clamp((T/2^25 + b2/4096)·400/2.25))`. AVX2 kernels (packus/min clamp, mulhrs square, madd dot,
  int64 widening per 16-unit group) or the scalar fallback; both give identical results.
- **OFF (default):** the lock's float path, unchanged arithmetic (bench/perft = lock pins, FMA 0).
- **Representation tag:** `refresh()` follows the mode; `update()` follows the parent; `evaluate()` follows the
  accumulator. A mode change takes effect at the next search (the root is refreshed at every search start).
  `setoption` stops a running search first and clears the TT; the mode flag is `std::atomic<bool>`.
- **Eligibility:** the option activates only if every lane satisfies `|b1| + Σ768|w1| + 4·max|w1| < 2^24` (exact
  float-grid accumulators, so float and int16 differ only in the output stage) and `2·H·8192·32768 ≤ 2^53`;
  otherwise `info string NnueInt16 unavailable; using float`. Lock net: lane bound 2,054,814 (8.2× below 2^24,
  int32 headroom ×1045).
- **Files:** `src/nnue_int16.inc` (new), `src/nnue.cpp` (3 hooks + includes), `include/forge/nnue.hpp`
  (Accumulator gains `integer_values` + `integer`; API `int16_available/int16_active/set_int16`), `src/uci.cpp`
  (option), `CMakeLists.txt` (tests), `tests/nnue_int16_tests.cpp`, `tools/nnue_int16_regression.py`.

```sh
# box-recipe build + lock identity (OFF) + ON bench
nice -n 19 bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/SA2/forge.exe
nice -n 19 $PY -I -B $LA/2_build/uci_check.py /f/opus_scratch/build/SA2/forge.exe --full          # ALL OK
nice -n 19 $PY -I -B opus_round1/sol_SA2/uci_bench.py <exe> --opt NnueInt16=true --depths 11 13 16 20 22
# tests (CTest): forge_nnue_int16_tests (AVX2 kernels), forge_nnue_int16_scalar_tests (-mno-avx2), nnue_int16_uci_regression
# planted bugs: 5 engine mutants, each must make the test fail
nice -n 19 $PY -I -B opus_round1/sol_SA2/mutation_check_sa2.py <worktree> <new out dir>
# NPS ON vs OFF, same binary (advisory, CPU-time NPS on the loaded PC)
nice -n 19 $PY -I -B opus_round1/sol_SA2/nps_ab_opts.py <exe> "<exe>::NnueInt16=true" 5 16 20 --allow-node-diff
```

### Parity (10,000 FENs, lock net)
```sh
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -Iinclude \
    opus_round1/sol_SA2/nnue_int16_dump.cpp src/nnue.cpp src/bitboard.cpp src/board.cpp src/eval.cpp src/eval_params.cpp -o dump_avx2.exe
#   (-march=x86-64 instead of znver5 -> the scalar integer kernels: dump_scalar.exe)
dump_avx2.exe fens_10k.txt > dump_avx2.tsv
$PY -I -B opus_round1/sol_SA2/sa2_parity.py --net src/nnue_weights.inc --fens fens_10k.txt --dump dump_avx2.tsv --dump dump_scalar.tsv --out parity.json
```
`sa2_parity.py`: exact Python integer reference (int64 + IEEE double, same rounding) and a float32 emulation of the
OFF path (same 16-lane order); also accumulator signatures, incremental-vs-fresh counts, and float-vs-int16 stats
(max/mean/p99, histogram, raw-net and full-static sign flips).

## 2. Trainer: `trainer_v3c_clip.py --weight-clip [C]` (default off)
= `train_resid_v3c.py` of opus-sol-S50 (ff98828a) + `--weight-clip` (`v3c_to_clip.diff`). Never run it under a
`train_resid*` name on the PC; the smoke runner uses renamed copies.
- After every optimizer step (after v3c's int16-rail projection) W1, B1, W2, B2 are clamped to ±K/4096,
  K = floor(C·4096) ∈ [1, 32766]. Bare `--weight-clip` = **K 21704** (C = 5.298828125): the largest K with
  773·K < 2^24, so any clipped net passes the engine's NnueInt16 eligibility check for every lane at any width,
  and every exported value is ≤ 21704 (33.8% below the int16 rail 32767).
- Every export is verified before a file is written (`INT16 CHECK` line: max|q| per tensor, values at the bound,
  values at the int16 rail, lane bound, int32 headroom); a value beyond K refuses the export. `weight_clip_units`
  goes into the checkpoint config and the per-epoch `.json` only when the clip is on.
- **int32 accumulator bound:** with int16 weights |w| ≤ K, a lane holds at most `|b1| + 32 active features` →
  |A| ≤ 33·K ≤ 1,081,311 for any int16 net (≤ 716,232 with K 21704); even all 768 inputs + 4 transient columns give
  773·32767 = 25,328,891 < 2^31 − 1. int32 accumulators cannot overflow for any int16-exportable net of any width;
  the output sum is int64 (per-group int32 lanes ≤ 4·8192·32768 = 2^30).
- Off: v3c byte-identical (artifacts, normalized stdout, settings dump).

```sh
cd /f/opus_scratch/sol_SA2
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TMP='F:\opus_scratch\sol_SA2\tmp' TEMP='F:\opus_scratch\sol_SA2\tmp'
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe; J=<worktree>/opus_round1/sol_SA2
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa2.py --stage      # renamed copies + pinned data32 sample
nice -n 19 $PY -I -B $J/test_trainer_clip_sa2.py -v
nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa2.py --suite r1 && nice -n 19 $PY -I -B $J/opus_nnue_smoke_sa2.py --compare r1
nice -n 19 $PY -I -B $J/mutation_check_trainer_sa2.py
```
Example queue line for the crew (not applied; needs CR + crew vote): `<name> --script <renamed trainer_v3c_clip.py>
--weight-clip <the run's usual args>`.

## Files
See `FILES.txt`. Logs in `logs/`; big outputs (dumps, smoke run dirs, mutant builds) stay in `F:\opus_scratch\sol_SA2`
and `F:\opus_scratch\build\SA2` with sha256 in the logs.
