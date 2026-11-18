# REPORT_dot_job4

## 1. Step0 PASS
PCA executable /tmp/forge-dot-pca-build/forge SHA25649b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a, same plain PCr15+A2A5 as Job3. GNU C++14.2.0, libstdc++.so.6.0.33, glibc2.41; CMake Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1. All five gates repeated in fresh processes, full labeled transcript step0_raw.txt:
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

## 2. PartA: original preregistered reading
Committed c1af536ab7f70feb3aeee60c72e619ed1c35cb15 before PartC. Lines below in unmodified PCA, not shifted candidate.
# Job4 Part A: reading before PartC
PCA /tmp/forge-dot-pca-src, search.cpp lines personally opened. Executable49b56941b2acc0c2b9272c4e14992f2561c9ef71dbaf3da74a8a684ae8bc416a. All statements below local code facts or explicitly conditional hypotheses, not observed outcome frequencies.

## A1: blends below excluded node
search.cpp2222-2223: `ss->excluded_move = move;` then `const int singular_score = search_child(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);`.
search.cpp1801-1802: `const Move excluded = ss->excluded_move;` / `(ss + 1)->excluded_move = Move::none();`. Exclusion is not inherited by ordinary descendants. Thus all bits can act at children/below when their normal gates hold.
Bit1 RFP1936-1937 requires `!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta) && mate_moves_ == 0 && board.halfmove_clock() + depth < 100`;1955-1959 depth<=RfpDepth and eval-margin>=beta plus bareking/optional guards.1960-1962: `return (tune::FailHighBlend & 1) != 0 && !is_mate_score(eval) && !is_mate_score(beta) ? beta + (eval - beta) / 3 : eval;`. It cannot act at excluded root but can at descendants.
Bit2 qsearch1683-1686 standpat failhigh and1756-1757 postloop: finite failhigh formula `best_score = (best_score + beta) / 2;`; no excluded/nonPV guard. qsearch returns at1692/1764, and stores blended scores. Verification depth is at least1 (2220), but descendants may enter qsearch.
Bit4 main2392-2394: `if ((tune::FailHighBlend & 4) != 0 && !pv_node && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta)) best_score = (best_score * depth + beta) / (depth + 1);`. No excluded guard: can act at excluded node itself and descendants, only nonPV finite failhigh.
TT cutoff1660-1664 returns `tt_score` unchanged; existing blended entries can flow across inside/outside boundary even when local formulas are disabled. The intended cut disables formula execution, not historical influence or TT sharing.

## A2: child negation
search.cpp2299,2309,2319: `score = -search_child(board, ss + 1, ... , -alpha - 1, -alpha, ...);` (depth reduced_depth or new_depth).2322 PV alternative uses `-beta, -alpha`.
For fixed nonPV positive-depth child raw best B>=child beta b, finite, depth d: without bit4 its returned value B gives excluded-node candidate -B. With bit4 return trunc0((B*d+b)/(d+1)) gives candidate -trunc0((B*d+b)/(d+1)). Since b<=blend<=B, candidate is greater than or equal to -B: it rises toward -b. C++ integer division truncates toward zero. This comparison holds fixed B,b,d, not an entire changed search.
At verification alpha=S-1,beta=S (S=singular_beta), a direct child null-window beta is b=1-S. Thus blended parent candidate<=S-1, still a fail-low alternative. Compression can erase a >24cp gap without crossing S. Deeper odd/even negations and tree changes need separate analysis.

## A3: formation of singular_score
search.cpp2332-2334: `if (score > best_score) { best_score = score; if (score > alpha) {`;2341-2345: `if (score >= beta) { ++ss->cutoff_count; break; } alpha = score;`.
It maximizes searched candidate values, updates alpha, cuts on failhigh, and normally returns fail-soft best_score (2411: `return best_score;`), not an unconditional clamp to alpha/beta. A fail-low result can be well below the null-window alpha and that distance drives double extension. Exceptions:2358-2359 `if (move_count == 0) { if (!excluded.is_none()) return alpha;`; abort2325 returns0. The excluded node's own bit4 final blend applies only on failhigh, preserves failhigh classification, and cannot affect the fail-low -24 test locally. Store2396 requires `excluded.is_none()`, so the excluded node does not store this result; descendants can.
Singular caller2228-2238: `if (singular_score < singular_beta) { extension = 1; if (!pv_node && singular_score < singular_beta - 24 && inherited_double_extensions <= 6) extension = 2; } else if (singular_beta >= beta) return singular_beta; else if (tt_score >= beta) extension = -2; else if (cut_node) extension = -1;`.

## A4: conditional direction, not a global monotonicity claim
With otherwise fixed direct child failures, bit4 increases their negated alternative values and thus can increase singular_score toward S. A result previously below S-24 can move into [S-24,S), changing eligible two-ply extensions to one-ply. Predict fewer doubles and more singles through this route. Direct finite child failhigh blending cannot by itself move the parent candidate above S-1, so it does NOT alone imply more multi-cut,-2,-1; their conditions remain false for that alternative. Whole-search frequencies are not derivable as monotone facts because searches, windows, pruning, TT payloads and path budgets change.
Chosen cut for PartC is worker-local nesting count around the excluded search call, including nested calls. Mode1 suppresses all four formula sites (bit2 has two) whenever count>0; mode2 allows formulas only when count>0;0 exactly PCA. Counter must decrement immediately after call before abort check. Existing TT entries are not segregated or rewritten: this experiment tests where blend formulas execute, not isolation of every causal influence.
Prediction direction for forthcoming preregistration: suppressing inside blending should recover some lost nodes/doubles; only-inside should retain substantial reduction. This is a hypothesis to test, not claimed established by source reading.


## 3. PartB: G known answers PASS
G at kimi5 commit5db05e09:353 lines, SHA256af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d. O from Job3:200 lines, SHA256ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8. PC20 first; Threads1 Hash16 built-in evaluation; go depth12. Each set one process, every position ucinewgame/isready/wait, FEN first4 fields +0 1. Full ordered settings and exe identity in each adjacent rows.txt.meta.txt. Nodes last depth/nodes info before bestmove. Harness stops unknown option/invalid value/ERROR.
- B_G0:17611204 nodes; first3 31779,46086,84457.
- B_G7:15879039 nodes; first3 30412,57137,44902.
Both match specified known sum/first3. O B1/B2 stand from Job3; no mismatch stop triggered. Raw+rows+metadata+summary files committed for both G sets.

## 4. PartC: scope cut and tests
DotSingularBlendMode0=PCA,1=blend only outside singular verification,2=blend only inside it. Worker-private nesting count resets at top-level search; scoped RAII increments around the excluded call and decrements on return/unwinding, including nested calls. All FOUR physical sites gated (RFP, qsearch standpat, qsearch postloop, main postloop). Counter does not rely on excluded_move, which descendants clear. No TT segregation: stored bounds can cross the scope boundary. No repository source edits.
Generated diff -ruN against fresh PCA and applied with patch -p1 -F0 to another fresh copy. Application output:
```
patching file include/forge/search.hpp
patching file src/search.cpp
```
Fresh applied source matches draft by diff-qr. Build output cut2_build.txt. Cut executable /tmp/forge-dot-cut2-build/forge SHA256b03779eefb747f276313b29f441c1021cc7ff80d41d07e500660494010a7790e, same compiler/flags/id as PCA. Generated patch output:
```diff
diff -ruN a/include/forge/search.hpp b/include/forge/search.hpp
--- a/include/forge/search.hpp	2026-11-18 14:05:18.259590837 +0100
+++ b/include/forge/search.hpp	2026-11-18 14:25:53.787115256 +0100
@@ -518,6 +518,7 @@
     std::chrono::steady_clock::time_point start_{};
     std::atomic<std::uint64_t> nodes_{0};
     std::uint64_t local_nodes_ = 0;
+    int dot_singular_nesting_ = 0; // per-worker, includes nested excluded searches
     const std::vector<Worker*>* all_workers_ = nullptr;
     std::uint64_t node_limit_ = 0;
     bool node_limit_specified_ = false;
@@ -575,6 +576,7 @@
     }
 #endif
     int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
+    bool dot_blend_allowed() const;
     int qsearch(Board& board, SearchStack* ss, int alpha, int beta);
     // B4 CuckooRep: every child search goes through these; with CuckooRep off they are the plain calls.
     int search_child(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
diff -ruN a/src/search.cpp b/src/search.cpp
--- a/src/search.cpp	2026-11-18 14:05:18.259303312 +0100
+++ b/src/search.cpp	2026-11-18 14:25:53.786998975 +0100
@@ -107,6 +107,7 @@
 int RfpMargin = 72;
 int RfpImproving = 40;
 // A2A5 (kimi5 job 25): fail-high blending and three reverse-futility conditions. All 0 = today's search.
+int DotSingularBlendMode = 0; // 0=PCA, 1=outside singular verification only, 2=inside only
 int FailHighBlend = 0;  // bit 1: rfp return blend; bit 2: qsearch fail-high blends; bit 4: main-search non-PV blend
 int RfpNoTtPv = 0;      // 1: the rfp step is skipped at a node whose tt-pv flag is set
 int RfpTtGuard = 0;     // 1: the rfp step is skipped when there is a TT move and it is not a capture
@@ -197,6 +198,7 @@
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
         {"RfpImproving", &RfpImproving, 0, 200},         {"RazorDepth", &RazorDepth, 0, 6},
+        {"DotSingularBlendMode", &DotSingularBlendMode, 0, 2},
         {"FailHighBlend", &FailHighBlend, 0, 7},         {"RfpNoTtPv", &RfpNoTtPv, 0, 1},
         {"RfpTtGuard", &RfpTtGuard, 0, 1},               {"RfpCorrMul", &RfpCorrMul, 0, 64},
         {"RazorBase", &RazorBase, 0, 1000},              {"RazorMultiplier", &RazorMultiplier, 0, 1000},
@@ -1619,6 +1621,11 @@
 // ---------------------------------------------------------------------------
 // Quiescence search
 
+bool Worker::dot_blend_allowed() const {
+    return tune::DotSingularBlendMode == 0 ||
+           (tune::DotSingularBlendMode == 1 ? dot_singular_nesting_ == 0 : dot_singular_nesting_ > 0);
+}
+
 int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {
     const bool pv_node = beta - alpha > 1;
     const int ply = ss->ply;
@@ -1682,7 +1689,7 @@
         best_score = eval;
         if (best_score >= beta) {
             // A2A5 bit 2 (a): the stand-pat fail high is blended toward beta before the store and the return.
-            if ((tune::FailHighBlend & 2) != 0 && !is_mate_score(best_score) && !is_mate_score(beta))
+            if ((tune::FailHighBlend & 2) != 0 && dot_blend_allowed() && !is_mate_score(best_score) && !is_mate_score(beta))
                 best_score = (best_score + beta) / 2;
 #if FORGE_SPD_TT_NOTLS
             if (!tt_hit) store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
@@ -1753,7 +1760,7 @@
     if (in_check && move_count == 0) return mated_in(ply);
 
     // A2A5 bit 2 (b): a fail-high best value is blended toward beta before the bound, the store and the return.
-    if ((tune::FailHighBlend & 2) != 0 && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta))
+    if ((tune::FailHighBlend & 2) != 0 && dot_blend_allowed() && best_score >= beta && !is_mate_score(best_score) && !is_mate_score(beta))
         best_score = (best_score + beta) / 2;
     const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
 #if FORGE_SPD_TT_NOTLS
@@ -1957,7 +1964,7 @@
             !(tune::RfpTtGuard != 0 && !tt_move.is_none() && !tt_move.is_capture()) &&
             eval - (tune::RfpMargin * depth - tune::RfpImproving * improving - rfp_worsening + rfp_corr) >= beta &&
             eval < MateInMaxPly) {
-            return (tune::FailHighBlend & 1) != 0 && !is_mate_score(eval) && !is_mate_score(beta)
+            return (tune::FailHighBlend & 1) != 0 && dot_blend_allowed() && !is_mate_score(eval) && !is_mate_score(beta)
                        ? beta + (eval - beta) / 3
                        : eval;
         }
@@ -2220,7 +2227,14 @@
             const int singular_depth = std::max(1, (depth - 1) / 2);
             const bool saved_tt_pv = ss->tt_pv;
             ss->excluded_move = move;
-            const int singular_score = search_child(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);
+            const int singular_score = [&] {
+                struct Scope {
+                    int& nesting;
+                    explicit Scope(int& value) : nesting(value) { ++nesting; }
+                    ~Scope() { --nesting; }
+                } scope(dot_singular_nesting_);
+                return search_child(board, ss, singular_depth, singular_beta - 1, singular_beta, cut_node);
+            }();
             ss->tt_pv = saved_tt_pv;
             ss->double_extensions = inherited_double_extensions;
             ss->excluded_move = Move::none();
@@ -2389,7 +2403,7 @@
     // bound is chosen, the entry is stored and the value returned. The correction-history update
     // below keeps the raw value.
     const int raw_best_score = best_score;
-    if ((tune::FailHighBlend & 4) != 0 && !pv_node && best_score >= beta && !is_mate_score(best_score) &&
+    if ((tune::FailHighBlend & 4) != 0 && dot_blend_allowed() && !pv_node && best_score >= beta && !is_mate_score(best_score) &&
         !is_mate_score(beta))
         best_score = (best_score * depth + beta) / (depth + 1);
     const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
@@ -2486,6 +2500,7 @@
 } // namespace
 
 SearchInfo Worker::search(Board board, const SearchLimits& limits, bool emit_info, const std::vector<Worker*>& all) {
+    dot_singular_nesting_ = 0;
     const auto origin = limits.start_time != std::chrono::steady_clock::time_point{}
         ? limits.start_time : limits.request_start;
     start_ = origin == std::chrono::steady_clock::time_point{}
```
Known wiring checks (all200 positions identical index/FEN/nodes/bestmove): C0_O0 to Job3B1, C0_O7 to Job3B2, C1_O0 to B1, C2_O0 to B1. Full evidence under these four labels and known_answer_equality.txt. Both requested no-blend controls passed; time/nps intentionally excluded from equality.

### Prediction committed alone before experimental sets
Commit8c232ed5da28fa73c39e1a8331c8f7c4c63694e8:
```
2026-11-18T13:29:28Z Prediction fixed before any FHB7 mode1/2 result.
Cut2 executable b03779eefb747f276313b29f441c1021cc7ff80d41d07e500660494010a7790e, GNU14.2.0 Release FORGE_MATE_ALPHA_GUARD=1; O200 ca2f576bb1632e46aa6143707de831d4d9ce361c5c6a9c7e7bc3fe913c8068b8, PC20 first T1 H16 built-in eval depth12 per-position reset. B1=8315168 B2=7913480.
FailHighBlend7 DotSingularBlendMode1 (outside only): point estimate 8500000, interval [8250000,9000000] nodes. Expect suppression inside singular verification to recover most aggregate lost nodes and perhaps exceed B1 because outside blending remains.
FailHighBlend7 DotSingularBlendMode2 (inside only): point estimate 7800000, interval [7400000,8100000] nodes. Expect retaining inside compression to preserve substantial shrinkage relative to B1.
These are hypotheses, not guarantees; TT sharing and changed child searches can defeat them. Four wiring sets all passed positional equality before this prediction. No experimental option1/2 FHB7 set has been run/read yet. G results to follow without a separate fitted prediction if time permits.
```
### Observed sums and ratios
```
Build b03779eefb747f276313b29f441c1021cc7ff80d41d07e500660494010a7790e; PC20 T1 H16 depth12 builtin eval; ordered metadata and raw per label.
C1_O7 sum 8150693 ratio_B1 0.9802198825 ratio_B2 1.0299758134 first3 [16156, 24537, 35989] recovered_fraction 0.5905404194300053
C2_O7 sum 8167140 ratio_B1 0.9821978341 ratio_B2 1.0320541658 first3 [20636, 21930, 25879] recovered_fraction 0.6314851327398379
C1_G7 sum 16401226 ratio_B1 0.9312949870 ratio_B2 1.0328853024 first3 [41508, 61339, 45026] recovered_fraction 0.30146492972667155
C2_G7 sum 16730023 ratio_B1 0.9499647497 ratio_B2 1.0535916563 first3 [44693, 52246, 60838] recovered_fraction 0.49128345163422654
Prediction mode1 O: direction relative B2 PASS; interval[8250000,9000000] FAIL below lower endpoint; point8500000 high by349307. Majority recovery direction supported on O:237213/401688=59.05%; no preregistered fraction, numeric interval still fails.
Prediction mode2 O: shrink vs B1 PASS; interval[7400000,8100000] FAIL above upper endpoint; point7800000 low by367140. Only-inside retains148028/401688 of uncut aggregate shrink, not most.
Conclusion: both scopes contribute under this intervention; no binary unique-path verdict. Shared TT entries and changed history/tree remain interacting routes. Frequency outcomes require PartD, not inferred from node totals.
```
**Both numerical intervals FAILED.** Outside-only rose relative to both-on as predicted but by less than the interval required. Inside-only remained below no-blend as predicted but retained less aggregate shrinkage than my point estimate anticipated. On O, outside-only recovers59.05% of the both-on node reduction; inside-only retains36.85% of that reduction. On G, outside-only recovers30.15%, inside-only retains50.87%. These intervention differences are not additive causal shares; each changes the subsequent tree/TT/history. Both scopes influence the outcome. No replacement prediction after seeing data.

## 5. PartD: optional counters completed, controls PASS
Kimi5 counter patch at5db05e09 SHA2567a6f6c322fc46fb8dc5f07efbb4e1acebb3c8b02f650af434aaa47d441fd3336. Original application with -F0 to cut2 had one contextual reject where the new blend guard changed the RFP line:
```
patching file src/search.cpp
Hunk #2 succeeded at 239 (offset 2 lines).
Hunk #3 succeeded at 1882 (offset 7 lines).
Hunk #4 FAILED at 1966.
Hunk #5 succeeded at 2234 (offset 7 lines).
Hunk #6 succeeded at 2259 (offset 14 lines).
Hunk #7 succeeded at 3172 (offset 15 lines).
Hunk #8 succeeded at 3190 (offset 15 lines).
1 out of 8 hunks FAILED -- saving rejects to file src/search.cpp.rej
```
Ported only rejected hunk's context to retain dot_blend_allowed(); counting expressions unchanged. Original reject committed count_reject.txt. Port application:
```
patching file src/search.cpp
Hunk #1 succeeded at 1973 (offset 7 lines).
```
Combined diff-ruN against PCA is cut2_count_combined.patch.txt; applied to fresh PCA with patch-p1-F0:
```
patching file include/forge/search.hpp
patching file src/search.cpp
```
Fresh combined source matched clean draft by diff-qr. count_build.txt records build; /tmp/forge-dot-cut2-count-build/forge SHA25629e2868379323f905532aeb1ba3a325c6a58260d803e5c80cf943c55845e62b4, same GNU/Release/guard flags.
Counters are the authorized kimi5 Threads1 diagnostic, not a strength change. Parse exactly one16-slot A25C per position (200), check closure slot0=sum slots1..6 in every row. D0_O0 and D0_O7 exactly reproduce B1/B2 every position; required tests/doubles48220/5794 and47952/2124 matched. Only then ran D1_O7,D2_O7; both reproduce corresponding plain cut2 result every position. Raw full transcripts, ordinary rows+meta+summary, and indexed counts.txt committed for all four D sets.
```
Counter build SHA29e2868379323f905532aeb1ba3a325c6a58260d803e5c80cf943c55845e62b4, GNU14.2.0 Release MATE_ALPHA_GUARD1; PC20 T1 H16 O200 depth12 built-in evaluation.
D0_O0 PASS positional identity C0_O0 nodes 8315168 tests 48220 single 13566 double 5794 double_per1000 0.6967989101 single_per1000 1.6314763574 all_slots [48220, 13566, 5794, 11268, 6978, 5010, 5604, 342931, 30767, 16174, 2212993, 2212993, 0, 0, 0, 2212993]
D0_O7 PASS positional identity C0_O7 nodes 7913480 tests 47952 single 12464 double 2124 double_per1000 0.2684027760 single_per1000 1.5750339926 all_slots [47952, 12464, 2124, 9361, 9212, 8675, 6116, 313345, 34051, 15289, 2080561, 2080561, 0, 0, 0, 2080561]
D1_O7 PASS positional identity C1_O7 nodes 8150693 tests 48648 single 10878 double 4091 double_per1000 0.5019205115 single_per1000 1.3346104436 all_slots [48648, 10878, 4091, 9327, 9511, 8682, 6159, 314648, 34707, 15183, 2135789, 2135789, 0, 0, 0, 2135789]
D2_O7 PASS positional identity C2_O7 nodes 8167140 tests 48092 single 16374 double 3111 double_per1000 0.3809166979 single_per1000 2.0048633916 all_slots [48092, 16374, 3111, 11374, 6613, 5007, 5613, 341821, 29436, 15773, 2172484, 2172484, 0, 0, 0, 2172484]
No count-derived strength claim. Other outcomes vary in whole tree; local fixed-child algebra does not predict every aggregate frequency.
```
Inside-only blending lowers doubles from0.6968 to0.3809 per1000 nodes and raises singles from1.6315 to2.0049; this supports the conditional conversion route in A4. Outside-only also lowers doubles (0.5019); both-on is lower still (0.2684). Thus the inside route is a contributor, not an isolated complete explanation. The all-tree single rate with both-on actually falls vs no blend; this does not invalidate fixed-child algebra but does invalidate any unconditional global 'singles always rise' claim. No such global guarantee is asserted in PartA.

## Facts
All Step0, G known-answer, four wiring and counter controls passed. PartA and prediction committed before required tests. Every experimental sum/count above has full raw+rows+metadata committed; labels identify exact build/settings. All native work ended13:32:21UTC; publication subsequently in bounded calls. Only own branch updated, no PR, repository engine source unchanged.

## Suspicions
Remaining TT/history/window interactions and outside-scope blending account for additional effects; precise causal shares are not measured. TT sharing means neither mode removes every inherited influence from the opposite scope.

## What I did not do
No NNUE, other depths, games, strength measurement, independent per-path causal attribution, or G counter sets. No changes to baseline settings to rescue a failed prediction.

## What I am not sure about
How effects generalize, and whether specific singular-outcome changes explain each changed position. Aggregate counts support a route, not a proof of exclusive causation. Exact model identifier unavailable and not inferred.

The PC's own net (this is the built-in evaluation), other depths, games. A tree size is not strength.

## Job2 correction accepted and applied
Reopened K1_summary.json.txt and base_plain_go_nodes_250000_fen5.raw.txt. Of32 hard-node cases,31 exactly met cap; all32 stayed within. Base/S14 position index5 consumed249294 of250000, depth64, score31997, PV g3g6 c6e5 g6h7. Report2's 'Every' sentence was false and was corrected atc7e6ad7d2fdcab8ce4df6d77ec1929c6c5071075. Count receipt job2_correction.txt; raw source/settings remain Job2 evidence. Hard limits are upper bounds, not a promise to consume all nodes. Job4 does not repeat the mistaken claim.

## Last command before report commit
`git status --short; ls -R forge-combo29/dot/job4` follows. Local branch is stale relative to connected-GitHub commits, so preserved evidence is untracked; no engine source modification is hidden or discarded. CLI push lacks credentials; connected GitHub used for authorized text writes.

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
?? forge-combo29/dot/job4/
forge-combo29/dot/job4:
B_G0.raw.txt
B_G0.rows.txt
B_G0.rows.txt.meta.txt
B_G0.summary.txt
B_G7.raw.txt
B_G7.rows.txt
B_G7.rows.txt.meta.txt
B_G7.summary.txt
C0_O0.raw.txt
C0_O0.rows.txt
C0_O0.rows.txt.meta.txt
C0_O0.summary.txt
C0_O7.raw.txt
C0_O7.rows.txt
C0_O7.rows.txt.meta.txt
C0_O7.summary.txt
C1_G7.raw.txt
C1_G7.rows.txt
C1_G7.rows.txt.meta.txt
C1_G7.summary.txt
C1_O0.raw.txt
C1_O0.rows.txt
C1_O0.rows.txt.meta.txt
C1_O0.summary.txt
C1_O7.raw.txt
C1_O7.rows.txt
C1_O7.rows.txt.meta.txt
C1_O7.summary.txt
C2_G7.raw.txt
C2_G7.rows.txt
C2_G7.rows.txt.meta.txt
C2_G7.summary.txt
C2_O0.raw.txt
C2_O0.rows.txt
C2_O0.rows.txt.meta.txt
C2_O0.summary.txt
C2_O7.raw.txt
C2_O7.rows.txt
C2_O7.rows.txt.meta.txt
C2_O7.summary.txt
D0_O0.counts.txt
D0_O0.raw.txt
D0_O0.rows.txt
D0_O0.rows.txt.meta.txt
D0_O0.summary.txt
D0_O7.counts.txt
D0_O7.raw.txt
D0_O7.rows.txt
D0_O7.rows.txt.meta.txt
D0_O7.summary.txt
D1_O7.counts.txt
D1_O7.raw.txt
D1_O7.rows.txt
D1_O7.rows.txt.meta.txt
D1_O7.summary.txt
D2_O7.counts.txt
D2_O7.raw.txt
D2_O7.rows.txt
D2_O7.rows.txt.meta.txt
D2_O7.summary.txt
D_gate.txt
count_build.txt
count_combined_apply.txt
count_initial_apply.txt
count_port_apply.txt
count_reject.txt
cut2.patch.txt
cut2_apply.txt
cut2_build.txt
cut2_count_combined.patch.txt
job2_correction.txt
known_answer_equality.txt
part_A_reading.txt
part_C_analysis.txt
part_D_analysis.txt
prediction.txt
run_set.py.txt
stamps.txt
step0_gate.py.txt
step0_raw.txt
step0_summary.txt

```
