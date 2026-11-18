# sol3 Job 16 — HistRework split and quiet-history readers

## (1) Step 0 — passed

Linux cloud, Case A. I identified the retained kF (Job 12), counted (Job
13), and counted plus guard (Job 15) executables by SHA-256. All three gave
the same embedded-evaluation pins below. The guarded build used its
default `NullMateGuard=0`.

| UCI options | bench 11 nodes | bench 13 nodes | startpos perft 5 nodes |
| --- | ---: | ---: | ---: |
| Default | 312,866 | 862,329 | 4,865,609 |
| PC20, Threads 1, Hash 16 | 278,024 | 587,276 | — |

[Pins, commands, and raw outputs](sol3/job16/stage0)

## (2) Part 1 — two independent HistRework levels

I froze my split against the Job 15 counted and guarded tree before
opening any Astra5 patch. Each spin defaults to `-1` (follow legacy
`HistRework`) and accepts explicit levels `0` to `3`. All four S14
ladders matched Astra5 Job 5 Part C on requested depth, reported depth,
bestmove, score type, score, and the last depth-info node count, 80 of 80
rows. Both-off explicitly set legacy 2 before overriding each half to 0.

| S14 quiet / correction | Matching rows | First g3g6 mate depth / nodes | D20 bestmove, score, nodes |
| --- | ---: | --- | --- |
| 2 / 2 | 20/20 | None through 20 | f6h5, cp 836, 774,832 |
| 0 / 0 | 20/20 | D16, 240,516 | g3g6, mate 2, 241,262 |
| 2 / 0 | 20/20 | None through 20 | f6h5, cp 814, 957,869 |
| 0 / 2 | 20/20 | D16, 227,749 | g3g6, mate 2, 228,946 |

Line numbers are in my reproduced Part 1 tree.

- `include/forge/search.hpp:404–405` and `src/search.cpp:182–183,259–265` declare, initialize, and resolve the two levels. `src/uci.cpp:545–546,810–813` advertises and sets them.
- `src/search.cpp:1090–1097` uses quiet level for table, map, blend weight, and fast scorer gate. The gate controls `1106–1110,1417–1435,1457–1468,1516–1519`. `2141–2144` gates the scalar map lookup and uses the quiet blend weight. `2171–2174` updates the dormant keyed-delta helper.
- `src/search.cpp:2274,3047` gates cutoff and PV quiet twin writes. `2370–2372,2727` gates per-ply map invalidation in quiescence and main search.
- `src/search.cpp:1970–1983` and `2025–2031` gate the joint correction key, weighted read, and write with the correction level. Worker allocation and clearing at `1691–1692,1716–1720` and correction cache propagation at `1833,1883` retain their previous lifecycle.

[Split patch](sol3/job16/histrework_split.patch.txt) · [All switched sites](sol3/job16/switched_sites.txt) · [Raw local ladders](sol3/job16/part1) · [Pinned Astra5 rows and raw output](sol3/job16/references)

## (3) Part 2 — three live readers, all-plain check passed

The main build compiles `FORGE_SEARCH_SPEED2=1` and
`FORGE_SPD_NO_ZERO_MOVELISTS=2` (`CMakeLists.txt:33–34`, build
receipt). `QuietReadPlainR1`, `R2`, and `R3` each default to 0 and
accept 0 or 1. At 1 the corresponding read omits the keyed twin. The
switches preserve main history, continuation histories, separate
`ThreatHistory`, and the keyed updates.

| Reader | Part 2 source and decision |
| --- | --- |
| R1 | `src/search.cpp:1093–1112` gates `if (rework)` and `value = b4::blend(plain, twin, quarters)` for quiet move ordering. The fused paths share `if (scorer.rework)` and read the twin for pawn pushes at `1419–1437`, other pieces at `1459–1470`, and castling at `1516–1522`. The generator and evasions also call `scorer.score(move, check_squares_)` at `1372,1571,1623`. The speed-0 alternatives at `1554,1576,1625` call `quiet_history(board_, ss_, move, tune::QuietReadPlainR1 == 0)` and keep the direct-check bonus. |
| R2 | `src/search.cpp:2144–2147` reads the threat map and twin when `include_rework && level != 0 && ss != nullptr`. The pre-move R2 snapshot is `pruning_history` at `2774–2777`. At `2840`, `lmr_depth <= tune::HistoryPruneDepth && pruning_history < history_prune_threshold` can discard the move. |
| R3 | `src/search.cpp:2778–2781` takes a separate pre-move `lmr_history` snapshot when the switches differ. At `2964`, `r -= std::clamp(lmr_history / tune::LmrHistoryDivisor, -2, 2)` adjusts the late-move reduction of a quiet. |

The other apparent reads are the dormant `rework_quiet_delta` at
`src/search.cpp:2173–2178` (declaration and definition only) and the
keyed learning updates. The `pruning_history / 8` consumer at
`2853–2859` requires a capture and receives capture history. The
[full source excerpts](sol3/job16/readers_switched_sites.txt) quote the
fused pawn/piece/castling reads, scalar blend, gates, and option wiring.

- S14 q2/c0, switches 111, matched Part 1 both-off 20/20. First mate D16 at 240,516 nodes, D20 at 241,262.
- PC20 q/c follow legacy 2, switches 000, matched the immutable Job 13 A1 PC20 ladder 20/20. D20 was f6h5, cp 916, 1,052,250 nodes and no mate appeared through 20.
- A supplementary build with effective `FORGE_SEARCH_SPEED2=0` repeated the both-off vs all-plain check with legacy 0 explicit in both arms and matched 20/20, including normalized last info/PV and all five NC0 values. CMake's earlier speed-1 define produced expected redefinition warnings. The captured GCC preprocessor output confirms effective speed 0. This auxiliary build retained `FORGE_SPD_NO_ZERO_MOVELISTS=2`.

[Reader patch](sol3/job16/quiet_readers.patch.txt) · [Known ladders](sol3/job16/part2) · [Speed-0 receipts and ladders](sol3/job16/scalar)

## (4) Prediction graded

The [prediction](sol3/job16/prediction.md) was committed alone as
`9a99bde0f7fd7338f83dc0246938ab880205bed1` and pushed before any
Part 3 search. S14 scored 3/6 exact and 4/6 inside the predicted range.
PC20 scored 3/6 exact and 6/6 inside the range. The S14 forecast put
all three R1-plain recoveries (L1, L5, and L6) in range,
and correctly had L2 absent
through 20. Its biggest misses were L3 and L4, both finding mate at D15.
That contradicts my prediction that move ordering would dominate.
Both profiles recovered with the LMR history reader plain even when
quiet ordering stayed blended.

[Prediction and run order](sol3/job16/stamps.txt)

## (5) Part 3 — same P, two profiles

`1` means plain at the specified reader. S14 uses q2/c0. PC20 uses
legacy 2 with both splits following it. The first-mate column requires
`bestmove g3g6` with a positive mate score. All mate rows in this table
reported mate 2. The table comes from the speed-1 reader build's raw
commands and output.

| Ladder | R1 R2 R3 | First mate depth and nodes | D20 move, score, nodes |
| --- | --- | --- | --- |
| [S14 L1](sol3/job16/part3/S14/L1) | 100 | D18, 709,856 | g3g6, mate 2, 710,342 |
| [S14 L2](sol3/job16/part3/S14/L2) | 010 | None through 20 | f6h5, cp 862, 799,950 |
| [S14 L3](sol3/job16/part3/S14/L3) | 001 | D15, 153,147 | g3g6, mate 2, 154,711 |
| [S14 L4](sol3/job16/part3/S14/L4) | 011 | D15, 155,599 | g3g6, mate 2, 157,150 |
| [S14 L5](sol3/job16/part3/S14/L5) | 101 | D16, 381,582 | g3g6, mate 2, 384,867 |
| [S14 L6](sol3/job16/part3/S14/L6) | 110 | D17, 405,598 | g3g6, mate 2, 406,153 |
| [PC20 L1](sol3/job16/part3/PC20/L1) | 100 | D17, 401,761 | g3g6, mate 2, 402,342 |
| [PC20 L2](sol3/job16/part3/PC20/L2) | 010 | None through 20 | f6h5, cp 948, 1,117,269 |
| [PC20 L3](sol3/job16/part3/PC20/L3) | 001 | D18, 550,507 | g3g6, mate 2, 551,879 |
| [PC20 L4](sol3/job16/part3/PC20/L4) | 011 | D18, 436,084 | g3g6, mate 2, 436,582 |
| [PC20 L5](sol3/job16/part3/PC20/L5) | 101 | D17, 300,959 | g3g6, mate 2, 302,640 |
| [PC20 L6](sol3/job16/part3/PC20/L6) | 110 | D17, 376,683 | g3g6, mate 2, 377,535 |

An independent parser matched all 400 last-info rows and all 400
NC0 lines to the saved tables, including the two scalar controls.
The parser checked the exact command sequence and reference fields
for each control. [Audit outputs](sol3/job16/audit)

## (6) What hides the mate on P

**The pair is R1 plus R3.** When the keyed twin fed quiet move ordering
and the LMR history term, the mate was absent through depth 20 with
history pruning either blended (S14 quiet-only and PC20 all-zero) or
plain (L2). With only one blended reader, L4 through L6 all found mate.
Each of L1 and L3 restored it while leaving the other two readers blended.
This pattern held with S14 q2/c0 and PC20 q2/c2.

On S14 the mate first returned at D15 with R3 plain and R1 blended,
regardless of R2 (L3 and L4). With R1 plain and R3 blended the mate first
returned at D18 or D17 (L1 and L6). On PC20 that ordering reversed by a
depth: making R1 plain returned it at D17 while making R3 plain with R1
blended returned it at D18. R2 changed the size of the search, and on S14
changed L1's recovery depth from 18 to 17 in L6. It never switched
mate-found status in a measured pair that differed by R2 alone.

### Facts

- R1 can alter a quiet move's index and thereby the guard and base
  reduction at `src/search.cpp:2953–2956`. R3 can change the same
  move's adjusted reduction via `2964`, after the score has been captured
  in the parent position. The reduced search and condition for a
  full-depth retry are at `2974–2978`. Root `Qg6` is a quiet non-check
  on the [P FEN](sol3/job16/references/P.fen.txt).
- R2's shallow history test runs inside `!root_node` and
  `quiet && !gives_check && prunable` at `2793–2794,2823–2844`. It
  can act on non-checking quiets below the root. Its results can alter
  subsequent histories and TT entries.
- Parts 1 and 2 used CMake 4.2.3 Release, GCC 14.2.0, Debian
  libstdc++ 14.2.0-19 and glibc 2.41-12+deb13u4, with
  `-march=x86-64-v4`. Split and reader executable SHA-256 values are
  `fb7ac9c7eb51bc2ff21917dfe0e7b9b558678c6f82abd05a3c6c811594c92ef1`
  and `40ace81ab55777c1e46787b079c35d02279b7eab59dcf70068a33a167894f910`.
  The P ladders used the built-in evaluation, Threads 1, Hash 16,
  MultiPV 1, NullMateGuard 0, and requested fixed depths 1–20 with
  `ucinewgame` and `isready` before each search. S14 and PC20 are
  specified by their saved `setoption` commands. Node counts in the
  tables come from the final depth-info line of each requested search.
  [Split build](sol3/job16/split_build.txt) · [Reader build](sol3/job16/readers_build.txt) · [S14 commands](sol3/job16/part3/S14/L1/engine.commands.txt) · [PC20 commands](sol3/job16/part3/PC20/L1/engine.commands.txt)

### Suspicions

R1 can send the quiet mate line into a different position in the move
order, and R3 can change the depth at which a late quiet is first
tested. Together those mechanisms can change whether a shallow
null-move beta cutoff answers a descendant before the mate is searched.
The ablation establishes the interaction at the root outcome. The
global `NC0` counters measure the cutoff class across the whole tree.
They do not identify a specific descendant as the first divergence.

### What I did not do

No Astra5 implementation or patch was opened. No engine source in
the repository was modified. I ran the auxiliary speed-0 build with
the configured no-zero-movelists setting of 2. The alternate
no-zero-movelists branch was checked in source.

### What I am not sure about

Which descendant cutoff first differs across R1/R3 settings, how much
of the difference comes from earlier history or TT updates, and how
often the interaction occurs on other positions.

### Limits of this check

The PC's own net and exe, other positions than P, games. One position's ladder says where this miss comes from, not how often such misses happen.

## Reproduction receipts

The two patches below were generated with `diff -ruN`, applied to
fresh copies with `patch -p1 -F0`, and compared to the corresponding
edited trees. All source edits and compilation products were in scratch.

### histrework_split.patch.txt

```text
$ diff -ruN base tree > histrework_split.patch.txt
exit 1 (trees differ)
bad3229f0c2eff6aa8555032af7813303e3fc1c32b81cf8f933c10673b01a302  histrework_split.patch.txt
$ patch --batch --forward -p1 -F0 -d applied -i "$PWD/histrework_split.patch.txt"
patching file include/forge/search.hpp
patching file src/search.cpp
patching file src/uci.cpp
exit 0
$ diff -rq tree applied
exit 0
```

```diff
diff -ruN base/include/forge/search.hpp tree/include/forge/search.hpp
--- base/include/forge/search.hpp	2026-11-18 05:55:01.805536775 -0800
+++ tree/include/forge/search.hpp	2026-11-18 06:55:16.735438299 -0800
@@ -401,6 +401,8 @@
 // B4 bundle (forge/r9; R9_NOTE.txt). With all four at their defaults the search is r7's, node for node.
 extern bool CuckooRep;               // upcoming-repetition draw bound before every child search (false = off)
 extern int HistRework;               // 0 = off; 1..3: threat-keyed quiet history twin + pawn x material correction
+extern int HistReworkQuiet;          // -1 follows HistRework; 0..3 overrides the quiet-history twin
+extern int HistReworkCorrection;     // -1 follows HistRework; 0..3 overrides the pawn x material correction
 extern bool TtPruneV2;               // TT-move pruning guards, cut-node IIR, opponent-worsening RFP, margins (false = off)
 extern bool CorrHistV2;              // static-eval correction keyed by the last two moves (false = off)
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
diff -ruN base/src/search.cpp tree/src/search.cpp
--- base/src/search.cpp	2026-11-18 06:38:20.662882071 -0800
+++ tree/src/search.cpp	2026-11-18 06:55:17.583397395 -0800
@@ -179,6 +179,8 @@
 // B4 bundle (forge/r9; R9_NOTE.txt): the defaults keep r7's search.
 bool CuckooRep = false;
 int HistRework = 0;
+int HistReworkQuiet = -1;
+int HistReworkCorrection = -1;
 bool TtPruneV2 = false;
 bool CorrHistV2 = false;
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
@@ -254,6 +256,14 @@
 
 namespace {
 
+[[nodiscard]] int hist_rework_quiet_level() {
+    return tune::HistReworkQuiet < 0 ? tune::HistRework : tune::HistReworkQuiet;
+}
+
+[[nodiscard]] int hist_rework_correction_level() {
+    return tune::HistReworkCorrection < 0 ? tune::HistRework : tune::HistReworkCorrection;
+}
+
 constexpr int HistoryMax = 16384;
 static_assert(b4::HistoryLimit == HistoryMax, "B4 HistRework bounds assume this history limit");
 static_assert(b4::CorrectionEntryLimit == CorrectionLimit, "B4 HistRework bounds assume this correction limit");
@@ -1077,14 +1087,14 @@
                         ? (ss - 4)->continuation : nullptr),
               board(b),
               worker(searcher),
-              rework_side(tune::HistRework != 0 && ss != nullptr
+              rework_side(hist_rework_quiet_level() != 0 && ss != nullptr
                               ? &(*searcher.rework_history_)[static_cast<std::size_t>(b.side_to_move())]
                               : nullptr),
-              threats(tune::HistRework != 0 && ss != nullptr
+              threats(hist_rework_quiet_level() != 0 && ss != nullptr
                           ? &searcher.ensure_threat_map(b, ss->ply)
                           : nullptr),
-              quarters(tune::HistRework != 0 ? b4::threat_quarters(tune::HistRework) : 0),
-              rework(tune::HistRework != 0 && ss != nullptr),
+              quarters(hist_rework_quiet_level() != 0 ? b4::threat_quarters(hist_rework_quiet_level()) : 0),
+              rework(hist_rework_quiet_level() != 0 && ss != nullptr),
               use_threat_hist(tune::ThreatHistory) {}
 
         [[nodiscard]] int score(Move move, const std::array<Bitboard, 7>& check_squares) const {
@@ -1957,7 +1967,7 @@
         correction += (np_w + np_b) / 2;
     }
     // B4 HistRework: pawn structure x non-pawn material. |entry| <= 8192, weight <= 100: |term| <= 8192.
-    if (const int level = tune::HistRework; level != 0) {
+    if (const int level = hist_rework_correction_level(); level != 0) {
         std::uint64_t jkey;
         if (ss != nullptr) {
             if ((ss->corr_valid & 4U) == 0U) {
@@ -2012,7 +2022,7 @@
     }
     // B4 HistRework: the joint table learns the same residual step (|step| <= 2048 * 16 / 256 = 128) with a
     // self-damping update instead of the add-and-clamp above.
-    if (tune::HistRework != 0) {
+    if (hist_rework_correction_level() != 0) {
         const std::uint64_t jkey = (ss != nullptr && (ss->corr_valid & 4U) != 0U)
             ? (board.pawn_key() ^ ss->corr_mat_mix)
             : b4::joint_key(board);
@@ -2128,10 +2138,10 @@
     const std::size_t p = static_cast<std::size_t>(piece);
     const int plain = (*main_history_)[side][move.from][move.to];
     int score = plain;
-    if (tune::HistRework != 0 && ss != nullptr) {
+    if (const int level = hist_rework_quiet_level(); level != 0 && ss != nullptr) {
         const Bitboard set = threat_set_for_piece(board, ss->ply, piece_type(piece));
         const int twin = (*rework_history_)[side][b4::square_bit(set, move.from)][b4::square_bit(set, move.to)][move.from][move.to];
-        score = b4::blend(plain, twin, b4::threat_quarters(tune::HistRework));
+        score = b4::blend(plain, twin, b4::threat_quarters(level));
     }
     if (ss != nullptr) {
         if ((ss - 1)->continuation != nullptr) score += (*(ss - 1)->continuation)[p][move.to];
@@ -2158,8 +2168,10 @@
 // The change of a quiet move's score when quarters/4 of its butterfly term come from the twin:
 // blend(plain, twin) - plain. |result| <= 2 * 16384.
 int Worker::rework_quiet_delta(const Board& board, const SearchStack* ss, Move move) const {
+    const int level = hist_rework_quiet_level();
+    if (level == 0) return 0;
     const int plain = (*main_history_)[static_cast<std::size_t>(board.side_to_move())][move.from][move.to];
-    return b4::blend(plain, rework_entry(board, ss, move), b4::threat_quarters(tune::HistRework)) - plain;
+    return b4::blend(plain, rework_entry(board, ss, move), b4::threat_quarters(level)) - plain;
 }
 
 // The twin learns the same bonus and maluses as the butterfly table (the same apply_history).
@@ -2259,7 +2271,7 @@
         update_continuation(ss, board.moved_piece(quiet), quiet.to, -bonus);
     }
     // B4 HistRework: the threat-keyed twin learns the same bonus and maluses.
-    if (tune::HistRework != 0) update_rework_history(board, ss, move, bonus, quiets, quiet_count);
+    if (hist_rework_quiet_level() != 0) update_rework_history(board, ss, move, bonus, quiets, quiet_count);
 }
 
 void Worker::update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count) {
@@ -2355,7 +2367,7 @@
     }
 
     // B4 HistRework: built lazily on first read inside generate_evasions.
-    if (in_check && tune::HistRework != 0) {
+    if (in_check && hist_rework_quiet_level() != 0) {
         threat_map_ready_[static_cast<std::size_t>(ply)] = 0U;
     }
     MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Quiescence);
@@ -2712,7 +2724,7 @@
              !tt_move.is_none() && tt_bound == BoundUpper && !ss->tt_pv) --depth;
 
     // B4 HistRework: lesser-attacker maps of this node are built lazily on first read.
-    if (tune::HistRework != 0) threat_map_ready_[static_cast<std::size_t>(ply)] = 0U;
+    if (hist_rework_quiet_level() != 0) threat_map_ready_[static_cast<std::size_t>(ply)] = 0U;
     MovePicker picker(board, *this, ss, tt_move, MovePicker::Mode::Main);
 #if FORGE_SPD_NO_ZERO_MOVELISTS
     // Read only below their counts (update_quiet_stats / update_capture_stats).
@@ -3032,7 +3044,7 @@
         }
 #endif
         // B4 HistRework: the twin gets the same bonus.
-        if (tune::HistRework != 0) apply_history(rework_entry(board, ss, best_move), history_bonus(depth) / 4);
+        if (hist_rework_quiet_level() != 0) apply_history(rework_entry(board, ss, best_move), history_bonus(depth) / 4);
     } else if (tune::FailLowContinuationBonus > 0 && best_move.is_none() && !(ss - 1)->current_move.is_none() &&
                (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_capture() && ply > 0) {
         // Every move failed low: the parent's quiet move refuted this line.
diff -ruN base/src/uci.cpp tree/src/uci.cpp
--- base/src/uci.cpp	2026-11-18 05:55:01.808987941 -0800
+++ tree/src/uci.cpp	2026-11-18 06:55:18.247365366 -0800
@@ -542,6 +542,8 @@
                          // B4 bundle (forge/r9): all four default off = r7's search.
                          "option name CuckooRep type check default false\n"
                          "option name HistRework type spin default 0 min 0 max 3\n"
+                         "option name HistReworkQuiet type spin default -1 min -1 max 3\n"
+                         "option name HistReworkCorrection type spin default -1 min -1 max 3\n"
                          "option name TtPruneV2 type check default false\n"
                          "option name CorrHistV2 type check default false\n";
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
@@ -805,6 +807,10 @@
                 else note_invalid();
             } else if (name == "HistRework") {
                 apply_spin(0, forge::b4::MaxReworkLevel, [&](int clamped) { forge::tune::HistRework = clamped; });
+            } else if (name == "HistReworkQuiet") {
+                apply_spin(-1, forge::b4::MaxReworkLevel, [&](int clamped) { forge::tune::HistReworkQuiet = clamped; });
+            } else if (name == "HistReworkCorrection") {
+                apply_spin(-1, forge::b4::MaxReworkLevel, [&](int clamped) { forge::tune::HistReworkCorrection = clamped; });
             } else if (name == "MultiPV") {
                 apply_spin(1, 8, [&](int clamped) { multipv = clamped; });
             } else if (name == "Hash") {
```

### quiet_readers.patch.txt

```text
$ diff -rq /workspace/work/sol3-job16-split/applied base
exit 0
$ diff -ruN base tree > quiet_readers.patch.txt
exit 1 (trees differ)
1eb84bb6677d36b195353f0cda1da36b5769b25b6a798d414651ea78985a4d3b  quiet_readers.patch.txt
$ patch --batch --forward -p1 -F0 -d applied -i "$PWD/quiet_readers.patch.txt"
patching file include/forge/search.hpp
patching file src/search.cpp
patching file src/uci.cpp
exit 0
$ diff -rq tree applied
exit 0
```

```diff
diff -ruN base/include/forge/search.hpp tree/include/forge/search.hpp
--- base/include/forge/search.hpp	2026-11-18 06:55:28.158903585 -0800
+++ tree/include/forge/search.hpp	2026-11-18 06:59:23.891402614 -0800
@@ -403,6 +403,9 @@
 extern int HistRework;               // 0 = off; 1..3: threat-keyed quiet history twin + pawn x material correction
 extern int HistReworkQuiet;          // -1 follows HistRework; 0..3 overrides the quiet-history twin
 extern int HistReworkCorrection;     // -1 follows HistRework; 0..3 overrides the pawn x material correction
+extern int QuietReadPlainR1;         // omit HistRework's twin from quiet move ordering
+extern int QuietReadPlainR2;         // omit HistRework's twin from quiet history pruning
+extern int QuietReadPlainR3;         // omit HistRework's twin from the quiet LMR term
 extern bool TtPruneV2;               // TT-move pruning guards, cut-node IIR, opponent-worsening RFP, margins (false = off)
 extern bool CorrHistV2;              // static-eval correction keyed by the last two moves (false = off)
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
@@ -721,7 +724,7 @@
                             const Move* quiets, int quiet_count);
     void update_capture_stats(const Board& board, Move best, int depth, const Move* captures, int capture_count);
     void update_continuation(SearchStack* ss, Piece piece, int to, int bonus);
-    [[nodiscard]] int quiet_history(const Board& board, const SearchStack* ss, Move move) const;
+    [[nodiscard]] int quiet_history(const Board& board, const SearchStack* ss, Move move, bool include_rework) const;
     [[nodiscard]] int threat_quiet_bonus(const Board& board, Move move) const;
     void update_threat_quiet(const Board& board, Move move, int bonus);
     [[nodiscard]] int pawn_history_value(const Board& board, Piece piece, Move move) const;
diff -ruN base/src/search.cpp tree/src/search.cpp
--- base/src/search.cpp	2026-11-18 06:55:28.159502461 -0800
+++ tree/src/search.cpp	2026-11-18 06:59:24.671364751 -0800
@@ -181,6 +181,9 @@
 int HistRework = 0;
 int HistReworkQuiet = -1;
 int HistReworkCorrection = -1;
+int QuietReadPlainR1 = 0;
+int QuietReadPlainR2 = 0;
+int QuietReadPlainR3 = 0;
 bool TtPruneV2 = false;
 bool CorrHistV2 = false;
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
@@ -1073,11 +1076,11 @@
         const PieceToHistory* cont4;
         const Board& board;
         const Worker& worker;
-        const LesserThreatHistory::value_type* rework_side;
-        const b4::LesserThreats* threats;
         int quarters;
         bool rework;
         bool use_threat_hist;
+        const LesserThreatHistory::value_type* rework_side;
+        const b4::LesserThreats* threats;
 
         QuietScorer(const Board& b, const Worker& searcher, const SearchStack* ss)
             : main((*searcher.main_history_)[static_cast<std::size_t>(b.side_to_move())]),
@@ -1087,15 +1090,14 @@
                         ? (ss - 4)->continuation : nullptr),
               board(b),
               worker(searcher),
-              rework_side(hist_rework_quiet_level() != 0 && ss != nullptr
+              quarters(tune::QuietReadPlainR1 == 0 && hist_rework_quiet_level() != 0
+                           ? b4::threat_quarters(hist_rework_quiet_level()) : 0),
+              rework(quarters != 0 && ss != nullptr),
+              use_threat_hist(tune::ThreatHistory),
+              rework_side(rework
                               ? &(*searcher.rework_history_)[static_cast<std::size_t>(b.side_to_move())]
                               : nullptr),
-              threats(hist_rework_quiet_level() != 0 && ss != nullptr
-                          ? &searcher.ensure_threat_map(b, ss->ply)
-                          : nullptr),
-              quarters(hist_rework_quiet_level() != 0 ? b4::threat_quarters(hist_rework_quiet_level()) : 0),
-              rework(hist_rework_quiet_level() != 0 && ss != nullptr),
-              use_threat_hist(tune::ThreatHistory) {}
+              threats(rework ? &searcher.ensure_threat_map(b, ss->ply) : nullptr) {}
 
         [[nodiscard]] int score(Move move, const std::array<Bitboard, 7>& check_squares) const {
             const Piece piece = board.piece_at(move.from);
@@ -1549,7 +1551,7 @@
         count_ = quiet_start();
         seeded_ = false;
         for (const Move move : buf) {
-            int score = searcher_.quiet_history(board_, ss_, move);
+            int score = searcher_.quiet_history(board_, ss_, move, tune::QuietReadPlainR1 == 0);
             if (direct_check(move)) score += 12000;
             push_scored(move, score);
         }
@@ -1571,7 +1573,7 @@
 #else
         for (const Move move : buf) {
             if (move.is_capture() || move.is_promotion()) continue;
-            int score = searcher_.quiet_history(board_, ss_, move);
+            int score = searcher_.quiet_history(board_, ss_, move, tune::QuietReadPlainR1 == 0);
             if (direct_check(move)) score += 12000;
             push_scored(move, score);
         }
@@ -1620,7 +1622,8 @@
 #if FORGE_SEARCH_SPEED2
             return scorer.score(move, check_squares_);
 #else
-            return searcher_.quiet_history(board_, ss_, move) + (direct_check(move) ? 12000 : 0);
+            return searcher_.quiet_history(board_, ss_, move, tune::QuietReadPlainR1 == 0) +
+                   (direct_check(move) ? 12000 : 0);
 #endif
         };
 
@@ -2132,13 +2135,13 @@
     return static_cast<int>(local_nodes_ % static_cast<std::uint64_t>(width)) - span;
 }
 
-int Worker::quiet_history(const Board& board, const SearchStack* ss, Move move) const {
+int Worker::quiet_history(const Board& board, const SearchStack* ss, Move move, bool include_rework) const {
     const std::size_t side = static_cast<std::size_t>(board.side_to_move());
     const Piece piece = board.moved_piece(move);
     const std::size_t p = static_cast<std::size_t>(piece);
     const int plain = (*main_history_)[side][move.from][move.to];
     int score = plain;
-    if (const int level = hist_rework_quiet_level(); level != 0 && ss != nullptr) {
+    if (const int level = hist_rework_quiet_level(); include_rework && level != 0 && ss != nullptr) {
         const Bitboard set = threat_set_for_piece(board, ss->ply, piece_type(piece));
         const int twin = (*rework_history_)[side][b4::square_bit(set, move.from)][b4::square_bit(set, move.to)][move.from][move.to];
         score = b4::blend(plain, twin, b4::threat_quarters(level));
@@ -2768,7 +2771,14 @@
         const bool quiet = !capture && !move.is_promotion();
         const bool gives_check = picker.has_cached_gives_check() ? picker.cached_gives_check() : board.gives_check(move);
         const Piece moved = board.moved_piece(move);
-        const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);
+        const bool prune_uses_rework = tune::QuietReadPlainR2 == 0;
+        const bool lmr_uses_rework = tune::QuietReadPlainR3 == 0;
+        const int pruning_history = quiet ? quiet_history(board, ss, move, prune_uses_rework)
+                                          : capture_history_value(board, move);
+        // Both scores use the parent position and histories before making the move.
+        const int lmr_history = quiet && lmr_uses_rework != prune_uses_rework
+                                    ? quiet_history(board, ss, move, lmr_uses_rework)
+                                    : pruning_history;
 
         // Shallow-depth pruning of unpromising moves.
         // Off by default, so the predicate below is the historical guard.
@@ -2827,7 +2837,7 @@
                     note_deferred_quiet_checks();
                     continue;
                 }
-                if (lmr_depth <= tune::HistoryPruneDepth && history < history_prune_threshold) {
+                if (lmr_depth <= tune::HistoryPruneDepth && pruning_history < history_prune_threshold) {
                     trace_case();
                     quiet_fail = true;
                     continue;
@@ -2846,7 +2856,7 @@
                     (!tune::MateAlphaGuard || !is_mate_score(alpha)) &&
 #endif
                     ss->static_eval + tune::CaptureFutilityBase + tune::CaptureFutilityMultiplier * lmr_depth +
-                            capture_value(board, move) + history / 8 <= alpha) {
+                            capture_value(board, move) + pruning_history / 8 <= alpha) {
                     trace_case();
                     continue;
                 }
@@ -2951,7 +2961,7 @@
             if (gives_check) r -= 1;
             if (in_check) r -= 1;
             if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
-            if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
+            if (quiet) r -= std::clamp(lmr_history / tune::LmrHistoryDivisor, -2, 2);
             if (tune::LmrSignedCorrection && quiet && ss->static_eval != ValueNone &&
                 ss->raw_eval != ValueNone) {
                 const int correction_cp = ss->static_eval - ss->raw_eval;
diff -ruN base/src/uci.cpp tree/src/uci.cpp
--- base/src/uci.cpp	2026-11-18 06:55:28.160301288 -0800
+++ tree/src/uci.cpp	2026-11-18 06:59:25.351331875 -0800
@@ -544,6 +544,9 @@
                          "option name HistRework type spin default 0 min 0 max 3\n"
                          "option name HistReworkQuiet type spin default -1 min -1 max 3\n"
                          "option name HistReworkCorrection type spin default -1 min -1 max 3\n"
+                         "option name QuietReadPlainR1 type spin default 0 min 0 max 1\n"
+                         "option name QuietReadPlainR2 type spin default 0 min 0 max 1\n"
+                         "option name QuietReadPlainR3 type spin default 0 min 0 max 1\n"
                          "option name TtPruneV2 type check default false\n"
                          "option name CorrHistV2 type check default false\n";
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
@@ -811,6 +814,12 @@
                 apply_spin(-1, forge::b4::MaxReworkLevel, [&](int clamped) { forge::tune::HistReworkQuiet = clamped; });
             } else if (name == "HistReworkCorrection") {
                 apply_spin(-1, forge::b4::MaxReworkLevel, [&](int clamped) { forge::tune::HistReworkCorrection = clamped; });
+            } else if (name == "QuietReadPlainR1") {
+                apply_spin(0, 1, [&](int clamped) { forge::tune::QuietReadPlainR1 = clamped; });
+            } else if (name == "QuietReadPlainR2") {
+                apply_spin(0, 1, [&](int clamped) { forge::tune::QuietReadPlainR2 = clamped; });
+            } else if (name == "QuietReadPlainR3") {
+                apply_spin(0, 1, [&](int clamped) { forge::tune::QuietReadPlainR3 = clamped; });
             } else if (name == "MultiPV") {
                 apply_spin(1, 8, [&](int clamped) { multipv = clamped; });
             } else if (name == "Hash") {
```

