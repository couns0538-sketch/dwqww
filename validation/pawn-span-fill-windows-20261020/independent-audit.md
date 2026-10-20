# Independent Windows 6.4.20 artifact audit

All **1538 checks passed** for frozen source `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`, parent `61f598056572dfade6994af8ad2e38817cd28aa3`.
The audit ran no engine and performed no rebuild. 72 source files
match frozen Git and root-source-gate bytes. The five declared export changes are
CMake/UCI version metadata, bitboard.hpp, eval.cpp and the new pawn-span test.
Board, NNUE source/weights, search, parameters and all old tests remain unchanged.

The package has 21 verified members and 20 checksum entries;
all nine built PEs and eight shipped PEs match their tested bytes and have AMD64
PE32+/system-CRT imports only. The actual static core and both runtime/pawn test
objects match original source, PE and compile identities. All 225 raw
originals and all 483 protected Windows 19 files retain exact bytes and hashes.

Original logs show eleven Wine checks, 37,320 pawn-span checks, three compiled
constexpr assertions, 347 runtime PSQT and 54 correction checks, core/perft, eight TT groups,
rule50, 18,947 legal witnesses, UCI/ponder, five OwnBook transitions and the exact
preregistered parent 352313 signature. Strict Zen5 Release/static/noLTO/noFMA flags,
AVX2 instructions and retained raw CRLF logs agree with original records.

ZIP SHA256: `92cf639dad35d5f44d6ef492eab1a927606aaaf609eec447a41f05775420e63c`.
Engine SHA256: `ae4351057435b02d8d876efdafd6b275724bdf46ef26833d49dfe60d748e3fe0`.
Raw SHA256: `86cf76fec26e902e53ec8a1d0799f716edf7aef9187fc8e4e32e913856dda9e5`.

This unaccepted candidate intends exact geometry/evaluation/search parity. Native 20
qualification is separate. Original 6.4.16 TSan FAILED 8/9 remains qualified. No speed,
NPS, Elo, native Windows/physical Ryzen or Stockfish superiority is established.
