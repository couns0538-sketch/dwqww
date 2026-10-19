# NNUE update differential driver

`tools/nnue_update_snapshot.cpp` calls the actual public NNUE API. Compile the
same driver separately against an immutable pre-fusion core and the candidate
core; compare their complete binary streams. It contains no copied update
arithmetic and does not calculate an expected result with a second formula.

At driver authoring, only static review was performed. Compilation and runtime
validation are owned by the main experiment; this note claims no passing
result. The driver is not added to CMake.

Coverage:

- All 31 possible add/remove masks for dirty counts 0 through 4, each with 32
  synthetic parents (992 cases). Count two includes all four flag masks.
- Finite constant and fixed-seed random parent values: signed zeros, positive
  and negative subnormals, the normal/subnormal boundary, values around 1,
  quantized values, large rounding boundaries, and the largest finite floats.
  Selected cases repeat a feature to exercise cancellation. Inputs are generated
  independently of the linked core. Both incoming validity values are used.
- Every case calls `update()` with distinct objects and in place. It checks
  parent value bits/validity are unchanged for distinct objects, both results
  have valid status, in-place/distinct value bits match, and count-zero updates
  copy all value bits. Child storage starts with a sentinel.
- Ten real FEN fixtures, every legal first move, 48-ply fixed-seed legal walks,
  and real null moves. Coverage assertions require both colors' king/queen-side
  castling, en passant, all four quiet promotions and all four capture promotions.
  Real states also emit separate full-refresh snapshots, without assuming their
  different addition order is a universal bitwise incremental-update oracle.

The stream uses explicit little-endian uint32 words without padding. Its header
is `0x3155554e, HiddenSize, fp_control`; each snapshot is `kind, case_id`, both
accumulator arrays' float bits, integer evaluation, and validity. Kinds 1/2 identify distinct
and in-place updates; 3/4 identify initial and subsequent full refreshes. The
`0x45564f43` trailer records case/snapshot/invariant counts, dirty-mask counts in
count/mask order, and each color's real move/null/castling/en-passant/promotion
counts. A readable count summary goes to stderr. Expect approximately 4 MB at
the shipped 128-hidden width; the exact size and counts must be recorded from
the actual run. The finite extreme inputs assume the unchanged shipped small
quantized weights; this is not a network-independent overflow test. NaNs, other
rounding modes, and exception-trapping equivalence are outside this check.

Use identical flags for both cores and both driver executables. Preserve
round-to-nearest and identical FTZ/DAZ settings. The driver rejects another
rounding mode. The header records the initial SSE MXCSR controls (FTZ/DAZ,
rounding and exception masks, excluding sticky flags), or `0xffffffff` on a
non-SSE target where controls must be frozen externally. Example Linux commands
(the source variables must identify frozen sources, and build variables their
corresponding immutable archives):

```sh
set -e
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -I "$BASE_SOURCE/include" "$SNAPSHOT_SOURCE/tools/nnue_update_snapshot.cpp" \
  "$BASE_BUILD/libforge_core.a" -pthread -o "$BASE_BUILD/nnue_update_snapshot"
g++ -std=c++20 -O3 -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -I "$CANDIDATE_SOURCE/include" "$SNAPSHOT_SOURCE/tools/nnue_update_snapshot.cpp" \
  "$CANDIDATE_BUILD/libforge_core.a" -pthread -o "$CANDIDATE_BUILD/nnue_update_snapshot"
"$BASE_BUILD/nnue_update_snapshot" > "$BASE_BUILD/nnue-update.bin" 2> "$BASE_BUILD/nnue-update.log"
"$CANDIDATE_BUILD/nnue_update_snapshot" > "$CANDIDATE_BUILD/nnue-update.bin" 2> "$CANDIDATE_BUILD/nnue-update.log"
cmp "$BASE_BUILD/nnue-update.bin" "$CANDIDATE_BUILD/nnue-update.bin"
sha256sum "$BASE_BUILD/nnue-update.bin" "$CANDIDATE_BUILD/nnue-update.bin"
```

Windows cross-compilation uses the same source and each frozen Windows core:

```sh
"$LLVM_MINGW_ROOT/bin/x86_64-w64-mingw32-clang++" -std=c++20 -O3 \
  -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static \
  -I "$BASE_SOURCE/include" "$SNAPSHOT_SOURCE/tools/nnue_update_snapshot.cpp" \
  "$BASE_WINDOWS_BUILD/libforge_core.a" -pthread \
  -o "$BASE_WINDOWS_BUILD/nnue_update_snapshot.exe"
"$LLVM_MINGW_ROOT/bin/x86_64-w64-mingw32-clang++" -std=c++20 -O3 \
  -march=znver5 -mtune=znver5 -fno-fast-math -ffp-contract=off -static \
  -I "$CANDIDATE_SOURCE/include" "$SNAPSHOT_SOURCE/tools/nnue_update_snapshot.cpp" \
  "$CANDIDATE_WINDOWS_BUILD/libforge_core.a" -pthread \
  -o "$CANDIDATE_WINDOWS_BUILD/nnue_update_snapshot.exe"
```

Run these through the experiment's configured Wine wrapper or native Windows,
preserve stdout as binary, require both exit statuses zero, and then compare
streams. Record Wine and native Windows separately. Keep this differential
check separate from output-layer instruction checks, CTest, exact cold/warm
one-thread search parity, and performance/strength acceptance.
