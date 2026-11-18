# sol3 — Job 13 mate-in-two and shallow null cutoffs

**Step 0 passed.** kF SHA-256 `340f78f4e4834a5bf1e6dc2d73eca3caa62b7a45d05011b5c1c092ace6e5e5ea` and net768 matched Job 12. The three default pins were bench 11 = 312866, bench 13 = 862329 and startpos perft 5 = 4865609. PC20 with net768 gave bench 11 = 882074 and bench 13 = 4275906. PC20 with embedded evaluation gave **278024 and 587276**, equal to the helpers' PC reference pair. [Hash and pin readback](sol3/job13/stage0/pins.txt) · [PC20 embedded raw](sol3/job13/stage0/pc20_builtin.stdout.txt) · [PC20 net768 raw](sol3/job13/stage0/pc20_net768.stdout.txt)

**Prediction grade.** A1 did not find the mate by depth 20, as forecast. A2 found it at 15, within the forecast range of 12–20. B1 and B2 both found it at 7, earlier than my forecast ranges of 12–20 and 8–18. The synthetic net changed the search enough to find the mate even at NullMoveBase 5. The prediction was published alone at `a5e4f634ef5ac628e370d4ed9cf5e10199e6f9f9`. [Prediction](sol3/job13/prediction.txt) · [Checkpoints](sol3/job13/stamps.txt)

### Part A kF with embedded evaluation

The ladder used PC20, Threads 1, Hash 16 MiB, MultiPV 1 and one new-game/ready barrier before each `go depth`. P is the supplied bench position. Independent python-chess enumeration found 59 legal root moves, zero mate-in-one moves and only `g3g6` forcing mate in two. Of Black's 34 replies, `f7g6` requires `e5g6#` and `e6f5` requires `e5f7#`. The other 32 permit `g6h7#`. If Black passes after `g3g6`, `g6h7` is the only quiet mate. [P and full reply enumeration](sol3/job13/references/P_mate_tree.txt) · [Fixed-depth runner](sol3/job13/fixed_depth.py)

A1 matched all 20 rows from Astra5 Job 3 on requested depth, reported depth, nodes, bestmove and score. At depth 2 the stored reference and kF both play `f6e8`. The other 19 rows play `f6h5`. A2 changes only NullMoveBase from 5 to 3 after PC20 and finds `g3g6 mate 2` on every rung from 15 to 20. [Astra5 raw ladder](sol3/job13/references/PC20.raw.txt) · [A1 comparison](sol3/job13/A1/reference_comparison.json) · [A2 raw rows](sol3/job13/A2/rows.tsv)

| Requested depth | Astra5 nodes | kF nodes | Both bestmove | Both score |
| ---: | ---: | ---: | --- | --- |
| 1 | 262 | 262 | `f6h5` | cp 78 |
| 2 | 408 | 408 | `f6e8` | cp 89 |
| 3 | 658 | 658 | `f6h5` | cp -4 |
| 4 | 961 | 961 | `f6h5` | cp 220 |
| 5 | 1100 | 1100 | `f6h5` | cp 220 |
| 6 | 1562 | 1562 | `f6h5` | cp 337 |
| 7 | 2358 | 2358 | `f6h5` | cp 465 |
| 8 | 5647 | 5647 | `f6h5` | cp 663 |
| 9 | 7436 | 7436 | `f6h5` | cp 636 |
| 10 | 12150 | 12150 | `f6h5` | cp 706 |
| 11 | 25366 | 25366 | `f6h5` | cp 653 |
| 12 | 52600 | 52600 | `f6h5` | cp 713 |
| 13 | 60141 | 60141 | `f6h5` | cp 722 |
| 14 | 83427 | 83427 | `f6h5` | cp 731 |
| 15 | 120238 | 120238 | `f6h5` | cp 665 |
| 16 | 182707 | 182707 | `f6h5` | cp 736 |
| 17 | 347819 | 347819 | `f6h5` | cp 826 |
| 18 | 440663 | 440663 | `f6h5` | cp 802 |
| 19 | 686815 | 686815 | `f6h5` | cp 885 |
| 20 | 1052250 | 1052250 | `f6h5` | cp 916 |

### Part B kF with net768

The runs used the same fixture, limits, reset and options as Part A. Both show the engine's active network line with checksum `30ab43b4ba5db5f3`. The two net runs already return `g3g6 mate 2` at depth 7 and keep it through depth 20. [B1 raw UCI](sol3/job13/B1/engine.stdout.txt) · [B2 raw UCI](sol3/job13/B2/engine.stdout.txt)

| Ladder | Evaluation | NullMoveBase | First requested depth with g3g6 and mate | Depth 20 move and score | Depth 20 nodes |
| --- | --- | ---: | ---: | --- | ---: |
| [A1](sol3/job13/A1/rows.tsv) | Embedded | 5 | Not by 20 | `f6h5`, cp 916 | 1052250 |
| [A2](sol3/job13/A2/rows.tsv) | Embedded | 3 | 15 | `g3g6`, mate 2 | 221469 |
| [B1](sol3/job13/B1/rows.tsv) | net768 | 5 | 7 | `g3g6`, mate 2 | 7135 |
| [B2](sol3/job13/B2/rows.tsv) | net768 | 3 | 7 | `g3g6`, mate 2 | 7136 |

B1 and B2 differ by one node on the mate rungs from 7 through 20. At the first mate rung, B1 used 4845 nodes and B2 used 4846. The first mate depth and root move stayed the same. [B1 rows](sol3/job13/B1/rows.tsv) · [B2 rows](sol3/job13/B2/rows.tsv)

### Part C independent NC0 counter

I generated the counter as a literal recursive diff against a clean kF tree, then applied it to another clean copy with `patch -p1 -F0` and no fuzz, offset or rejects. The two instrumented scratch trees were byte-identical. The counter records one line after each `bestmove`. For an actual shallow null cutoff, it recreates the null position on a private board, enumerates legal noncapture and nonpromotion moves, and checks each resulting checking position for legal replies. It counts the cutoff once when any quiet move mates. [Patch](sol3/job13/null_count.patch.txt) · [Diff command](sol3/job13/C0/diff_receipt.txt) · [Clean application](sol3/job13/C0/patch_apply.txt) · [Build](sol3/job13/C0/build_nc.txt)

The counted build SHA-256 is `c5a1417f5b648d7865a298cff3cdce9f53d123819ea494fd048d0ac55fe7a521`. On P, all 16 counted rows per evaluator matched the plain kF's nodes and move, using PC20 and NullMoveBase 5. At depth 16 embedded evaluation recorded `NC0 6204 5570 3846 3612 52`, meeting the positive-control requirement. net768 recorded `NC0 35 35 14 14 2` at depth 16. [Embedded identity](sol3/job13/C0/P_builtin/identity.json) · [Embedded gate](sol3/job13/C0/P_builtin/depth16_gate.txt) · [net768 identity](sol3/job13/C0/P_net768/identity.json) · [net768 counters](sol3/job13/C0/P_net768/verified_raw.json)

G's 353 six-field positions came from kimi5 at `5db05e095d5e81622eb0de13eb8a738a0ae1d22a`, with SHA-256 `af3aefd80fcea207b215e95560f5921aa7a3bb9186d4cdfadf2e567207b5c54d`. Both G arms used PC20, Threads 1, Hash 16 MiB, MultiPV 1, `ucinewgame` and `isready` before every position, and `go depth 12`. Counted and plain builds agreed on nodes and bestmove at all 353 positions in both evaluators. C1 also matched all 353 position, node and move records of Astra5 Job 1 PCA. Its node sum was 17611204 and its first three counts were 31779, 46086 and 84457. [G fixture and provenance](sol3/job13/references/source.txt) · [C1 Astra5 Job 1 comparison](sol3/job13/C1/reference_comparison.json) · [C1 counted identity](sol3/job13/C1/identity.json) · [C2 counted identity](sol3/job13/C2/identity.json)

I opened Astra5 Job 4 only after both of my G runs were pushed. Their matching embedded `G_F0` arm agreed with ours on all five counter values, nodes and bestmove at every one of the 353 positions. The P depth-16 vector matched too. [Published own head before opening](sol3/job13/astra5_job4/pre_astra_own_remote.txt) · [Astra5 summary](sol3/job13/astra5_job4/summary.txt) · [Independent row comparison](sol3/job13/astra5_job4/readback.json)

Each counter entry below is the total followed by the rate per 1000 nodes. The raw summing program independently re-parsed all 353 `NC0` lines per local G arm and checked attachment to the preceding bestmove. [Summing program](sol3/job13/C0/verify_counters_raw.py) · [C1 raw totals](sol3/job13/C1/counted/sums.json) · [C2 raw totals](sol3/job13/C2/counted/sums.json)

| Counter | C1 kF embedded | Astra5 G_F0 embedded | C2 kF net768 |
| --- | ---: | ---: | ---: |
| NC0 lines | 353 | 353 | 353 |
| Last-iteration nodes | 17611204 | 17611204 | 42620225 |
| [0] Null searches started | 357628 (20.306846) | 357628 (20.306846) | 525990 (12.341324) |
| [1] Starts with child depth ≤0 | 325285 (18.470344) | 325285 (18.470344) | 495511 (11.626194) |
| [2] Actual null cutoffs | 244577 (13.887580) | 244577 (13.887580) | 264362 (6.202736) |
| [3] Cutoffs with child depth ≤0 | 233592 (13.263829) | 233592 (13.263829) | 256034 (6.007336) |
| [4] Shallow cutoffs with quiet mate | 513 (0.029129) | 513 (0.029129) | 1453 (0.034092) |
| G positions with at least one [4] | 81/353 | 81/353 | 189/353 |

### Answer

The pinned r15d source with Carbon2’s consolidated pieces, built here as kF, reproduced Astra5's PC20 built-in ladder on P. NullMoveBase 3 alone brought the forced mate into the embedded search at depth 15. With net768, the mate already appeared at depth 7 at base 5 and still did so at base 3. At depth 12 on G, [4] counted 513 events on 81 positions with embedded evaluation and 1453 events on 189 positions with net768. [Depth ladders](sol3/job13/A1/rows.tsv) · [Event totals and position counts](sol3/job13/astra5_job4/readback.json)

## Facts

- I used CMake Release, GCC 14.2.0 and Debian libstdc++ from GCC 14.2.0-19. Every reported counted result used the same fixed depth and options as its plain comparison. [Compiler and build](sol3/job13/C0/build_nc.txt) · [C1 command](sol3/job13/C1/counted/run.meta) · [C2 command](sol3/job13/C2/counted/run.meta)
- The C1 comparison in fixture order against Astra5 stays exact both before the counter and after attaching all five independent counter fields. [Job 1 comparison](sol3/job13/C1/reference_comparison.json) · [Job 4 comparison](sol3/job13/astra5_job4/readback.json)

## Suspicions

The two-ply reduction change can put the reported depth-11 null child back into ordinary search, where the quiet `g6h7` is eligible. The controlled root result supports that explanation for the embedded run. The evaluator change also changes which branches get searched and the denominator for the event rate.

## What I did not do

I ran neither games nor a performance test. The instrumented build stayed in the scratch workspace.

## What I am not sure about

The count of 52 on P combines all shallow cutoffs in the depth-16 tree. Identifying the particular cutoff that determines the missed root mate would require matching its position and window to a node-level trace. These first-mate depths use a reset before every search, so a search that retains prior game state could reach the move at a different rung.

## Limits of this check

The PC's own net (net768 is not it), the PC's compiler (clang on Windows), games, other depths. A count is not strength. [UTC step record](sol3/job13/stamps.txt)

<details>
<summary>Literal diff and patch application output</summary>

```diff
diff -ruN base/include/forge/search.hpp tree/include/forge/search.hpp
--- base/include/forge/search.hpp	2026-11-18 05:27:32.636359833 -0800
+++ tree/include/forge/search.hpp	2026-11-18 05:50:28.994453077 -0800
@@ -70,6 +70,7 @@
     std::vector<Move> pv;
     // A searchmoves intersection with no legal moves is not checkmate or stalemate.
     bool restricted_root_empty = false;
+    std::array<std::uint64_t, 5> null_counts{};
 };
 
 constexpr int MaxPly = 128;
@@ -637,6 +638,9 @@
     bool root_prev_best_done_ = false;     // that move was searched to its end in the root search now running
     std::uint64_t null_tries_ = 0;
     std::uint64_t null_cutoffs_ = 0;
+    std::uint64_t null_shallow_tries_ = 0;
+    std::uint64_t null_shallow_cutoffs_ = 0;
+    std::uint64_t null_quiet_mates_ = 0;
     // True only inside a NullThreatVerify confirmation, so that reduced search
     // does not use null moves. Stays false for the whole default search.
     bool null_blocked_ = false;
@@ -731,6 +735,7 @@
 #endif
     void record_move(SearchStack* ss, const Board& board, const Move& move);
     void record_null_move(SearchStack* ss);
+    void count_null_cutoff(const Board& board, int child_depth);
     [[gnu::always_inline]] bool check_node_or_periodic_stop() {
         if (fast_single_node_stop_) {
             if (local_nodes_ < node_limit_ && (local_nodes_ & 1023U) != 0) {
diff -ruN base/src/search.cpp tree/src/search.cpp
--- base/src/search.cpp	2026-11-18 05:27:32.638032655 -0800
+++ tree/src/search.cpp	2026-11-18 05:50:29.798414298 -0800
@@ -1883,6 +1883,28 @@
     child->runtime_psqt.valid = false;
 }
 
+void Worker::count_null_cutoff(const Board& board, int child_depth) {
+    ++null_cutoffs_;
+    if (child_depth > 0) return;
+    ++null_shallow_cutoffs_;
+
+    // The actual null search has been undone. Test its position on a copy.
+    Board null_child = board;
+    NullUndo null_undo;
+    null_child.make_null_move(null_undo);
+    for (const Move move : null_child.legal_moves()) {
+        if (move.is_capture() || move.is_promotion()) continue;
+        Undo undo;
+        (void)null_child.make_move(move, undo);
+        const bool mate = null_child.in_check() && null_child.legal_moves().empty();
+        null_child.unmake_move(move, undo);
+        if (mate) {
+            ++null_quiet_mates_;
+            return;
+        }
+    }
+}
+
 
 int Worker::corrected_eval(const Board& board, int raw_eval, const SearchStack* ss) const {
     // Keep the recognized ending score exact: correction history must not tilt a draw or the corner drive.
@@ -2589,9 +2611,9 @@
             board.has_non_pawn_material(board.side_to_move()) &&
             !(tt_hit && tt_bound == BoundUpper && tt_score < beta) &&
             !(tune::NullSeeVeto && null_see_veto_threat(board))) {
-            ++null_tries_;
             const int reduction = tune::NullMoveBase + depth / tune::NullMoveDepthDivisor +
                                   std::min((eval - beta) / tune::NullMoveEvalDivisor, 3);
+            const int child_depth = depth - reduction;
             ss->current_move = Move::none();
             ss->moved_piece = Empty;
             ss->continuation = &(*continuation_history_)[Empty][0];
@@ -2603,7 +2625,9 @@
 #if FORGE_SEARCH_SPEED2
             shared_.tt.prefetch(board.key());
 #endif
-            int null_score = -search_child(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
+            ++null_tries_;
+            if (child_depth <= 0) ++null_shallow_tries_;
+            int null_score = -search_child(board, ss + 1, child_depth, -beta, -beta + 1, !cut_node);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
             if (null_score >= beta) {
@@ -2615,7 +2639,7 @@
                 const bool threat_gate =
                     depth < 14 && tune::NullThreatVerify && cheaper_enemy_attacks_dearer(board);
                 if (depth < 14 && !threat_gate) {
-                    ++null_cutoffs_;
+                    count_null_cutoff(board, child_depth);
                     return null_score;
                 }
                 // Same reduced depth as the high-depth verification. A threat
@@ -2623,13 +2647,13 @@
                 const bool saved_block = null_blocked_;
                 if (threat_gate) null_blocked_ = true;
                 ss->null_move_allowed = false;
-                const int verification = search_child(board, ss, depth - reduction, beta - 1, beta, false);
+                const int verification = search_child(board, ss, child_depth, beta - 1, beta, false);
                 null_blocked_ = saved_block;
                 ss->double_extensions = inherited_double_extensions;
                 ss->null_move_allowed = true;
                 if (aborted_) return 0;
                 if (verification >= beta) {
-                    ++null_cutoffs_;
+                    count_null_cutoff(board, child_depth);
                     return null_score;
                 }
             }
@@ -3129,6 +3153,9 @@
     pondering_ = limits.ponder;
     null_tries_ = 0;
     null_cutoffs_ = 0;
+    null_shallow_tries_ = 0;
+    null_shallow_cutoffs_ = 0;
+    null_quiet_mates_ = 0;
     null_blocked_ = false;
     root_moves_ = limits.search_moves;
     root_restricted_ = limits.search_moves_specified;
@@ -3859,6 +3886,9 @@
     shared_.stop.store(true, std::memory_order_relaxed);
     for (auto& helper : helpers) helper.join();
     shared_.stop.store(external_stop, std::memory_order_relaxed);
+    const Worker& worker = *workers_.front();
+    result.null_counts = {worker.null_tries_, worker.null_shallow_tries_, worker.null_cutoffs_,
+                          worker.null_shallow_cutoffs_, worker.null_quiet_mates_};
     return result;
 }
 
diff -ruN base/src/uci.cpp tree/src/uci.cpp
--- base/src/uci.cpp	2026-11-18 05:27:32.639155943 -0800
+++ tree/src/uci.cpp	2026-11-18 05:50:30.450382850 -0800
@@ -447,6 +447,9 @@
             {
                 const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                 std::cout << "bestmove " << best << prediction << std::endl;
+                std::cout << "NC0";
+                for (const std::uint64_t count : result.null_counts) std::cout << ' ' << count;
+                std::cout << std::endl;
             }
             {
                 const std::lock_guard<std::mutex> lock(stop_mutex);
```

```text
patching file include/forge/search.hpp
patching file src/search.cpp
patching file src/uci.cpp
```

</details>
