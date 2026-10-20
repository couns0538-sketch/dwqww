Forge 6.4.18 candidate - Windows x64 Zen5 / Ryzen 7 9850X3D

Load forge-6.4.18-ryzen-9850x3d.exe as a UCI engine in your chess GUI.
Frozen source/tests: fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b. Parent: 47f0560221d986e41a309853e1295c557fcf5bf6 (6.4.17).

This independent unaccepted search ablation changes correction-history EMA decay
to a residual increment. It is not a known-bug repair or accepted strength
improvement. The new dedicated test exercises the actual worker methods for signed
depth/clipping, learned-entry retention, feedback convergence, material/pawn-table
coupling, saturation and mate-score output clamps. NNUE/eval source, headers and
weights remain byte-identical to 6.4.17; inherited 6.4.17 promotion SEE remains.

Nine Wine checks passed: core/perft with 28 mirrored SEE cases, correction-history
actual-method contract (54 checks), eight TT groups,
rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook transitions and
first observed candidate18 bench11 signature 352313.
The new signature was unknown before execution; prior-version counts were not imposed.
AVX2 clamp/multiply/add and output-layer checks passed without fused arithmetic.

Compiler: LLVM-MinGW23.1.3, strict C++20 Release, -march=znver5 -mtune=znver5,
-fno-fast-math -ffp-contract=off, static linking, no LTO. Seven original PEs, actual
core, frozen source, commands, stdout/stderr and disassembly remain retained and archived
in manifest-verified windows-originals.zip. Earlier clock/TT/legal/rule50/OwnBook and
path-accounting policies remain inherited with their existing limits.

This Windows stage establishes bounded correctness only; native gates are separate.
This is not an accepted release. Original 6.4.16 full TSan FAILED 8/9; the separate 6.4.16
five-case OwnBook diagnostic provides finite coverage only. Candidate 6.4.18 native gates
are reported separately. No accepted NPS or Elo improvement exists. No throughput
or timed match ran. Native Windows, physical Ryzen and Stockfish superiority remain unproven.

Optional tests:
forge_tests.exe
forge_correction_history_tests.exe
forge_tt_tests.exe
forge_rule50_tests.exe
forge_legal_witness_tests.exe legal_witness_fixtures.tsv forge-10000.epd

See provenance.json, source-hashes.json, test-hashes.json, nnue-parent-identity.json,
windows-originals-SHA256.json and SHA256SUMS.
