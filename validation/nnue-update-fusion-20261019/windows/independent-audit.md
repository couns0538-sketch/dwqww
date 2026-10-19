Independent read-only audit passed with no blockers.

The Windows 6.4.10 candidate ZIP has 13 files and 3,628,551 bytes, SHA256 `771ea7ab84bd86a006c6197af56e81911625224144f33d3fd59ebcb51d5ecd2a`. CRC, directory byte equality and all 12 SHA256SUMS entries passed. There are no duplicate names, Windows case collisions, unsafe paths or symlinks.

All 66 exported files match source commit `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`; the 21 production and five test manifest entries agree. All 13 compilation records use the frozen source export and strict floating-point flags. All 81 base evidence files agree with their saved copies, including decompressed disassembly. Five packaged executable hashes match the actual build, runtime before/after records and provenance. Fresh PE inspection covered six build executables and four snapshot helpers: AMD64 with 13 KERNEL32/UCRT imports each.

Independent cmp checks confirmed all four Windows-parent, Windows-candidate, Linux-parent and Linux-candidate update streams are identical: 4,097,860 bytes, SHA256 `ca9e7405c5f7b7506455a3b6b104683ccc8d83e75b0bbaf8d9c17c3ecce1ff45`. All four original snapshot streams are also identical: 21,192,328 bytes, SHA256 `3ef4bacc1877f34b929c6c4cd349c56ff0c07c93545b292914775bcd9ae173a5`.

Parsed update headers consistently show 128 hidden units and MXCSR 0x1f80: nearest rounding, FTZ/DAZ disabled. Parsed coverage confirms 1,644 cases, 3,940 snapshots, 1,644 parent-preservation checks, 1,644 in-place checks, all 31 dirty masks and both-color special moves.

Separate emitted nnue::update inspection verified the count-two/remove/add guard at 0x14000d618..d630, original fallback selection, subtraction before addition, and one child store per lane. Zen5 vector routes use eight ZMM groups per perspective; scalar alias alternatives preserve the same order. No fused arithmetic occurs, and the standalone retained symbol instructions match fresh disassembly. The separate production output-layer checker passed, with YMM counts 32 max, 32 min, 64 multiply and 32 add. See nnue-update-fastpath-independent-audit.json for detailed instruction addresses.

Raw Wine evidence supports eight successful functional/signature checks: core with six perft references, eight TT groups, rule50, 18,947 legal comparisons, 27 UCI checks, ten ponder checks, five OwnBook transitions, and bench11 at 351,063 nodes. The OwnBook evidence adapter changes only the import root and temporary path translation; wrapper-to-PE provenance is explicit.

All 359 preservation records remain unchanged, including prior 6.4.9 source, build, core, package and evidence, and all prior 6.4.8 packages and validation bundle. The explicit 6.4.9 evidence manifest and prior 6.4.8 preservation checks each cover 70 records. No new offline validation bundle exists.

The auditor used archive/hash/source comparisons, cmp, stream parsing, llvm-readobj and llvm-objdump. The audit edited no files and ran no builds, engines or timing trials. These results establish correctness parity and static code properties. Speed, Elo, native Windows, physical Ryzen and Stockfish superiority remain unproven.
