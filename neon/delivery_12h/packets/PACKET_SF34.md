# Opus Placement Packet — `SF34_tactical_cutoff_quiet_malus_and_prior_refute`

**Status:** **UNSCREENED / HOLD (DO NOT PLACE YET)** — Syntactically orthogonal (`git apply --check RC=0`, stacks cleanly with `V3P + SF35 + SF36 + (SF38 XOR SF39) + SF40`), quick Master Gates `hard_pass=true`, and `-20.98%` nodes under FULL 45-option Big Tune `bench 13`; however, **ZERO `fastchess` Elo matches** have been run (`run_cpu_wave2_queue.py` was stopped per `NEON_TO_OPUS.md:770`).

---

## 1. Live Artifact Inventory & Hashes

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch` | 2,205 | 34 | `056b3bae0db5193ebff6d7f4cd0a0d72e6646c8a56fc2fe40c08b3d53946b325` |
| Binary | `C:\nnue-lab\neon\forge_fixes\builds\SF34_tactical_cutoff_quiet_malus_and_prior_refute.exe` | 2,384,384 | — | `87e21bf01cd316a4d64d9fdecf696329f8541336735ac4e5a121fa851f63d41a` |
| Gate JSON | `C:\nnue-lab\neon\forge_fixes\gate_SF34_tactical_cutoff_quiet_malus_and_prior_refute.json` | 7,342 | 220 | `cf5495cb6b5bef8caa971309cf173731bbe86400245d4c2588a92ea10f1931d5` |
| Target Source | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

Baseline `forge/r15dsg/src/search.cpp` matches `C:\nnue-lab\forge\r15dsg\SOURCE_INPUTS.sha256` line 28 byte-for-byte.

---

## 2. Verbatim Patch Diff (`34` lines, `1` hunk)

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2493,6 +2493,31 @@
     if (best_score >= beta) {
         if (!best_move.is_capture() && !best_move.is_promotion()) {
             update_quiet_stats(board, ss, best_move, depth + (best_score > beta + 100), quiets_tried.data(), quiet_count);
+        } else if (quiet_count > 0) {
+            // SF34 (clean-room Stockfish update_all_stats): penalize quiet moves that failed before a tactical cutoff.
+            const int malus = -history_bonus(depth);
+            const Color us = board.side_to_move();
+            for (int i = 0; i < quiet_count; ++i) {
+                const Move quiet = quiets_tried[static_cast<std::size_t>(i)];
+                apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], malus);
+                update_threat_quiet(board, quiet, malus);
+#if FORGE_PAWN_HISTORY
+                update_pawn_history(board, board.moved_piece(quiet), quiet, malus);
+#endif
+                update_continuation(ss, board.moved_piece(quiet), quiet.to, malus);
+                if (tune::HistRework != 0) apply_history(rework_entry(board, ss, quiet), malus);
+            }
+        }
+        // SF34 (clean-room Stockfish): instant first-move cutoff refutes the opponent's prior quiet move.
+        if (ply > 0 && move_count == 1 && depth >= 3 && !in_check && !(ss - 1)->current_move.is_none() &&
+            (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_capture() &&
+            !(ss - 1)->current_move.is_promotion()) {
+            const int refute_malus = -history_bonus(depth) / 2;
+            const Color prev_side = opposite(board.side_to_move());
+            apply_history((*main_history_)[static_cast<std::size_t>(prev_side)][(ss - 1)->current_move.from]
+                                          [(ss - 1)->current_move.to],
+                          refute_malus);
+            update_continuation(ss - 1, (ss - 1)->moved_piece, (ss - 1)->current_move.to, refute_malus);
         }
         update_capture_stats(board, best_move, depth, captures_tried.data(), capture_count);
     } else if (!best_move.is_none() && (!best_move.is_capture() && !best_move.is_promotion())) {
```

---

## 3. Target Methods, Baseline vs Patched Behavior & Flag Dependencies

- **Enclosing method:** `Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta, bool cut_node)` (`C:\nnue-lab\forge\r15dsg\src\search.cpp:1908-2534`), hunk at lines `2493-2498`.
- **Baseline (`src/search.cpp:2493-2498`):**
  - On `best_score >= beta`, when `best_move` is quiet (`!is_capture() && !is_promotion()`), calls `update_quiet_stats(...)` which awards bonus to `best_move` and malus to `quiets_tried[0..quiet_count-1]`.
  - When `best_move` is a tactical capture or promotion (e.g., a late BadCapture ordered after quiet moves), `quiets_tried[0..quiet_count-1]` receive **zero** malus; only `update_capture_stats(...)` executes.
  - When `move_count == 1` causes an immediate beta cutoff, the opponent's prior quiet move `(ss - 1)->current_move` receives **no** refutation malus.
- **Patched (clean-room Stockfish `update_all_stats()` + `moveCount == 1` prior-move malus):**
  1. **Tactical-cutoff quiet malus:** Adds `else if (quiet_count > 0)` applying `malus = -history_bonus(depth)` (`src/search.cpp:324-326`) to every `quiets_tried[i]` across `main_history_`, `update_threat_quiet` (gated on `tune::ThreatHistory`), `#if FORGE_PAWN_HISTORY update_pawn_history`, `update_continuation` (1-, 2-, 4-ply back, with 4-ply at `malus / 2`), and `rework_entry` (when `tune::HistRework != 0`).
  2. **First-move cutoff prior refutation:** When `ply > 0 && move_count == 1 && depth >= 3 && !in_check` and `(ss - 1)->current_move` was a non-empty quiet move (`!is_capture() && !is_promotion()`), applies `refute_malus = -history_bonus(depth) / 2` to `main_history_[opposite(stm)][prev.from][prev.to]` and `update_continuation(ss - 1, (ss - 1)->moved_piece, prev.to, refute_malus)`. Note `ply > 0` guarantees `(ss - 1) - 4 >= &stack_[0]` (`stack_[0..3]` sentinel frames initialized at `src/search.cpp:2893-2916`).
- **Build-flag & UCI option dependencies:**
  - `build_fast.py` does NOT define `FORGE_PAWN_HISTORY=1`, so `FORGE_PAWN_HISTORY` defaults to `0` (`include/forge/search.hpp:402`); the `#if FORGE_PAWN_HISTORY` branch is compiled out in standard `r15dsg` builds.
  - `tune::HistRework` (`2` in Big Tune `pipeline/config.forge.toml:214`) activates `rework_entry(...)` (`threat_maps_[ss->ply]` populated at `src/search.cpp:2191`).

---

## 4. Gate & Benchmark Evidence (ZERO `fastchess` Elo Matches Run)

- **Quick Master Gates (`gate_SF34_tactical_cutoff_quiet_malus_and_prior_refute.json`, `r0067/train/cand.fnn3`):**
  - `hard_pass = true` (`overall_status = "PASS_WITH_ADVISORY_FLAGS"` — standard `r0067` net_sanity S2/S5/S7 advisories).
  - `perft`: `6/6` PASS (`startpos` perft 5 = `4,865,609`).
  - `v3_parity`: `120/120` FENs `max_diff_cp = 0`, `8/8` OB covered.
  - `loader_safety`: `13/13` PASS.
  - `bench` (`r0067`): `default_bench_11 = 241,858`, `default_bench_13 = 597,003` (`2,912,209` NPS), `b4_bench_11 = 223,838`, `b4_bench_13 = 665,903` (`2,642,472` NPS).
- **Important Benchmark Basis Distinction (3-option B4 vs 45-option FULL Big Tune):**
  - `ROUND12_BUILD_REPORT.json` (`build_round12_search.py:180-196`) ran `bench 13` with only **3 B4 options** (`HistRework=2, CorrHistV2=true, TtPruneV2=true`, `base = 503,542`): `SF34 = 835,472` (`+65.92%` nodes, `2,871,037` NPS).
  - `PACKET_ROUND12_SF34_SF36.md:12` & `test_round12_sf34_sf36.py:17-48` ran `full_bench13` under **FULL 45-param Big Tune** (`pipeline/config.forge.toml:214`, `base = 576,063`): `SF34 = 455,215` (**`-20.98%` nodes**, `2.956M` vs `2.954M` NPS), passing the `>= 10%` node-reduction fail-before/pass-after test (`cand rc=0`, `base rc=1`).
  - Both measurements correspond to distinct UCI presets and must not be conflated.
- **Elo Status:** **ZERO `fastchess` Elo matches** exist (`ALL_MATCHES_SCOREBOARD.md` `52` rows / `matches/` `48` dirs contain zero `SF34` runs). Queued `SF34_tactical_cutoff_quiet_malus_600g_50k` (`seed=202611490`) in `run_cpu_wave2_queue.py:67-69` was stopped per `NEON_TO_OPUS.md:770` (`OPUS_TO_NEON.md:2866-2870`).

---

## 5. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint.** `V3P` modifies ONLY `include/forge/nnue_v3.hpp` and `src/nnue_v3.cpp`; `SF34` modifies ONLY `src/search.cpp`.
- **vs Round 12–14 & TM (`SF17/SF18`):**
  - `git -C C:\nnue-lab\forge\r15dsg apply --check`: `RC=0`.
  - Pairwise sequential `git apply` on isolated `forge/r15dsg` copies: `RC=0` in both orders with `V3P`, `SF35` (`min_line_gap=351`), `SF36` (`min_line_gap=1558`), `SF38` (`min_line_gap=988`), `SF39` (`min_line_gap=988`), and `SF40` (`min_line_gap=9`, `8` unchanged lines `2499-2506` separate `SF34` `2493-2498` and `SF40` `2507-2512`).
  - Full combined stack apply (`V3P -> SF34 -> SF35 -> SF36 -> SF38 -> SF40` and `V3P -> SF34 -> SF35 -> SF36 -> SF39 -> SF40`): **ALL `RC=0`**.
