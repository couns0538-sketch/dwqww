Permanent actual-core PV metadata regression is frozen and ready for root integration.

Source pv_metadata_tests.cpp is intended for tests/pv_metadata_tests.cpp; add target
and CTest forge_pv_metadata_tests linked to forge_core+Threads::Threads, registered
SIXTH immediately after forge_nearest_pawn_tests. That makes14CTest suites.
TEST-SCHEMA.json records actual output/counts and source/binary/result hashes.

ONE standalone compile/link/run against unchanged frozen21core/headers completed:
56assertions, exactly2expected failures, actual expected exit1. Original stderr:
FAIL PV_nonPVhit preserves caller PV flag
FAIL PV_abort_verification preserves caller PV flag
All54other assertions pass, including three controls, legal nonempty completed PVs,
FEN/key/pawn-key/history/check restoration, and actual2node aborted search.
The limit2 case reaches the seeded first TT move's same-ply singular verification;
its changed parent flag on abort distinguishes this from an ordinary child frame.
No diagnostic code, extern symbol, private ABI trick or search-source inclusion.
Existing production SearcherTestProbe friendship is the sole access mechanism.

Compiler flags: GCC14,-O3,-DNDEBUG,C++20,x86-64-v3,znver5,no-fast-math,
ffp-contract=off,no-LTO; one standalone compiler invocation (no parallel build).
Both compiler/test process exits, raw stdout/stderr and owned-group cleanup are
preserved under baseline-attempt1; all original source headers/core/inputs rehash
identically. No full GREEN build was launched. Future frozen22Release/ASan/TSan
must exercise this EXACT source with56assertions/zero failures before acceptance.
Any unexpected failure must be retained and investigated, not silently tuned.

Parent RED diagnostic source/probe and natural25legal flag losses are preserved
in ../red-attempt1, ../RED-LEGAL-TRACE-AUDIT.json and ../RED-RESULT.md.
Minimal two-line diagnostic GREEN and natural618calls/zero losses are in
../green-attempt1, ../GREEN-AUDIT.json and ../GREEN-RESULT.md. None was repeated
for this new permanent regression. Production edits, CMake edits, version changes,
branch/index operations and commits remain root-owned and were not performed.
This is finite regression evidence, not speed, Elo or full candidate qualification.
