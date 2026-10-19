Independent read-only audit passed with no blockers.

Auditor: /root/windows649/audit_windows649. The auditor modified no files and ran no builds or engine/timing tests.

ZIP forge-6.4.9-candidate-windows-zen5.zip: 3,619,602 bytes; SHA256 f34560a98bdc7c2f6d39d470d25ddb1d85fdef460292b28b5741af82ee9affa1. All 13 archive files passed CRC and byte equality against the package directory. Zero duplicate names, Windows case collisions, unsafe paths or symlinks. All 12 SHA256SUMS entries passed.

All 64 exported source files match commit4edda780c68a742f20565d4e6a54a0c99a2c88a6 and the full manifest; package manifests correctly contain21 production files and5 test files. All13 compilation records use frozen export paths and recorded Zen5/optimization/floating-point flags. Actual build/validation drivers and copied evidence match saved copies, including decompressed disassembly. All5 delivered executables match build results, runtime before/after hashes and provenance.

Raw evidence supports8 successful functional/signature checks: core with6 perft references;8TT groups;0targetedrule50 failures;18,947 legal-oracle comparisons;27UCI checks;10ponder checks;5OwnBook transitions; bench11=351,063 nodes. All retained stderr files are empty.

OwnBook exchanges show true -> false -> true -> false with external-book reload -> true. Enabled states return external e2e4; disabled states emit searched depth records without a book-move indication. The evidence adapter changes only import root and temporary book pathname sent/expected under Wine Z: mapping; assertions and transitions remain intact. The test transcript's engine hash identifies the immutable Wine-launch wrapper; its contents and outer manifests connect it to actual delivered PE SHA2564ef3b482057f615239032c097cc909174fbcc34f4afe7307a7019b2705fea956. The adaptation-provenance record explains this accurately.

Independent commands: Python archive/hash/raw-evidence checks; git show source comparisons; llvm-readobj --file-headers --coff-imports on all6 build executables; llvm-objdump -d --no-show-raw-insn on delivered engine; Wine --version. All6PEs are AMD64 with13 imports each, restricted to KERNEL32/UCRT. Delivered disassembly has YMM vmaxps32/vminps32/vmulps64/vaddps32, fused arithmetic0. Wine observed: wine-10.0 (Debian10.0~repack-6).

All70 prior-artifact preservation records match current files. Prior6.4.8 ZIP remains4b4de385808f5a383aa60de6bfc09cf48c02e5d23c191624540026cdac95b55e. No6.4.9 offline validation bundle exists.

Scope: Wine correctness and bounded node signatures only. No speed, Elo, native Windows, physical Ryzen or Stockfish superiority result.
