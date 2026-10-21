# Independent Windows 6.4.21 artifact audit

All **1615 checks passed** for source `2e151d019bc58dff2ab4e76e99ef99516af8d222`, parent `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`.
No engine or rebuild ran. All 73 source files match frozen Git
and the root proof whose byte hash is explicitly pinned to root authorization.
The five changes are CMake/UCI metadata, bitboard.hpp, eval.cpp and new nearest-pawn
tests; all old tests, Board, NNUE, search and evaluation parameters are unchanged.

The ZIP has 22 safe verified members and 21 checksum entries.
All ten built and nine shipped PEs match tested bytes and system-CRT AMD64 PE32+
requirements. Core and all runtime/pawn/nearest object/source/PE/compile identities
match originals. All 229 raw files and 521 protected Windows 20
files retain exact bytes/hashes, including original CRLF stream bytes.

Twelve Wine checks passed with 791680 nearest comparisons across 395840 sets,
six nearest constexpr assertions, 37320 pawn-span/three constexpr assertions,
347 runtime PSQT, 54 correction, 8 TT groups, rule50, 18947 legal comparisons,
UCI/ponder, 5 OwnBook transitions and exact preregistered 352313 signature. Strict
Zen5 C++20 Release/static j1/noLTO/noFMA and AVX2 records agree with provenance.

ZIP SHA256: `e2af16d497f5c1560d413d601c3af50e364c3dfa30e3a17d49936812ac712227`.
Engine SHA256: `cffc884ebedcce85b3636160b8ed9b74450f99122a185481206fd53729916aa9`.
Raw SHA256: `0eb2bb2b85255110e4793702d635e552e146a04179d5c27760c539419c6a5aff`.

This is bounded Windows/Wine artifact correctness only. Native 21 qualification
is separate; original 6.4.16 TSan FAILED 8/9 remains qualified. No 21 speed, NPS,
Elo, native Windows/physical Ryzen or Stockfish superiority result is established.
