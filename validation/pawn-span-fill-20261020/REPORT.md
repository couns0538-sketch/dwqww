The bounded pawn-span prototype is stable at version19. Production changes only
add constexpr `forward_fill(Color, Bitboard)` and replace the evaluation pawn
traversal with a fill of its already-computed attack mask. No other optimization,
cache, NNUE arithmetic, search heuristic or version changed.

The clean GCC14 Release build used x86-64-v3/generic, no LTO, strict floating-point
flags and-j2. All12 CTests and the direct37,320 mask comparisons passed. All75
working/exported source files were captured before/after each stage and remained
unchanged. Full original source/build/core/engine remain outside the checkout at
the paths in CHECKPOINT.json. The original prototype was genuinely checkpointed
by root as5ad72e16 while its identical frozen source was executing.

After that GREEN, root requested only a failure-label correction: stored PawnTable
entries derive from the existing pawn attack function, so they corroborate an
input route rather than independently generating geometry. The original passed
mask/file loop and explicit square/rank walk are independent oracles. Original
unit bytes remain first-unit-source.cpp and in the original exported source.
The final label fixture compiled successfully. Its first relocated linker command
failed because I retained a relative CMake dependency-output path; that failed
command, object and raw records remain. A separate link corrected only that
output path and the final unit again passed37,320 checks. The original full build
and production core/engine stayed byte-identical throughout.

Final75-source hashes are in FINAL-SOURCE-75.json; PATCH-FINAL.diff contains the
final patch. The full12CTest result belongs to the first fixture; the final wording
fixture has a separate successful compile/link/direct-test result. There is no
missing-API parent RED or old-engine bug claim. No benchmark, performance trial or
match was run. Existing actual19 captures establish baseline bench321912 only.

Root/peer full evaluation/trace-coefficient and search parity remain pending,
followed by frozen20 validation and any separately authorized speed experiment.
