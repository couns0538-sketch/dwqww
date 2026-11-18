# astra5 job 5 — do the flagged null cutoffs change the root move?

## Step 0 — all 12 fresh-process checks passed

The same Job 1 PC and PCA executables, using their built-in evaluation, reproduced each required result. [Raw input, output and executable hashes](astra5/job5/step0)

| Build | Settings | Bench 11 | Bench 13 | Perft 5 |
|---|---|---:|---:|---:|
| PC | No setoption | 312,866 | 862,329 | 4,865,609 |
| PC | S14 | 242,796 | 656,517 | — |
| PC | PC20 | 278,024 | 587,276 | — |
| PCA | No setoption | 312,866 | 862,329 | 4,865,609 |
| PCA | PC20 | 278,024 | 587,276 | — |

All A/B ladders below use PC20, Threads 1, Hash 16, and `ucinewgame` followed by `isready` before each `go depth D`. P is `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`. Each O/G suite search uses depth 12. Each ratio uses its own disabled arm as the denominator. The 81 flagged and 272 unflagged G positions are fixed by Job 4’s depth-12 slot [4] and aligned by index and FEN before comparing moves.

## Part A — refuse exactly the flagged cutoffs

The `NullMateGuard` spin (default 0, range 0–1) is added on top of the Job 4 floor tree. When the null score reaches beta with a child depth of zero or less, the guard reconstructs the null child on a copy and checks whether the side to move has a legal quiet mate in one. A positive result lets the original node proceed past the null-move block, skipping both immediate return and verification. The inherited floor stays at zero. [Source locations and patch application](astra5/job5/A/build)

<details><summary>Verbatim diff -ruN and patch -p1 -F0 outputs</summary>

```diff
diff -ruN pcfloor/include/forge/search.hpp guard-design/include/forge/search.hpp
--- pcfloor/include/forge/search.hpp	2026-11-15 05:25:59.000000000 +0000
+++ guard-design/include/forge/search.hpp	2026-11-15 05:25:59.000000000 +0000
@@ -251,6 +251,7 @@
 extern int NullMoveMinDepth;
 extern int NullMoveBase;
 extern int NullChildFloor;
+extern int NullMateGuard;
 extern int NullMoveDepthDivisor;
 extern int NullMoveEvalDivisor;
 extern int RfpDepth;
diff -ruN pcfloor/src/search.cpp guard-design/src/search.cpp
--- pcfloor/src/search.cpp	2026-11-15 05:25:59.000000000 +0000
+++ guard-design/src/search.cpp	2026-11-15 05:25:59.000000000 +0000
@@ -102,6 +102,7 @@
 int NullMoveMinDepth = 3;
 int NullMoveBase = 3;
 int NullChildFloor = 0;
+int NullMateGuard = 0;
 int NullMoveDepthDivisor = 3;
 int NullMoveEvalDivisor = 200;
 int RfpDepth = 8;
@@ -190,6 +191,7 @@
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
         {"NullChildFloor", &NullChildFloor, 0, 3},
+        {"NullMateGuard", &NullMateGuard, 0, 1},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -1754,6 +1756,23 @@
 }
 
 // ---------------------------------------------------------------------------
+// Test a private copy of the null child, using the job 4 counter's legal quiet-mate test.
+namespace {
+bool quiet_mate_after_null(Board parent) {
+    NullUndo null_undo;
+    parent.make_null_move(null_undo);
+    for (const Move move : parent.legal_moves()) {
+        if (!move.is_quiet() || !parent.gives_check(move)) continue;
+        Undo undo;
+        (void)parent.make_move(move, undo);
+        const bool mate = parent.in_check() && parent.legal_moves().empty();
+        parent.unmake_move(move, undo);
+        if (mate) return true;
+    }
+    return false;
+}
+} // namespace
+
 // Main alpha-beta search
 
 int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
@@ -1968,7 +1987,8 @@
             int null_score = -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
-            if (null_score >= beta) {
+            if (null_score >= beta &&
+                !(tune::NullMateGuard && null_child_depth <= 0 && quiet_mate_after_null(board))) {
                 if (is_mate_score(null_score)) null_score = beta;
                 // Depth >= 14 always verifies, as before. Below that, a cutoff
                 // stands unless NullThreatVerify is on and a cheaper enemy piece
```

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

</details>

A, NullMateGuard 0: all 20 P ladder depths, 200 O rows and 353 G rows matched job 4 floor 0. Each P TSV row matched its UCI transcript.

NullMateGuard 1 first reported g3g6 with a positive mate score at depth 13 (86,114 nodes).

| D | Value 0 move / score / nodes | Value 1 move / score / nodes |
| --- | --- | --- |
| 1 | f6h5 / cp 78 / 262 | f6h5 / cp 78 / 262 |
| 2 | f6e8 / cp 89 / 408 | f6e8 / cp 89 / 408 |
| 3 | f6h5 / cp -4 / 658 | f6h5 / cp -4 / 658 |
| 4 | f6h5 / cp 220 / 961 | f6h5 / cp 220 / 961 |
| 5 | f6h5 / cp 220 / 1,100 | f6h5 / cp 220 / 1,100 |
| 6 | f6h5 / cp 337 / 1,562 | f6h5 / cp 337 / 1,562 |
| 7 | f6h5 / cp 465 / 2,358 | f6h5 / cp 465 / 2,358 |
| 8 | f6h5 / cp 663 / 5,647 | f6h5 / cp 663 / 5,647 |
| 9 | f6h5 / cp 636 / 7,436 | f6h5 / cp 636 / 7,436 |
| 10 | f6h5 / cp 706 / 12,150 | f6h5 / cp 706 / 12,150 |
| 11 | f6h5 / cp 653 / 25,366 | f6h5 / cp 566 / 25,559 |
| 12 | f6h5 / cp 713 / 52,600 | f6h5 / cp 628 / 57,030 |
| 13 | f6h5 / cp 722 / 60,141 | g3g6 / mate 2 / 86,114 |
| 14 | f6h5 / cp 731 / 83,427 | g3g6 / mate 2 / 86,346 |
| 15 | f6h5 / cp 665 / 120,238 | g3g6 / mate 2 / 86,523 |
| 16 | f6h5 / cp 736 / 182,707 | g3g6 / mate 2 / 86,700 |
| 17 | f6h5 / cp 826 / 347,819 | g3g6 / mate 2 / 86,877 |
| 18 | f6h5 / cp 802 / 440,663 | g3g6 / mate 2 / 87,056 |
| 19 | f6h5 / cp 885 / 686,815 | g3g6 / mate 2 / 87,237 |
| 20 | f6h5 / cp 916 / 1,052,250 | g3g6 / mate 2 / 87,420 |

| Suite | Rows | Value 0 nodes | Value 1 nodes | Node ratio | Value 1 first three | Changed best moves |
| --- | --- | --- | --- | --- | --- | --- |
| O | 200 | 8,315,168 | 8,315,218 | 1.00000601 | 21812, 26844, 35173 | 0 |
| G | 353 | 17,611,204 | 17,848,355 | 1.01346592 | 31779, 46086, 84520 | 12 |

| Pre-treatment G group | Changed / positions | Changed move rate |
| --- | --- | --- |
| Job 4 NC0[4] > 0 | 12 / 81 | 14.8148% |
| Job 4 NC0[4] = 0 | 0 / 272 | 0.0000% |


## Part B — add quiet checks at the first direct null-child quiescence ply

`QsNullChecks` (default 0, range 0–1) extends the Part A tree. `NullMateGuard` and the floor both stay at zero. On a direct, nonpositive-depth null child, B keeps the usual capture and promotion stages and then yields quiet checking moves. It uses the ordinary legality, SEE, stand-pat and beta-cutoff rules. Descendants revert to normal quiescence and in-check nodes retain all evasions. A separate transposition-table key at that one special ply prevents bounds for capture-only quiescence from being reused as if the new moves had already been searched, and vice versa. The changed move set and its TT behavior are measured together. [Source references and UCI listing](astra5/job5/B/build)

<details><summary>Verbatim diff -ruN and patch -p1 -F0 outputs</summary>

```diff
diff -ruN before/include/forge/search.hpp after/include/forge/search.hpp
--- before/include/forge/search.hpp	2026-11-18 05:57:00.410530151 -0800
+++ after/include/forge/search.hpp	2026-11-18 05:57:00.462465080 -0800
@@ -275,6 +275,7 @@
 extern int ProbcutMargin;
 extern int QsFutilityMargin;
 extern int QsSeeMargin;
+extern int QsNullChecks;
 extern int AspirationDelta;
 extern int HistoryBonusQuadratic;
 extern int HistoryBonusLinear;
@@ -573,12 +574,12 @@
     }
 #endif
     int search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
-    int qsearch(Board& board, SearchStack* ss, int alpha, int beta);
+    int qsearch(Board& board, SearchStack* ss, int alpha, int beta, bool null_quiet_checks = false);
     // B4 CuckooRep: every child search goes through these; with CuckooRep off they are the plain calls.
     int search_child(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
-    int qsearch_child(Board& board, SearchStack* ss, int alpha, int beta);
+    int qsearch_child(Board& board, SearchStack* ss, int alpha, int beta, bool null_quiet_checks = false);
     [[gnu::cold]] int search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node);
-    [[gnu::cold]] int qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta);
+    [[gnu::cold]] int qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta, bool null_quiet_checks = false);
     // B4 HistRework: the twin's slot of a quiet move at the node of `ss` (its maps are threat_maps_[ss->ply]), the
     // change of a quiet move's score when part of its butterfly term comes from the twin, and the twin's update.
     [[nodiscard]] std::int16_t& rework_entry(const Board& board, const SearchStack* ss, Move move) const;
diff -ruN before/src/search.cpp after/src/search.cpp
--- before/src/search.cpp	2026-11-18 05:57:00.409029005 -0800
+++ after/src/search.cpp	2026-11-18 05:57:00.469210716 -0800
@@ -126,6 +126,7 @@
 int ProbcutMargin = 180;
 int QsFutilityMargin = 160;
 int QsSeeMargin = 40;
+int QsNullChecks = 0;
 int AspirationDelta = 18;
 int HistoryBonusQuadratic = 20;
 int HistoryBonusLinear = 48;
@@ -206,6 +207,7 @@
         {"SingularDepth", &SingularDepth, 2, 20},        {"SingularMargin", &SingularMargin, 0, 10},
         {"IirDepth", &IirDepth, 1, 20},                  {"ProbcutDepth", &ProbcutDepth, 1, 20},
         {"ProbcutMargin", &ProbcutMargin, 0, 1000},      {"QsFutilityMargin", &QsFutilityMargin, 0, 1000},
+        {"QsNullChecks", &QsNullChecks, 0, 1},
         {"QsSeeMargin", &QsSeeMargin, 0, 500},           {"AspirationDelta", &AspirationDelta, 4, 200},
         {"HistoryBonusQuadratic", &HistoryBonusQuadratic, 0, 100},
         {"HistoryBonusLinear", &HistoryBonusLinear, 0, 500},
@@ -683,7 +685,7 @@
         }
     }
 
-    [[nodiscard]] Move next(bool skip_quiets) {
+    [[nodiscard]] Move next(bool skip_quiets, bool null_quiet_checks = false) {
         while (true) {
             switch (stage_) {
             case MainTT:
@@ -762,6 +764,21 @@
                     if (move == tt_move_) continue;
                     return move;
                 }
+                if (!null_quiet_checks) return Move::none();
+                buffer_.clear();
+#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
+                board_.generate_pseudo_legal(buffer_, Board::GenMode::Quiets);
+#else
+                board_.generate_pseudo_legal(buffer_, false);
+#endif
+                index_ = 0;
+                stage_ = QsQuietChecks;
+                [[fallthrough]];
+            case QsQuietChecks:
+                while (index_ < buffer_.size()) {
+                    const Move move = buffer_[index_++];
+                    if (move.is_quiet() && board_.gives_check(move)) return move;
+                }
                 return Move::none();
 
             case EvasionGenerate:
@@ -789,7 +806,7 @@
 private:
     enum Stage : int {
         MainTT, GenerateCaptures, GoodCaptures, Killer1, Killer2, CounterMove, GenerateQuiets, QuietMoves, BadCaptures,
-        QsTT, QsGenerate, QsCaptures,
+        QsTT, QsGenerate, QsCaptures, QsQuietChecks,
         EvasionTT, EvasionGenerate, Evasions
     };
     struct Scored {
@@ -1616,7 +1633,7 @@
 // ---------------------------------------------------------------------------
 // Quiescence search
 
-int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta) {
+int Worker::qsearch(Board& board, SearchStack* ss, int alpha, int beta, bool null_quiet_checks) {
     const bool pv_node = beta - alpha > 1;
     const int ply = ss->ply;
     if (((local_nodes_ & 1023U) == 0 || node_limit_specified_) && should_stop()) aborted_ = true;
@@ -1640,10 +1657,14 @@
         if (alpha >= beta) return alpha;
     }
 
+    // The first null-child qsearch has additional legal continuations. Its bounds
+    // are reusable within that move set, but not interchangeable with normal bounds.
+    constexpr std::uint64_t NullQuietChecksKey = 0x93fd26bcab6b0f4dULL;
+    const auto tt_key = null_quiet_checks ? board.key() ^ NullQuietChecksKey : board.key();
 #if FORGE_SPD_TT_NOTLS
-    const TTProbe tt_probe = probe_tt(board.key());
+    const TTProbe tt_probe = probe_tt(tt_key);
 #else
-    const TTProbe tt_probe = shared_.tt.probe(board.key());
+    const TTProbe tt_probe = shared_.tt.probe(tt_key);
 #endif
     const bool tt_hit = tt_probe.hit;
     const TTEntry& tte = tt_probe.entry;
@@ -1679,9 +1700,9 @@
         best_score = eval;
         if (best_score >= beta) {
 #if FORGE_SPD_TT_NOTLS
-            if (!tt_hit) store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
+            if (!tt_hit) store_tt(tt_probe, tt_key, score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
 #else
-            if (!tt_hit) shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
+            if (!tt_hit) shared_.tt.store(tt_probe, tt_key, score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
 #endif
             return best_score;
         }
@@ -1697,7 +1718,7 @@
     Move best_move = Move::none();
     int move_count = 0;
     Move move;
-    while (!(move = picker.next(false)).is_none()) {
+    while (!(move = picker.next(false, null_quiet_checks)).is_none()) {
         if (!board.is_legal(move)) continue;
         ++move_count;
         if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {
@@ -1748,9 +1769,9 @@
 
     const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
 #if FORGE_SPD_TT_NOTLS
-    store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
+    store_tt(tt_probe, tt_key, score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
 #else
-    shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
+    shared_.tt.store(tt_probe, tt_key, score_to_tt(best_score, ply), in_check ? ValueNone : ss->raw_eval, best_move, 0, bound, tt_pv, board.halfmove_clock());
 #endif
     return best_score;
 }
@@ -1984,7 +2005,11 @@
             const int reduced_depth = depth - reduction;
             const int null_child_depth = tune::NullChildFloor > 0 ? std::max(reduced_depth, tune::NullChildFloor)
                                                                   : reduced_depth;
-            int null_score = -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
+            // A nonpositive depth normally dispatches directly to qsearch_child.
+            // Only the null probe opts in; recursive qsearch_child calls use false.
+            int null_score = tune::QsNullChecks && null_child_depth <= 0
+                ? -qsearch_child(board, ss + 1, -beta, -beta + 1, true)
+                : -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
             if (null_score >= beta &&
@@ -2423,9 +2448,9 @@
     return search(board, ss, depth, alpha, beta, cut_node);
 }
 
-int Worker::qsearch_child(Board& board, SearchStack* ss, int alpha, int beta) {
-    if (tune::CuckooRep) [[unlikely]] return qsearch_cuckoo(board, ss, alpha, beta);
-    return qsearch(board, ss, alpha, beta);
+int Worker::qsearch_child(Board& board, SearchStack* ss, int alpha, int beta, bool null_quiet_checks) {
+    if (tune::CuckooRep) [[unlikely]] return qsearch_cuckoo(board, ss, alpha, beta, null_quiet_checks);
+    return qsearch(board, ss, alpha, beta, null_quiet_checks);
 }
 
 int Worker::search_cuckoo(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
@@ -2440,13 +2465,13 @@
     return search(board, ss, depth, alpha, beta, cut_node);
 }
 
-int Worker::qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta) {
+int Worker::qsearch_cuckoo(Board& board, SearchStack* ss, int alpha, int beta, bool null_quiet_checks) {
     constexpr int DrawScore = 0;
     if (alpha < DrawScore && may_repeat(board) && board.upcoming_repetition(root_history_index_)) {
         if (beta <= DrawScore) return DrawScore;
-        return std::max(qsearch(board, ss, DrawScore, beta), DrawScore);
+        return std::max(qsearch(board, ss, DrawScore, beta, null_quiet_checks), DrawScore);
     }
-    return qsearch(board, ss, alpha, beta);
+    return qsearch(board, ss, alpha, beta, null_quiet_checks);
 }
 
 namespace {
```

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

</details>

B, QsNullChecks 0: all 20 P ladder depths, 200 O rows and 353 G rows matched job 4 floor 0. Each P TSV row matched its UCI transcript.

QsNullChecks 1 first reported g3g6 with a positive mate score at depth 13 (77,758 nodes).

| D | Value 0 move / score / nodes | Value 1 move / score / nodes |
| --- | --- | --- |
| 1 | f6h5 / cp 78 / 262 | f6h5 / cp 78 / 262 |
| 2 | f6e8 / cp 89 / 408 | f6e8 / cp 89 / 408 |
| 3 | f6h5 / cp -4 / 658 | f6h5 / cp -4 / 658 |
| 4 | f6h5 / cp 220 / 961 | f6h5 / cp 220 / 961 |
| 5 | f6h5 / cp 220 / 1,100 | f6h5 / cp 220 / 1,100 |
| 6 | f6h5 / cp 337 / 1,562 | f6h5 / cp 337 / 1,562 |
| 7 | f6h5 / cp 465 / 2,358 | f6h5 / cp 465 / 2,358 |
| 8 | f6h5 / cp 663 / 5,647 | f6h5 / cp 569 / 5,541 |
| 9 | f6h5 / cp 636 / 7,436 | f6h5 / cp 651 / 7,391 |
| 10 | f6h5 / cp 706 / 12,150 | f6h5 / cp 594 / 10,981 |
| 11 | f6h5 / cp 653 / 25,366 | f6h5 / cp 578 / 27,962 |
| 12 | f6h5 / cp 713 / 52,600 | f6h5 / cp 647 / 56,518 |
| 13 | f6h5 / cp 722 / 60,141 | g3g6 / mate 2 / 77,758 |
| 14 | f6h5 / cp 731 / 83,427 | g3g6 / mate 2 / 77,953 |
| 15 | f6h5 / cp 665 / 120,238 | g3g6 / mate 2 / 78,127 |
| 16 | f6h5 / cp 736 / 182,707 | g3g6 / mate 2 / 78,305 |
| 17 | f6h5 / cp 826 / 347,819 | g3g6 / mate 2 / 78,483 |
| 18 | f6h5 / cp 802 / 440,663 | g3g6 / mate 2 / 78,662 |
| 19 | f6h5 / cp 885 / 686,815 | g3g6 / mate 2 / 78,843 |
| 20 | f6h5 / cp 916 / 1,052,250 | g3g6 / mate 2 / 79,026 |

| Suite | Rows | Value 0 nodes | Value 1 nodes | Node ratio | Value 1 first three | Changed best moves |
| --- | --- | --- | --- | --- | --- | --- |
| O | 200 | 8,315,168 | 8,324,278 | 1.00109559 | 21904, 26930, 37398 | 15 |
| G | 353 | 17,611,204 | 17,824,520 | 1.01211252 | 31477, 46277, 104653 | 72 |

| Pre-treatment G group | Changed / positions | Changed move rate |
| --- | --- | --- |
| Job 4 NC0[4] > 0 | 22 / 81 | 27.1605% |
| Job 4 NC0[4] = 0 | 50 / 272 | 18.3824% |


## Prediction grades

Commit `9e94590` contained only `prediction.txt`. Both disabled arms had passed before the commit was pushed, and both enabled arms ran afterward. All eight outcomes fell inside their inclusive ranges. Two point forecasts were exact. [Frozen prediction](astra5/job5/prediction.txt)

### Part A

| Forecast | Point | Inclusive range | Actual | Exact | Within range |
| --- | --- | --- | --- | --- | --- |
| mate | 14 | 10 to 18 | 13 | no | yes |
| G_ratio | 1.005 | 0.99 to 1.03 | 1.01346592 | no | yes |
| flagged | 6 | 1 to 18 | 12 | no | yes |
| unflagged | 0 | 0 to 0 | 0 | yes | yes |

### Part B

| Forecast | Point | Inclusive range | Actual | Exact | Within range |
| --- | --- | --- | --- | --- | --- |
| mate | 13 | 8 to 18 | 13 | yes | yes |
| G_ratio | 1.06 | 0.99 to 1.17 | 1.01211252 | no | yes |
| flagged | 16 | 5 to 32 | 22 | no | yes |
| unflagged | 25 | 5 to 60 | 50 | no | yes |

## Part C — which part of HistRework hides the mate?

PC `HistRework 2` activates two components. The quiet-history component maintains threat maps and threat-indexed quiet-move history, blends that history into the quiet score, and updates it during search. The resulting score feeds ordering, history pruning and LMR. The correction component reads and learns an additional pawn-structure/non-pawn-material correction term. The split patch gives each component a level override. Both default to −1, which follows the existing `HistRework` option. The source inventory quotes the affected sites in the original PC tree. [Source inventory](astra5/job5/C/reading.txt) · [Split patch](astra5/job5/histrework_split.patch.txt)

| PC with split patch, S14 on P | First `g3g6` mate depth | Nodes there | Depth-20 result | Check |
|---|---:|---:|---|---|
| Both components at level 2 | None through 20 | — | `f6h5`, cp 836, 774,832 nodes | All 20 rows equal Job 4 B4 |
| Both components off | 16 | 240,516 | `g3g6`, mate 2, 241,262 nodes | All 20 rows equal S14 |
| Both follow HistRework 2 | None through 20 | — | `f6h5`, cp 836, 774,832 nodes | All 20 rows equal Job 4 B4 |
| Both follow HistRework 0 | 16 | 240,516 | `g3g6`, mate 2, 241,262 nodes | All 20 rows equal S14 |
| Quiet history alone, level 2 | None through 20 | — | `f6h5`, cp 814, 957,869 nodes | Isolated component |
| Correction alone, level 2 | 16 | 227,749 | `g3g6`, mate 2, 228,946 nodes | Isolated component |

The quiet-history component alone reproduced the miss on this S14 ladder. Correction alone preserved the depth-16 discovery. This separates the two components but leaves ordering, pruning and reduction effects within quiet history unresolved. [Raw ladders](astra5/job5/C/rows) · [120-row readback](astra5/job5/C/checks.txt)

## Answer — root move changes were concentrated in flagged positions

**The exact guard changed the chosen move in 12 of 81 flagged G positions (14.81%) and in zero of 272 unflagged positions.** Its node cost was 237,151 additional nodes on G (+1.35%) and 50 on O (+0.0006%). Expanded quiescence changed 22 of 81 flagged positions (27.16%) and 50 of 272 unflagged positions (18.38%). Its node cost was 213,316 on G (+1.21%) and 9,110 on O (+0.11%). Both fixed the proven mate on P at depth 13. These are node costs. Move generation, SEE and quiet-mate enumeration also take time, which this experiment did not measure.

## Facts

Both zero settings matched the prior move and node rows at every known-answer position and depth. The exact guard reused the original definition of a flagged cutoff. The first difference from baseline therefore requires an eligible event on the original path in these tested runs. The broader quiescence treatment can also affect quiet checks that do not give immediate mate, so moves can change outside the flagged group.

## Suspicions

Some of the G root changes may repair a tactical mistake, as both treatments do on the independently solved position P. No move-quality or mate oracle classified the changed G moves. The difference between the treatments’ move counts could reflect nonmating checks, altered TT bounds or search-order effects.

## What I did not do

I did not run games, time the two fixes, or classify the G move changes as improvements. I did not change the repository engine source. All engine changes are plain-text patches.

## What I am not sure about

Whether either treatment improves equal-time play and whether the flagged-position rates generalize to other suites remain open. The frequency of individually better moves cannot be inferred from the number of changed best moves.

## What this cannot see

```text
the PC's own net (this is the built-in evaluation), other settings, games. A tree size or a changed move is not strength; the PC decides any change with games.
```

## Pre-commit working tree and evidence files

```text
$ git status --short && ls -R forge-combo29/astra5/job5
 A forge-combo29/REPORT_astra5_job5.md
M  forge-combo29/astra5/job5/stamps.txt
forge-combo29/astra5/job5:
A
A-one.md
A-zero.md
B
B-one.md
B-zero.md
C
histrework_split.patch.txt
measure5.py
null_guard.patch.txt
prediction.txt
qs_null_checks.patch.txt
readback5.py
stamps.txt
step0
step0-pc.txt
step0-pca.txt

forge-combo29/astra5/job5/A:
build
one
zero

forge-combo29/astra5/job5/A/build:
floor-base-apply.txt
guard-build.txt
guard-source.txt
guard-uci.txt
null-guard-apply.txt

forge-combo29/astra5/job5/A/one:
G.tsv
G.tsv.meta
O.tsv
O.tsv.meta
P.meta
P.raw.txt
P.tsv
checks.txt

forge-combo29/astra5/job5/A/zero:
G.tsv
G.tsv.meta
O.tsv
O.tsv.meta
P.meta
P.raw.txt
P.tsv
checks.txt

forge-combo29/astra5/job5/B:
build
one
zero

forge-combo29/astra5/job5/B/build:
qs-build.txt
qs-patch-apply.txt
qs-source.txt
qs-uci.txt

forge-combo29/astra5/job5/B/one:
G.tsv
G.tsv.meta
O.tsv
O.tsv.meta
P.meta
P.raw.txt
P.tsv
checks.txt

forge-combo29/astra5/job5/B/zero:
G.tsv
G.tsv.meta
O.tsv
O.tsv.meta
P.meta
P.raw.txt
P.tsv
checks.txt

forge-combo29/astra5/job5/C:
build.txt
checks.txt
patch-apply.txt
provenance.txt
reading.txt
rows
run_split.py
uci.txt

forge-combo29/astra5/job5/C/rows:
both_off.meta
both_off.raw.txt
both_off.tsv
both_on.meta
both_on.raw.txt
both_on.tsv
correction_only.meta
correction_only.raw.txt
correction_only.tsv
follow_off.meta
follow_off.raw.txt
follow_off.tsv
follow_on.meta
follow_on.raw.txt
follow_on.tsv
quiet_only.meta
quiet_only.raw.txt
quiet_only.tsv

forge-combo29/astra5/job5/step0:
pc-PC20-bench-11.txt
pc-PC20-bench-13.txt
pc-S14-bench-11.txt
pc-S14-bench-13.txt
pc-no-setoption-bench-11.txt
pc-no-setoption-bench-13.txt
pc-no-setoption-go-perft-5.txt
pc-uci.txt
pca-PC20-bench-11.txt
pca-PC20-bench-13.txt
pca-no-setoption-bench-11.txt
pca-no-setoption-bench-13.txt
pca-no-setoption-go-perft-5.txt
pca-uci.txt
```
