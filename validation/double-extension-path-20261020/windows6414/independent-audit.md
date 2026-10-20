# Independent Windows 6.4.14 artifact audit

All **914 checks passed** on the immutable source `21538ec5416c909fc98a08688242a0b3b9710b25`.
The audit executed no engine and performed no rebuild.

The release ZIP (10,525,258 bytes) has 18 unique,
safe, non-symlink members, complete CRC and 17 verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All 69 source-export hashes match frozen Git objects. NNUE/eval
source, headers and weights match parent `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`. All 156 raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All 186
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the 351,063-node signature. Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. README/provenance correctly limit the claims.

Release SHA256: `6364f10a3aa1240fe1a8567e67b0720e1d015ce0bd1f0f26e384813b517ec269`.
Engine SHA256: `9db37be54c7b3407096a0721f07f9ab622f396e8b9260966915fe325707fd715`.
Raw evidence SHA256: `569921a209e973297845a4cd2ccc720ef60991b39eb213f9171abe68352d410f`.

This validates bounded Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
