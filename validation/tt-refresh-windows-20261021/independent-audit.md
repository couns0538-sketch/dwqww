# Independent Windows 6.4.23 artifact audit

All **1827 checks passed** for source `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`, parent `ff2e269c6058be84456e3b98344826d17b0056eb`.
No engine or rebuild ran. All 74 source files match frozen Git
and the root proof whose byte hash is explicitly pinned to root authorization.
The four changes are CMake/UCI metadata, search.cpp and extended TT tests;
all other tests, Board, NNUE, evaluation and evaluation parameters are unchanged.

The ZIP has 23 safe verified members and 22 checksum entries.
All eleven built and ten shipped PEs match tested bytes and system-CRT AMD64 PE32+
requirements. Core and all runtime/pawn/nearest/PV metadata/TT object/source/PE/compile identities
match originals. All 259 raw files and 604 protected Windows 22
files retain exact bytes/hashes, including original CRLF stream bytes.

Thirteen Wine checks passed with 791680 nearest comparisons across 395840 sets,
six nearest constexpr assertions, 37320 pawn-span/three constexpr assertions,
56 PV metadata assertions, 347 runtime PSQT, 54 correction, 12 TT groups, rule50, 18947 legal comparisons,
UCI/ponder, 5 OwnBook transitions and first normal candidate signature 334752. Strict
Zen5 C++20 Release/static j1/noLTO/noFMA and AVX2 records agree with provenance.

ZIP SHA256: `c3ae058154624a2c91ff32e89d78cdb222cb02d166664cddcbd7f2d4bfa17b50`.
Engine SHA256: `58705c2fdc287e98ed62bcea913cb284dff956b48cad2582a0029df56152a902`.
Raw SHA256: `02bfb4fc46a6c7a1195ac0152b1c0120572abc075e9a06dc86875abd458069c4`.

This is bounded Windows/Wine artifact correctness only. Native 23 qualification
is separate; original 6.4.16 TSan FAILED 8/9 remains qualified. No 23 speed, NPS,
Elo, native Windows/physical Ryzen or Stockfish superiority result is established.
