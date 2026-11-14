# Independent review of pass 8

I reviewed frozen source and existing logs only. No native engine, build, oracle, experiment state, production source, or Git operation was run or changed by this reviewer. Plain-JavaScript checks below parse recorded text and test KRK move geometry; they do not search chess positions.

## Terminal origin and identity

Pass 8 has 3,931 contiguous events. The selected frame-19727 subtree has **145 frames**, each with one recorded return, and **zero mate-valued TT probes**. Its one checkmate return is frame **19871**, qsearch, black ply **15**, raw trace line **2000** / sequence **1999**, reason **SOURCE_LINE_1161** (pinned `search.cpp:1161`; scratch `search-origin.cpp:1200`). The FEN is `8/8/8/8/8/R7/2K5/k7 b - - 15 8`; the return is `mated_in(15) = −31985`. This is an actual terminal test, not a TT-derived mate leaf.

I independently compared all **24** retained executions across eight passes: every complete stdout matches the pinned baseline after replacing only numeric time/nps, every paired trace matches after address remapping, and every summary reports code 0, signal null, completed true, timeout false. Source changes after the previously reviewed fourth pass only widen the watched keys/clusters and selected frame IDs. They add no new TT operation or generation mutation.

## Local forced line and bound propagation

From frame 19727, the selected continuation is:

`b1a1 d1c2 a1a2 d2d3 a2a1 d3a3#`

It follows frames **19727 → 19728 → 19867 → 19868 → 19869 → 19870 → 19871**. An independent geometric check shows:

| Black frame | All legal replies | Recorded reply |
|---|---|---|
| 19727 | b1a1 | b1a1 |
| 19867 | a1a2 | a1a2 |
| 19869 | a2a1 | a2a1 |
| 19871 | none; Ka1 is checked by Ra3 | terminal return |

Every white move on that line is legal. Thus this particular six-ply continuation covers every defense from frame 19727 and establishes a local at-most-six-ply mating strategy. This is stronger than merely showing one cooperative terminal line, but does **not** establish the fastest mate, a strategy from the original root, or general search correctness. The selected line has no repeated entry-history key and ends at clock 15.

The return is negated through the callers, retaining magnitude 31985. Frame 19867 at ply 11 stores raw **−31996**, BoundUpper, depth 4; frame 19728 at ply 10 stores **31995**, BoundLower, depth 5; frame 19727 at ply 9 stores **−31994**, BoundUpper, depth 6. These payloads have the expected position-relative distances along the checked local line.

The later 110-frame producer subtree rooted at frame 22252 reads seven pre-subtree mate payloads spanning **three** keys: the two negative Upper keys written by 19727 and 19867, and the positive Lower key written by 19728. In particular, frame 22353 reads key `9061667836344179611` / raw 31995 / Lower from 19728. Describing only “two preexisting Upper dependencies” is accurate for the negative subset, not for all external mate probes. All three producers come from the same checked terminal path. The remaining observed mate dependencies have writers within the 22252 subtree. Frame 22252 ultimately stores raw **−31990**, Upper, at ply 7/depth 7. The retained oracle query checks 26 producer probe/store values and every numerical inequality agrees with its no-history DTM table.

## What the full subtree does not prove

All **144** recorded parent→child edges in the 145-frame subtree pass legal-move and exact-FEN transition checks. Nevertheless, the whole subtree is selective: only 23 of 72 black frames have every legal move represented among recorded child searches. The other 49 include MAIN_FINAL cutoffs, qsearch, TT returns, stand pat, and draw returns. There are five draw-return sites and two repeated entry-history frames (19809 and 19840). “No mate-valued TT probes” does not mean “no TT cutoffs”: this subtree also contains ordinary-score TT returns and five reverse-futility returns. It is not an exhaustive global proof tree. The forced-defense finding above is deliberately restricted to the selected local terminal line.

## Later qualifier changes

At frames 24345/24349, white's narrow window is [31982,31983]. The chain reaches frames **24348/24352**, which return **MAIN_TT −31979** from a stored **Exact −31990**, depth 6, at black ply 11. The new oracle query gives that child position DTM **10**, normalized **−31990**: this particular Exact payload agrees with the oracle. Therefore these later discrepancies do not establish that this child Exact entry is corrupt.

The first numerical mismatch in the inspected later sequence is instead white parent **24347**, which stores **Upper 31989** while the oracle gives DTM 7 / normalized **31993**. Subsequent parent classifications propagate that selective result. The wider-window frame **24358** eventually consumes a qsearch result at **24363**: its incoming Exact −31992 agrees with oracle DTM 8, is substituted into local evaluation, and returns QS_FINAL −31979 at ply 13 without extending the PV. Parent 24358 stores **Exact 31987**, whereas its global no-history DTM score is 31995.

The retained later oracle query contains **27** values, **15** of which do not satisfy their Upper/Lower/Exact relation against global DTM; I recomputed every printed relation. These mismatches must be reported, while distinguishing selective finite-depth classifications from exact global mate distance. They do not show that the original positive mating deadline is too short. Neither the terminal trace nor an unqualified UCI mate number licenses a universal exact-mate claim.

The source supports a separate pruning concern: main `ss->static_eval` stays the ordinary corrected evaluation even when local `eval` is replaced by a TT score. The shallow quiet-futility guard at pinned `src/search.cpp:1392–1402` compares `ss->static_eval` with alpha and has no mate-alpha/PV exclusion in this version. A high mate alpha can therefore make that pruning condition applicable. Individual skipped moves and each pruning predicate were not logged in pass 8, so this review does not assert an instrumented first-pruning cause or a minimal fix.

## Evidence and review errors

Raw pass-8 trace SHA256: `2ba0e33a87c4d5c47f520d5289e53512a63a2abc41d64990eee57d5c1761e8df`. Exact parser commands, outputs and complete extracted ledgers are retained as `pass8-*` and `eight-pass-corrected-identity-command.txt` in this directory. A preliminary parser used nonexistent summary field `exitCode` and guessed directory `fifthpass`; its false booleans and ENOENT are retained, followed by the corrected checks using actual field `code` and discovered directory `pass5`. Those were review-parser mistakes, not native failures. Some verbose tool-display output was truncated; the complete extracted ledgers and original raw files remain available.

The private two-switch static-evaluation counterfactual is reviewed separately once its retained result set is complete. It has not been installed in production or established as a correctness fix.
