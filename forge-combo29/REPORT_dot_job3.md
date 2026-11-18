# REPORT_dot_job3

## 1. Step 0: PASS
PCA is the plain PCr15 tree (no Job2 counters) plus kimi5 A2A5 at 5db05e09; input patch SHA256 0bcb88c59fe3659f4ab71a4fededd453f4713e6dd4d86e6e0c45b557ba86b991. Applied to fresh isolated source with patch -p1 -F0, no rejects:
```
patching file src/search.cpp
patching file include/forge/search.hpp
```
GNU C++14.2.0, libstdc++.so.6.0.33, glibc2.41; CMake Release, -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1. No source change in the repository. PCA executable and all five fresh-process gate outputs are labeled in dot/job3/step0_raw.txt; summary:
```json
{
  "exe_sha256": "49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a",
  "id": [
    "id name Chess Engine Forge 6.4.24 candidate"
  ],
  "options": [
    "option name FailHighBlend type spin default 0 min 0 max 7",
    "option name RfpNoTtPv type spin default 0 min 0 max 1",
    "option name RfpTtGuard type spin default 0 min 0 max 1",
    "option name RfpCorrMul type spin default 0 min 0 max 64"
  ],
  "known_answers": [
    [
      "PCA_default",
      11,
      312866
    ],
    [
      "PCA_default",
      13,
      862329
    ],
    [
      "PCA_PC20",
      11,
      278024
    ],
    [
      "PCA_PC20",
      13,
      587276
    ],
    [
      "perft",
      5,
      4865609
    ]
  ],
  "gate": "PASS"
}
```

## 2. Part A (committed before any Part B run)
Commit eb519e77576960b2832ae0d461266e7c8fc83c10 preserves the following original hypotheses, not rewritten after the outcome.

# Job3 Part A — committed before Part B
PCA = base6b98f217 + PCr15 patch d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a + A2A5 patch0bcb88c59fe3659f4ab71a4fededd453f4713e6dd4d86e6e0c45b557ba86b991. All line numbers below are in PCA src/search.cpp, personally opened. Step0 PASS, executable49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a. This is reading and hypotheses, not PartB/C evidence.

## A1 — exactly where scores change
- Bit1, reverse futility, lines1936-1937 outer gate:
  `if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta) && mate_moves_ == 0 && board.halfmove_clock() + depth < 100)`.
  Lines1955-1959 require !bare_king_mode, depth<=RfpDepth, the optional RFP guard predicates, and eval minus its margin>=beta, with eval<MateInMaxPly. Lines1960-1962:
  `return (tune::FailHighBlend & 1) != 0 && !is_mate_score(eval) && !is_mate_score(beta) ? beta + (eval - beta) / 3 : eval;`
  This touches the RFP early RETURN, not a local TT store.
- Bit2, qsearch non-check stand-pat fail high, lines1669-1672 distinguish in-check from stand-pat. Lines1683-1686:
  `if (best_score >= beta) {`
  `if ((tune::FailHighBlend & 2) != 0 && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score + beta) / 2;`
  It can act at PV or non-PV qsearch nodes. Store occurs only on !tt_hit at1688/1690, then return1692.
- Bit2, qsearch after its move loop, lines1753-1764:
  `if (in_check && move_count == 0) return mated_in(ply);`
  `if ((tune::FailHighBlend & 2) != 0 && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score + beta) / 2;`
  Then bound and depth0 store1760/1762, return1764. No non-PV restriction, no explicit excluded-move guard at either qsearch blend.
- Bit4, positive-depth main search after its move loop, lines2391-2394:
  `const int raw_best_score = best_score;`
  `if ((tune::FailHighBlend & 4) != 0 && !pv_node && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score * depth + beta) / (depth + 1);`
  Main depth<=0 already goes to qsearch_child at1775. There is no excluded.is_none guard on this blend: an excluded-move verification can blend its return, but cannot store here because2396 guards the store.
- TT cutoff returns do NOT receive a fresh blend: qsearch1660-1664 returns tt_score; main1860-1872 returns tt_score. They may already contain a blended stored value. Null returns1998/2012, ProbCut2048, singular early return2234, terminal/draw/maxply paths1791-1796 do not directly execute an FHB formula, though child values can already be affected.
- All formulas are integer arithmetic (C++ truncation toward zero); finite fail-high values remain at/above beta, so the local blend does not turn a fail high into a fail low.

## A2 — singular step and outcomes
Lines1818-1822:
`const int tt_score = tt_hit && tte.score_usable(board.halfmove_clock()) && rule50_score_for_this_clock(tte.rule50_clock, board.halfmove_clock()) ? score_from_tt(tte.score, ply) : ValueNone;`
`const int tt_depth = tt_hit ? tte.depth : -1;`
`const Bound tt_bound = tt_hit ? tte.bound() : BoundNone;`

Lines2214-2216:
`if (mate_moves_ == 0 && !root_node && depth >= tune::SingularDepth && move == tt_move && excluded.is_none() && tt_bound != BoundUpper && tt_score != ValueNone && !is_mate_score(tt_score) && tt_depth >= depth - 3) {`
`const int singular_beta = tt_score - tune::SingularMargin * depth;`

It reads the usable stored SEARCH SCORE, not tte.eval/raw static evaluation. PC20 SingularDepth=6. Lines2220-2226:
`const int singular_depth = std::max(1, (depth - 1) / 2);`
`ss->excluded_move = move;`
`const int singular_score = search_child(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);`
It is same board/same stack ply, null window, original tt_move excluded; tt_pv and inherited_double_extensions restored, exclusion cleared afterward. Move loop2094 says `if (move == excluded) continue;`. Main TT cutoff1860 and forward-pruning1936 require excluded.is_none, so this verification bypasses those shortcuts. CuckooRep wrapper2437-2444 also explicitly leaves the singular verification alone.

Lines2228-2239:
`if (singular_score < singular_beta) { extension = 1;`
`if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) { extension = 2; }`
`} else if (singular_beta >= beta) { return singular_beta;`
`} else if (tt_score >= beta) { extension = -2;`
`} else if (cut_node) { extension = -1; }`
Otherwise extension stays0. Thus a strict24cp gap plus non-PV and path-budget gate makes the double extension. Check extension2240-2242 is an else-if alternative, not added on top of this branch. Lines2244-2245:
`ss->double_extensions = inherited_double_extensions + (extension == 2);`
`int new_depth = depth - 1 + extension;`

## A3 — stored payload and downstream readers
Main-loop lines2391-2401 first save raw_best_score, then overwrite best_score with the bit4 blend, choose bound, and store:
`store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());`
Both compile-time TT arms2398/2400 use BLENDED best_score. The pre-local-blend value is used only for correction-history gates/update2405-2409:
`update_correction(board, depth, raw_best_score, ss->static_eval, ss);`
Return2411 is `return best_score;`.
Raw here means before THIS node's bit4 blend, not an imaginary score from a wholly unblended subtree.

Later readers of the stored score include:
- main cutoff1860-1872 and qsearch cutoff1660-1664;
- singular threshold2216 and negative-extension branch2235;
- bound-aware evaluation substitution1886-1889 and1677-1680;
- null-move upper-bound guard1969 and ProbCut veto2019.
They all read tt_score decoded from tte.score, subject to their separate usability/depth/clock gates. Qsearch bit2 stores blended depth0 payload too; that depth0 payload cannot itself satisfy a SingularDepth6 test's required tt_depth>=depth-3, though it changes descendant searches and subsequent main entries. RFP bit1 has no store at its own early-return site.

## A4 — ranked hypotheses, fixed before any PartB run
1. **Main bit4 store -> lower tt_score -> lower singular_beta -> harder double-gap test.** Compressing a finite fail-high stored score toward beta lowers or preserves the candidate move's reference bound. With the alternatives fixed, singular_score < singular_beta-24 becomes harder to satisfy, so double extensions fall. This is the shortest explicit data path and my first-ranked explanation.
   Cut chosen: keep the return blended but store raw_best_score at the MAIN post-loop store behind a new default0 spin. Expect the FHB7 tree to GROW relative to uncut FHB7, moving toward the FHB0 tree, because some reference thresholds and double extensions recover. FHB0 must remain exactly identical since raw_best_score==best_score when bit4 is off. No numeric prediction yet; PartC will commit it alone after wiring checks.
2. **Descendant return/window path.** Bit1/bit2 and bit4 child returns alter the excluded-alternative search as well as the original move search; negation can turn a smaller child fail-high into a larger parent alternative score. This can narrow the double-extension gap even if a local main TT store is restored.
3. **Feedback through other TT consumers, move ordering and changed tree/history.** Changed stored bounds affect cutoffs, eval substitution, pruning and future entries; changed trees also change correction/history updates despite the local raw correction value. These interactions can dominate a simple arithmetic direction.

Crucial limit: storing raw at the main site cuts one major transmission route, but changes ALL later consumers of that payload, not only singular_beta; it also leaves descendant and qsearch-store blending intact. An increased node sum would support contribution of this route, not prove it is the unique cause or directly count recovered double extensions. A contrary result would reject my directional prediction rather than be relabeled success.


## 3. Part B: all three required known answers equal
Input O.epd at kimi5 5db05e09: 200 positions, SHA256 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8. Built-in evaluation, PC20 first (exact ordered settings in each adjacent .meta.txt), Threads1 Hash16, depth12. One process per setting; each position uses ucinewgame, isready and readyok before position/go. Harness stops on unknown option, invalid value, ERROR. FEN is first four EPD fields plus 0 1. Nodes are the last depth/nodes info before bestmove.
- B1 FHB0: 8315168; first3 21812,26844,35173. Equal.
- B2 FHB7: 7913480; first3 18623,19820,32078. Equal.
- B3 FHB7 + SingularDepth20: 8464273; first3 26752,32523,30913. Equal.
Source: B1/B2/B3.raw.txt and rows.txt, each with adjacent rows.txt.meta.txt and summary.txt in dot/job3. No mismatch gate triggered. B3 ratio below is to B1, not to a separate FHB0+SingularDepth20 baseline, which was not run.

## 4. Part C: path cut, prediction, and adverse result
New spin DotRawMainTt, default0 range0..1. At1 only the main post-loop TT payload uses raw_best_score, while the return remains blended. It changes both TT storage compile-time arms, no qsearch store or return. This affects all consumers of that TT payload, not exclusively singular thresholds. The patch is diagnostic, not a proposed strength improvement.
Generated diff -ruN, applied via patch -p1 -F0 to another fresh PCA copy. Application output: `patching file src/search.cpp`. Fresh applied and drafted source trees matched by diff -qr. Build output is cut_build.txt. Executable SHA256 0eb52c2ee61d38639eef5ca5c8d9379c502a472dacb3a2a0fcf0b4ccfdba3fd1, same compiler/flags/id; patch and application stdout are committed separately and reproduced here:
```diff
diff -ruN a/src/search.cpp b/src/search.cpp
--- a/src/search.cpp	2026-11-18 14:05:18.259303312 +0100
+++ b/src/search.cpp	2026-11-18 14:13:12.656836412 +0100
@@ -107,6 +107,7 @@
 int RfpMargin = 72;
 int RfpImproving = 40;
 // A2A5 (kimi5 job 25): fail-high blending and three reverse-futility conditions. All 0 = today's search.
+int DotRawMainTt = 0;  // diagnostic path cut: store pre-blend main-search score, return remains blended
 int FailHighBlend = 0;  // bit 1: rfp return blend; bit 2: qsearch fail-high blends; bit 4: main-search non-PV blend
 int RfpNoTtPv = 0;      // 1: the rfp step is skipped at a node whose tt-pv flag is set
 int RfpTtGuard = 0;     // 1: the rfp step is skipped when there is a TT move and it is not a capture
@@ -197,6 +198,7 @@
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
         {"RfpImproving", &RfpImproving, 0, 200},         {"RazorDepth", &RazorDepth, 0, 6},
+        {"DotRawMainTt", &DotRawMainTt, 0, 1},
         {"FailHighBlend", &FailHighBlend, 0, 7},         {"RfpNoTtPv", &RfpNoTtPv, 0, 1},
         {"RfpTtGuard", &RfpTtGuard, 0, 1},               {"RfpCorrMul", &RfpCorrMul, 0, 64},
         {"RazorBase", &RazorBase, 0, 1000},              {"RazorMultiplier", &RazorMultiplier, 0, 1000},
@@ -2395,9 +2397,9 @@
     const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
     if (excluded.is_none() && !(root_node && root_restricted_)) {
 #if FORGE_SPD_TT_NOTLS
-        store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
+        store_tt(tt_probe, board.key(), score_to_tt(tune::DotRawMainTt ? raw_best_score : best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
 #else
-        shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
+        shared_.tt.store(tt_probe, board.key(), score_to_tt(tune::DotRawMainTt ? raw_best_score : best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
 #endif
     }
     // Teach the static evaluation about this pawn structure when the search
```
Known-answer wiring: DotRawMainTt0 reproduces B1 and B2 at all200 positions (FEN, nodes, bestmove); see C0_equality.txt and C0_B1/C0_B2 raw+rows+meta. Times/nps are not compared as deterministic results.

Prediction committed ALONE at d022dec8372e53e2e283a4574a33c7e11d80f0c6 before either option1 set:
```
2026-11-18T13:14:31Z Pre-run prediction, committed alone before any DotRawMainTt=1 set.
Build /tmp/forge-dot-pca-cut-build/forge SHA256 0eb52c2ee61d38639eef5ca5c8d9379c502a472dacb3a2a0fcf0b4ccfdba3fd1; Release GNU14.2.0, FORGE_MATE_ALPHA_GUARD=1. O 200 positions input ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, PC20 sent first, Threads1 Hash16 built-in evaluation, depth12, reset each position, one process per setting.
FailHighBlend7 DotRawMainTt1: point estimate 8,200,000 nodes; predicted interval 8,050,000 to 8,600,000 inclusive. Direction: increase from B2 7,913,480 toward B1 8,315,168 as higher stored raw scores raise later singular thresholds and facilitate extension outcomes. This is a directional hypothesis, not a strength claim; other TT consumers and still-blended descendants may defeat it.
FailHighBlend0 DotRawMainTt1: exactly 8,315,168 nodes, range [8,315,168,8,315,168], all 200 position nodes and bestmoves identical to B1; raw and blended main score coincide when bit4 off.
Option0 already passed both B1 and B2 position-by-position equality. No option1 results have been run or read.
```
Observed results and ratios, exact raw calculations in C1_analysis.txt:
```
FHB0 cut1 vs B1: all200 nodes/bestmove/FEN equal
B1 sum 8315168 ratio_to_B1 1.0000000000 first3 [21812, 26844, 35173] exe_sha 49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a
B2 sum 7913480 ratio_to_B1 0.9516921366 first3 [18623, 19820, 32078] exe_sha 49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a
B3 sum 8464273 ratio_to_B1 1.0179316882 first3 [26752, 32523, 30913] exe_sha 49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a
C0_B1 sum 8315168 ratio_to_B1 1.0000000000 first3 [21812, 26844, 35173] exe_sha 0eb52c2ee61d38639eef5ca5c8d9379c502a472dacb3a2a0fcf0b4ccfdba3fd1
C0_B2 sum 7913480 ratio_to_B1 0.9516921366 first3 [18623, 19820, 32078] exe_sha 0eb52c2ee61d38639eef5ca5c8d9379c502a472dacb3a2a0fcf0b4ccfdba3fd1
C1_FHB7 sum 7905110 ratio_to_B1 0.9506855424 first3 [15193, 20580, 29159] exe_sha 0eb52c2ee61d38639eef5ca5c8d9379c502a472dacb3a2a0fcf0b4ccfdba3fd1
C1_FHB0 sum 8315168 ratio_to_B1 1.0000000000 first3 [21812, 26844, 35173] exe_sha 0eb52c2ee61d38639eef5ca5c8d9379c502a472dacb3a2a0fcf0b4ccfdba3fd1
FHB7 cut effect vs B2: -8370 nodes; ratio 0.9989423110944868
Prediction FHB7: FAIL direction, FAIL interval[8050000,8600000]; FHB0 PASS exact sum and positional identity.
Conclusion: first-ranked directional prediction not supported. Main stored-score route alone does not explain aggregate shrinkage under this cut; remaining return/window feedback or other TT interactions may dominate. No singular-count attribution demonstrated.
```
**Grade: FHB7 direction and numerical interval FAILED. FHB0 exact identity PASSED.** The cut leaves essentially the full aggregate tree reduction in place and slightly lowers total nodes further. It therefore does not support my first-ranked prediction that restoring this main stored-score route would recover the missing aggregate nodes. It does not prove stored scores have no effect on singular outcomes: no singular counters were added, and the cut changes multiple TT consumers. Remaining descendant return/window and feedback routes are hypotheses, not findings. No post-result tuning or replacement prediction.

## Facts
- All required Step0 and PartB gates passed; option0 matches position-by-position; option1 FHB0 also matches position-by-position.
- PartA and prediction were committed before their required subsequent runs.
- Main store uses blended score on PCA; patch substitutes pre-local-blend score only at selected main store. Pre-local-blend is not a wholly unblended-subtree value.
- All seven set raw transcripts, rows, metadata and summaries are committed as text; harnesses and patch/application/build evidence included.
- Repository engine source untouched; isolated build files remain outside repository, only own branch updated, no PR.

## Suspicions
Descendant return/window effects or other TT feedback may dominate; not resolved by this experiment.

## What I did not do
No singular counters, no second cut, no game matches, no NNUE run, no other depth/position set, no performance or strength claim. B3 is a known-answer reproduction, not a complete independent singular-on/off causal comparison.

## What I am not sure about
Which remaining pathway accounts for the two-ply extension reduction, or whether the primary route changes per-position singular counts despite the failed aggregate direction. Exact model identifier is not exposed; not inferred.

The PC's own net (this is the built-in evaluation), other depths, other position sets, games. A tree size is not strength.

## Evidence/publication context
Native experiment work completed13:14:50UTC after claim13:04:42UTC; date-u receipts in stamps.txt. CLI push credentials unavailable, connected GitHub text writes used. Local status includes preserved Job2 evidence and connector-written files untracked relative to stale local branch; this is disclosed, not reset. No engine source file appears as modified.

## Last command before report commit
`git status --short; ls -R forge-combo29/dot/job3` output follows. Report publication uses the connected GitHub tool, not a source-tree commit.

```
 M forge-combo29/dot/job2/stamps.txt
?? forge-combo29/dot/job2/K1_base_count_search_extract.txt
?? forge-combo29/dot/job2/K1_base_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_base_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_matrix.py.txt
?? forge-combo29/dot/job2/K1_matrix_console.txt
?? forge-combo29/dot/job2/K1_pc_count_search_extract.txt
?? forge-combo29/dot/job2/K1_pc_diagnostic_gate.raw.txt
?? forge-combo29/dot/job2/K1_pc_plain_search_extract.txt
?? forge-combo29/dot/job2/K1_summary.json.txt
?? forge-combo29/dot/job2/K2_analysis.txt
?? forge-combo29/dot/job2/K2_base_raw.txt
?? forge-combo29/dot/job2/K2_base_search_extract.txt
?? forge-combo29/dot/job2/K2_cap.py.txt
?? forge-combo29/dot/job2/K2_console.txt
?? forge-combo29/dot/job2/K2_fault_replay.py.txt
?? forge-combo29/dot/job2/K2_fault_result.txt
?? forge-combo29/dot/job2/K2_pc_raw.txt
?? forge-combo29/dot/job2/K2_pc_search_extract.txt
?? forge-combo29/dot/job2/K2_replay_count.raw.txt
?? forge-combo29/dot/job2/K2_replay_fault.raw.txt
?? forge-combo29/dot/job2/K2_replay_plain.raw.txt
?? forge-combo29/dot/job2/K2_summary.json.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/base_count_only.patch.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/base_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/manifest.sha256.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_count_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_count_only.patch.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_250000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_nodes_50000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen0.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen1.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen2.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen3.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen4.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen5.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen6.raw.txt
?? forge-combo29/dot/job2/pc_plain_go_softnodes_2000_fen7.raw.txt
?? forge-combo29/dot/job2/pc_planted_overrun.patch.txt
?? forge-combo29/dot/job3/
forge-combo29/dot/job3:
B1.raw.txt
B1.rows.txt
B1.rows.txt.meta.txt
B1.summary.txt
B2.raw.txt
B2.rows.txt
B2.rows.txt.meta.txt
B2.summary.txt
B3.raw.txt
B3.rows.txt
B3.rows.txt.meta.txt
B3.summary.txt
C0_B1.raw.txt
C0_B1.rows.txt
C0_B1.rows.txt.meta.txt
C0_B1.summary.txt
C0_B2.raw.txt
C0_B2.rows.txt
C0_B2.rows.txt.meta.txt
C0_B2.summary.txt
C0_equality.txt
C1_FHB0.raw.txt
C1_FHB0.rows.txt
C1_FHB0.rows.txt.meta.txt
C1_FHB0.summary.txt
C1_FHB7.raw.txt
C1_FHB7.rows.txt
C1_FHB7.rows.txt.meta.txt
C1_FHB7.summary.txt
C1_analysis.txt
cut_apply_output.txt
cut_build.txt
cut_path.patch.txt
part_A_reading.txt
prediction.txt
run_set.py.txt
stamps.txt
step0_gate.py.txt
step0_patch_output.txt
step0_raw.txt
step0_summary.txt

```
