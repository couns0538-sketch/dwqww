# Astra5 job 6 — timing the shallow null-move mate guard

## 1. Step 0

The rebuilt job 5 guard matched the original executable byte for byte. Its SHA-256 was `7336a7753d0a89d6e85121d62d779212f22f1f6653e2c66022dae83e94771f57`. Each gate started a fresh engine process using the built-in evaluation.

| Settings | Bench 11 nodes | Bench 13 nodes | Perft 5 nodes |
|---|---:|---:|---:|
| Defaults | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

The build used the PC source, job 4 floor patch and job 5 exact guard, with GNU C++ 14.2.0 and CMake 3.31.10 in Release mode. [Build and five transcripts](astra5/job6/step0)

## 2. Part A — cost of the exact guard

On O at depth 12, the Job 4 floor-0 counter yielded 85,212 eligible shallow null cutoffs. I summed zero-based slot [3] after the `NC0` tag across the 200 ordered rows. The first three counts were 269, 334, 374. Guard 0 skips the test. The 85,212 baseline opportunities per O run supply the reference count for guard 1. [Counter recount](astra5/job6/count_calls.txt)

All timing used the 200 O positions in job 5 order at depth 12 with PC20, the built-in evaluation, NullChildFloor 0, Threads 1 and Hash 16. Each run started one process pinned to logical CPU 1 on a Linux AMD EPYC 9V74 virtual machine. It received `ucinewgame` and answered `isready` before every search. The harness verified the pin and checked the node sum, including in warm-ups. Guard 0 must return 8,315,168 nodes. Guards 1 and 2 must return 8,315,218.

Odd blocks used ABBA, even blocks BAAB, after one excluded warm-up on that block's first arm. A block ratio divides the sum of both B times by the sum of both A times. The pooled ratio applies the same division across all measured runs. CPU is the direct engine PID's user plus system time from `wait4`. Wall time runs from process launch preparation through exit and collection. Each clock uses its own A1 floor. A median outside that floor's full range with at least ten block ratios on the same side of 1 reads **MEASURED**. The CPU reading controls B1 eligibility. [Timing harness](astra5/job6/time_blocks.py) · [Raw times and build settings](astra5/job6/timing)

The A2 median was inside the floor range on both clocks, with 9 of 12 ratios above 1 on each. Both clocks read **not measurable here**.

### A1 — byte-copy floor, guard 0 versus 0

All twelve blocks completed.

<details><summary>Per-run measurements</summary>

| Block | Slot | Arm | Guard | Positions | Nodes | Engine CPU (s) | Wall (s) | Status |
|---:|---:|:---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | A | 0 | 200 | 8315168 | 5.700581 | 6.096123 | ok |
| 1 | 2 | B | 0 | 200 | 8315168 | 5.477917 | 5.817785 | ok |
| 1 | 3 | B | 0 | 200 | 8315168 | 5.617112 | 5.704785 | ok |
| 1 | 4 | A | 0 | 200 | 8315168 | 5.660659 | 5.701910 | ok |
| 2 | 1 | B | 0 | 200 | 8315168 | 5.398487 | 5.804656 | ok |
| 2 | 2 | A | 0 | 200 | 8315168 | 5.670661 | 5.711155 | ok |
| 2 | 3 | A | 0 | 200 | 8315168 | 5.819352 | 5.865120 | ok |
| 2 | 4 | B | 0 | 200 | 8315168 | 5.749273 | 5.792044 | ok |
| 3 | 1 | A | 0 | 200 | 8315168 | 5.780704 | 5.827298 | ok |
| 3 | 2 | B | 0 | 200 | 8315168 | 5.594032 | 5.642626 | ok |
| 3 | 3 | B | 0 | 200 | 8315168 | 5.627335 | 5.665346 | ok |
| 3 | 4 | A | 0 | 200 | 8315168 | 5.707296 | 5.748926 | ok |
| 4 | 1 | B | 0 | 200 | 8315168 | 5.781114 | 5.825101 | ok |
| 4 | 2 | A | 0 | 200 | 8315168 | 5.784286 | 5.829568 | ok |
| 4 | 3 | A | 0 | 200 | 8315168 | 5.861723 | 5.907418 | ok |
| 4 | 4 | B | 0 | 200 | 8315168 | 6.144767 | 6.199512 | ok |
| 5 | 1 | A | 0 | 200 | 8315168 | 5.773290 | 5.815823 | ok |
| 5 | 2 | B | 0 | 200 | 8315168 | 5.665383 | 5.705476 | ok |
| 5 | 3 | B | 0 | 200 | 8315168 | 5.661632 | 5.699300 | ok |
| 5 | 4 | A | 0 | 200 | 8315168 | 5.650597 | 5.692846 | ok |
| 6 | 1 | B | 0 | 200 | 8315168 | 5.719553 | 5.759576 | ok |
| 6 | 2 | A | 0 | 200 | 8315168 | 5.881213 | 5.928972 | ok |
| 6 | 3 | A | 0 | 200 | 8315168 | 5.986244 | 6.030955 | ok |
| 6 | 4 | B | 0 | 200 | 8315168 | 5.854136 | 5.896083 | ok |
| 7 | 1 | A | 0 | 200 | 8315168 | 5.763449 | 5.805012 | ok |
| 7 | 2 | B | 0 | 200 | 8315168 | 5.647783 | 5.687502 | ok |
| 7 | 3 | B | 0 | 200 | 8315168 | 5.510473 | 5.545133 | ok |
| 7 | 4 | A | 0 | 200 | 8315168 | 5.561493 | 5.603657 | ok |
| 8 | 1 | B | 0 | 200 | 8315168 | 5.907239 | 5.956115 | ok |
| 8 | 2 | A | 0 | 200 | 8315168 | 5.858112 | 5.900341 | ok |
| 8 | 3 | A | 0 | 200 | 8315168 | 5.668577 | 5.710793 | ok |
| 8 | 4 | B | 0 | 200 | 8315168 | 5.595250 | 5.633495 | ok |
| 9 | 1 | A | 0 | 200 | 8315168 | 5.725616 | 5.767642 | ok |
| 9 | 2 | B | 0 | 200 | 8315168 | 5.855764 | 5.899526 | ok |
| 9 | 3 | B | 0 | 200 | 8315168 | 5.691685 | 5.734269 | ok |
| 9 | 4 | A | 0 | 200 | 8315168 | 5.596071 | 5.634571 | ok |
| 10 | 1 | B | 0 | 200 | 8315168 | 5.640896 | 5.683356 | ok |
| 10 | 2 | A | 0 | 200 | 8315168 | 5.554646 | 5.592502 | ok |
| 10 | 3 | A | 0 | 200 | 8315168 | 5.697575 | 5.740804 | ok |
| 10 | 4 | B | 0 | 200 | 8315168 | 5.765253 | 5.812314 | ok |
| 11 | 1 | A | 0 | 200 | 8315168 | 5.708744 | 5.750272 | ok |
| 11 | 2 | B | 0 | 200 | 8315168 | 5.450965 | 5.645091 | ok |
| 11 | 3 | B | 0 | 200 | 8315168 | 5.649222 | 5.690859 | ok |
| 11 | 4 | A | 0 | 200 | 8315168 | 5.547256 | 5.583307 | ok |
| 12 | 1 | B | 0 | 200 | 8315168 | 5.759477 | 5.805520 | ok |
| 12 | 2 | A | 0 | 200 | 8315168 | 5.728780 | 5.770596 | ok |
| 12 | 3 | A | 0 | 200 | 8315168 | 5.692884 | 5.733025 | ok |
| 12 | 4 | B | 0 | 200 | 8315168 | 5.633777 | 5.677602 | ok |

</details>

<details><summary>Excluded warm-up runs</summary>

| Block | Slot | Arm | Guard | Positions | Nodes | Engine CPU (s) | Wall (s) | Status |
|---:|---:|:---:|---:|---:|---:|---:|---:|---|
| 1 | 0 | A | 0 | 200 | 8315168 | 5.530141 | 5.972312 | ok |
| 2 | 0 | B | 0 | 200 | 8315168 | 5.412012 | 5.770445 | ok |
| 3 | 0 | A | 0 | 200 | 8315168 | 5.813171 | 5.860584 | ok |
| 4 | 0 | B | 0 | 200 | 8315168 | 5.664652 | 5.704090 | ok |
| 5 | 0 | A | 0 | 200 | 8315168 | 5.746380 | 5.794364 | ok |
| 6 | 0 | B | 0 | 200 | 8315168 | 5.374963 | 5.778621 | ok |
| 7 | 0 | A | 0 | 200 | 8315168 | 5.809567 | 5.851953 | ok |
| 8 | 0 | B | 0 | 200 | 8315168 | 5.823014 | 5.866338 | ok |
| 9 | 0 | A | 0 | 200 | 8315168 | 5.554162 | 5.591491 | ok |
| 10 | 0 | B | 0 | 200 | 8315168 | 5.529445 | 5.568348 | ok |
| 11 | 0 | A | 0 | 200 | 8315168 | 5.650228 | 5.692911 | ok |
| 12 | 0 | B | 0 | 200 | 8315168 | 5.721197 | 5.763459 | ok |

</details>

| Block | CPU B/A | Wall B/A |
|---:|---:|---:|
| 1 | 0.976568 | 0.976652 |
| 2 | 0.970213 | 1.001764 |
| 3 | 0.976790 | 0.976827 |
| 4 | 1.024032 | 1.024506 |
| 5 | 0.991520 | 0.990973 |
| 6 | 0.975246 | 0.974559 |
| 7 | 0.985282 | 0.984570 |
| 8 | 0.997901 | 0.998146 |
| 9 | 1.019941 | 1.020310 |
| 10 | 1.013680 | 1.014326 |
| 11 | 0.986157 | 1.000209 |
| 12 | 0.997513 | 0.998218 |

| Clock | Min | Max | Median | Below 1 | Above 1 | Pooled B/A | Reading |
|---|---:|---:|---:|---:|---:|---:|---|
| CPU | 0.970213 | 1.024032 | 0.988839 | 9/12 | 3/12 | 0.992857 | floor |
| Wall | 0.974559 | 1.024506 | 0.998182 | 7/12 | 5/12 | 0.996645 | floor |

### A2 — guard 0 versus 1

All twelve blocks completed.

<details><summary>Per-run measurements</summary>

| Block | Slot | Arm | Guard | Positions | Nodes | Engine CPU (s) | Wall (s) | Status |
|---:|---:|:---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | A | 0 | 200 | 8315168 | 5.703369 | 5.747329 | ok |
| 1 | 2 | B | 1 | 200 | 8315218 | 5.780862 | 5.823031 | ok |
| 1 | 3 | B | 1 | 200 | 8315218 | 5.717648 | 5.764455 | ok |
| 1 | 4 | A | 0 | 200 | 8315168 | 5.547035 | 5.582653 | ok |
| 2 | 1 | B | 1 | 200 | 8315218 | 5.709190 | 5.748275 | ok |
| 2 | 2 | A | 0 | 200 | 8315168 | 6.027423 | 6.074618 | ok |
| 2 | 3 | A | 0 | 200 | 8315168 | 5.754795 | 5.796972 | ok |
| 2 | 4 | B | 1 | 200 | 8315218 | 5.579456 | 5.614331 | ok |
| 3 | 1 | A | 0 | 200 | 8315168 | 5.781356 | 5.828863 | ok |
| 3 | 2 | B | 1 | 200 | 8315218 | 5.692501 | 5.733255 | ok |
| 3 | 3 | B | 1 | 200 | 8315218 | 5.956756 | 6.001097 | ok |
| 3 | 4 | A | 0 | 200 | 8315168 | 5.826799 | 5.870267 | ok |
| 4 | 1 | B | 1 | 200 | 8315218 | 5.814199 | 5.856953 | ok |
| 4 | 2 | A | 0 | 200 | 8315168 | 5.444531 | 5.588497 | ok |
| 4 | 3 | A | 0 | 200 | 8315168 | 5.402923 | 5.862438 | ok |
| 4 | 4 | B | 1 | 200 | 8315218 | 5.621356 | 6.017455 | ok |
| 5 | 1 | A | 0 | 200 | 8315168 | 5.807258 | 5.850531 | ok |
| 5 | 2 | B | 1 | 200 | 8315218 | 5.672879 | 5.714741 | ok |
| 5 | 3 | B | 1 | 200 | 8315218 | 6.379094 | 6.455697 | ok |
| 5 | 4 | A | 0 | 200 | 8315168 | 5.890894 | 5.933455 | ok |
| 6 | 1 | B | 1 | 200 | 8315218 | 5.849913 | 5.893567 | ok |
| 6 | 2 | A | 0 | 200 | 8315168 | 5.908423 | 5.954246 | ok |
| 6 | 3 | A | 0 | 200 | 8315168 | 5.870314 | 5.915907 | ok |
| 6 | 4 | B | 1 | 200 | 8315218 | 5.847353 | 5.891486 | ok |
| 7 | 1 | A | 0 | 200 | 8315168 | 5.937905 | 5.981758 | ok |
| 7 | 2 | B | 1 | 200 | 8315218 | 5.691218 | 5.734621 | ok |
| 7 | 3 | B | 1 | 200 | 8315218 | 6.046289 | 6.093815 | ok |
| 7 | 4 | A | 0 | 200 | 8315168 | 5.790478 | 5.833342 | ok |
| 8 | 1 | B | 1 | 200 | 8315218 | 5.663697 | 5.701240 | ok |
| 8 | 2 | A | 0 | 200 | 8315168 | 5.635504 | 5.676316 | ok |
| 8 | 3 | A | 0 | 200 | 8315168 | 5.640433 | 5.681183 | ok |
| 8 | 4 | B | 1 | 200 | 8315218 | 5.796864 | 5.839222 | ok |
| 9 | 1 | A | 0 | 200 | 8315168 | 5.696797 | 5.739386 | ok |
| 9 | 2 | B | 1 | 200 | 8315218 | 5.842590 | 5.889545 | ok |
| 9 | 3 | B | 1 | 200 | 8315218 | 5.759111 | 5.798540 | ok |
| 9 | 4 | A | 0 | 200 | 8315168 | 6.221560 | 6.272933 | ok |
| 10 | 1 | B | 1 | 200 | 8315218 | 5.866781 | 5.912282 | ok |
| 10 | 2 | A | 0 | 200 | 8315168 | 5.802926 | 5.849236 | ok |
| 10 | 3 | A | 0 | 200 | 8315168 | 6.037601 | 6.093649 | ok |
| 10 | 4 | B | 1 | 200 | 8315218 | 5.992652 | 6.044415 | ok |
| 11 | 1 | A | 0 | 200 | 8315168 | 5.898865 | 5.944508 | ok |
| 11 | 2 | B | 1 | 200 | 8315218 | 5.794042 | 5.836604 | ok |
| 11 | 3 | B | 1 | 200 | 8315218 | 5.822386 | 5.869581 | ok |
| 11 | 4 | A | 0 | 200 | 8315168 | 5.693848 | 5.733135 | ok |
| 12 | 1 | B | 1 | 200 | 8315218 | 5.662218 | 6.080602 | ok |
| 12 | 2 | A | 0 | 200 | 8315168 | 5.651674 | 5.691608 | ok |
| 12 | 3 | A | 0 | 200 | 8315168 | 5.573094 | 5.613044 | ok |
| 12 | 4 | B | 1 | 200 | 8315218 | 5.857794 | 5.900952 | ok |

</details>

<details><summary>Excluded warm-up runs</summary>

| Block | Slot | Arm | Guard | Positions | Nodes | Engine CPU (s) | Wall (s) | Status |
|---:|---:|:---:|---:|---:|---:|---:|---:|---|
| 1 | 0 | A | 0 | 200 | 8315168 | 5.372418 | 5.802645 | ok |
| 2 | 0 | B | 1 | 200 | 8315218 | 5.647846 | 5.685896 | ok |
| 3 | 0 | A | 0 | 200 | 8315168 | 5.750310 | 5.791129 | ok |
| 4 | 0 | B | 1 | 200 | 8315218 | 5.886773 | 5.934310 | ok |
| 5 | 0 | A | 0 | 200 | 8315168 | 5.734717 | 5.774745 | ok |
| 6 | 0 | B | 1 | 200 | 8315218 | 5.710894 | 5.751696 | ok |
| 7 | 0 | A | 0 | 200 | 8315168 | 5.561653 | 5.597592 | ok |
| 8 | 0 | B | 1 | 200 | 8315218 | 5.774492 | 5.821635 | ok |
| 9 | 0 | A | 0 | 200 | 8315168 | 5.711734 | 5.752915 | ok |
| 10 | 0 | B | 1 | 200 | 8315218 | 5.953232 | 5.998953 | ok |
| 11 | 0 | A | 0 | 200 | 8315168 | 5.898048 | 5.944771 | ok |
| 12 | 0 | B | 1 | 200 | 8315218 | 5.589589 | 5.721422 | ok |

</details>

| Block | CPU B/A | Wall B/A |
|---:|---:|---:|
| 1 | 1.022053 | 1.022728 |
| 2 | 0.958109 | 0.957126 |
| 3 | 1.003541 | 1.003011 |
| 4 | 1.054216 | 1.036982 |
| 5 | 1.030246 | 1.032795 |
| 6 | 0.993083 | 0.992831 |
| 7 | 1.000778 | 1.001129 |
| 8 | 1.016373 | 1.016109 |
| 9 | 0.973431 | 0.973008 |
| 10 | 1.001597 | 1.001157 |
| 11 | 1.002046 | 1.002444 |
| 12 | 1.026303 | 1.059878 |

| Clock | Min | Max | Median | Below 1 | Above 1 | Pooled B/A | Reading |
|---|---:|---:|---:|---:|---:|---:|---|
| CPU | 0.958109 | 1.054216 | 1.002793 | 3/12 | 9/12 | 1.006287 | not measurable here |
| Wall | 0.957126 | 1.059878 | 1.002727 | 3/12 | 9/12 | 1.007850 | not measurable here |

## 3. Part B — an exact test using the existing null child

Value 2 examines the search's existing null child before the caller undoes the null move. The tested build generates pseudo-legal quiet moves, filters for a check, then verifies the candidate's legality. For each surviving move it makes the move on the same board, tests for check and the absence of a legal reply, and undoes the move. It stops on the first mate. This removes the board copy, the repeated null move, legality checks on quiet non-checks and the need to enumerate every legal reply. Value 1 still calls the job 5 by-value helper. [Patch](astra5/job6/null_guard_fast.patch.txt)

The value-2 build had SHA-256 `2939f91814c0dfcf502a44b21deb00c0c7622d90140c2b6f9bd7a0140dd9a5ea`. The build directory contained the executable and build products and used the built-in evaluation. The known-answer runs preceded the first timed block. [Build record](astra5/job6/fast-build) · [Raw rows and P transcript](astra5/job6/fast-rows)

| Workload | Equal deterministic rows | Nodes | First three node counts |
|---|---:|---:|---|
| O | 200/200 | 8,315,218 | 21812, 26844, 35173 |
| G | 353/353 | 17,848,355 | 31779, 46086, 84520 |
| P | 20/20 | — | 262, 408, 658 |

P first reported `g3g6` with a positive mate score at depth 13 (86,114 nodes). Depth 20 used 87,420 nodes.

O and G use depth 12. P compares the depth 1–20 ladder, including score, best move, nodes and PV. The UCI time and NPS fields vary with execution speed and are omitted from the equality check.

P reported mate in two at both depths 13 and 20. Every O and G row agreed on index, FEN, node count and best move.

### Patch creation and application

The following is the full stdout of `diff -ruN guard-base guard-fast` on a fresh copy of the job 5 source and the design tree (exit 1).

```diff
diff -ruN guard-base/src/search.cpp guard-fast/src/search.cpp
--- guard-base/src/search.cpp	2026-11-18 06:44:53.158142480 -0800
+++ guard-fast/src/search.cpp	2026-11-18 06:45:08.033319837 -0800
@@ -191,7 +191,7 @@
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
         {"NullChildFloor", &NullChildFloor, 0, 3},
-        {"NullMateGuard", &NullMateGuard, 0, 1},
+        {"NullMateGuard", &NullMateGuard, 0, 2},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
@@ -1771,6 +1771,26 @@
     }
     return false;
 }
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
 } // namespace
 
 // Main alpha-beta search
@@ -1985,10 +2005,12 @@
             const int null_child_depth = tune::NullChildFloor > 0 ? std::max(reduced_depth, tune::NullChildFloor)
                                                                   : reduced_depth;
             int null_score = -search_child(board, ss + 1, null_child_depth, -beta, -beta + 1, !cut_node);
+            const bool fast_guard_veto = tune::NullMateGuard == 2 && !aborted_ && null_score >= beta &&
+                                         null_child_depth <= 0 && has_quiet_mate(board);
             board.unmake_null_move(undo);
             if (aborted_) return 0;
-            if (null_score >= beta &&
-                !(tune::NullMateGuard && null_child_depth <= 0 && quiet_mate_after_null(board))) {
+            if (null_score >= beta && !fast_guard_veto &&
+                !(tune::NullMateGuard == 1 && null_child_depth <= 0 && quiet_mate_after_null(board))) {
                 if (is_mate_score(null_score)) null_score = beta;
                 // Depth >= 14 always verifies, as before. Below that, a cutoff
                 // stands unless NullThreatVerify is on and a cheaper enemy piece
```

In a separate fresh copy, `patch -p1 -F0 < ../null_guard_fast.patch.txt` exited 0 with this stdout.

```text
patching file src/search.cpp
```

The subsequent `diff -qr guard-fast guard-applied` returned no output and exited 0.

### B1 eligibility

B1 was skipped as prescribed because A2 read **not measurable here**. All value-2 known answers had passed before A1.

## 4. Frozen prediction

| Measure | Point | Inclusive range | Observed | Range result |
|---|---:|---|---:|---|
| Largest A1 CPU ratio | 1.010 | 1.004–1.016 | 1.024032 | outside |
| Smallest A1 CPU ratio | 0.990 | 0.984–0.996 | 0.970213 | outside |
| Median A2 CPU ratio | 1.060 | 1.045–1.075 | 1.002793 | outside |
| A2 CPU ratios above 1 | 12 | 11–12 | 9 | outside |
| Exact row agreement (1 = yes) | 1 | 1–1 | 1 | inside |
| Median B1 CPU ratio | 0.959 | 0.946–0.972 | — | ungraded |

Of the five forecasts with an observation, the row-equivalence forecast hit its point and range. All four timing forecasts missed their ranges. The B1 forecast is ungraded.

## 5. Cost on O

**CPU.** Guard 0 averaged 5.772742 s per 200-position run and guard 1 averaged 5.809035 s. Guard 1 minus guard 0 was +0.036294 s per run, or +0.426 µs per baseline shallow null cutoff. The pooled change was +0.629%. The A2 reading was not measurable here.

**Wall.** Guard 0 averaged 5.838161 s per 200-position run and guard 1 averaged 5.883990 s. Guard 1 minus guard 0 was +0.045829 s per run, or +0.538 µs per baseline shallow null cutoff. The pooled change was +0.785%. The A2 reading was not measurable here.

Per-call values divide the difference in mean whole-run times by the baseline count of eligible cutoffs. They include the net effect of the 50-node tree difference and do not time individual calls.

The experiment leaves open whether the revised implementation removes any measurable time cost on O.

## Facts

All 120 timed-workload processes, including the 24 warm-ups, returned the expected node sum. A1 compared distinct files with identical SHA-256 digests. A2 used the original job 5 binary for both arms. The two independent readbacks agreed on both floors, medians, direction counts, and pooled ratios. The forecast was pushed on its own at `246a35a1ed937108b9f81484627b8cbe043b0c20` before any value-2 validation or timing. [Prediction](astra5/job6/prediction.txt) · [Step timestamps](astra5/job6/stamps.txt)

## Suspicions

Constructing a board copy and checking the legality of many non-checking moves costs work in value 1. The timing series does not isolate those operations. The byte-copy control showed enough block-to-block variation to cover the guard's median difference.

## What I did not do

The A2 reading closed the B1 timing gate. The comparison of values 1 and 2 therefore covers decisions on the specified rows. The time saved by value 2 remains unknown.

**What this cannot see**, in the job's words

> the PC's own net (with a net every node costs more, so the test's share of the time is smaller there), its compiler (clang with a profile on Windows) and processor, other depths, games. A time on your machine is a second opinion for the PC, never its number.

## What I am not sure about

The timing does not resolve the true guard cost on this machine. The 85,212 denominator comes from the baseline counter build. The 50 extra nodes in guard 1 leave open a small change in the actual call count under the enabled guard. Matching the observed rows establishes agreement on these workloads, without measuring game strength.

## Pre-commit inventory

`git status --short` followed by `ls -R forge-combo29/astra5/job6` produced the following output.

```text
A  forge-combo29/REPORT_astra5_job6.md
M  forge-combo29/astra5/job6/stamps.txt
forge-combo29/astra5/job6:
count_calls.txt
fast-build
fast-rows
null_guard_fast.patch.txt
prediction.txt
stamps.txt
step0
time_blocks.py
timing
validate.py

forge-combo29/astra5/job6/fast-build:
build.txt
hashes.txt
patch-apply.txt

forge-combo29/astra5/job6/fast-rows:
G.meta.txt
G.tsv
O.meta.txt
O.tsv
P.meta.txt
P.raw.txt
P.tsv
checks.txt

forge-combo29/astra5/job6/step0:
PC20-bench-11.txt
PC20-bench-13.txt
build.txt
checks.txt
default-bench-11.txt
default-bench-13.txt
default-go-perft-5.txt
patch-application.txt

forge-combo29/astra5/job6/timing:
A1-readback.txt
A1.meta.txt
A1.tsv
A2-readback.txt
A2.meta.txt
A2.tsv
B1-status.txt
machine.txt
```
