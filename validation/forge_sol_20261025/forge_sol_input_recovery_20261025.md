# Authoritative handoff recovery

Recovered from user-uploaded `/workspace/attachments/fa34ca69-5f5f-432c-a27c-3b89a9611cc3/forge_handoff_20261025_0406.zip`, SHA256 `ad8f84a16b1f21b723913d683dde67e130ab3fd34dd6dd90337352d1c3aee491`. All 86 rows of the embedded README_CONTENTS.md manifest were byte-verified: zero failures.

The inner lock source archive, SHA256 `dd2f9e992341738996b11c64efca6ddafdffa8363530034d1d1394a06379116f`, was read in memory. All 73 manifest files match both their declared SHA256 and Git commit `f4911f2` byte for byte. Net SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`, MD5 `6d22f612c855e17c62d396d32da99ea4`. No source mismatch or recipe/trainer access gap remains.

## Exact PC recipe

Original `01_lock/pc_build/build_h256_e12.ps1` SHA256 `a5c88c838ff91b778501d913de38dc1286e1958268b78810b0483cea5306bd23`. Its log SHA256 `b89749700278e9052ebc4046f8e409d1231c4a410b66bddf9a70042925f874fd`.

```
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o forge_h256_e12.exe
```

Compiler: `C:\msys64\ucrt64\bin\g++.exe`, MSYS2 Rev14 15.2.0. Direct g++ compilation, not CMake. Original source tree has only embedded net changed versus the PC ep10 tree; the script verifies 20 compile files, 73 source-manifest files, net SHA256 and MD5, and baseline/candidate d11/d13 nodes. Log records executable SHA256 `456743d9c065d2dec2d9a52ef23992f36908efc1243b6916edab9a8ab3c7fdfa`. It records a legacy SIMD checker false negative for absence of vmaxps because AVX512VL uses masked zeroing; that old FAIL is not evidence of FMA.

The lock recipe does not enable FORGE_EXPOSE_TUNABLES. The prompt separately permits it for option builds.

## Trainer and PGO notes

Original `07_nnue/train_resid_v3b.py` recovered, SHA256 `5cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f`. Its changes and next-week notes are alongside it.

HANDOFF_PROMPT.md Task C lines 96-106 requests Linux bash and PowerShell/MSYS2 two-stage PGO using exact lock recipe; both stages retain no-FMA/no-fast-math flags; training uses bench16 plus specified varied fixed-depth FENs with no external data. No source changes or new UCI option. Gates: identical five-depth lock benches, both perft5 counts, ctest13/14 and exact four known FAIL lines, FMA0; bench20 ABAB at least eight pairs with median, CPU and load. Gain below3% means drop. Backup if PGO is blocked: result-consistency skip filter in trainer v3b, OFF CLI default, retain RAM fix, fixed-seed byte-identical outputs with flag OFF; user trains/gates it.

The idea board's older rank2 row mentions build C, whereas the actual handoff Task C specifies exact lock recipe. Apply the current user's instructions if they further clarify scope.

No engine was built/run; no repository or Git index/ref was modified. Only selected small handoff files and these verification notes were written in this recovery directory.
