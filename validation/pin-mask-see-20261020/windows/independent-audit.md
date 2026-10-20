# Independent Windows 6.4.16 artifact audit

All **1151 checks passed** on the immutable source `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`.
The audit executed no engine and performed no rebuild.

The release ZIP (10,560,696 bytes) has 18 unique,
safe, non-symlink members, complete CRC and 17 verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All 69 source-export hashes match frozen Git objects. The exact
three changed files are board.cpp and the two version labels. All test sources, NNUE/eval
source, headers and weights match parent `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`. All 158 raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All 408
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the 382,424-node signature (required frozen-parent parity). Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. README/provenance correctly limit the claims.

Release SHA256: `b11c5a86b4b5dea3c42b9edc1c3787674b3c9f294e6de908cbe28f53c0e64b11`.
Engine SHA256: `60ab9a68a448276e3f1e499debbe91ae4603805bb37316729667eb6fd9efaa95`.
Raw evidence SHA256: `11afa82386e94fe189ddd3a65345bcd26fe4b6f962281b2f236644115f8f98c7`.

This validates the Windows stage only; native gates remain separate and this is
not an accepted release. It validates bounded Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
