# Forge 6.4.20 source-only Windows checkpoint

Exported frozen `fc2391870b3bf2cd4d8fc20c7406ea6439c69c5e`: all 72 filtered files match the 75-input
root source proof after excluding three tracked pyc files. The exact root proof
is retained with SHA256 `9d20b35515e4be3e9230039869409a4a46003fede3a11949e93c720e3c4ab770`.

The actual delta against Windows19 is exactly CMakeLists.txt,
include/forge/bitboard.hpp, src/eval.cpp, src/uci.cpp and tests/pawn_span_tests.cpp.
All other exports and old tests match. Frozen CMake/UCI identify6.4.20; 12 CTests
are registered and the pawn source contains three constexpr assertions. Tool
hashes were verified without compiler/runtime/version queries. All483 protected
Windows19 files remain unchanged.

Source export and static checks passed; original command stdout/stderr and source,
production/test hashes are preserved. The pawn test source SHA256 is
`dfbcef1dc8e90ad1237fdac67328a172aec4012d775be75c326b1bd541bfe83e`. No Windows compiler, engine, Wine, package or
artifact audit ran. Build/runtime/package authorization remains absent and the
default gate rejects execution. Expected347/54/37320/352313 counts are preregistered
requirements, not newly observed runtime results. Await separate root clearance
after full native20 validation and independent audit; no strength claim follows.
