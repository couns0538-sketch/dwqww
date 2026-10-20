Independent read-only audit passed with no blockers.

The Forge 6.4.11 Windows ZIP has 13 files and 3,630,828 bytes, SHA256 `59978ffd9c38688663179642541859d7540d620b9669bfe9e1186f0a0184aa46`. CRC, directory byte equality and all 12 SHA256SUMS entries passed. There are no duplicate names, Windows case collisions, unsafe paths or symlinks.

All 66 exported files match the frozen manifests, including 21 production and five test entries. Differences from audited 6.4.10 are limited to CMake/UCI version strings and the new capture block. The saved extraction/package drivers consistently pin `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`. All 13 compilation records retain strict floating-point flags, and all 87 base evidence files match their saved copies. Six build executables, four snapshot helpers and two retained engine copies passed fresh PE inspection: AMD64, with 13 imports restricted to KERNEL32/UCRT each. Packaged executable hashes match the actual build, before/after runtime records and provenance.

The engine SHA256 is `a14eaeeac37707075134f42f4c68a2fb6d3121ef65b77f7754511766749093e2`; actual core SHA256 is `9855bc83fd2dbeca89129e8d510d1d8c33235201e557e4dfe0e13b6e112a6364`.

Independent cmp checks confirmed Windows 6.4.10, Windows 6.4.11 and corresponding Linux streams are byte-identical. Update streams have 4,097,860 bytes, SHA256 `ca9e7405c5f7b7506455a3b6b104683ccc8d83e75b0bbaf8d9c17c3ecce1ff45`; original streams have 21,192,328 bytes, SHA256 `3ef4bacc1877f34b929c6c4cd349c56ff0c07c93545b292914775bcd9ae173a5`. Headers consistently show 128 hidden units and MXCSR 0x1f80: nearest rounding, FTZ/DAZ disabled.

Parsed coverage confirms 1,644 cases, 3,940 snapshots, 1,644 parent-preservation checks and 1,644 exact in-place checks. All 31 dirty masks and both-color special moves are covered. There are 79 count-three remove/remove/add cases and 621 inherited count-two remove/add cases, each exercised distinct and in place. Retained actual cores, engines and driver sources match their frozen originals.

Fresh emitted-code inspection verified the count-three/remove/remove/add guard, two ordered subtractions followed by addition, and one child store per lane on ZMM and scalar alias routes. The inherited count-two path and original other-pattern fallback remain. Retained standalone symbol disassembly matches fresh output, with zero fused arithmetic. The existing production output-layer checker passed separately. Detailed instruction addresses are in nnue-capture-fastpath-independent-audit.json.

Raw Wine evidence supports eight successful checks: core with six perft references, eight TT groups, rule50, 18,947 legal comparisons, 27 UCI checks, ten ponder checks, five OwnBook transitions and bench11 at 351,063 nodes. The OwnBook adapter changes only the import root and temporary path translation, and wrapper-to-PE provenance is explicit.

All 683 preservation records remain unchanged, including previous source/build/core/package/evidence. The explicit 6.4.10 evidence manifest check covers 103 records. No new offline validation bundle exists.

The auditor used file/archive hashing, cmp, stream parsing, llvm-readobj and llvm-objdump. No files were edited and no builds, engines, timing trials, Git commands or network jobs were run during the audit. These results establish correctness parity and static code properties. Speed, Elo, native Windows, physical Ryzen and Stockfish superiority remain unproven.
