# Forge 6.4.20 Windows candidate validation

Frozen source `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`, parent `61f598056572dfade6994af8ad2e38817cd28aa3`.
The change replaces repeated per-pawn span construction with equivalent geometry
from the existing enemy-pawn attack mask and a pure unsigned constexpr fill using
8/16/32-bit shifts. This can reduce evaluation work; no speed gain is measured here.

The fresh LLVM-MinGW 23.1.3 Zen5 C++20 Release build passed on its first attempt,
with static linking, j1 and no FMA, fast-math or LTO. All nine actual PEs, static
core, runtime and pawn test objects, frozen source and original build/configuration/
flag/command/stdout/stderr records are retained. The source delta is exactly five
exports; Board, NNUE source/weights, search and all earlier tests remain unchanged.

All eleven Wine checks passed on the first attempt: core/perft, 37,320 pawn-span
checks, three compiled constexpr assertions, 347 runtime PSQT checks, 54 correction
checks, eight TT groups, rule50, 18,947 legal comparisons, UCI, ponder, five OwnBook
transitions and the exact preregistered 352313-node parent signature. Input hashes
remained unchanged; AVX2 instructions and no fused operations were verified.

Packaging ran after source/build/runtime writers closed. The ZIP contains 21
members with 20 complete checksums, including eight shipped PEs. The raw ZIP
retains 225 original files, both actual test objects and all source/proof records.
An independent read-only audit passed all 1,538 checks on its first execution:
72 frozen exports, exact root-source-proof hash, actual PE/core/object identities,
safe archives, original raw bytes and 483 protected Windows 19 files unchanged.
No engine, build, audit retry or waiver occurred. The two root-approved auditor
provenance assertions were added before its first execution; original auditor
bytes, exact diff and static review note are retained. Historical source-only
pins remain explicitly qualified, rather than relabeled as final package pins.

Artifact: `releases/forge-6.4.20-candidate-windows-zen5.zip` (14,531,624 bytes).
ZIP SHA256: `92cf639dad35d5f44d6ef492eab1a927606aaaf609eec447a41f05775420e63c`.
Engine SHA256: `ae4351057435b02d8d876efdafd6b275724bdf46ef26833d49dfe60d748e3fe0`.
Core SHA256: `3a9325658d49ba957033ffa152087df2d6a0f15b5145933024328a50de61fc0c`.
Raw SHA256: `86cf76fec26e902e53ec8a1d0799f716edf7aef9187fc8e4e32e913856dda9e5`.

All Windows build/runtime/package/audit CPU work finished 23:33:08.185113 UTC.
No compiler, engine, compression, hash or audit job remains active for this stage.
No production-source or Git change was made by this Windows qualification task.

This is a correctness/artifact-validated candidate, not an Elo-accepted release.
Native 20 qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified.
No speed/NPS gain, timed match, Elo gain, native Windows/physical Ryzen test or
Stockfish superiority is established. Next: preserve/push these immutable files
and continue separately calibrated equal-time native performance/strength tests.
