Forge 6.4.13 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.13-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
This executable targets Zen5. Frozen source and tests:
cecf0b9e3af5602053bcaf5c5d16ffc09f58850d

This candidate preserves finite timed UCI admission accounting and restores the
accepted worker-local timing contract for untimed analysis, infinite and pondering.
The accepted start_time API field takes precedence; request_start remains supported
for existing callers. Ponder budgets still start at ponderhit. Existing expired-budget
preflight and helper node reset behavior remain, together with the prior TT and NNUE work.

The inherited TT path permits opted-in single-worker UCI owner access behind one gate
and a sequential stripe drain; shared/default library callers and SMP retain stripes.
Foreign diagnostics may block for a whole search. Clear, resize, new_search and destruction
still require every accessor quiescent. The inherited below90 rule50 grouping remains
heuristic, not universal history correctness. NNUE/eval source and weights are byte-identical
to frozen6.4.12; no large redundant snapshot differential was needed or run.

Eight Wine10 checks passed: core/reference perft (including new accepted/legacy timestamp
assertions), eight TT groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five
external OwnBook transitions, and stdin bench11 at351,063 nodes (Hash16MiB/Threads1),
matching frozen Windows6.4.12. SIMD checks verified 256-bit clamp/multiply/add without
fused arithmetic. Source, fixture, corpus, tool and tested PE hashes stayed unchanged.
See README-checks.json and provenance.json.

Compiler: LLVM-MinGW23.1.3, C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking. All six built executables, actual core,
frozen source, commands, build records, stdout/stderr and disassembly are in the
manifest-verified windows-originals.zip. Originals are retained in repository archives.

Native sanitizer results are recorded separately in repository checkpoints. This is a
correctness candidate; no accepted NPS or Elo improvement exists. No Windows throughput
or timed match was run. Native Windows, physical Ryzen and Stockfish superiority remain
unproven. Earlier portable offline validator bundles remain separate.

Optional included tests from this directory:
forge_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See source-hashes.json, test-hashes.json, nnue-parent-identity.json, provenance.json,
windows-originals-SHA256.json and SHA256SUMS.
