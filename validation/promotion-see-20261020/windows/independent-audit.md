# Independent Windows 6.4.17 artifact audit

All **1211 checks passed** on the immutable source `47f0560221d986e41a309853e1295c557fcf5bf6`.
The audit executed no engine and performed no rebuild.

This is attempt 2 after one authorized audit-harness correction. Attempt 1
failed because its README predicate required lowercase `no accepted`, while
the truthful README starts the sentence with `No accepted`. The corrected
checker changes only that phrase comparison to casefold; all other checks
remain exact. The original checker and failed stdout/stderr/command are
retained unchanged. The exact one-line diff, corrected checker SHA256 and
schema-versioned correction provenance are saved alongside this report.

The release ZIP (10,591,760 bytes) has 18 unique,
safe, non-symlink members, complete CRC and 17 verified checksums. Every
member matches the expanded directory. The distributed engine and four test
executables match the exact Wine-tested bytes. All six built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All 69 source-export hashes match frozen Git objects. The exact
four changed files are board.cpp, tests/tests.cpp and the two version labels.
The other four test files, NNUE/eval source, headers and weights match parent `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`. All 165 raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All 435
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all eight Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, UCI/ponder, five book
transitions and the 382,424-node signature (actual Windows signature frozen before packaging; no parent/native-parity requirement). Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. The source, tested PE and raw bench transcript
match the pre-package signature freeze embedded in provenance. Freeze/package
timestamps establish the declared ordering. README/provenance correctly limit
the claims.

Release SHA256: `9c532d5394b58f8654e316de99b4a5771149e75327c31586ae179814212e85f9`.
Engine SHA256: `abfec902a99737df1855f2eb54e0267b4744d1f98b81a040b5b06220ab34ab7d`.
Raw evidence SHA256: `7f3a177d074b65953b2f0693ead05eafae078c62ddaba28f2a5928adb533ad40`.

This validates the Windows stage only; native gates remain separate and this is
not an accepted release. The original 6.4.16 TSan FAILED 8/9 qualification remains
explicit; no full parent native pass is inherited. This audit validates bounded
Wine correctness and artifact provenance. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
