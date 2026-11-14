# Read-only r3-18 / r3-19 / r3-20 review

Base: `e04556ddc3a430b2e751159b0d46111ef56c8b89`. Reviewed exact source, tests and reports at the three requested tips. All objects already existed; no fetch was needed. No build, native search, test execution, branch/ref update or repository edit was performed. Shell command traces and real outputs are in the accompanying text logs. Files below mean paths within `forge-combo29` at the stated revision.

## r3-18 — 1316c38c1cd6dce7ae719804ca72b43b4c2fc165

No specific engine correctness regression found by inspection. `src/nnue.cpp:283-329` preserves the existing quiet/capture feature arithmetic and the sixteen-lane accumulation order. Other dirty-list shapes and the AVX-512 path retain update-then-evaluate (`413-426`). `src/search.cpp:852-925` reuses the preceding accumulator across null moves and advances feature/PSQT pointers only after a real move. The UseNNUE-false early return remains unchanged. These changes execute by default when NNUE is enabled; no new UCI option.

Test finding: `tests_r3_18/lazy_eval_identity.cpp:199-200,214-215,262-275` increments refresh-network/total mismatch counters but still returns zero. A zero process exit alone cannot certify identity; the counters must also be checked. The special-move catalog exercises update/evaluate rather than the fused Worker path. Its direct null checks unmake the null immediately, so it has no dedicated null-then-real-move descendant chain. Its dirty-list comparison is partly tautological because dirty_pieces now wraps dirty_from_move.

Author reports the expected bench11/13/16/perft5 counts, one million identity samples and 10,000 depth8 comparisons. Threads>1, UseNNUE=false, AVX-512, other Hash/MultiPV settings and games are explicitly unverified. No sanitizer evidence is supplied. Do not transfer these claims to the pinned soak build without running its gates.

## r3-19 — 3def809de68d726715fa3dd21626f706f0f30e16

**Portability regression:** `src/eval.cpp:220-221,283-284` calls `_pext_u64` without a BMI2 guard. The helper fallbacks in `include/forge/bitboard.hpp` do not cover those direct calls. The previous portable CMake configuration permits a non-BMI2 target (`CMakeLists.txt:14-18,36-43`); such a target now has undeclared intrinsics or target-option mismatch. This conclusion is source-derived, not a reproduced compiler diagnostic. Required x86-64-v3 has BMI2, so this does not demonstrate drift in that target.

The branch adds duplicate eval-only PEXT tables and an unconditional startup equivalence/abort check, and rewrites piece, king and threat evaluation. On legal positions the algebra and piece iteration order otherwise appear preserved; kings remain excluded from threat targets. Default HCE and residual-NNUE evaluation both use the rewrite. Its one-million eval and 10,000 depth8 comparisons are author-reported; the committed identity_walk harness writes records for an external comparison and keeps Searcher history/TT between its successive searches. Only Threads1 was checked, no sanitizer or game evidence. Tip is a report-only follow-up to source commit 758df95baabcdb2dd97aaa9b5507518b5cd02450.

## r3-20 — 7fef1fc378b6c966649315c11573bbdc1529435e

**Explicit build-switch behavior changes:** `include/forge/bitboard.hpp:17-19` undefines an explicitly selected `FORGE_SPD_SLIDER_PEXT=0` and forces it to 1 whenever BMI2 is available. Thus portable x86-64-v3 builds cease using the requested multiply-magic path. This is described in the branch report but contradicts the existing CMake option's documented behavior. Non-BMI2 targets still retain the multiply path.

No demonstrated search-semantic regression found in the reviewed changes. `src/search.cpp:682-737` preserves earliest-index ties for first/AVX2 picks and retains the same std::sort tail; TT replacement keeps first empty/earliest equal-score replacement; board generator order, inlined legality/check paths and one-color checker calculation appear equivalent to the base. No new UCI option; these rewrites execute in default builds.

Only REPORT_r3_20.md documents the two 10,000-position depth8 comparisons; no new test/reproduction harness is committed. Its report explicitly limits searches to Threads1 and excludes clock, ponder, MultiPV and games. No sanitizer evidence is supplied. Last source change is f522db9138c3578295deb78dcef4ca4c466564b5; subsequent commits update the report.

## Integration relevance and limits

All three are optimization rewrites, not demonstrated fixes for the pinned soak's mate/PV, rule50-equality or race findings. No performance/strength claim is verified here. r3-18 and r3-20 both touch search.cpp; r3-19 and r3-20 both touch bitboard.hpp/cpp, with changed initialization and slider selection. Combining 19+20 would retain redundant eval PEXT tables while the general slider path also becomes PEXT. Standalone author-reported identity does not prove combined-build identity, SMP safety or sanitizer cleanliness. Do not modify the ongoing pinned experiment based on this read-only review.
