# opus-r3-stack merge resolutions — read against the merged branches, 2026-10-28

Method: for every merge commit on the stack's first-parent line, the automatic merge of its two parents was recomputed
(`git merge-tree --write-tree`), and the committed merge was diffed against it (`fable_review/deep/r3_resolutions.sh`,
files `deep/r3/<merge>.txt`): that diff is exactly what R3-1 did by hand. Twelve merges merged clean (R3 agent
branches: evidence and tools only; O1, O6; r3-gates, port-b, port-c as whole branches). Twelve R3-1 merges conflicted
because the stack had split src/search.cpp into src/search/*.inc (O3) while the Sol branches patched search.cpp;
their resolutions were read line by line against the branch's own `git diff d4f4312 <branch> -- src include`.

| merge | branch | conflicts | manual resolution | read against the branch | verdict |
|---|---|---|---|---|---|
| c157c7e1 | S14 FORGE_NOZERO_MOVE_BUFFERS | 1 | movepicker.hpp: the two UninitArray buffers under the switch | identical to the branch's search.cpp hunk (board.hpp merged clean) | OK. Note: both variants keep the 64-entry `bad_captures_` (mistake 2 of the review applies to the stack as well: the fix is `MoveList::Capacity` in both branches of the `#if`) |
| 36492b15 | S29 FORGE_SPEEDSTACK | 2 | material_key_table.hpp comment merged (shared with S11); alphabeta.inc: the two child prefetches after the S13 ones; evaluation.inc: `#ifdef FORGE_SPEEDSTACK return table_key #else lock code` | identical hunks at the same three sites (null-move child, probcut child, material_key) | OK (with both S13 and the stack on, the child bucket is prefetched twice: harmless) |
| 71dca776 | S11 MaterialKeyTable | 6 | CMake/search_options.hpp/options.inc/uci.cpp marker removal keeping both sides; evaluation.inc: the option test in material_key | identical | OK |
| c892c9eb | S13 TtChildPrefetch | 3 | search_types.hpp (SearchLimits field), thread_data.hpp (shared atomics, worker bool), alphabeta.inc (two prefetch sites), iterative.inc (snapshot), searcher.inc (snapshot + announce) | identical, each hunk at the corresponding site of the split files | OK |
| c7e24905 | S41 NetScale | 3 | evaluation.inc static_evaluate scaling, tune.inc holds `net_scale::percent`, uci.cpp option block | identical; the stack scales only the compiled-in network (v2 nets are not scaled, stated in the code) | OK |
| 467a59b3 | SIT IntendedThreefold | 6 | alphabeta.inc (claim, floor, TT gating, placeholder store, fail-low guard, correction guard), qsearch.inc (claim, floor, stores), board.hpp / CMake / uci marker removal | identical hunk for hunk with the branch's search.cpp (70 lines); board.cpp merged clean | OK |
| d02112c1 | S12 FORGE_NNUE_LAZY_ACC | 4 | search_types.hpp / thread_data.hpp (lazy types, owner pointer, counters), evaluation.inc (static_evaluate_lazy, counters, record_move/null), iterative.inc, searcher.inc (enable snapshot, stats), tune.inc (requested flag, computed_owner), uci.cpp | identical | OK |
| 97484ee5 | A1 HistRework | 4 | history.hpp, thread_data.hpp (members last), alphabeta.inc (threat maps after IIR, PV-move bonus), evaluation.inc (joint term), history.inc (threat twin), qsearch.inc (evasion maps), tune.inc, worker.inc, uci.cpp; plus an R3-only addition: the joint term also in correction_plus.inc so HistRework combines with CorrHistPlus | coherent with the branch; R3-1's ON pins for HistRework 1/2/3 matched the branch | OK (the CorrHistPlus+HistRework combination is R3's own design, documented in the code) |
| 1bec425d | O2 NNUE kernels | 2 | nnue.hpp/nnue.cpp: every O2 kernel under `#if FORGE_NNUE_O2`, `#else` the AL1 loops; CMake switch | the stack's forge_nnue_parity_tests compares against a verbatim AL1 copy; R3-1: off = token-identical to the pre-O2 file, on = token-identical to O2's | OK |
| a0179ce8 | C6 CuckooRep | 8 | alphabeta.inc header/macros for eight instances (CorrMargins x CorrExt x CuckooRep), cuckoo.inc wrapper macro for the four CuckooRep instances, iterative.inc instance selection, options | coherent; R3-1's CuckooRep ON pins matched the branch | OK |
| 9588a109 | S08fix FORGE_PROF | 5 | 231 lines in alphabeta/qsearch/movepicker/searcher/tt/iterative/evaluation + thread_data, uci: every counter under `#ifdef FORGE_PROF` with `#else` keeping the lock code | OFF build unchanged by construction; the ON build's pruning conditions are restated inside the PROF branches, which S08fix's CI verifies with bench_prof node pins | OK |
| e523aae9 / d5023654 | port-b (S32, S37, S04fix), port-c (SA2 NnueInt16) | 1 / 3 | CMake blocks kept side by side; nnue.cpp refresh/evaluate get both the PROF counter and the int16 early return; uci.cpp brace/#endif repair | trivial, compiles (CI green) | OK |

Verdict: no merge resolution changes a branch's logic. One item for the owner: the stack's `bad_captures_` is still 64 entries in both `#if` branches (movepicker.hpp); apply the fable-review-buffix change there too.
