# Unchanged R10 native qualification (Linux cloud)

This evidence qualifies source `7f79c34901fdd118bc4bf904f4bcaec4006047c6` and its existing HalfKA loader only. It does not establish AL1 768x256 export-format compatibility, target-PC qualification, GPU training, NPS improvement, or playing strength.

GCC 14.2.0, Release `-O3 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256`. Exact configure/build recipe, original build output, effective compiler flags, source/binary/network/fixture hashes, and qualification command arguments are retained here.

All five OFF pins PASS: d11=312866, d13=862329, d16=3024920, d20=12389307, d22=34048354. Startpos perft5=4865609 and kiwipete perft5=193690690 PASS. Whole-executable disassembly FMA mnemonic counts: forge=0, halfka_tool=0. Tracked source bytes and frozen file hashes remained unchanged.

Full CTest: 14/15 passed; exit 8; only forge_tests failed. Exactly four diagnostics were observed:

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 623 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

The referenced historical known-failure checker is absent from this pinned snapshot; the report preserves the actual observed diagnostics without treating CTest exit 8 as success. Original CTest stdout and LastTest.log are in `ctest/`.

CTest created untracked Python cache files in the pinned worktree. The first qualification preflight stopped before compiling/running tests because it initially required no untracked files. `qualification_run.log` preserves that preflight failure. The final run accepts those recorded untracked cache files while verifying all tracked source hashes before/after; no source files were edited or caches deleted.

`halfka_tool` was compiled from the existing `opus_r10/tools/halfka_tool.cpp` and the frozen engine core, using the same architecture and floating-point flags. Its path is `/tmp/astra-r10-native/halfka_tool`; invoke `eval NET FENS OUTPUT` for raw/cp results plus native AVX2 versus scalar mismatch checks. These baseline results do not themselves assert that an exported net passed parity.
