# Opus Placement Packet — `SF40_tt_recency_pv_admit_and_pv_conthist`

**Status:** **UNSCREENED / HOLD (DO NOT PLACE YET)** — Syntactically orthogonal (`git apply --check RC=0`, stacks cleanly with `V3P + SF34 + SF35 + SF36 + (SF38 XOR SF39)`), quick Master Gates `hard_pass=true`; however, **no `ROUND14_BUILD_REPORT.json` or `PACKET_ROUND14*` exists on disk**, and **ZERO `fastchess` Elo matches** have been run (`run_cpu_wave2_queue.py` was stopped per `NEON_TO_OPUS.md:770`).

---

## 1. Live Artifact Inventory & Hashes

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF40_tt_recency_pv_admit_and_pv_conthist.patch` | 3,174 | 54 | `16dd427a387abb59a828a7eeb545032e1de6166ec691e93fff99b92532115c62` |
| Binary | `C:\nnue-lab\neon\forge_fixes\builds\SF40_tt_recency_pv_admit_and_pv_conthist.exe` | 2,382,848 | — | `b07d2c704a5b4ba4a65371ebfa4430c8f8bf557e9874d217732f3afbffb06fe2` |
| Gate JSON | `C:\nnue-lab\neon\forge_fixes\gate_SF40_tt_recency_pv_admit_and_pv_conthist.json` | 7,331 | 220 | `cb52a98407fd836b65146a6c36e66d8bdc9bb174b14607d3bbd6c7e4e98e6538` |
| Builder Script | `C:\nnue-lab\neon\forge_fixes\build_round14_sf40.py` | 5,687 | 120 | `8aa74ac6ed0a5624d449d63aa2bda284cfd9c12c244df9cea9595e8e66823026` |
| Target Source | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

Baseline `forge/r15dsg/src/search.cpp` matches `C:\nnue-lab\forge\r15dsg\SOURCE_INPUTS.sha256` line 28 byte-for-byte.

---

## 2. Verbatim Patch Diff (`54` lines, `5` hunks in `src/search.cpp`)

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -508,13 +508,13 @@
     }
     TTEntry* replace = &cluster.entries[0];
     int replace_score = replace->occupied()
-                            ? replace->depth - 4 * static_cast<int>((32U + generation - replace->generation()) & 31U)
+                            ? replace->depth - 8 * static_cast<int>((32U + generation - replace->generation()) & 31U)
                             : 0;
 #pragma GCC unroll 1
     for (TTEntry& entry : cluster.entries) {
         if (!entry.occupied()) return snapshot(entry, false);
         const int age = static_cast<int>((32U + generation - entry.generation()) & 31U);
-        const int score = entry.depth - 4 * age;
+        const int score = entry.depth - 8 * age;
         if (score < replace_score) {
             replace = &entry;
             replace_score = score;
@@ -553,7 +553,7 @@
     }
     const bool same_position = entry->key32 == key32 && entry->occupied();
     const bool stale_slot = entry != &cluster.entries[probe.slot_];
-    const bool admit = bound == BoundExact || !same_position || depth + 4 > entry->depth ||
+    const bool admit = bound == BoundExact || !same_position || depth + 4 + (pv ? 2 : 0) > entry->depth ||
                        entry->generation() != generation_;
     // Same-slot stores still refresh the move when the new score is rejected.
     // A stale slot must not paint that rejected move onto the deeper entry.
@@ -623,7 +623,7 @@
     };
     for (const TTEntry& entry : cluster.entries) {
         if (!entry.occupied()) return snapshot(entry, false);
-        if (entry.depth - 4 * relative_age(entry) < replace->depth - 4 * relative_age(*replace)) replace = &entry;
+        if (entry.depth - 8 * relative_age(entry) < replace->depth - 8 * relative_age(*replace)) replace = &entry;
     }
     return snapshot(*replace, false);
 }
@@ -647,7 +647,7 @@
     }
     const bool same_position = entry->key32 == key32 && entry->occupied();
     const bool stale_slot = entry != &cluster.entries[probe.slot_];
-    const bool admit = bound == BoundExact || !same_position || depth + 4 > entry->depth ||
+    const bool admit = bound == BoundExact || !same_position || depth + 4 + (pv ? 2 : 0) > entry->depth ||
                        entry->generation() != generation_;
     // Same rule as store_body: keep a rejected shallow move off a different slot.
     if ((!stale_slot || admit) && (!move.is_none() || !same_position)) entry->move = move;
@@ -2507,6 +2507,8 @@
 #endif
         // B4 HistRework: the twin gets the same bonus.
         if (tune::HistRework != 0) apply_history(rework_entry(board, ss, best_move), history_bonus(depth) / 4);
+        // SF40 (clean-room Stockfish): quiet new-PV move also teaches continuation history.
+        update_continuation(ss, board.moved_piece(best_move), best_move.to, history_bonus(depth) / 4);
     } else if (tune::FailLowContinuationBonus > 0 && best_move.is_none() && !(ss - 1)->current_move.is_none() &&
                (ss - 1)->moved_piece != Empty && !(ss - 1)->current_move.is_capture() && ply > 0) {
         // Every move failed low: the parent's quiet move refuted this line.
```

---

## 3. Target Methods, Baseline vs Patched Behavior & Flag Dependencies

- **Enclosing methods in `C:\nnue-lab\forge\r15dsg\src\search.cpp`:**
  1. `TranspositionTable::probe_body<TakeLock>` (`466-524`, `#if FORGE_SPD_TT_NOTLS`): changes eviction age penalty from `4 * age` to `8 * age` (`511, 517`).
  2. `TranspositionTable::store_body<TakeLock>` (`533-577`, `#if FORGE_SPD_TT_NOTLS`): changes same-position admission threshold from `depth + 4 > entry->depth` to `depth + 4 + (pv ? 2 : 0) > entry->depth` (`556`).
  3. `TranspositionTable::probe` (`590-629`, `#else` fallback): symmetrically changes `4 * relative_age(...)` to `8 * relative_age(...)` (`626`).
  4. `TranspositionTable::store` (`631-670`, `#else` fallback): symmetrically changes `depth + 4 > entry->depth` to `depth + 4 + (pv ? 2 : 0) > entry->depth` (`650`).
  5. `Worker::search` (`1908-2534`, quiet new-PV branch `2498-2510`): after `HistRework` twin update (`2509`), adds `update_continuation(ss, board.moved_piece(best_move), best_move.to, history_bonus(depth) / 4);` so 1-, 2-, and 4-ply continuation history tables also receive the quarter bonus alongside `main_history_`, `threat_history_`, and `rework_history_`.
- **Build-flag dependencies:** `build_fast.py:28` compiles with `-DFORGE_SPD_TT_NOTLS=1`, activating `probe_body`/`store_body` (`#if` path); both `#if` and `#else` TT paths are updated identically so non-NOTLS builds stay consistent.

---

## 4. Gate & Benchmark Evidence (Missing `ROUND14_BUILD_REPORT.json` & ZERO Matches)

- **Quick Master Gates (`gate_SF40_tt_recency_pv_admit_and_pv_conthist.json`, `r0067`):**
  - `hard_pass = true` (`perft 5 = 4,865,609` `6/6`, `v3_parity 120/120` `0 cp`, `loader 13/13`).
  - `bench` (`r0067`): `default_bench_11 = 244,906`, `default_bench_13 = 765,889` (`3,138,889` NPS), `b4_bench_11 = 180,986`, `b4_bench_13 = 807,590` (`2,843,626` NPS).
- **Missing Round 14 Report Note:** `build_round14_sf40.py:109-115` computed `full_bench13` (45-option Big Tune) to stdout and wrote `gate_SF40_*.json`, without writing a `ROUND14_BUILD_REPORT.json` or `PACKET_ROUND14*` file; therefore no `FULL` Big Tune `bench 13` figure for `SF40` is persisted on disk.
- **Elo Status:** **ZERO `fastchess` Elo matches** (`ALL_MATCHES_SCOREBOARD.md` / `matches/`). Queued `SF40_tt_recency_pv_admit_and_pv_conthist_600g_50k` (`seed=202611497`) in `run_cpu_wave2_queue.py:77-78` was stopped (`NEON_TO_OPUS.md:770`).

---

## 5. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint** (`nnue_v3.hpp`/`nnue_v3.cpp` vs `src/search.cpp`).
- **vs Round 12–13 & TM (`SF17/SF18`):**
  - `git -C C:\nnue-lab\forge\r15dsg apply --check`: `RC=0`.
  - Pairwise sequential `git apply` on isolated `forge/r15dsg` copies: `RC=0` in both orders with `V3P`, `SF34` (`min_line_gap=9`, `8` unchanged lines `2499-2506` separate `SF34` and `SF40`), `SF35` (`min_line_gap=124`), `SF36` (`min_line_gap=274`), `SF38` (`min_line_gap=245`), and `SF39` (`min_line_gap=245`).
  - Full combined stacks (`V3P -> SF34 -> SF35 -> SF36 -> (SF38|SF39) -> SF40`): **ALL `RC=0`**.
