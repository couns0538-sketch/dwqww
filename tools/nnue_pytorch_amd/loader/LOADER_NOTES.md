# Native data loader on Windows: builds, numbers, merge notes (R6 J4)

The loader is nnue-pytorch's C++ `data_loader/cpp` (GPL-3.0), built as a DLL that the Python side loads with ctypes.
Everything here was measured on grok-pc (Zen 5, Windows 11) on 2026-10-29.

## What to merge
1. **CMake patch** (`src/data_loader/cpp/CMakeLists.txt`, in patch 0003). Low risk:
   - `NNUE_BMI2=AUTO|ON|OFF` cache option. AUTO keeps the Linux `/proc/cpuinfo` detection. Where that file is
     missing (native Windows) and the compiler is GNU, a `check_cxx_source_runs` probe uses
     `__builtin_cpu_supports("bmi2")` and rejects znver1/znver2, where pdep is slow.
     On grok-pc this prints `-- Adding BMI2 support`.
   - MSVC-style compilers (cl / clang-cl, `CMAKE_CXX_COMPILER_FRONTEND_VARIANT=MSVC`) get `/arch:AVX2 /O2` flags
     instead of the GNU ones, and `-mbmi2` is only added for GNU-style drivers.
     Real `cl.exe` was **not** tested; clang++ (GNU driver, MSVC target) was.
2. **`NNUE_DATA_LOADER_LIB=<path>`** (`src/data_loader/_native.py`, in patch 0003) loads exactly that DLL.
   Without it the upstream rule applies: the newest `build/**/*training_data_loader.*` wins.
3. **Which DLL to use on this PC.** Recommended: `clang23_msvc` (1.88x per thread), unless runs must reproduce a
   g++/Linux build bit for bit (see "Equality"). In that case use `gxx_pgo2` (1.08x).

## How to build (`build_loader.sh <variant>`, BelowNormal, `-j2`, output `F:\opus_scratch\r6\loader\<variant>`)
| variant | compiler | notes |
|---|---|---|
| `gxx_bmi2` | MSYS2 ucrt64 g++ 15.2 | DLL linked `-static -Wl,--exclude-libs,ALL`; BMI2 auto-detected |
| `gxx_bmi2_off` | same | `-DNNUE_BMI2=OFF`, for A/B |
| `gxx_pgo2` | same | CMake `PGO_Generate` -> `ninja pgo_run` (5 x 131072 positions of small.binpack) -> `PGO_Use`; the bash PGO script is not needed |
| `clang23_msvc` | AMD clang 23 from the ROCm SDK (`F:\nnue_pytorch\venv\Lib\site-packages\_rocm_sdk_core\lib\llvm\bin\clang++.exe`), MSVC target | `-DNNUE_BMI2=ON -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded` (static CRT, no DLL dependencies); output `training_data_loader.dll` (no `lib` prefix, still matched by the glob) |

Build pitfalls hit on the way:
- g++ fails silently (even on CMake's trivial test) unless `C:\msys64\ucrt64\bin` is on PATH, because
  `cc1plus` needs its DLLs.
- A `-static` MinGW DLL re-exports libgcc/libgcov symbols, so the exe that links it sees `_Unwind_Resume` and
  `__gcov_indirect_call_profiler_v4` twice. Fix: `-Wl,--exclude-libs,ALL` on the DLL, and no `-static` for the exe.
- LLVM 18 (`C:\Program Files\LLVM`) cannot compile against the MSVC 14.51 STL:
  `error STL1000: Unexpected compiler version, expected Clang 20 or newer`. The ROCm SDK's clang 23 can.
- clang PGO is not possible here: the ROCm SDK has no `llvm-profdata`, and LLVM 18's would not read clang-23
  profiles.

## Numbers (single thread, `training_data_loader_bench.exe -i 40 -p 1 -c 0 small.binpack`, feature set Full_Threats+PP_3Wide+K32H3, 131072 positions per iteration, builds alternated, 2 rounds)
| build | MPos/s round 1 / 2 | vs setup build |
|---|---|---|
| setup (g++ 15.2, -static, BMI2 off) | 0.249 / 0.249 | 1.00x |
| gxx_bmi2 | 0.264 / 0.264 | 1.06x |
| gxx_pgo2 | 0.269 / 0.272 | 1.08x |
| **clang23_msvc** | **0.460 / 0.473** | **1.88x** |

small.binpack skips 96.5% of its positions (filter + skipping config), so this bench mostly measures decode and
skip speed. Training effect at the smoke config (K32H3^, L1 256, batch 4096): none. The setup DLL and the clang DLL
with 1 or 2 workers gave 424k-436k pos/s, all GPU-bound.

## Equality (`dl_equal.py`)
- `fens` mode, features from a fixed list of 32,768 FENs: the sha256 over every batch field is **identical** for
  setup, gxx_pgo2 and clang23_msvc, for both K32H3 and the full feature set.
- `stream` mode, binpack, 1 thread, 12 batches: deterministic per build (the setup DLL twice gives the same hash),
  and identical between the g++ builds. **clang23_msvc differs.**
- `window` mode, order-independent fingerprint:
  - First shuffle window (1,048,576 positions): same multiset in both builds (`4e403d7c5857d50b`, 242,393
    distinct), but in a different order.
  - Two windows: different (271,242 vs 271,345 distinct).
- Cause: `std::shuffle` (`lib/parallel_dataloader.h`) is implementation-defined. libstdc++ and the MSVC STL produce
  different permutations from the same thread-local `mt19937_64`, and the skip decisions that follow draw from the
  same engine, so later windows keep different, equally valid positions.
- If cross-compiler reproducibility matters, replace `std::shuffle` with an explicit Fisher-Yates that draws from
  the engine directly. That is an idea only, not done in R6.

## Triton and the loader
upstream `data_loader/_transport.py` imports a Triton unpack kernel (`_cuda_transport.py`), but `move_indices`
packs only when `torch.version.hip is None`. **On ROCm the loader never uses Triton** and sends dense index rows;
the prefetch stream only does the H2D copy. An earlier version of these notes said the loader would fail without
the venv on PATH; that was wrong. What does need the venv on PATH is Triton itself: the R6 kernels (they fall back
to torch) and torch.compile (it does not fall back).
