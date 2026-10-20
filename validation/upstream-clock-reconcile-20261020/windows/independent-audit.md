# Independent Windows 6.4.13 artifact audit

All **872 checks passed** on the immutable source `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d`.
The audit executed no engine and performed no rebuild.

The release ZIP (10,514,835 bytes) has 18 unique,
safe, non-symlink members, complete CRC and 17 verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All 69 source-export hashes match frozen Git objects. NNUE/eval
source, headers and weights match parent `8865666cc0ab4961cd507bae40ff6ce44e9319df`. All 151 raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All 175
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the 351,063-node signature. Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. README/provenance correctly limit the claims.

Release SHA256: `ca2512f2b7a91a3b9e391992fa8e5ebc622e79daa5a9fcc088f3b2819a74cbb7`.
Engine SHA256: `3693e6f2ffefea3cfe100d1f1c920ad21e6cdd5fff7ef389896728773be1f56a`.
Raw evidence SHA256: `203cc47c0446b7e07747ea73eb41777c5c6b13db2aafa20ae04251f0b55be8d4`.

This validates bounded Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.

The first audit-helper attempt stopped on a dotted-version archive-path construction error before opening the release ZIP. The failed helper and exact error are retained; the corrected path passed the complete audit. No release, raw evidence, original result or engine behavior changed.
