# Independent Windows 6.4.22 artifact audit

All **1779 checks passed** for source `ff2e269c6058be84456e3b98344826d17b0056eb`, parent `2e151d019bc58dff2ab4e76e99ef99516af8d222`.
No engine or rebuild ran. All 74 source files match frozen Git
and the root proof whose byte hash is explicitly pinned to root authorization.
The four changes are CMake/UCI metadata, search.cpp and new PV metadata tests;
all old tests, Board, NNUE, evaluation and evaluation parameters are unchanged.

The ZIP has 23 safe verified members and 22 checksum entries.
All eleven built and ten shipped PEs match tested bytes and system-CRT AMD64 PE32+
requirements. Core and all runtime/pawn/nearest/PV metadata object/source/PE/compile identities
match originals. All 266 raw files and 543 protected Windows 21
files retain exact bytes/hashes, including original CRLF stream bytes.

Thirteen Wine checks passed with 791680 nearest comparisons across 395840 sets,
six nearest constexpr assertions, 37320 pawn-span/three constexpr assertions,
56 PV metadata assertions, 347 runtime PSQT, 54 correction, 8 TT groups, rule50, 18947 legal comparisons,
UCI/ponder, 5 OwnBook transitions and first normal candidate signature 334752. Strict
Zen5 C++20 Release/static j1/noLTO/noFMA and AVX2 records agree with provenance.

ZIP SHA256: `328706574973ca49ef185cc1fbfdf321b6dfac78c52a22db0e087553a1ca1205`.
Engine SHA256: `56c55eb68eec6e5361ca18fb3e7e06e789352d825eaa3a336d65e62a47a3fcf8`.
Raw SHA256: `559fd23a49fa357e99ad3e4e0a18bc7c3c1042c7b9e23ac8d4d194eef5232d74`.

This is bounded Windows/Wine artifact correctness only. Native 22 qualification
is separate; original 6.4.16 TSan FAILED 8/9 remains qualified. No 22 speed, NPS,
Elo, native Windows/physical Ryzen or Stockfish superiority result is established.
