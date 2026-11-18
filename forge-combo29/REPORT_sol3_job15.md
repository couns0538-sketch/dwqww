# sol3 — Job 15 exact null-mate guard

**Step 0 passed.** The retained plain kF and counted kF hashes matched Job 14. Both fresh default bench pairs were 312866 and 862329, with startpos perft 5 equal to 4865609. With PC20 and embedded evaluation both returned 278024 and 587276. [Hash gate](sol3/job15/stage0/input_hashes.txt) · [Plain pins](sol3/job15/stage0/kF/pins.txt) · [Counted pins](sol3/job15/stage0/counted/pins.txt)

### Independent guard and K1–K5

I froze my patch before reading any Astra5 implementation. `NullMateGuard` is a spin from 0 to 1 with default 0. After a null-search beta result with child depth at most zero, Guard1 checks for a legal noncapture, nonpromotion move that gives mate on a private copy of the null board. At a match it continues the ordinary search. The accepted-cutoff counters remain at both original return sites. The checker in the guard and the counter uses the same board-copy predicate. The independently edited and freshly patched scratch trees matched byte for byte. [Patch](sol3/job15/null_mate_guard.patch.txt) · [Patch application](sol3/job15/guard/patch_apply.txt) · [Option check](sol3/job15/guard/option_gate.txt) · [Build](sol3/job15/guard/build.txt)

All O/G runs used PC20, Threads 1, Hash 16 MiB, MultiPV 1, the exact Job 14 fixture order and `go depth 12` with a new-game/ready reset before each position. O kept the reference's `0 1` clocks. N1 and N2 use net768, a generated, untrained net, with the active checksum `30ab43b4ba5db5f3` recorded in each raw log. [Fixture and reference provenance](sol3/job15/references/source.txt) · [Run driver](sol3/job15/fixed_depth.py)

- K1 Guard0 matched all 200 O and 353 G Job 14 rows, including nodes, move, score and all five counter values. [O gate](sol3/job15/K1/O/known_gate.txt) · [G gate](sol3/job15/K1/G/known_gate.txt)
- K2 Guard1 matched Astra5's O and G reference nodes and bestmove position by position. O gained 50 nodes with no root-move change. G gained 237151 nodes and changed 12 moves, all on the 81 Base5-flagged positions. [O reference comparison](sol3/job15/K2/O/known_gate.json) · [G reference comparison](sol3/job15/K2/G/known_gate.json) · [G flagged split](sol3/job15/K2/G/summary.json)
- K3 matched all 20 of Astra5's P ladder rows. The first `g3g6 mate 2` was requested depth 13 at 86114 nodes. Depth 20 used 87420 nodes. [P ladder](sol3/job15/K3/P/rows.tsv) · [Comparison](sol3/job15/K3/P/known_gate.json)
- K4 found zero accepted [4] events in every guarded embedded O, G and P search. K5 matched nodes and bestmove for all 272 unflagged G rows. All 196 unflagged O rows also held. [K4 and K5 G](sol3/job15/K2/G/K4_K5.json) · [K4 and K5 O](sol3/job15/K2/O/K4_K5.json) · [K4 P](sol3/job15/K3/P/K4.json)

### Prediction grade

4 of 6 completed runs landed inside all three ranges, and 16 of 18 measured values landed in range. [Frozen prediction](sol3/job15/prediction.txt)

Synthetic G Guard1 had flagged changes 82 outside [12, 70]. [Readback](sol3/job15/N1/G/Guard1/summary.json)

Synthetic O Guard1 had flagged changes 58 outside [4, 45]. [Readback](sol3/job15/N1/O/Guard1/summary.json)

The synthetic P mate threshold was 7, against a depth-6 forecast and range 5–8. [Threshold](sol3/job15/N2/P/Guard1/threshold.json)

### Results

Each ratio uses Guard0 on the same evaluation and set. P combines the twenty independent depth rungs. Flagged groups are defined by the Guard0 [4] values. [Raw re-parser](sol3/job15/summarize_arm.py)

| Setting | Evaluation | Set | Node sum | Ratio | First three | NC0 sums [0]–[4] | [4] positions | Changed moves flagged / others |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | --- |
| [Guard0](sol3/job15/K1/O/summary.json) | Embedded | O | 8,315,168 | 1.00000 | 21,812, 26,844, 35,173 | 123578 / 113502 / 86995 / 85212 / 5 | 4 | 0/4 · 0/196 |
| [Guard1](sol3/job15/K2/O/summary.json) | Embedded | O | 8,315,218 | 1.00001 | 21,812, 26,844, 35,173 | 123578 / 113502 / 86990 / 85207 / 0 | 0 | 0/4 · 0/196 |
| [Guard0](sol3/job15/K1/G/summary.json) | Embedded | G | 17,611,204 | 1.00000 | 31,779, 46,086, 84,457 | 357628 / 325285 / 244577 / 233592 / 513 | 81 | 0/81 · 0/272 |
| [Guard1](sol3/job15/K2/G/summary.json) | Embedded | G | 17,848,355 | 1.01347 | 31,779, 46,086, 84,520 | 369197 / 335253 / 252148 / 240542 / 0 | 0 | 12/81 · 0/272 |
| [Guard0](sol3/job15/N1/G/Guard0/summary.json) | Synthetic net768 | G | 42,620,225 | 1.00000 | 95,007, 39,469, 131,900 | 525990 / 495511 / 264362 / 256034 / 1453 | 189 | 0/189 · 0/164 |
| [Guard1](sol3/job15/N1/G/Guard1/summary.json) | Synthetic net768 | G | 43,662,795 | 1.02446 | 95,007, 39,472, 121,540 | 538518 / 507159 / 266919 / 258447 / 0 | 0 | 82/189 · 0/164 |
| [Guard0](sol3/job15/N1/O/Guard0/summary.json) | Synthetic net768 | O | 32,504,791 | 1.00000 | 37,409, 213,822, 139,142 | 426716 / 402179 / 179259 / 174906 / 539 | 118 | 0/118 · 0/82 |
| [Guard1](sol3/job15/N1/O/Guard1/summary.json) | Synthetic net768 | O | 33,025,665 | 1.01602 | 56,140, 212,688, 144,373 | 430411 / 405779 / 180843 / 176416 / 0 | 0 | 58/118 · 0/82 |
| [Guard0](sol3/job15/N2/P/Guard0/summary.json) | Synthetic net768 | P | 88,641 | 1.00000 | 104, 168, 494 | 510 / 510 / 210 / 210 / 32 | 16 | 0/16 · 0/4 |
| [Guard1](sol3/job15/N2/P/Guard1/summary.json) | Synthetic net768 | P | 88,638 | 0.99997 | 104, 168, 494 | 478 / 478 / 162 / 162 / 0 | 0 | 0/16 · 0/4 |

### Answer

The independent guard reproduced Astra5’s embedded O and G node counts and root moves on every row, and all twenty P ladder rows. [Embedded O](sol3/job15/K2/O/known_gate.json) · [Embedded G](sol3/job15/K2/G/known_gate.json) · [P ladder](sol3/job15/K3/P/known_gate.json)

Synthetic G changed 82 of 189 flagged root moves and 0 of 164 unflagged root moves. Nodes changed +2.446% from Guard0. 164 of 164 unflagged rows kept both nodes and move. The guard accepted 0 measured shallow quiet-mate cutoffs. [K4/K5 readback](sol3/job15/N1/G/Guard1/K4_K5.json)

Synthetic O changed 58 of 118 flagged root moves and 0 of 82 unflagged root moves. Nodes changed +1.602% from Guard0. 82 of 82 unflagged rows kept both nodes and move. The guard accepted 0 measured shallow quiet-mate cutoffs. [K4/K5 readback](sol3/job15/N1/O/Guard1/K4_K5.json)

Synthetic P changed 0 of 16 flagged root moves and 0 of 4 unflagged root moves. Nodes changed -0.003% from Guard0. 4 of 4 unflagged rows kept both nodes and move. The guard accepted 0 measured shallow quiet-mate cutoffs. [K4/K5 readback](sol3/job15/N2/P/Guard1/K4_K5.json)

The synthetic P ladder kept the first mate at depth 7 with both settings. Guard1 used 88638 nodes summed over all rungs, compared with 88641 for Guard0. [Guard0 threshold](sol3/job15/N2/P/Guard0/threshold.json) · [Guard1 threshold](sol3/job15/N2/P/Guard1/threshold.json)

## Facts

- The independent guard executable SHA-256 is `84997d4122e58bc3da2a94d4430b2780d31bcd72fa4a9e7e46a071dd7bf1bace`, built in CMake Release with GCC 14.2.0 and Debian libstdc++ from GCC 14.2.0-19. Guard0 on synthetic G and O matched every corresponding Job 14 output and all five counts. [Build output](sol3/job15/guard/build.txt) · [G Job 14 gate](sol3/job15/N1/G/Guard0/job14_gate.txt) · [O Job 14 gate](sol3/job15/N1/O/Guard0/job14_gate.txt)
- With PC20 Base5, divisor 3 and a maximum bonus of 3, a parent depth of 14 already gives child depth at least 2. `NullThreatVerify` was off. Thus the shallow null beta results in this configuration use the unverified cutoff branch, which aligns the guard's stop condition with the baseline's accepted-cutoff count. [UCI defaults](sol3/job15/guard/uci.txt) · [Guarded code](sol3/job15/null_mate_guard.patch.txt) · [PC20 commands](sol3/job15/K2/G/engine.commands.txt)
- The standalone forecast commit was `c172f5f68d7814f12cdde0d55fb007a71c036f10`. Its own UTC stamps entry precedes the first new run. [Prediction](sol3/job15/prediction.txt) · [Clock and exits](sol3/job15/stamps.txt)

## Suspicions

The specific predicate explains why changed rows concentrate on baseline-flagged positions. A cold unflagged search never encounters a qualifying first difference along its original path. Rejecting a cutoff can change the rest of the tree on another position, so the number of changed root moves need not be proportional to the number of baseline events.

## What I did not do

I ran no games or CPU comparison and opened only the peer's result files. The guard source and its clean reapplication stayed in scratch.

## What I am not sure about

Shared use of the quiet-mate predicate gives a direct guard/counter consistency check. A shared predicate error could still agree on both sides, and the independent Astra5 replay samples only the specified positions. The baseline-path argument uses PC20's verification settings. A tuning that can verify a shallow null result before accepting it would need its own check.

## Limits of this check

The PC's own net and exe, other depths, games, time, the cost of the guard's test in CPU time. A node count or a changed move is not strength. [Raw step exits](sol3/job15/stamps.txt)

<details>
<summary>Literal diff and patch application output</summary>

```diff
diff -ruN base/src/search.cpp tree/src/search.cpp
--- base/src/search.cpp	2026-11-18 05:55:01.807977026 -0800
+++ tree/src/search.cpp	2026-11-18 06:38:20.623188616 -0800
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
+        {"NullMateGuard", &NullMateGuard, 0, 1},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -1883,12 +1885,10 @@
     child->runtime_psqt.valid = false;
 }
 
-void Worker::count_null_cutoff(const Board& board, int child_depth) {
-    ++null_cutoffs_;
-    if (child_depth > 0) return;
-    ++null_shallow_cutoffs_;
+namespace {
 
-    // The actual null search has been undone. Test its position on a copy.
+[[nodiscard]] bool null_child_has_quiet_mate(const Board& board) {
+    // The real null search has been undone. Recreate its position on a copy.
     Board null_child = board;
     NullUndo null_undo;
     null_child.make_null_move(null_undo);
@@ -1898,11 +1898,18 @@
         (void)null_child.make_move(move, undo);
         const bool mate = null_child.in_check() && null_child.legal_moves().empty();
         null_child.unmake_move(move, undo);
-        if (mate) {
-            ++null_quiet_mates_;
-            return;
-        }
+        if (mate) return true;
     }
+    return false;
+}
+
+} // namespace
+
+void Worker::count_null_cutoff(const Board& board, int child_depth) {
+    ++null_cutoffs_;
+    if (child_depth > 0) return;
+    ++null_shallow_cutoffs_;
+    if (null_child_has_quiet_mate(board)) ++null_quiet_mates_;
 }
 
 
@@ -2630,7 +2637,8 @@
             int null_score = -search_child(board, ss + 1, child_depth, -beta, -beta + 1, !cut_node);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
-            if (null_score >= beta) {
+            if (null_score >= beta &&
+                !(tune::NullMateGuard && child_depth <= 0 && null_child_has_quiet_mate(board))) {
                 if (is_mate_score(null_score)) null_score = beta;
                 // Depth >= 14 always verifies, as before. Below that, a cutoff
                 // stands unless NullThreatVerify is on and a cheaper enemy piece
```

```text
patching file src/search.cpp
```

</details>
