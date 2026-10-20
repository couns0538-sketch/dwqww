# Independent Windows 6.4.18 artifact audit

All **1064 checks passed** on the immutable source `fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b`.
The audit executed no engine and performed no rebuild.

The release ZIP (12,049,843 bytes) has 19 unique,
safe, non-symlink members, complete CRC and 18 verified checksums. Every
member matches the expanded directory. The distributed engine and five test
executables match the exact Wine-tested bytes. All seven built PE files were
independently parsed as AMD64 PE32+ with system/UCRT imports only; the actual
static core hash matches the runtime input record.

All 70 source-export hashes match frozen Git objects. The exact
four changed files are CMakeLists.txt, src/search.cpp, src/uci.cpp and the new tests/correction_history_tests.cpp.
All parent test files, NNUE/eval source, headers and weights match parent `47f0560221d986e41a309853e1295c557fcf5bf6`. All 183 raw files
match original bytes, hashes and sizes in the embedded and external raw ZIP
manifest; that exact archive is embedded in the release. All 206
parent evidence files remain unchanged. Original Wine CRLF logs remain intact.

The original records show all nine Wine checks passed, including core/perft,
eight TT groups, rule50, 18,947 legal comparisons, actual correction-history feedback, UCI/ponder, five book
transitions and the 352,313-node signature (actual Windows signature frozen before packaging; no parent/native-parity requirement). Strict Zen5 C++20 Release/static
flags, AVX2 instructions and absence of fused arithmetic agree with original
compile and disassembly records. The source, tested PE and raw bench transcript
match the pre-package signature freeze embedded in provenance. Freeze/package
timestamps establish the declared ordering. README/provenance correctly limit
the claims.

Release SHA256: `286a913f8bb6366d28020ef83bce5235809d1d991d41023609f0ea6446284ebc`.
Engine SHA256: `38ee9caa98d5f6c80bbcaae5c1ebf2ff628cc2a4c99b2e9e7a6fd5474534bcc9`.
Raw evidence SHA256: `a7adc1a20220266c4cfdbdef2b964c4e4bbdfa22fdaab6e8bbfc8e8d058b03ab`.

This validates the Windows stage only; native gates remain separate and this is
not an accepted release. The original 6.4.16 TSan FAILED 8/9 qualification remains
explicit; no full parent native pass is inherited. This audit validates bounded
Wine correctness and artifact provenance. The one-line EMA-to-residual increment
change remains an unaccepted search ablation, not a known-bug repair. No speed,
NPS, Elo, native Windows, physical Ryzen or Stockfish superiority is established.
