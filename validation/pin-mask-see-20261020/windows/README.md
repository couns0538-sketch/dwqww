Frozen Forge 6.4.16 Windows correctness evidence

Source/tests: `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`. Parent: `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad` (6.4.15).
Strict static LLVM-MinGW23.1.3 Zen5/C++20 Release build, one job, no FMA/LTO/fast-math.
Eight Wine checks passed: core/perft including unchanged 23 mirrored SEE cases,
eight TT groups, rule50, 18,947 legal-witness comparisons, UCI, ponder, five OwnBook
transitions and exact parent15 Windows bench11 signature 382424.
This signature was required before execution; no expectation was relaxed.

The own-king pin lookup mask replaces repeated per-attacker SEE attack queries.
King recapture logic remains unchanged. Only src/board.cpp and two version labels
differ from frozen15; all tests, headers, NNUE/eval sources and weights match exactly.
This Windows evidence is separate from native gates; packaging alone does not accept
this candidate or establish release readiness. No NPS/Elo/native Windows/Ryzen claim.
All six original PEs, core, frozen source, commands, logs and disassembly are retained
and archived. Prior 6.4.14 native bench-output anomaly remains qualified separately.
