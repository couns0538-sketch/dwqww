# Independent Windows 6.4.24 artifact audit

All **1870 checks passed** for source `7db08eac6ead99d641834c56ccec06a06600586a`, parent `1d3ed25bea2c8b781f7ee5a178af0f66061b3984`.
No engine or rebuild ran. All 74 source files match frozen Git
and the root proof whose byte hash is explicitly pinned to root authorization.
The four changes are CMake/UCI metadata, search.cpp and extended core SEE tests;
all other tests, Board, NNUE, evaluation and evaluation parameters are unchanged.

The ZIP has 23 safe verified members and 22 checksum entries.
All eleven built and ten shipped PEs match tested bytes and system-CRT AMD64 PE32+
requirements. Core and all runtime/pawn/nearest/PV metadata/TT/core-test object/source/PE/compile identities
match originals. All 271 raw files and 597 protected Windows 23
files retain exact bytes/hashes, including original CRLF stream bytes.

Thirteen Wine checks passed with 791680 nearest comparisons across 395840 sets,
six nearest constexpr assertions, 37320 pawn-span/three constexpr assertions,
504 SEE threshold assertions, 56 PV metadata assertions, 347 runtime PSQT, 54 correction,
12 TT groups, rule50, 18947 legal comparisons,
UCI/ponder, 5 OwnBook transitions and first normal candidate signature 334752,
which exactly matches parent23 334752 after capture. Strict
Zen5 C++20 Release/static j1/noLTO/noFMA and AVX2 records agree with provenance.

ZIP SHA256: `0db112fab29653eb43ac74924fb08a4a956bbf5085555f1a166a64d83fc392db`.
Engine SHA256: `b58058055615e299ed49279929ee71fced5d505845d8049dabaeed57aa07269c`.
Raw SHA256: `a0d7eb076035bee8fdee9f1ee9e83b1f79cd33ddd0ada5f1a29065fc5a827722`.

Pure SEE proof reuse intends exact parent evaluation/search behavior with a
nonpositive-threshold guard and defined arithmetic. This is bounded Windows/Wine
artifact correctness only. Native 24 qualification
is separate; original 6.4.16 TSan FAILED 8/9 remains qualified. No 24 speed, NPS,
Elo, native Windows/physical Ryzen or Stockfish superiority result is established.
