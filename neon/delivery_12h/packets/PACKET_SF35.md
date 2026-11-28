# Opus Placement Packet — `SF35_razoring_d3_quadratic_and_nmp_minply`

**Status:** **UNSCREENED / HOLD + BIG-TUNE SHADOWING ADVISORY** — Syntactically orthogonal (`git apply --check RC=0`, stacks cleanly with `V3P + SF34 + SF36 + (SF38 XOR SF39) + SF40`), quick Master Gates `hard_pass=true`; however, **ZERO `fastchess` Elo matches** have been run (`NEON_TO_OPUS.md:770`), and under live Big Tune `RazorDepth=3` **shadows** the quadratic `depth<=3` razoring clause.

---

## 1. Live Artifact Inventory & Hashes

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF35_razoring_d3_quadratic_and_nmp_minply.patch` | 3,473 | 61 | `4cd9f3953d840e249c1a2c397debb5b6fb0cd684f4c45f702e296b40af8aec5a` |
| Binary | `C:\nnue-lab\neon\forge_fixes\builds\SF35_razoring_d3_quadratic_and_nmp_minply.exe` | 2,382,848 | — | `c7897b1f2f606bf07dadad3ad7f9070f0a5a59d180e48f6426b424de2f8687a1` |
| Gate JSON | `C:\nnue-lab\neon\forge_fixes\gate_SF35_razoring_d3_quadratic_and_nmp_minply.json` | 7,333 | 220 | `910add99c855581c4ede8bebfe458f311fcfc89c5879486aa40d3783df78dfc3` |
| Target HPP | `C:\nnue-lab\forge\r15dsg\include\forge\search.hpp` | 33,146 | 667 | `07af2ca6290fc019be33ebbc2b88cd30ecd56f7ba94eefefa271c83ca01a7e7f` |
| Target CPP | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

Both `r15dsg` targets match `C:\nnue-lab\forge\r15dsg\SOURCE_INPUTS.sha256` (lines 11 and 28) byte-for-byte.

---

## 2. Verbatim Patch Diff (`61` lines, `5` hunks across `2` files)

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -558,6 +558,7 @@
     // True only inside a NullThreatVerify confirmation, so that reduced search
     // does not use null moves. Stays false for the whole default search.
     bool null_blocked_ = false;
+    int min_nmp_ply_ = 0;
     // B4 (forge/r9). Allocated with the worker and zeroed by clear(); read and written only while their option is
     // on. Per worker: rework twin 32 KiB, joint correction 128 KiB, continuation correction 6.5 KiB, maps 7.4 KiB.
     std::unique_ptr<LesserThreatHistory> rework_history_;          // HistRework
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2073,11 +2073,13 @@
 
     if (!pv_node && !in_check && excluded.is_none() && !is_mate_score(beta) && mate_moves_ == 0 &&
         board.halfmove_clock() + depth < 100) {
-        // Razoring: hopeless positions fall back to quiescence.
-        if (!bare_king_mode && depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) {
-            const int razor = qsearch_child(board, ss, alpha - 1, alpha);
+        // Razoring (SF35 clean-room Stockfish quadratic depth<=3): hopeless positions verify in quiescence.
+        if (!bare_king_mode &&
+            ((depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha) ||
+             (depth <= 3 && eval + 450 + 280 * depth * depth < alpha))) {
+            const int razor = qsearch_child(board, ss, alpha, alpha + 1);
             if (aborted_) return 0;
-            if (razor < alpha) return razor;
+            if (razor <= alpha) return razor;
         }
         // Reverse futility pruning.
         // B4 TtPruneV2: when the opponent's static eval fell on their move ("opponent worsening"), the fail high is a
@@ -2091,7 +2093,8 @@
             return eval;
         }
         // Null move pruning.
-        if (!bare_king_mode && depth >= tune::NullMoveMinDepth && eval >= beta && ss->static_eval >= beta - 24 * depth + 180 &&
+        if (!bare_king_mode && depth >= tune::NullMoveMinDepth && ply >= min_nmp_ply_ && eval >= beta &&
+            ss->static_eval >= beta - 24 * depth + 180 &&
             ss->null_move_allowed && (!tune::NullThreatVerify || !null_blocked_) &&
             !(ss - 1)->current_move.is_none() &&
             board.has_non_pawn_material(board.side_to_move()) &&
@@ -2129,9 +2132,12 @@
                 // Same reduced depth as the high-depth verification. A threat
                 // confirmation also refuses null moves in that whole search.
                 const bool saved_block = null_blocked_;
+                const int saved_min_nmp = min_nmp_ply_;
                 if (threat_gate) null_blocked_ = true;
+                min_nmp_ply_ = ply + 3 * std::max(0, depth - reduction) / 4;
                 ss->null_move_allowed = false;
                 const int verification = search_child(board, ss, depth - reduction, beta - 1, beta, false);
+                min_nmp_ply_ = saved_min_nmp;
                 null_blocked_ = saved_block;
                 ss->double_extensions = inherited_double_extensions;
                 ss->null_move_allowed = true;
@@ -2636,6 +2642,7 @@
     null_tries_ = 0;
     null_cutoffs_ = 0;
     null_blocked_ = false;
+    min_nmp_ply_ = 0;
     root_moves_ = limits.search_moves;
     root_restricted_ = limits.search_moves_specified;
     root_bare_king_ = board.occupied(White) == board.pieces(White, King) ||
```

---

## 3. Target Methods, Baseline vs Patched Behavior & CRITICAL Big-Tune Shadowing

- **Enclosing scopes & methods:**
  - `include/forge/search.hpp:558-564`: `class Worker` (`469-620`) — adds `int min_nmp_ply_ = 0;` after `null_blocked_`.
  - `src/search.cpp:2073-2083, 2091-2099, 2129-2142`: `Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node)` (`1908-2534`).
  - `src/search.cpp:2636-2643`: `Worker::search(Board board, const SearchLimits& limits, ...)` (`2623-3251`) — resets `min_nmp_ply_ = 0;` at root start.
- **Baseline vs Patched Behavior:**
  1. **Razoring (`2076-2081`):** Baseline checks `depth <= tune::RazorDepth && eval + tune::RazorBase + tune::RazorMultiplier * depth < alpha`, probes `qsearch_child(board, ss, alpha - 1, alpha)`, and returns `razor` on `razor < alpha`. Patched adds an OR-clause `(depth <= 3 && eval + 450 + 280 * depth * depth < alpha)`, shifts the qsearch window to `(alpha, alpha + 1)`, and returns `razor` on `razor <= alpha`.
  2. **NMP `min_nmp_ply_` (`2094, 2132-2142, 2639`):** Baseline enters NMP regardless of prior verification depth (only `ss->null_move_allowed` and `null_blocked_` restrict nested null moves). Patched gates NMP on `ply >= min_nmp_ply_` and, during high-depth NMP verification (`depth >= 14`), sets `min_nmp_ply_ = ply + 3 * std::max(0, depth - reduction) / 4` (saving/restoring around `search_child(...)`), preventing immediate re-entry into NMP inside the verification subtree even after a real move restores `null_move_allowed = true`.
- **CRITICAL BIG-TUNE SHADOWING HAZARD (Forensic Finding):**
  - Engine defaults (`src/search.cpp:103-105`) are `RazorDepth = 2`, `RazorBase = 150`, `RazorMultiplier = 350` (where depth 3 had no razoring, so the quadratic `depth <= 3` clause would activate at depth 3).
  - Under live **45-option Big Tune** (`pipeline/config.forge.toml:214`), `RazorDepth = 3`, `RazorBase = 182`, `RazorMultiplier = 379`:
    - Depth 1: linear margin `561` cp vs quadratic `730` cp (`eval + 561 < alpha` is strictly wider than `eval + 730 < alpha`).
    - Depth 2: linear margin `940` cp vs quadratic `1570` cp.
    - Depth 3: linear margin `1319` cp vs quadratic `2970` cp.
  - Because `RazorDepth = 3` already covers depths `1..3` with strictly smaller margins at every depth, **the quadratic `depth <= 3` OR-clause NEVER triggers independently under Big Tune**. Thus, under live Big Tune, `SF35`'s active behavioral changes are **solely**: (a) shifting the razoring `qsearch_child` window from `(alpha - 1, alpha)` / `razor < alpha` to `(alpha, alpha + 1)` / `razor <= alpha`, and (b) `ply >= min_nmp_ply_` during NMP verification (`depth >= 14`).

---

## 4. Gate & Benchmark Evidence (ZERO `fastchess` Elo Matches Run)

- **Quick Master Gates (`gate_SF35_razoring_d3_quadratic_and_nmp_minply.json`, `r0067`):**
  - `hard_pass = true` (`perft 5 = 4,865,609` `6/6`, `v3_parity 120/120` `0 cp`, `loader 13/13`).
  - `bench` (`r0067`): `default_bench_11 = 259,693`, `default_bench_13 = 725,148` (`3,251,784` NPS), `b4_bench_11 = 187,930`, `b4_bench_13 = 632,195` (`3,068,907` NPS). Notice `b4_bench_11/13` is identical to `base_r15dsg.exe` (`187,930 / 632,195`) because B4 `bench 13` rarely enters `depth >= 14` NMP verification and `(alpha, alpha+1)` didn't shift nodes on those positions.
- **Build Report vs Packet Basis:**
  - `ROUND12_BUILD_REPORT.json` (3-option partial B4 `base = 503,542`): `SF35 = 503,542` (`0.0%` delta, `3,015,221` NPS).
  - `test_round12_sf34_sf36.py` & `PACKET_ROUND12_SF34_SF36.md` test **only `SF34` and `SF36`** — `SF35` has **no** FULL 45-option Big Tune `bench 13` figure persisted on disk.
- **Elo Status:** **ZERO `fastchess` Elo matches** exist (`ALL_MATCHES_SCOREBOARD.md` / `matches/`). Queued `SF35_razoring_d3_quadratic_nmp_600g_50k` (`seed=202611491`) in `run_cpu_wave2_queue.py:70-71` was stopped per `NEON_TO_OPUS.md:770`.

---

## 5. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint** (`V3P` touches `nnue_v3.hpp`/`nnue_v3.cpp`; `SF35` touches `search.hpp`/`search.cpp`).
- **vs Round 12–14 & TM (`SF17/SF18`):**
  - `git -C C:\nnue-lab\forge\r15dsg apply --check`: `RC=0`.
  - **Context adjacency with `SF38`/`SF39`:** `SF35` (`search.hpp` hunk `@@ -558,6`, lines `558-563`) and `SF38`/`SF39` (`search.hpp` hunk `@@ -561,7`, lines `561-567`) share read-only context lines `561-563`, editing different lines (`560->561` vs `564-565`). Pairwise sequential `git apply` succeeds with **`RC=0` in both orders** (`SF35 -> SF38`, `SF38 -> SF35`, `SF35 -> SF39`, `SF39 -> SF35`).
  - Line-disjoint with `SF34` (`min_line_gap=351`), `SF36` (`min_line_gap=1138`), and `SF40` (`min_line_gap=124`).
  - Combined stacks (`V3P -> SF34 -> SF35 -> SF36 -> (SF38|SF39) -> SF40`): **ALL `RC=0`**.
