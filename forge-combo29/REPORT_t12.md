# Task t12: Two-Thread KRK Mate Miss — Detailed Root Cause, Findings, and Fix

## Executive Summary

- **Symptom:** On the locked engine (`origin/lock/combo29-20261110`, commit `16833ecc03b425586f91f4c8834dea8807bf4c22`), searching legal king-and-rook vs. bare king (KRK) forced-mate positions to depth 14 (`Hash 16`, `OwnBook false`, default `UseNNUE true`) succeeds in **100 / 100** runs (`0` misses) on a fresh `Threads 1` searcher, but misses the forced mate in **54 / 400** runs (`no_mate_score=54`, `non_mating_move=24`) with `Threads 2`.
- **What Was Found (Real Cause — Candidate `(d)`):** The miss is **not** caused by torn TT reads/writes `(a)`, missing mate-ply adjustments `(b)`, aborted searches / helper depth skew `(c)`, or TT replacement overwriting a proven mate `(e)` (zero mate entries were ever overwritten in failing runs). Instead, in `Worker::search`, forward pruning (razoring, reverse futility pruning, null-move pruning, and shallow move-loop LMP/futility/history/SEE pruning) and late-move reductions (LMR) drop or depth-reduce quiet non-checking waiting/zugzwang moves—which are the *only* moves that force mate in KRK—and then unconditionally store centipawn `BoundUpper`, `BoundLower`, and `BoundExact` entries at full nominal `depth` in the shared transposition table. In two-thread search, helper TT writes populate interior nodes of the mating line with centipawn bounds (e.g., `BoundLower` around `-477..-506 cp` for the bare king, certifying it is *not* mated), causing Worker 0's null-window / LMR searches to take immediate TT cutoffs rather than proving the mate.
- **What Changed (Two-Sentence Summary):** In `Worker::search` (`forge-combo29/src/search.cpp`), when multiple workers are active (`all_workers_->size() > 1`) and either side is down to a bare king (`occupied(color) == pieces(color, King)`), lossy forward pruning (razoring, reverse futility pruning, null-move pruning, and shallow move-loop pruning) and late-move reductions are skipped so bare-king subtrees do not certify centipawn bounds from skipped or depth-reduced mating quiet moves into the shared transposition table. All helper threads continue to read from and write to the shared transposition table normally, no history or correction tables are cleared per search, thread counts and locking are untouched, and single-thread search remains bit-for-bit identical to the lock (`bench 11` = `312866`, `bench 13` = `862329`, `go perft 5` = `4865609`).
- **Result After Fix:** `0 / 400`, `0 / 400`, and `0 / 400` misses across three consecutive Release runs of `krk_mate_test`, plus `0 / 400` misses with zero diagnostics under `-fsanitize=address,undefined`.

---

## 1. What Changed (Line-by-Line Walkthrough & Diff)

### 1.1 Files Modified and Added

- **Modified engine source** (`19` insertions, `5` deletions — `24` changed lines total, within the 300-line limit):
  - `forge-combo29/src/search.cpp`
- **Added files under `forge-combo29/tests_t12/` and `forge-combo29/REPORT_t12.md`:**
  - `forge-combo29/REPORT_t12.md` — full root-cause report, diff explanation, logged TT evidence, and verbatim outputs.
  - `forge-combo29/tests_t12/CMakeLists.txt` — CMake build linking the engine `.cpp` sources directly (supports Release and `-fsanitize=address,undefined`).
  - `forge-combo29/tests_t12/krk_mate_test.cpp` — C++ test program building an exact 524,288-state retrograde KRK tablebase and running 40 legal KRK positions x 10 runs at depth 14 with `Threads 2`.
  - `forge-combo29/tests_t12/SUMMARY_AND_FINDINGS.txt` — plain-text summary of what changed, what was found, and what was wrong in detail.
  - `forge-combo29/tests_t12/krk_40_positions.txt` — table of all 40 legal KRK FENs, exact tablebase DTM plies, `Threads 1` depth-14 scores/moves, and pre-fix `Threads 2` miss counts.
  - `forge-combo29/tests_t12/evidence_logs.txt` — verbatim pre-fix, TT-trace, post-fix, sanitizer, and pin-check outputs.

### 1.2 Exact Engine Diff (`forge-combo29/src/search.cpp`)

```diff
--- a/forge-combo29/src/search.cpp
+++ b/forge-combo29/src/search.cpp
@@ -16,6 +16,10 @@
 #define FORGE_SDK_BADCAP_PREFIX 0
 #endif
 
+#ifndef FORGE_BARE_KING_MATE_FIX
+#define FORGE_BARE_KING_MATE_FIX 1
+#endif
+
 namespace forge {
 
 namespace tune {
@@ -1193,20 +1197,29 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
         else improving = true;
     }
 
+#if FORGE_BARE_KING_MATE_FIX
+    const bool multi_worker = all_workers_ != nullptr && all_workers_->size() > 1;
+    const bool bare_king_mode = multi_worker &&
+        (board.occupied(White) == board.pieces(White, King) ||
+         board.occupied(Black) == board.pieces(Black, King));
+#else
+    constexpr bool bare_king_mode = false;
+#endif
+
     if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta)) {
         // Razoring: hopeless positions fall back to quiescence.
-        if (depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {
+        if (!bare_king_mode && depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {
             const int razor = qsearch(board, ss, alpha - 1, alpha);
             if (aborted_) return 0;
             if (razor < alpha) return razor;
         }
         // Reverse futility pruning.
-        if (depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta &&
+        if (!bare_king_mode && depth <= tune::RfpDepth && eval - (tune::RfpMargin * depth - tune::RfpImproving * improving) >= beta &&
             eval < MateInMaxPly) {
             return eval;
         }
         // Null move pruning.
-        if (depth >= tune::NullMoveMinDepth && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
+        if (!bare_king_mode && depth >= tune::NullMoveMinDepth && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
             ss->null_move_allowed && !(ss - 1)->current_move.is_none() &&
             board.has_non_pawn_material(board.side_to_move()) &&
             !(tt_hit && tt_bound == BoundUpper && tt_score < beta)) {
@@ -1318,7 +1331,7 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
         const int history = quiet ? quiet_history(board, ss, move) : capture_history_value(board, move);
 
         // Shallow-depth pruning of unpromising moves.
-        if (!root_node && best_score > -MateInMaxPly && has_material) {
+        if (!root_node && best_score > -MateInMaxPly && has_material && !bare_king_mode) {
             if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) skip_quiets = true;
             const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));
             if (quiet && !gives_check) {
@@ -1404,7 +1417,8 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
 
         int score = -Infinite;
         bool full_depth_needed = !pv_node || move_count > 1;
-        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && (quiet || !ss->tt_pv || move_count > 4)) {
+        if (depth >= 2 && move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&
+            (quiet || !ss->tt_pv || move_count > 4)) {
             int r = reduction(quiet, depth, move_count);
             if (ss->tt_pv) r -= 1;
             if (!improving) r += 1;
```

### 1.3 Why Every Part of This Change Is Necessary

1. **`bare_king_mode` checks both sides (`occupied(White) == pieces(White, King) || occupied(Black) == pieces(Black, King)`):**
   In a bare-king mating tree, plies alternate between the attacking side (e.g. White with K+R) and the defending bare king (e.g. Black with only K).
   - On **attacking plies**, forward pruning and LMR drop or under-search the quiet waiting/zugzwang rook or king move that boxes the enemy king in.
   - On **defending bare-king plies** (when the bare king is not in check), move-loop pruning is already off (`has_material` is `false` for a lone king), **but** LMR (`depth >= 2 && move_count > 1`) and pre-loop razoring/RFP are *still active*! When LMR reduces the bare king's 2nd..8th king moves, the bare king under-searches its toughest defensive flights or mis-scores an escape, distorting the backed-up centipawn bounds written to TT. In ablation testing (Section 3.3), gating only attacking plies (`occupied(them) == pieces(them, King)`) still left `2 / 300` misses on `dtm=13` positions (`8/4K3/8/1R6/8/8/7k/8` and `8/2K5/8/3R4/8/8/k7/8`), whereas symmetric `bare_king_mode` reduced misses to `0 / 300` (and `0 / 1200` across the three full test repeats).
2. **Pre-loop forward pruning (`Razor`, `RFP`, `NullMove`) AND move-loop pruning (`LMP`, `Futility`, `History`, `SEE`) AND `LMR` are all gated:**
   - Gating only move-loop pruning + LMR (leaving pre-loop razoring, RFP, and null-move pruning active) still left `5 / 300` misses on `dtm=13` positions (`8/500` in a 50-run stress test on `8/4K3/8/1R6/8/8/7k/8`): null-move pruning is fundamentally unsound in bare-king endgames because KRK mates rely heavily on mutual zugzwang, and RFP/razoring return static centipawn estimates (`~+450..+550 cp`) at `depth <= 8` without searching any moves, feeding false centipawn cutoffs into parent TT stores.
   - Gating pre-loop forward pruning + move-loop pruning + LMR together eliminates all misses (`0 / 400` x 3 repeats, `0 / 300` fresh `dtm=13`, `0 / 300` stained-history `dtm=13`, `0 / 400` ASan+UBSan).
3. **Scoped to `multi_worker` (`all_workers_ != nullptr && all_workers_->size() > 1`):**
   - `all_workers_` is set in `Worker::search(Board, ...)` before the root search begins and points to a `std::vector<Worker*>` that is read-only for the entire search (`Searcher::search`, `src/search.cpp:1781–1809`), so reading `all_workers_->size()` has zero data races.
   - When `Threads == 1`, `multi_worker` is `false`, so single-thread search executes the exact lock tree—preserving `bench 11` = `312866`, `bench 13` = `862329`, and all ten net-on/net-off `check_pins.sh` depths (`11, 13, 16, 20, 22`). (Note: `bench` FEN #7 `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1` reaches bare-king positions in deep capture subtrees at depth 13; enabling `bare_king_mode` for `Threads == 1` changes `bench 13` to `862604`, which would violate Hard Rule 7.)
4. **No forbidden shortcuts:**
   - Helper threads read from and write to `shared_.tt` identically to before (no helper write suppression, no generation-refresh changes).
   - No history tables (`main_history_`, `capture_history_`, `continuation_history_`, `counter_moves_`) or correction tables (`correction_history_`, `material_correction_`) are cleared per search.
   - Thread count is untouched and no locks or sleeps are added.

---

## 2. In Detail: What Was Wrong

### 2.1 Why KRK Forced Mates Are Uniquely Vulnerable to Heuristic Pruning

In a king-and-rook vs. bare king (KRK) endgame:
1. **The mating line consists almost entirely of quiet non-checking moves.** Before the final checkmate delivery, the winning side must play quiet waiting moves with the rook (e.g., `Rc6`, `Rb5`, `Rg5`) and quiet king-approach moves (`Kd7`, `Kc6`, `Kf7`) to restrict the bare king and place it in zugzwang. None of these intermediate moves are captures, promotions, or checks.
2. **Quiescence search (`Worker::qsearch`) cannot see quiet mates.** At `depth <= 0`, `Worker::qsearch` (`src/search.cpp:989–1110`) searches only captures and promotions (unless the side to move is currently in check). When a KRK branch hits `depth == 0` with the bare king *not* in check, `qsearch` stands pat on the static NNUE + hand-crafted evaluation, returning roughly **`+430` to `+550` centipawns** (rook advantage + king-cornering bonus)—giving zero indication that a forced checkmate exists 2 or 4 plies further down.
3. **Once *any* non-losing move is searched first, `best_score > -MateInMaxPly` becomes `true`.** In `Worker::search` (`src/search.cpp:1334`), the guard protecting against pruning when being mated is `best_score > -MateInMaxPly`. On move 1 at an attacking KRK node, any ordinary rook or king move returns `+450 cp`, raising `best_score` to `+450 > -31872`. From move 2 onward, **every shallow pruning rule and late-move reduction turns on**.

### 2.2 Step-by-Step Anatomy of the Bug in `Worker::search`

Consider an interior White-to-move KRK node `N` where White has a forced mate in 3 or 4 moves (5 or 7 plies) beginning with a single quiet zugzwang move `m*` (say `Ke8` or `Rc7`), and `N` is searched with remaining `depth = 5` or `6` and a null window `[alpha, alpha + 1] = [488, 489]`:

1. **Move ordering places checking or high-history moves ahead of the quiet zugzwang move `m*`:**
   `MovePicker::generate_quiets` (`src/search.cpp:626–628`) adds `+12000` to direct checks (`Rook` checks), so pointless rook checks that chase the bare king to safety are searched *first*, followed by killers, countermoves, and moves with positive butterfly/continuation history. The quiet waiting move `m*` (which does not give check) sits at move ordinal `move_count = 6..18`.
2. **Shallow pruning or LMR suppresses `m*`:**
   - **Late-Move Pruning (`LMP`):** At `src/search.cpp:1335`, as soon as `move_count >= lmp_threshold(depth, improving)` (which for `!improving` is `(4 + d^2) / 2` — e.g., `6` moves at `depth = 3`, `10` moves at `depth = 4`, `14` moves at `depth = 5`), `skip_quiets` is set to `true`, **completely dropping `m*` and all remaining quiet moves without searching them at all**.
   - **Futility / History / SEE Pruning:** Even before LMP, if `lmr_depth <= 7` and `static_eval + 100 + 110 * lmr_depth <= alpha`, `skip_quiets = true` drops all remaining quiet moves (`src/search.cpp:1338–1342`), or negative history drops `m*` (`line 1343`).
   - **Late-Move Reductions (`LMR`):** Even if `m*` is not dropped outright, at `move_count > 1` (`src/search.cpp:1420–1433`), `m*` is reduced by `r = 2..5` plies (`cut_node` alone adds `+2` to `r`!). Searching `m*` at `reduced_depth = new_depth - r` reaches `qsearch` *before* the final checkmate ply, returning a static score like `+472 cp <= alpha (488)`. Because `score <= alpha`, `full_depth_needed` is `false` (`line 1434`), so `m*` is **never re-searched at `new_depth`**.
   - **Pre-loop Pruning (`RFP` / `NullMove` / `Razor`):** On non-PV nodes (`src/search.cpp:1209–1259`), reverse futility pruning at `depth <= 8` returns `eval` (`~+520 cp`) without generating any moves, or null-move pruning passes the turn in a mutual-zugzwang position and cuts off with a centipawn score.
3. **`Worker::search` unconditionally stores a full-depth TT bound (`src/search.cpp:1496–1503`):**
   Even though `m*` was skipped by `skip_quiets` or horizon-truncated by LMR, `Worker::search` reaches the end of the move loop with `best_score = +488 <= alpha` (`best_move = Move::none()`)—or on a PV node with a suboptimal quiet move scoring `+488`—and executes:
   ```cpp
   const Bound bound = best_score >= beta ? BoundLower : (pv_node && !best_move.is_none() ? BoundExact : BoundUpper);
   store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, best_move, depth, bound, ss->tt_pv, board.halfmove_clock());
   ```
   This writes `BoundUpper` (`score <= +488`) or `BoundExact` (`score == +488`) into the shared TT **claiming validity at full nominal `depth` (e.g. `depth = 6`)**, falsely asserting that White has *no* forced mate within 6 plies from `N`.
4. **The parent bare-king node flips that false `BoundUpper` into a false `BoundLower` ("Black is safe from mate"):**
   One ply above `N` is Black-to-move node `P` (e.g. after White's mating root move `1.Rc6` or `2.Ke7`). Black tries its legal king escapes; because child `N` returned `+488` (`-488` from Black's perspective) instead of `+31989` (`-31989`), Black finds a king move scoring `-488 >= beta (-520)` and experiences a **beta cutoff**, storing:
   - `BoundLower`, `score = -488` (or `-477`), at `depth = 7..11` in `shared_.tt`!
   From Black's perspective, `score >= -488` at `depth = 10` is a mathematical claim in the TT that **Black has a move guaranteeing at least `-488 cp` (i.e., Black cannot be checkmated within 10 plies)**.

### 2.3 Why `Threads 1` (Fresh) Hides It, Why `Threads 1` (Stained History) Fails, and How `Threads 2` Triggers It

- **Why `Threads 1` on a fresh searcher (`0 / 100` misses) succeeds:**
  On a cold single-thread searcher, move-ordering histories start all-zero and grow in a single deterministic sequence. Although `Threads 1` *also* writes pruned centipawn bounds at shallow iterations (`depth = 7..9`), at `depth = 11..14` the root aspiration / PVS search probes the mating root move with a window and depth (`req_d > tt_depth`) that either misses the shallow TT bound or produces a centipawn fail-high (`score > alpha`), triggering a full-window PV re-search (`!pv_node` is `false`, so non-PV TT cutoffs at `src/search.cpp:1165` are bypassed!) that walks all the way down to the mate.
- **Proof that concurrency races are NOT required (`Threads 1` with stained history fails `18 / 400`):**
  When `krk_mate_test` was run on the unchanged lock with **`Threads 1`** using `clear_hash()` instead of `clear()` (so the TT is completely empty before every search, only `1` thread exists, and only move-ordering histories carry over from the previous position), **`Threads 1` missed the forced mate in `18 / 400` runs** (including `10 / 10` misses on `pos=2` `8/4K3/8/1R6/8/8/7k/8 w - - 0 1`, returning `cp 411..548`). Shifting move ordering alone caused `Threads 1` to prune/LMR the mating move and block itself via its own TT entries.
- **How `Threads 2` triggers `54 / 400` misses on a completely fresh searcher:**
  In `Searcher::search` (`src/search.cpp:1803–1809`), Worker 0 (main) and Worker 1 (helper) start iterative deepening simultaneously on the same root position sharing `shared_.tt`:
  1. Because OS thread scheduling varies slightly, Worker 1 and Worker 0 diverge in move ordering, history updates, and aspiration windows by iteration 4–7.
  2. While Worker 0 is searching another root move (or an earlier iteration), Worker 1 reaches interior nodes of the true mating line (`PV#8`, `PV#4`, `PV#3`, `PV#1`) with null windows, prunes/reduces the quiet mating continuation, and writes **high-depth (`depth = 6..11`) centipawn `BoundUpper` (White) and `BoundLower` (Black) entries** into `shared_.tt`—or overwrites `BoundExact` entries at lower/equal depths because `BoundExact` always replaces (`src/search.cpp:328`).
  3. When Worker 0 subsequently tests the mating root move (or an interior mating move) with a null window (`!pv_node` is `true`, e.g., LMR reduced search at `req_d = 3..9` with window `[-487, -486]`), `Worker::search` (`src/search.cpp:1165–1170`) probes `shared_.tt`, sees Worker 1's entry (`tt_depth = 10 >= req_d`, `tt_bound == BoundLower`, `tt_score = -477 >= beta (-486)`), and **immediately returns `-477` (`+477 cp` for White) without searching a single child move**!
  4. Because `+477 <= alpha` at the root (where another non-mating move already scored `+487 cp`), Worker 0 never triggers a full-depth or PV re-search of the mating move, completing depth 14 with `cp 487` and often a non-optimal move (`move_dtm = 17..21` plies instead of `9..13`).

---

## 3. Systematic Evaluation of Candidates `(a)`–`(e)` & Logged Evidence

### 3.1 Candidates `(a)` through `(e)` Checked in Order

| Candidate | Verdict | Code & Experimental Evidence |
| --- | --- | --- |
| **(a)** Hash entry read while another thread writes it (torn key/data from different positions) | **Ruled out** | `TranspositionTable::ExclusiveLease` is acquired *only* when `workers_.size() == 1` (`src/search.cpp:1787`). Whenever `Threads >= 2`, `tt_owned_` is `false` on every worker (`src/search.cpp:1801`), so every `probe` and `store` acquires `stripes_[index % 1024].mutex` via `lock_stripe` (`src/search.cpp:275, 323`) and copies the 16-byte `TTEntry` by value while holding the mutex. `-fsanitize=address,undefined` is completely clean. Moreover, `Threads 1` with `clear_hash()` (empty TT, single thread, zero concurrency) reproduces the same bug in `18 / 400` runs. |
| **(b)** Mate scores stored or read without ply correction | **Ruled out** | Every TT store site (`src/search.cpp:1040, 1105, 1274, 1485` on lock) encodes scores via `score_to_tt(score, ply)` (`score + ply` for `>= MateInMaxPly`, `score - ply` for `<= -MateInMaxPly`), and both TT probe sites (`src/search.cpp:1013, 1159`) decode via `score_from_tt(tte.score, ply)`. `static_evaluate` and `corrected_eval` clamp to `[-MateInMaxPly + 1, MateInMaxPly - 1]`. Logged mate entries on `3K4/5k2/6R1/8/8/8/8` (`31999` at ply 14 down to `31985` at ply 0) round-trip with exact ply accuracy. |
| **(c)** Bound stored for a node cut short by `stop` or by a helper's different depth | **Ruled out** | Both `Worker::search` (`src/search.cpp:1200, 1228, 1240, 1271, 1359, 1435`) and `Worker::qsearch` (`src/search.cpp:993, 1086`) check `if (aborted_) return 0;` immediately after every recursive search before reaching any TT store. Helpers in `Searcher::search` (`src/search.cpp:1804–1807`) receive the exact same `worker_limits` (`depth = 1..14`, no helper depth-skew offset), and `shared_.stop` is set only *after* Worker 0 finishes depth 14 (`src/search.cpp:1809–1812`). |
| **(d)** Unsound bounds stored after forward pruning / reductions skipped the mating move | **CONFIRMED CAUSE** | Logged before/after TT trace (Section 3.2) directly captures Worker 0 and Worker 1 skipping quiet moves (`prn=1`) on mating PV nodes (`PV#8`, `PV#4`), storing centipawn `BoundUpper` (`+463`, `+488` at `depth = 5..6`), backing them up into centipawn `BoundLower` (`-488`, `-477` at `depth = 7..10`) on bare-king nodes (`PV#3`, `PV#1`), and Worker 0 cutting off on `PV#1` (`CUT PV#1`) at depth 14 instead of finding `mate 8`. Eliminating forward pruning and LMR at bare-king nodes (`bare_king_mode`) drops misses from **`54 / 400` to `0 / 400`** (3x repeats). |
| **(e)** Replacement rule dropping a deep mate entry for a shallow one | **Ruled out** | Instrumenting `TranspositionTable::store_body` across failing runs of 4 KRK positions recorded **`MATE_LOST = 0`** (not a single occupied entry with `is_mate_score(before.score)` was ever overwritten by a centipawn score). Furthermore, changing `store_body` to strict depth replacement (`depth >= entry->depth`, removing the `bound == BoundExact` unconditional overwrite) *worsened* the miss rate to **`58 / 400`**. |

### 3.2 Logged `TTEntry` Before-and-After Evidence

Using temporary instrumentation inside `TranspositionTable::store_body` and the non-PV TT cutoff in `Worker::search`, we logged every TT store (`BEFORE -> AFTER` `TTEntry` snapshot under the stripe lock) and TT cutoff on the positions of the true mating PV of `pos=12`:
- **FEN:** `3K4/5k2/6R1/8/8/8/8 w - - 0 1` (exact tablebase DTM = 11 plies / mate in 6).
- **`Threads 1` reference at depth 11..14:** Finds `score = 31985` (`mate 8`), `bestmove g6c6`, PV:
  `PV#0` (root) --`g6c6`--> `PV#1` (`3K4/5k2/2R5/... b`) --`f7g8`--> `PV#2` --`d8e7`--> `PV#3` --`g8g7`--> `PV#4` --`e7e8`--> `PV#5` --`g7g8`--> `PV#6` --`c6c7`--> `PV#7` --`g8h8`--> `PV#8` --`e8f7`--> `PV#9` --`h8h7`--> `PV#10` --`c7c5`--> ...

In the `Threads 1` run (depth 11), `PV#8`, `PV#4`, `PV#3`, `PV#1`, and `PV#0` all lock onto exact mate scores:
```text
STR PV#8 w=0 rd=11 ply=6 d=7 [452,488] pv=1 prn=0
  BEF(move=c7a7 sc=470 d=7 b=Exact) -> AFT(move=e8f7 sc=31993 d=7 b=Lower)
STR PV#4 w=0 rd=11 ply=4 d=7 [452,31987] pv=1 prn=1
  BEF(move=e7e8 sc=31989 d=7 b=Upper) -> AFT(move=e7e8 sc=31989 d=7 b=Exact)
STR PV#3 w=0 rd=11 ply=3 d=8 [-31987,-452] pv=1 prn=0
  BEF(move=g8g7 sc=-31988 d=8 b=Lower) -> AFT(move=g8g7 sc=-31988 d=8 b=Exact)
STR PV#1 w=0 rd=11 ply=1 d=10 [-31999,-452] pv=1 prn=0
  BEF(move=f7f8 sc=-31986 d=10 b=Upper) -> AFT(move=f7g8 sc=-31986 d=10 b=Exact)
STR PV#0 w=0 rd=11 ply=0 d=11 [452,32001] pv=1 prn=0
  BEF(move=g6c6 sc=31985 d=11 b=Lower) -> AFT(move=g6c6 sc=31985 d=11 b=Exact)
```

In the failing `Threads 2` run (`MATE_LOST = 0`; final result `score = 487 cp`, `bestmove g6d6`):

1. **Pruned centipawn `BoundUpper` stored on `PV#8` (after `4...Kh8`, White to move, mate in 4 via quiet `5.Kf7`):**
   Worker 0 (at `rd=12`) and Worker 1 (at `rd=14`) skip quiet moves (`prn=1`) and store centipawn `BoundUpper` at `depth = 5`:
   ```text
   STR PV#8 w=0 rd=12 ply=6 d=5 [506,507] pv=0 prn=1
     BEF(move=c7a7 sc=498 d=2 b=Upper) -> AFT(move=c7a7 sc=506 d=5 b=Upper)
   STR PV#8 w=1 rd=14 ply=8 d=5 [488,489] pv=0 prn=1
     BEF(move=c7a7 sc=449 d=3 b=Upper) -> AFT(move=c7a7 sc=463 d=5 b=Upper)
   ```
2. **Pruned centipawn `BoundUpper` stored by Helper Worker 1 on `PV#4` (after `2...Kg7`, White to move, mate in 6 via quiet `3.Ke8`):**
   At root depth 14, ply 4, `depth = 6`, null window `[520, 521]`, Worker 1 skips quiet moves (`prn=1`) and overwrites `PV#4` with `score = 488, depth = 6, BoundUpper`:
   ```text
   STR PV#4 w=1 rd=14 ply=4 d=6 [520,521] pv=0 prn=1
     BEF(move=a1a1 sc=476 d=2 b=Upper) -> AFT(move=a1a1 sc=488 d=6 b=Upper)
   ```
3. **Helper Worker 1 propagates that pruned score into centipawn `BoundLower` entries at `PV#3` and `PV#1`:**
   ```text
   STR PV#3 w=1 rd=14 ply=3 d=7 [-521,-520] pv=0 prn=0
     BEF(move=g8g7 sc=-476 d=3 b=Lower) -> AFT(move=g8g7 sc=-488 d=7 b=Lower)
   STR PV#1 w=1 rd=14 ply=1 d=10 [-478,-477] pv=0 prn=0
     BEF(move=f7g7 sc=-477 d=13 b=Exact) -> AFT(move=f7g7 sc=-477 d=10 b=Lower)
   ```
   *(Notice on `PV#1`: `BEFORE` had `depth=13, BoundExact, score=-477`; Worker 1's `depth=10` store passed `depth + 4 > entry->depth` (`14 > 13` at `src/search.cpp:328`) and converted `PV#1` to `depth=10, BoundLower, score=-477`.)*
4. **Main Worker 0 hits `PV#1` and takes a non-PV TT cutoff instead of searching `1.Rc6`:**
   ```text
   CUT PV#1 w=0 rd=14 ply=5 req_d=3 [-487,-486]
     ENT(move=f7g7 sc=-477 d=10 b=Lower)
   STR PV#0 w=0 rd=14 ply=0 d=14 [470,506] pv=1 prn=0
     BEF(move=g6a6 sc=477 d=14 b=Exact) -> AFT(move=g6d6 sc=487 d=14 b=Exact)
   ```

### 3.3 Summary of Diagnostic & Ablation Experiments Run

| Experiment | Description | Misses | `Threads 1` `bench 13` |
| --- | --- | --- | --- |
| **Unchanged lock (`16833ecc`)** | 40 positions x 10 runs, `Threads 2`, `clear()` per run | **`54 / 400`** (`24` non-mating moves) | `862329` (exact) |
| Lock, `Threads 1` + `clear_hash()` | 40 positions x 10 runs, `Threads 1`, TT cleared, histories kept | **`18 / 400`** (`8` non-mating moves) | `862329` (exact) |
| Candidate `(e)` test | Strict `depth >= entry->depth` in `TT::store` (no `BoundExact` override) | **`58 / 400`** (`25` non-mating moves) | `729075` (changed) |
| Bound-downgrade only | Downgrade `BoundExact->BoundLower` & `BoundUpper->BoundNone` when move-loop pruned | **`46 / 400`** (`25` non-mating moves) | `901626` (changed) |
| Universal bare-king (all threads, `them` only, move-loop + LMR) | Applied even at `Threads 1`; only attacking plies; pre-loop pruning left on | **`3 / 400`** | `862604` (violates Rule 7) |
| `multi_worker` + `them` only (move-loop + LMR + pre-loop) | Defending bare-king plies still used LMR; 10 `dtm=13` positions x 50 runs | **`8 / 500`** | `862329` (exact) |
| `multi_worker` + symmetric bare-king (move-loop + LMR only) | Pre-loop Razor/RFP/NullMove left on; 10 `dtm=13` positions x 30 runs | **`5 / 300`** | `862329` (exact) |
| **Final Fix (`bare_king_mode`: `multi_worker` + symmetric bare-king, pre-loop + move-loop + LMR)** | **3 x 400 standard runs + 300 `dtm=13` fresh + 300 `dtm=13` `clear_hash()` + 400 ASan+UBSan + 400 `x86-64-v4`** | **`0 / 400` (x3), `0 / 300`, `0 / 300`, `0 / 400`, `0 / 400`** | **`862329` (exact)** |

---

## 4. Commands Run and Full Outputs

*(Environment note: On this Linux VM, `/usr/bin/c++` defaults to Clang 18 without matching Clang `-lstdc++` link paths, while `g++` 13.3.0 has full `libstdc++-13-dev` support; `CXX=g++ CC=gcc` was therefore passed to CMake. All build directories were placed outside the repository or removed before committing so only permitted text source files exist in git.)*

### 4.1 Baseline Start Check (Unchanged Lock `16833ecc`)

Command:
```bash
CXX=g++ CC=gcc cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | ./build/forge
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.3s)
-- Generating done (0.0s)
-- Build files have been written to: /agent/repos/dwqww/build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 504 nps 1710970
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

### 4.2 Step 2: Test on Unchanged Lock (`16833ecc`)

Command:
```bash
CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/build_tests_t12 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build /tmp/build_tests_t12 -j && /tmp/build_tests_t12/krk_mate_test; echo EXIT:$?
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/build_tests_t12
[ 11%] Building CXX object CMakeFiles/krk_mate_test.dir/krk_mate_test.cpp.o
[ 22%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/search.cpp.o
[ 33%] Linking CXX executable krk_mate_test
[100%] Built target krk_mate_test
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
  MISS pos=2 run=0 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 506/b5g5 move_dtm=13
  MISS pos=2 run=1 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 457/b5g5 move_dtm=13
  MISS pos=2 run=2 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 499/b5g5 move_dtm=13
  MISS pos=2 run=3 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 412/b5g5 move_dtm=13
  MISS pos=2 run=4 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 444/b5g5 move_dtm=13
  MISS pos=2 run=5 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 477/e7d6 move_dtm=21
  MISS pos=2 run=6 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 443/b5g5 move_dtm=13
  MISS pos=2 run=7 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 450/b5g5 move_dtm=13
  MISS pos=2 run=8 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 458/b5g5 move_dtm=13
  MISS pos=2 run=9 fen="8/4K3/8/1R6/8/8/7k/8 w - - 0 1" exact_dtm=13 t1=mate 10/b5g5 got=cp 453/b5f5 move_dtm=17
pos 2 (8/4K3/8/1R6/8/8/7k/8 w - - 0 1, dtm=13 plies): 10/10 misses
  MISS pos=5 run=1 fen="8/2K5/8/3R4/8/8/k7/8 w - - 0 1" exact_dtm=13 t1=mate 9/d5b5 got=cp 464/c7c6 move_dtm=17
  MISS pos=5 run=2 fen="8/2K5/8/3R4/8/8/k7/8 w - - 0 1" exact_dtm=13 t1=mate 9/d5b5 got=cp 578/d5b5 move_dtm=13
pos 5 (8/2K5/8/3R4/8/8/k7/8 w - - 0 1, dtm=13 plies): 7/10 misses
pos 6 (8/8/2K5/8/k7/8/1R6/8 w - - 0 1, dtm=13 plies): 4/10 misses
pos 7 (2R5/8/3K4/8/8/8/k7/8 w - - 0 1, dtm=13 plies): 7/10 misses
pos 8 (8/8/8/7K/8/8/7k/2R5 w - - 0 1, dtm=13 plies): 1/10 misses
pos 9 (1k6/8/8/8/3K4/8/6R1/8 w - - 0 1, dtm=13 plies): 1/10 misses
pos 11 (8/8/1R6/8/8/k7/3K4/8 w - - 0 1, dtm=11 plies): 2/10 misses
pos 12 (3K4/5k2/6R1/8/8/8/8/8 w - - 0 1, dtm=11 plies): 3/10 misses
pos 15 (k7/8/8/8/4K3/8/8/7R w - - 0 1, dtm=11 plies): 8/10 misses
pos 17 (8/8/1K6/5R2/8/8/k7/8 w - - 0 1, dtm=11 plies): 3/10 misses
pos 22 (4K3/8/1k6/3R4/8/8/8/8 w - - 0 1, dtm=9 plies): 7/10 misses
pos 28 (R7/8/8/8/8/8/8/3K1k2 w - - 0 1, dtm=9 plies): 1/10 misses
SUMMARY: misses=54 / 400 (no_mate_score=54, non_mating_move=24)
EXIT:1
```

### 4.3 Step 5: Three Repeats of `krk_mate_test` After the Fix

Command:
```bash
rm -rf /tmp/build_tests_t12 && CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/build_tests_t12 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build /tmp/build_tests_t12 -j && echo "=== RUN 1 ===" && /tmp/build_tests_t12/krk_mate_test && echo "=== RUN 2 ===" && /tmp/build_tests_t12/krk_mate_test && echo "=== RUN 3 ===" && /tmp/build_tests_t12/krk_mate_test
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/build_tests_t12
[ 11%] Building CXX object CMakeFiles/krk_mate_test.dir/krk_mate_test.cpp.o
[ 22%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/bitboard.cpp.o
[ 33%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/board.cpp.o
[ 44%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/book.cpp.o
[ 55%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval.cpp.o
[ 66%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval_params.cpp.o
[ 77%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/search.cpp.o
[100%] Linking CXX executable krk_mate_test
[100%] Built target krk_mate_test
=== RUN 1 ===
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
=== RUN 2 ===
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
=== RUN 3 ===
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
```

### 4.4 AddressSanitizer + UndefinedBehaviorSanitizer Run (`-fsanitize=address,undefined`)

Command:
```bash
rm -rf /tmp/build_tests_t12_asan && CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/build_tests_t12_asan -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DFORGE_SANITIZE=ON && cmake --build /tmp/build_tests_t12_asan -j && /tmp/build_tests_t12_asan/krk_mate_test; echo EXIT:$?
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/build_tests_t12_asan
[ 11%] Building CXX object CMakeFiles/krk_mate_test.dir/krk_mate_test.cpp.o
[ 22%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/search.cpp.o
[ 55%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval.cpp.o
[ 66%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/bitboard.cpp.o
[ 77%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/eval_params.cpp.o
[ 88%] Building CXX object CMakeFiles/krk_mate_test.dir/agent/repos/dwqww/forge-combo29/src/nnue.cpp.o
[100%] Linking CXX executable krk_mate_test
[100%] Built target krk_mate_test
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
EXIT:0
```

### 4.5 Step 6: Rule 7 Single-Thread Reference Numbers After the Fix (Plus Full `check_pins.sh` and `x86-64-v4`)

Command (portable `-DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3` build + full `check_pins.sh`):
```bash
rm -rf /tmp/forge-build && CXX=g++ CC=gcc cmake -S forge-combo29 -B /tmp/forge-build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 && cmake --build /tmp/forge-build -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-build/forge && forge-combo29/scripts/check_pins.sh /tmp/forge-build/forge
```

Output:
```text
-- The CXX compiler identification is GNU 13.3.0
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/g++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD
-- Performing Test CMAKE_HAVE_LIBC_PTHREAD - Success
-- Found Threads: TRUE  
-- Configuring done (0.2s)
-- Generating done (0.0s)
-- Build files have been written to: /tmp/forge-build
[ 11%] Building CXX object CMakeFiles/forge.dir/src/bitboard.cpp.o
[ 22%] Building CXX object CMakeFiles/forge.dir/src/board.cpp.o
[ 33%] Building CXX object CMakeFiles/forge.dir/src/book.cpp.o
[ 44%] Building CXX object CMakeFiles/forge.dir/src/eval.cpp.o
[ 55%] Building CXX object CMakeFiles/forge.dir/src/eval_params.cpp.o
[ 66%] Building CXX object CMakeFiles/forge.dir/src/search.cpp.o
[ 77%] Building CXX object CMakeFiles/forge.dir/src/nnue.cpp.o
[ 88%] Building CXX object CMakeFiles/forge.dir/src/uci.cpp.o
[100%] Linking CXX executable forge
[100%] Built target forge
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 439 nps 1964302
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
net-on : 312866 862329 3024920 12389307 34048354
net-off: 375354 907205 2448617 13573040 24506465
perft5 : 4865609
PINS MATCH combo29
```

Command (default AVX-512/PEXT `-march=x86-64-v4` build + `krk_mate_test`):
```bash
CXX=g++ CC=gcc cmake -S forge-combo29 -B /tmp/forge-v4 -DCMAKE_BUILD_TYPE=Release && cmake --build /tmp/forge-v4 -j && printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/forge-v4/forge && CXX=g++ CC=gcc cmake -S forge-combo29/tests_t12 -B /tmp/tests-v4 -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4 && cmake --build /tmp/tests-v4 -j && /tmp/tests-v4/krk_mate_test
```

Output:
```text
info string bench depth 11 nodes 312866 time 159 nps 1967710
info string bench depth 13 nodes 862329 time 423 nps 2038602
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
config positions=40 runs_per_pos=10 threads=2 hash_mb=16 depth=14 use_nnue=true
threads_1_check: 0 / 100 misses
SUMMARY: misses=0 / 400 (no_mate_score=0, non_mating_move=0)
```

---

## 5. Not Verified

- **The exact external 40-position list behind the reported `57 / 400` number:** No external FEN file came with the task; `krk_mate_test.cpp` generates 40 deterministic legal KRK positions via an exact retrograde tablebase (`forge-combo29/tests_t12/krk_40_positions.txt`) and reproduced a comparable `54 / 400` miss rate (`0 / 100` on `Threads 1`) on the unchanged lock, dropping to `0 / 400` across all three post-fix runs and under ASan+UBSan.
- **Single-thread bare-king searches on a stained/warm history state:** Because Rule 7 requires `Threads 1` reference node counts (`bench 11` = `312866`, `bench 13` = `862329`, where `bench 13` includes rook-endgame FEN #7 `6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1` whose deep subtrees reach bare-king nodes), `bare_king_mode` is active only when `all_workers_->size() > 1`. Extending it to `Threads 1` would alter `bench 13` (to `862604` nodes) and violate Rule 7.
- **Non-bare-king quiet mates (endgames where the losing side still has pawns or pieces):** `bare_king_mode` applies specifically when one side has only a king (`occupied(color) == pieces(color, King)`).
- **Clang and Windows ThinLTO/PGO builds, ThreadSanitizer, and playing strength / Elo / speed:** On this VM, `/usr/bin/clang++` lacks matching libstdc++ linker paths so GCC 13.3.0 was used; no Elo or speed claims are made.
