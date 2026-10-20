# Forge 6.4.20 Windows preparation checkpoint

The Windows 20 pipeline is prepared from immutable tested Windows 19 source
`61f598056572dfade6994af8ad2e38817cd28aa3`. The candidate source is not frozen yet.
All ten Python scripts parse; source/build authorization gates reject execution.
No source export, version bump, compiler, engine, Wine, packaging, artifact-audit
or Git action ran. Candidate source/build and release paths remain absent.

The intended source change is an unsigned constexpr forward_fill helper using
8/16/32-bit shifts, plus equivalent pawn-span geometry from the existing enemy
pawn-attack mask. The future declared export delta is exactly CMakeLists.txt,
include/forge/bitboard.hpp, src/eval.cpp, src/uci.cpp and tests/pawn_span_tests.cpp.
All old tests, Board, NNUE source/headers/weights, search and parameters must match
Windows 19. Root supplies version 20 and final source; this agent does not edit it.

Preregistered future requirements: 72 exported files (75 native inputs excluding
three tracked pyc files), 12 CTests, 11 Wine checks, 37,320 pawn-span checks and
three compiled constexpr assertions. Retain runtime PSQT 347, correction 54, 8 TT groups,
18,947 legal comparisons, UCI/ponder and five OwnBook transitions. Require the
exact Windows parent bench signature 352313; preserve any mismatch and stop.
Nine built PEs and eight shipped PEs are expected, excluding bench from shipment.
Both actual runtime and pawn test objects/source/testedPE/compile identities are
retained. Strict LLVM-MinGW 23.1.3 Zen5 Release/static, j1, no FMA/LTO/fast-math.

The protection manifest covers all 483 actual Windows 19 files: validation records,
source/build trees and expanded/ZIP release artifacts. Every original hash still
matches. Derived script diffs and provenance are in PIPELINE-ADAPTATION.json.

Wait for root final 40-character source SHA and full native 12x3 CTest, 8 active and 56 parity clearance.
The concrete build-clear record must contain source_commit, parent_source_commit,
runtime_summary_checks=347, correction_checks=54, pawn_span_checks=37320,
source_files=72, bench_expected_nodes=352313, and the root frozen source-gate path
and SHA256. Then export exact Git bytes, prepare source/pins/root-gate snapshots,
build j1, run bounded Wine checks, freeze the exact signature, use closed-writer
run-package.py and invoke the read-only artifact auditor after its ready marker.
No present build/runtime/audit pass or speed, NPS, Elo, native Windows/Ryzen or
Stockfish-superiority result is claimed. An independent preparation-agent dispatch
was unavailable due to the thread limit; only static local preparation was checked.
