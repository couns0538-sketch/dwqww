# Independent Windows 6.4.15 artifact audit

All **929 checks passed** on the immutable source `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`.
The audit executed no engine and performed no rebuild.

The release ZIP (10,541,371 bytes) has 18 unique,
safe, non-symlink members, complete CRC and 17 verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All 69 source-export hashes match frozen Git objects. The exact
four changed files are board.cpp, tests/tests.cpp and the two version labels. NNUE/eval
source, headers and weights match parent `21538ec5416c909fc98a08688242a0b3b9710b25`. All 158 raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All 190
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the 382,424-node signature (recorded, not parent-parity required). Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. README/provenance correctly limit the claims.

Release SHA256: `1eb3a128e4e905921e0440482076b0fd47bf0194e08a91eb099efe7fbce5df42`.
Engine SHA256: `9e5335f917decbdc9ef6ee76e71ec85d5ff7695d5078e90e76c3dac8498bc5dc`.
Raw evidence SHA256: `451a2a71b7da77136cce8041c5f4db463a4e0617811f0b4c192f8b46956652e3`.

This validates bounded Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
