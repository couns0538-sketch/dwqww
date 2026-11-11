# EvalInfo initialization audit (research only)

## Finding
The initialization is not already optimized away under GCC 14.2.0, Linux x86-64-v4, -O3. Both nontraced/runtime and traced instantiations clear all 200 bytes before doing useful evaluation work. Three 64-byte `vmovdqu8` stores at stack offsets 288, 352 and 416 plus one 8-byte zero store at 480 survive. The nontraced clear precedes the runtime-valid branch, so runtime PSQT does not avoid it. Existing hce-eval-inspect.o agrees; this audit additionally reproduced assembly directly from immutable commit 16833ecc03b425586f91f4c8834dea8807bf4c22 and its exact headers.

This is evidence for a candidate, not performance evidence. No timing, engine execution, games, production changes, native Windows inspection or gain claim was made. GCC output does not establish what the Windows Clang 23 ThinLTO+PGO lock does.

## Complete field dataflow
EvalInfo is private to eval.cpp. Its sole construction is evaluate_position. All other occurrences are references passed to the four evaluation helpers; there is no whole-object copy, bytewise inspection or external escape. Trace changes parameter accumulation, not the field initialization sequence.

- attacked_by[each side][0, Pawn, King]: all six entries (48 bytes) are assigned in the first two-color setup loop before evaluate_pieces or any other reader. Their zero initialization is redundant.
- attacked_by[each side][Knight, Bishop, Rook, Queen]: eight entries (64 bytes) are OR-accumulators in evaluate_pieces and later readers may run even if no such piece exists. They MUST start at zero.
- attacked_twice: both entries (16 bytes) assigned from double pawn and king/pawn overlap in the first setup loop, before the piece loop OR-accumulation and subsequent readers. Initial zeros redundant.
- mobility_area: both entries (16 bytes) assigned in the second setup loop, after both pawn attack maps are ready and before evaluate_pieces reads them. Initial zeros redundant.
- king_zone: both entries (16 bytes) assigned in the first setup loop, before any evaluate_pieces/evaluate_king read. Initial zeros redundant.
- king_square: both entries (8 bytes) assigned together before either setup loop or helper uses them. Initial zeros redundant.
- king_attackers and king_attack_units: each is two ints (16 bytes total); conditional increments in evaluate_pieces, then reads in evaluate_king. They MUST start at zero, including positions with no eligible attackers.
- passed: both entries (16 bytes) assigned either together from valid matching pawn cache, or from both evaluate_pawn_structure outputs. Each pawn evaluator initializes its local passed=0 and assigns passed_out even on an empty pawn loop. Trace always follows the latter path. Neither path reads info.passed before assignment. Initial zeros redundant.

Total required initial zero state: 80 bytes. Redundant initial zero state: 120 bytes. No padding issue is being used to infer semantic equivalence; consumers read named fields only.

## Public, runtime, trace and tuner considerations
Public cached/uncached and runtime evaluation all enter evaluate_position<false>; runtime presence only selects the PSQT calculation. Cache hit and miss both establish passed before consumers. evaluate_traced clears EvalTrace, then invokes evaluate_position<true>; it shares all relevant EvalInfo setup. This audit does not authorize changing EvalTrace or Accumulator initialization, trace coefficients, tunable table reads, cache behavior or runtime state. Parameter tuning alters score coefficients, not this field dataflow. Valid Board preconditions remain unchanged.

## Narrow next experiment, not a patch
A conservative first experiment can keep attacked_by and both counter arrays fully zero initialized, removing only the five definitely-overwritten array member initializers (72 bytes) and using default initialization rather than value initialization for EvalInfo. Merely changing `EvalInfo info{}` to `EvalInfo info` does nothing while all default member initializers remain. Removing all zero initialization is incorrect. A fully selective 80-byte initialization is possible but more invasive. Either experiment still needs assembly comparison, exact cached/uncached/runtime/traced coefficient agreement, empty-piece/endgame/cache hit/miss cases, sanitizer coverage and controlled performance testing before adoption. Fewer zeroed bytes need not mean fewer stores or faster search.

## Artifacts and reproduction
- eval_init_assembly_excerpt.txt: both baseline function prologues.
- eval_init_evidence/baseline.s: complete generated assembly, no binary.
- eval_init_evidence/baseline.cpp and include/: only the pinned evaluation source and headers extracted with git show, no repository archive.
- eval_init_reproduce.sh: exact extraction/build command.
- eval_init_hashes.txt: source and assembly hashes.

## Temporary source-only variant screen
After the field proof, compiled two guarded, default-off temporary source variants. Both keep the original struct and original `EvalInfo info{};` initialization verbatim in their #else branches. No production file was edited.

- Baseline: three 64-byte stores plus one 8-byte store, 200 bytes issued/distinct, four stores.
- Conservative: attacked_by retained zero initialized, only five overwritten arrays lose member initializers. Two 64-byte stores overlap by 16 bytes; two 8-byte counter stores. 144 bytes issued, 128 distinct bytes, still four stores.
- Selective: only N/B/R/Q maps plus counters cleared. Two 32-byte stores plus two 8-byte counter stores. 80 bytes issued/distinct, still four stores.
- All variants: same 512-byte stack frame. Static nontraced assembly instruction count 2331, stack-referencing instruction count 416. Traced counts 2382/2382/2381, stack-reference counts 422 for all. These are static textual instruction counts, not dynamic work or micro-op counts.
- Both alternatives cause register-assignment changes and some instruction scheduling changes beyond the initialization; neither removes nontraced instructions or stack references. Selective default-off assembly matches baseline exactly after removing only the source filename directive.

Recommendation: a real redundant-byte opportunity, but no clear instruction-count improvement. Keep low priority rather than adding a production switch now. Any future timing must compare exact outputs first and account for incidental codegen changes. No candidate engine has been run, and no runtime equivalence or speed result is claimed.

Variant source and assembly are in eval_init_evidence/{conservative,selective}.{cpp,s}. Compile each with the reproduction flags plus -DFORGE_SPD_EVAL_INIT=1; omit the define for default-off. No object/executable was produced. A compiler supporting -Wundef could use an explicit default macro definition in a future production patch; these evidence-only variants use standard undefined-in-#if equals zero behavior.

Preserve only eval_init_REVIEW.md, eval_init_assembly_excerpt.txt, eval_init_hashes.txt, eval_init_reproduce.sh and eval_init_generate_variants.py as concise branch evidence. eval_init_evidence/ is a reproducible temporary workspace and should not be committed.

Temporary snapshots were moved recoverably to /workspace/shared/forge-build/eval-init-snapshots before the evidence commit. Reproduction regenerates the original tests/eval_init_evidence paths recorded in the hashes.
