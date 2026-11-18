# Astra5 job 7 — exact null-move guard on r15d and kF

## 1. Step 0

The three patches applied to the specified base in order with zero offsets, fuzz or rejects. All 29 r15d file hashes matched the supplied manifest. Running the preprocessor with the actual compiler flags confirmed `__AVX512F__=1`, `__AVX512BW__=1` and `__BMI2__=1`. The native Linux r15d executable had SHA-256 `9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671`. [Source identities, compiler and controls](astra5/job7/step0)

| Unmodified r15d, built-in evaluation | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
|---|---:|---:|---:|
| Defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

Every result in this table came from a fresh engine process. All O and G row checks below used PC20, Threads 1, Hash 16 and depth 12. Each position started after `ucinewgame` and a completed `isready` handshake. P used the same settings at each requested depth from 1 through 20.

## 2. Part A — standalone r15d patch

The option is `NullMateGuard`, a UCI spin with default 0 and values 0, 1 and 2. Value 0 uses r15d's original cutoff. At a null score at or above beta with reduced child depth at most zero, value 1 tests for a quiet mate using a private board copy. Value 2 tests the same condition on the search's still-active null child. It filters for checking quiet moves, verifies legality, and stops when the opponent has no legal reply. Each candidate move is undone before return. A positive test prevents the null cutoff. [Patch](astra5/job7/null_guard_r15d.patch.txt)

| Location in freshly patched r15d | Change |
|---|---|
| `include/forge/search.hpp:256` | Declare the guard option. |
| `src/search.cpp:105` | Set its default to zero. |
| `src/search.cpp:193` | Register the spin and its 0–2 range. |
| `src/search.cpp:1910` | Add the copied-board quiet-mate predicate used by value 1. |
| `src/search.cpp:1926` | Add the predicate that tests quiet checks on the existing null child for value 2. |
| `src/search.cpp:2153` | Preserve the original reduced depth in a local and use it for the null-child search. |
| `src/search.cpp:2155` | Evaluate value 2 before undoing the null move. |
| `src/search.cpp:2159` | Gate the cutoff on the value-2 result and the value-1 check after undo. |

The patched executable had SHA-256 `ca7ef24ddd1cc80216712646bf71beaa9eacf1ac2184e0e0f11d078b10ff4f2e`. A separate pristine r15d copy accepted the patch without offsets. The resulting source tree matched the design tree byte for byte. [Build and changed source locations](astra5/job7/A/build)

| Evaluation | Suite | Guard | Equal rows | Nodes | First three | Active net |
|---|---|---:|---:|---:|---|---|
| builtin | O | 0 | 200/200 | 8,315,168 | 21812, 26844, 35173 | — |
| builtin | O | 1 | 200/200 | 8,315,218 | 21812, 26844, 35173 | — |
| builtin | O | 2 | 200/200 | 8,315,218 | 21812, 26844, 35173 | — |
| builtin | G | 0 | 353/353 | 17,611,204 | 31779, 46086, 84457 | — |
| builtin | G | 1 | 353/353 | 17,848,355 | 31779, 46086, 84520 | — |
| builtin | G | 2 | 353/353 | 17,848,355 | 31779, 46086, 84520 | — |
| builtin | P | 1 | 20/20 | 809,404 | 262, 408, 658 | — |
| builtin | P | 2 | 20/20 | 809,404 | 262, 408, 658 | — |

All 1,699 built-in rows matched the archived job 5 results. Both P ladders first reported `g3g6` mate in two at depth 13 with 86,114 nodes. At depth 20 both used 87,420 nodes. The P table sums nodes over 20 independent searches. Ladder identity covers deterministic depth, score, mate flag, move, nodes and final PV. Elapsed time and NPS vary by run. [Built-in row sets and comparisons](astra5/job7/A)

<details><summary>Full r15d diff and fresh-application output</summary>

`diff -ruN r15d r15d-guard` exited 1 with the following output.

```diff
diff -ruN r15d/include/forge/search.hpp r15d-guard/include/forge/search.hpp
--- r15d/include/forge/search.hpp	2026-11-18 07:05:53.909378684 -0800
+++ r15d-guard/include/forge/search.hpp	2026-11-18 07:06:21.143408951 -0800
@@ -253,6 +253,7 @@
 extern int LmrNoisyDivisor;   // x0.01
 extern int NullMoveMinDepth;
 extern int NullMoveBase;
+extern int NullMateGuard;
 extern int NullMoveDepthDivisor;
 extern int NullMoveEvalDivisor;
 extern int RfpDepth;
diff -ruN r15d/src/search.cpp r15d-guard/src/search.cpp
--- r15d/src/search.cpp	2026-11-18 07:05:53.912838835 -0800
+++ r15d-guard/src/search.cpp	2026-11-18 07:06:21.144378073 -0800
@@ -102,6 +102,7 @@
 int LmrNoisyDivisor = 340;
 int NullMoveMinDepth = 3;
 int NullMoveBase = 3;
+int NullMateGuard = 0;
 int NullMoveDepthDivisor = 3;
 int NullMoveEvalDivisor = 200;
 int RfpDepth = 8;
@@ -189,6 +190,7 @@
         {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
+        {"NullMateGuard", &NullMateGuard, 0, 2},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -1903,6 +1905,43 @@
 }
 
 // ---------------------------------------------------------------------------
+namespace {
+// Reference test: rebuild the null child on a private board and enumerate legal moves.
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
+
+// The search already made the null move. Only quiet checks require a legality
+// test, and one legal reply suffices to disprove mate.
+bool has_quiet_mate(Board& null_child) {
+    MoveList candidates;
+#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
+    null_child.generate_pseudo_legal(candidates, Board::GenMode::Quiets);
+#else
+    null_child.generate_pseudo_legal(candidates, false);
+#endif
+    for (const Move move : candidates) {
+        if (!move.is_quiet() || !null_child.gives_check(move) || !null_child.is_legal(move)) continue;
+        Undo undo;
+        (void)null_child.make_move(move, undo);
+        const bool mate = null_child.in_check() && !null_child.has_legal_move();
+        null_child.unmake_move(move, undo);
+        if (mate) return true;
+    }
+    return false;
+}
+} // namespace
+
 // Main alpha-beta search
 
 int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
@@ -2111,10 +2150,14 @@
 #if FORGE_SEARCH_SPEED2
             shared_.tt.prefetch(board.key());
 #endif
-            int null_score = -search_child(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
+            const int null_child_depth = depth - reduction;
+            int null_score = -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
+            const bool fast_guard_veto = tune::NullMateGuard == 2 && !aborted_ && null_score >= beta &&
+                                         null_child_depth <= 0 && has_quiet_mate(board);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
-            if (null_score >= beta) {
+            if (null_score >= beta && !fast_guard_veto &&
+                !(tune::NullMateGuard == 1 && null_child_depth <= 0 && quiet_mate_after_null(board))) {
                 if (is_mate_score(null_score)) null_score = beta;
                 // Depth >= 14 always verifies, as before. Below that, a cutoff
                 // stands unless NullThreatVerify is on and a cheaper enemy piece
```

A separate pristine r15d copy accepted `patch -p1 -F0` (exit 0). The complete application output follows.

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

</details>

## 3. Part B — comparison with sol3 on net768

The deterministic network generator from sol3 produced a 9,463,528-byte file with SHA-256 `c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7`. The engine received `NNUEArchFile` followed by `NNUEArch=true`. Both fresh PC20 bench processes and every network row process logged the checksum `30ab43b4ba5db5f3` and `NNUE v3 active`. Bench 11 returned 882,074 nodes and bench 13 returned 4,275,906. [Bench transcripts and reference hashes](astra5/job7/B)

The independent comparator is sol3 job 15, revision `3f31930c6fe19462ae68c7f94acb6ea201a110f7`. Its guard values 0 and 1 supply the references. Our value 2 was checked against both sol3 value 1 and the observed r15d value-1 rows. The comparisons below check position order, FEN, node count and root move. [Sol3 reference rows](https://github.com/couns0538-sketch/dwqww/tree/3f31930c6fe19462ae68c7f94acb6ea201a110f7/forge-combo29/sol3/job15/N1)

| Evaluation | Suite | Guard | Equal rows | Nodes | First three | Active net |
|---|---|---:|---:|---:|---|---|
| net768 | G | 0 | 353/353 | 42,620,225 | 95007, 39469, 131900 | yes |
| net768 | G | 1 | 353/353 | 43,662,795 | 95007, 39472, 121540 | yes |
| net768 | G | 2 | 353/353 | 43,662,795 | 95007, 39472, 121540 | yes |
| net768 | O | 0 | 200/200 | 32,504,791 | 37409, 213822, 139142 | yes |
| net768 | O | 1 | 200/200 | 33,025,665 | 56140, 212688, 144373 | yes |
| net768 | O | 2 | 200/200 | 33,025,665 | 56140, 212688, 144373 | yes |

All 1,659 rows agreed with sol3. Comparing the two enabled r15d modes directly gave zero differences across all 553 O and G positions. The node sums in the table count search work at fixed depth. [Independent row readback](astra5/job7/B/comparison.md)

## 4. Frozen prediction

The prediction was the only file in commit `7bd3a69917206fe9a5a6937bb33e9dae1f73795f`, pushed after the built-in row checks and before the first net768 engine run. [Frozen prediction](astra5/job7/prediction.txt)

| Prediction | Forecast | Observed | Grade |
|---|---|---|---|
| net768 G, guard 0, all rows equal sol3 | Yes | Yes | Hit |
| net768 G, guard 1, all rows equal sol3 | Yes | Yes | Hit |
| net768 G, guard 2, all rows equal sol3 | Yes | Yes | Hit |
| net768 O, guard 0, all rows equal sol3 | Yes | Yes | Hit |
| net768 O, guard 1, all rows equal sol3 | Yes | Yes | Hit |
| net768 O, guard 2, all rows equal sol3 | Yes | Yes | Hit |
| Original patch applies unchanged on kF with zero offsets or rejects | No | No | Hit |
| All requested kF rows equal r15d | Yes | Yes | Hit |

All eight forecasts matched their declared outcomes.

## 5. Part C — kF portability

After Part B, the nine-file carbon2 speed patch with SHA-256 `3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30` applied to fresh r15d. Unmodified kF reproduced the five Step 0 controls with the built-in evaluation. Defaults returned 312,866 and 862,329 at bench 11 and 13, and 4,865,609 at perft 5. PC20 returned 278,024 and 587,276 at bench 11 and 13. [Build evidence and controls](astra5/job7/C)

The r15d patch returned exit 0 on kF, with a +81-line offset in the header and +492-line offsets in two search hunks. Those offsets failed the declared clean-application criterion. The kF diff was regenerated and applied to a separate fresh kF tree with zero offsets. All 46 added and two removed source lines were identical in the two patches. Only file headers and hunk coordinates changed. The kF executable had SHA-256 `c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb` before the guard and `78580ff9a25c4099eb842f2b88b3d69bdffd5a8a9cd4a31dab93fb8d4b013675` after it. [Clean kF patch](astra5/job7/null_guard_kF.patch.txt)

<details><summary>Original r15d patch application on kF and final fresh application</summary>

`patch -p1 -F0` on kF using the original r15d patch produced the following output.

```text
patching file include/forge/search.hpp
Hunk #1 succeeded at 334 (offset 81 lines).
patching file src/search.cpp
Hunk #3 succeeded at 2397 (offset 492 lines).
Hunk #4 succeeded at 2642 (offset 492 lines).
patch exit 0
```

The full kF `diff -ruN` output follows.

```diff
diff -ruN kF/include/forge/search.hpp kF-guard/include/forge/search.hpp
--- kF/include/forge/search.hpp	2026-11-18 07:11:30.416479202 -0800
+++ kF-guard/include/forge/search.hpp	2026-11-18 07:11:40.707300421 -0800
@@ -334,6 +334,7 @@
 extern int LmrNoisyDivisor;   // x0.01
 extern int NullMoveMinDepth;
 extern int NullMoveBase;
+extern int NullMateGuard;
 extern int NullMoveDepthDivisor;
 extern int NullMoveEvalDivisor;
 extern int RfpDepth;
diff -ruN kF/src/search.cpp kF-guard/src/search.cpp
--- kF/src/search.cpp	2026-11-18 07:11:30.417540480 -0800
+++ kF-guard/src/search.cpp	2026-11-18 07:11:40.707802596 -0800
@@ -102,6 +102,7 @@
 int LmrNoisyDivisor = 340;
 int NullMoveMinDepth = 3;
 int NullMoveBase = 3;
+int NullMateGuard = 0;
 int NullMoveDepthDivisor = 3;
 int NullMoveEvalDivisor = 200;
 int RfpDepth = 8;
@@ -189,6 +190,7 @@
         {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
+        {"NullMateGuard", &NullMateGuard, 0, 2},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -2395,6 +2397,43 @@
 }
 
 // ---------------------------------------------------------------------------
+namespace {
+// Reference test: rebuild the null child on a private board and enumerate legal moves.
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
+
+// The search already made the null move. Only quiet checks require a legality
+// test, and one legal reply suffices to disprove mate.
+bool has_quiet_mate(Board& null_child) {
+    MoveList candidates;
+#if FORGE_SPD_NO_ZERO_MOVELISTS >= 2
+    null_child.generate_pseudo_legal(candidates, Board::GenMode::Quiets);
+#else
+    null_child.generate_pseudo_legal(candidates, false);
+#endif
+    for (const Move move : candidates) {
+        if (!move.is_quiet() || !null_child.gives_check(move) || !null_child.is_legal(move)) continue;
+        Undo undo;
+        (void)null_child.make_move(move, undo);
+        const bool mate = null_child.in_check() && !null_child.has_legal_move();
+        null_child.unmake_move(move, undo);
+        if (mate) return true;
+    }
+    return false;
+}
+} // namespace
+
 // Main alpha-beta search
 
 int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node) {
@@ -2603,10 +2642,14 @@
 #if FORGE_SEARCH_SPEED2
             shared_.tt.prefetch(board.key());
 #endif
-            int null_score = -search_child(board, ss + 1, depth - reduction, -beta, -beta + 1, !cut_node);
+            const int null_child_depth = depth - reduction;
+            int null_score = -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
+            const bool fast_guard_veto = tune::NullMateGuard == 2 && !aborted_ && null_score >= beta &&
+                                         null_child_depth <= 0 && has_quiet_mate(board);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
-            if (null_score >= beta) {
+            if (null_score >= beta && !fast_guard_veto &&
+                !(tune::NullMateGuard == 1 && null_child_depth <= 0 && quiet_mate_after_null(board))) {
                 if (is_mate_score(null_score)) null_score = beta;
                 // Depth >= 14 always verifies, as before. Below that, a cutoff
                 // stands unless NullThreatVerify is on and a cheaper enemy piece
```

The final application to another fresh kF returned the following output.

```text
patching file include/forge/search.hpp
patching file src/search.cpp
```

</details>

| Evaluation | Suite | Guard | Equal rows | Nodes | First three | Active net |
|---|---|---:|---:|---:|---|---|
| builtin | O | 0 | 200/200 | 8,315,168 | 21812, 26844, 35173 | — |
| builtin | O | 1 | 200/200 | 8,315,218 | 21812, 26844, 35173 | — |
| builtin | O | 2 | 200/200 | 8,315,218 | 21812, 26844, 35173 | — |
| builtin | G | 0 | 353/353 | 17,611,204 | 31779, 46086, 84457 | — |
| builtin | G | 1 | 353/353 | 17,848,355 | 31779, 46086, 84520 | — |
| builtin | G | 2 | 353/353 | 17,848,355 | 31779, 46086, 84520 | — |
| builtin | P | 1 | 20/20 | 809,404 | 262, 408, 658 | — |
| builtin | P | 2 | 20/20 | 809,404 | 262, 408, 658 | — |
| net768 | G | 0 | 353/353 | 42,620,225 | 95007, 39469, 131900 | yes |
| net768 | G | 1 | 353/353 | 43,662,795 | 95007, 39472, 121540 | yes |
| net768 | G | 2 | 353/353 | 43,662,795 | 95007, 39472, 121540 | yes |
| net768 | O | 0 | 200/200 | 32,504,791 | 37409, 213822, 139142 | yes |
| net768 | O | 1 | 200/200 | 33,025,665 | 56140, 212688, 144373 | yes |
| net768 | O | 2 | 200/200 | 33,025,665 | 56140, 212688, 144373 | yes |

The comparison includes every built-in O/G value and both P ladders, plus both O and G under net768 at all three values. All 3,358 kF rows agreed with the corresponding observed r15d rows. [Comparisons and run transcripts](astra5/job7/C)

## Facts

On r15d and kF, disabling the guard matched the reference decisions. The copied-board test and the live-child test agreed on every measured root result. All network row logs confirmed the active synthetic evaluation and its expected checksum.

## Suspicions

The two enabled modes agree because each looks for the same legal quiet mate at an eligible null cutoff. Equal root rows alone leave open whether both tests made the same decision at every internal node.

## What I did not do

This job checked decisions. It included neither a timing comparison nor a playing-strength match.

**What this cannot see**, in the job’s words

> the PC's own net, its compiler (clang with a profile on Windows) and processor, other depths, games. Whether the guard plays better is a question for games, not for rows.

## What I am not sure about

The independent implementation and the two engine trees agree on the sampled positions. They could still share an error. Their agreement does not establish how often the guard selects a better move in games.

## Pre-commit inventory

`git status --short` followed by `ls -R forge-combo29/astra5/job7` produced the following output.

```text
A  forge-combo29/REPORT_astra5_job7.md
M  forge-combo29/astra5/job7/stamps.txt
forge-combo29/astra5/job7:
A
B
C
null_guard_kF.patch.txt
null_guard_r15d.patch.txt
prediction.txt
rows.py
stamps.txt
step0

forge-combo29/astra5/job7/A:
G
O
P
build
comparison.md

forge-combo29/astra5/job7/A/G:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/A/G/Guard0:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/G/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/G/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/O:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/A/O/Guard0:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/O/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/O/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/P:
Guard1
Guard2

forge-combo29/astra5/job7/A/P/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/P/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/A/build:
build.txt
changed-places.txt
hashes.txt
patch-apply.txt

forge-combo29/astra5/job7/B:
G
O
bench11.log
bench13.log
comparison.md
provenance.txt

forge-combo29/astra5/job7/B/G:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/B/G/Guard0:
checks.txt
differences.tsv
driver.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/B/G/Guard1:
checks.txt
differences.tsv
driver.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/B/G/Guard2:
checks.txt
differences.tsv
driver.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/B/O:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/B/O/Guard0:
checks.txt
differences.tsv
driver.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/B/O/Guard1:
checks.txt
differences.tsv
driver.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/B/O/Guard2:
checks.txt
differences.tsv
driver.txt
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C:
applied-guard.sha256.txt
build-guard.txt
build-plain.txt
builtin
comparison.md
executables.sha256.txt
final-apply.txt
kF-source.sha256.txt
net768
patch-decision.txt
plain-control
port-readback.txt
r15d-guard-on-kF.txt
readback.tsv
reapply-tree-compare.txt
row-exits.tsv
stack-apply.txt
stack-sha256.txt

forge-combo29/astra5/job7/C/builtin:
G
O
P

forge-combo29/astra5/job7/C/builtin/G:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/C/builtin/G/Guard0:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/G/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/G/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/O:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/C/builtin/O/Guard0:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/O/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/O/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/P:
Guard1
Guard2

forge-combo29/astra5/job7/C/builtin/P/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/builtin/P/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/net768:
G
O

forge-combo29/astra5/job7/C/net768/G:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/C/net768/G/Guard0:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/net768/G/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/net768/G/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/net768/O:
Guard0
Guard1
Guard2

forge-combo29/astra5/job7/C/net768/O/Guard0:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/net768/O/Guard1:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/net768/O/Guard2:
checks.txt
differences.tsv
rows.tsv
run.log
settings.txt

forge-combo29/astra5/job7/C/plain-control:
PC20-bench-11.txt
PC20-bench-13.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
gates.txt

forge-combo29/astra5/job7/step0:
PC20-bench-11.txt
PC20-bench-13.txt
build.txt
defaults-bench-11.txt
defaults-bench-13.txt
defaults-go-perft-5.txt
defines.txt
gates.txt
patch-application.txt
patches.sha256.txt
provenance.txt
r15d-check.txt
r15d.sha256.txt
```
