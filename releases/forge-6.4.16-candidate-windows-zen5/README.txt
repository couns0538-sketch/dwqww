Forge 6.4.16 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.16-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
Frozen source/tests: 553caef144ae2e1b696ba35d7a0eb1a50a03fde9. Parent: 8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad (6.4.15).

This candidate uses own-king pin lookup masks for hypothetical SEE recaptures,
replacing repeated per-attacker attack queries while requiring the same eligibility
results. King recapture logic is unchanged. Only board.cpp and version labels differ
from frozen15. All tests, headers, NNUE/eval source and weights match the parent.
Earlier clock, TT, legal/rule50, OwnBook and double-extension fixes remain inherited.
Lifecycle operations still require quiescent accessors; rule50 remains a heuristic.

Eight Wine checks passed: core/perft with unchanged 23 mirrored SEE cases, eight
TT groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook
transitions and exact parent15 Windows bench11 signature 382424.
Parent parity was required before execution, without relaxed expectations.
AVX2 clamp/multiply/add and output-layer checks passed without fused arithmetic.

Compiler: LLVM-MinGW23.1.3, strict C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, no LTO. All six built PEs, actual
core, frozen source, commands, stdout/stderr and disassembly are retained and saved
in manifest-verified windows-originals.zip. Prior6.4.14 native bench-output anomaly
remains qualified in its separate evidence.

This Windows stage establishes bounded correctness only; native gates are separate.
This is not an accepted release; packaging alone does not establish release readiness. This is an isolated candidate;
no accepted NPS or Elo improvement exists. No throughput or timed match was run.
Native Windows, physical Ryzen and Stockfish superiority remain unproven.

Optional tests:
forge_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See provenance.json, source-hashes.json, test-hashes.json, nnue-parent-identity.json,
windows-originals-SHA256.json and SHA256SUMS.
