# Opus Placement Packet — `SF39_corrhist_minor_plus_major`

**Status:** **HOLD / PLACEMENT BLOCKER (SEMANTIC DEFECT IN `record_move` / `record_null_move`)** — Syntactically orthogonal (`git apply --check RC=0`, stacks cleanly with `V3P + SF34 + SF35 + SF36 + SF40`), quick Master Gates `hard_pass=true`, and `-7.66%` nodes under FULL 45-option Big Tune `bench 13`; however, (1) **`SF39` omits `corr_valid` bits `8U`/`16U` invalidation/copy in `Worker::record_move` and `Worker::record_null_move`**, causing child nodes to read stale `corr_major_idx`/`corr_minor_idx` values, (2) **`SF39` is mutually exclusive with `SF38`** (strict superset), and (3) **ZERO `fastchess` Elo matches** have been run (`NEON_TO_OPUS.md:770`).

---

## 1. Live Artifact Inventory & Hashes

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF39_corrhist_minor_plus_major.patch` | 6,265 | 129 | `4160fef92c8c4f42b5e4c75f676d66532b6be696d63c60d2c7f9325e62563ee5` |
| Binary | `C:\nnue-lab\neon\forge_fixes\builds\SF39_corrhist_minor_plus_major.exe` | 2,381,824 | — | `6a44170b029d1d87b6cfc46092636a4086f3ba0bb67fda7572fd66c83d885025` |
| Gate JSON | `C:\nnue-lab\neon\forge_fixes\gate_SF39_corrhist_minor_plus_major.json` | 7,323 | 220 | `36b471d941419f279c3e67c09de7232debe9947f145b99a4b1ea272a090ebc8d` |
| Target HPP | `C:\nnue-lab\forge\r15dsg\include\forge\search.hpp` | 33,146 | 667 | `07af2ca6290fc019be33ebbc2b88cd30ecd56f7ba94eefefa271c83ca01a7e7f` |
| Target CPP | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

Both `r15dsg` targets match `C:\nnue-lab\forge\r15dsg\SOURCE_INPUTS.sha256` (lines 11 and 28) byte-for-byte.

---

## 2. Verbatim Patch Diff (`129` lines, `7` hunks across `2` files)

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -454,6 +454,8 @@
     mutable std::array<std::uint16_t, 2> corr_np_idx{};
     mutable std::uint64_t corr_mat_mix = 0;
     mutable std::uint8_t corr_valid = 0;
+    mutable std::uint16_t corr_major_idx = 0;
+    mutable std::uint16_t corr_minor_idx = 0;
 };
 
 // State shared by every worker of one Searcher.
@@ -561,7 +563,9 @@
     // B4 (forge/r9). Allocated with the worker and zeroed by clear(); read and written only while their option is
     // on. Per worker: rework twin 32 KiB, joint correction 128 KiB, continuation correction 6.5 KiB, maps 7.4 KiB.
     std::unique_ptr<LesserThreatHistory> rework_history_;          // HistRework
-    std::unique_ptr<CorrectionHistory> joint_correction_;          // HistRework
+    std::unique_ptr<CorrectionHistory> joint_correction_;
+    std::unique_ptr<CorrectionHistory> major_correction_;
+    std::unique_ptr<CorrectionHistory> minor_correction_;          // HistRework
     std::unique_ptr<ContinuationCorrection> continuation_correction_;  // CorrHistV2
     std::array<b4::LesserThreats, MaxPly + 8> threat_maps_{};      // HistRework: maps of the node at each ply
     bool tt_prune_v2_ = false;                                     // TtPruneV2: this search's snapshot
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -258,6 +258,32 @@
 // A searched quiet missed alpha by at least this many centipawns.
 constexpr int QuietWideGap = 176;
 
+// Clean-room Stockfish/Stormphrax major-piece (K+R+Q) and minor-piece (K+N+B) structure keys.
+[[nodiscard]] std::uint64_t splitmix64_corr(std::uint64_t x) {
+    x += 0x9e3779b97f4a7c15ULL;
+    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
+    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
+    return x ^ (x >> 31);
+}
+
+[[nodiscard]] std::uint64_t major_piece_key(const Board& board) {
+    std::uint64_t h = splitmix64_corr(board.pieces(White, King) ^ (board.pieces(Black, King) * 0x9e3779b97f4a7c15ULL));
+    h ^= splitmix64_corr(board.pieces(White, Rook) ^ 0x1111111111111111ULL);
+    h ^= splitmix64_corr(board.pieces(Black, Rook) ^ 0x2222222222222222ULL);
+    h ^= splitmix64_corr(board.pieces(White, Queen) ^ 0x3333333333333333ULL);
+    h ^= splitmix64_corr(board.pieces(Black, Queen) ^ 0x4444444444444444ULL);
+    return h;
+}
+
+[[nodiscard]] std::uint64_t minor_piece_key(const Board& board) {
+    std::uint64_t h = splitmix64_corr(board.pieces(White, King) ^ (board.pieces(Black, King) * 0x517cc1b727220a95ULL));
+    h ^= splitmix64_corr(board.pieces(White, Knight) ^ 0x5555555555555555ULL);
+    h ^= splitmix64_corr(board.pieces(Black, Knight) ^ 0x6666666666666666ULL);
+    h ^= splitmix64_corr(board.pieces(White, Bishop) ^ 0x7777777777777777ULL);
+    h ^= splitmix64_corr(board.pieces(Black, Bishop) ^ 0x8888888888888888ULL);
+    return h;
+}
+
 [[nodiscard]] int score_to_tt(int score, int ply) {
     if (score >= MateInMaxPly) return score + ply;
     if (score <= -MateInMaxPly) return score - ply;
@@ -1208,6 +1234,8 @@
       non_pawn_black_correction_(std::make_unique<CorrectionHistory>()),
       rework_history_(std::make_unique<LesserThreatHistory>()),
       joint_correction_(std::make_unique<CorrectionHistory>()),
+      major_correction_(std::make_unique<CorrectionHistory>()),
+      minor_correction_(std::make_unique<CorrectionHistory>()),
       continuation_correction_(std::make_unique<ContinuationCorrection>()) {
     clear();
 }
@@ -1233,6 +1261,8 @@
     // B4 (forge/r9): cleared here like every other table, so no game inherits another game's statistics.
     *rework_history_ = LesserThreatHistory{};
     *joint_correction_ = CorrectionHistory{};
+    *major_correction_ = CorrectionHistory{};
+    *minor_correction_ = CorrectionHistory{};
     *continuation_correction_ = ContinuationCorrection{};
     threat_maps_ = {};
     for (SearchStack& ss : stack_) ss = SearchStack{};
@@ -1469,6 +1499,32 @@
                                                      [static_cast<std::size_t>((ss - 2)->current_move.to)];
         }
     }
+    {
+        std::size_t mj_idx;
+        if (ss != nullptr) {
+            if ((ss->corr_valid & 8U) == 0U) {
+                ss->corr_major_idx = static_cast<std::uint16_t>(major_piece_key(board) & (CorrectionSize - 1U));
+                ss->corr_valid |= 8U;
+            }
+            mj_idx = ss->corr_major_idx;
+        } else {
+            mj_idx = major_piece_key(board) & (CorrectionSize - 1U);
+        }
+        correction += (*major_correction_)[side][mj_idx] / 2;
+    }
+    {
+        std::size_t mn_idx;
+        if (ss != nullptr) {
+            if ((ss->corr_valid & 16U) == 0U) {
+                ss->corr_minor_idx = static_cast<std::uint16_t>(minor_piece_key(board) & (CorrectionSize - 1U));
+                ss->corr_valid |= 16U;
+            }
+            mn_idx = ss->corr_minor_idx;
+        } else {
+            mn_idx = minor_piece_key(board) & (CorrectionSize - 1U);
+        }
+        correction += (*minor_correction_)[side][mn_idx] / 2;
+    }
     return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);
 }
 
@@ -1499,6 +1555,20 @@
             : b4::joint_key(board);
         std::int32_t& entry = (*joint_correction_)[side][jkey & (CorrectionSize - 1U)];
         entry = b4::gravity(entry, diff * weight / 256, CorrectionLimit);
+    }
+    {
+        const std::size_t mj_idx = (ss != nullptr && (ss->corr_valid & 8U) != 0U)
+            ? static_cast<std::size_t>(ss->corr_major_idx)
+            : (major_piece_key(board) & (CorrectionSize - 1U));
+        std::int32_t& mj_entry = (*major_correction_)[side][mj_idx];
+        mj_entry = b4::gravity(mj_entry, diff * weight / 256, CorrectionLimit);
+    }
+    {
+        const std::size_t mn_idx = (ss != nullptr && (ss->corr_valid & 16U) != 0U)
+            ? static_cast<std::size_t>(ss->corr_minor_idx)
+            : (minor_piece_key(board) & (CorrectionSize - 1U));
+        std::int32_t& mn_entry = (*minor_correction_)[side][mn_idx];
+        mn_entry = b4::gravity(mn_entry, diff * weight / 256, CorrectionLimit);
     }
     // B4 CorrHistV2: the two continuation entries take the same step as the tables above.
     if (tune::CorrHistV2 && ss != nullptr) {
```

---

## 3. CRITICAL PLACEMENT-BLOCKER DEFECTS & Prior Wave 2 Context

- **Enclosing scopes & methods:** Identical locations to `SF38` (`SearchStack`, `Worker`, anonymous `splitmix64_corr`/`major_piece_key`/`minor_piece_key`, `Worker::Worker`, `Worker::clear`, `Worker::corrected_eval`, `Worker::update_correction`).
- **CRITICAL DEFECT #1 — Missing `corr_valid` bits `8U`/`16U` Invalidation/Copy in `record_move` & `record_null_move`:**
  - `SF39` caches `ss->corr_major_idx` (bit `8U`) and `ss->corr_minor_idx` (bit `16U`) inside `Worker::corrected_eval` (`1499-1528`), and reads them in `Worker::update_correction` (`1555-1574`).
  - Just like `SF38`, `SF39` **omits updates to `Worker::record_move` (`src/search.cpp:1336-1352`) and `Worker::record_null_move` (`src/search.cpp:1394-1398`)**:
    - `record_move` sets `child->corr_valid = keep;` (`1351`) leaving bits `8U` and `16U` **set unconditionally** while **never copying** `corr_major_idx` / `corr_minor_idx` and **never invalidating** them on `K/R/Q`, `K/N/B`, promotions, or captures.
    - `record_null_move` copies `corr_valid` (`1398`) without copying `corr_major_idx` or `corr_minor_idx`.
  - **Consequence:** Child plies read stale `stack_[ply + 1].corr_major_idx` and `corr_minor_idx` values from earlier search branches instead of recomputing `major_piece_key`/`minor_piece_key`.
  - **Required fix before screening/placement:**
    - In `Worker::record_move`: invalidate bit `8U` if moved/captured piece is `Rook`/`Queen`, moved piece is `King`, or `move.is_promotion()`, else copy `child->corr_major_idx = ss->corr_major_idx`; invalidate bit `16U` if moved/captured piece is `Knight`/`Bishop`, moved piece is `King`, or `move.is_promotion()`, else copy `child->corr_minor_idx = ss->corr_minor_idx`.
    - In `Worker::record_null_move`: copy both `child->corr_major_idx = ss->corr_major_idx;` and `child->corr_minor_idx = ss->corr_minor_idx;`.
- **DEFECT #2 — Table Size & Option-Gate Note:**
  - `PACKET_ROUND13_SF38_SF39.md:16` describes `SF39`'s combined size as `128 KiB`, whereas `CorrectionHistory` (`2 * 16384 * 4` bytes) is **`128 KiB` per table (`256 KiB` total per worker for `SF39`)**.
  - Both tables apply unconditionally in `corrected_eval` and `update_correction` (not gated on `tune::HistRework != 0`).
- **Wave 2 Minor CorrHist Prior Context:** `proto_1_corrhist_minor` (`K+N+B` only) scored `+11.01 [-4.82, +26.88]` (`600g`) and `W2_proto_1_confirm` scored `+7.64 [-4.34, +19.65]` (`1,000g`, `NEON_TO_OPUS.md:770`).

---

## 4. Gate & Benchmark Evidence (ZERO `fastchess` Elo Matches Run)

- **Quick Master Gates (`gate_SF39_corrhist_minor_plus_major.json`, `r0067`):** `hard_pass = true` (`perft 5 = 4,865,609` `6/6`, `v3_parity 120/120` `0 cp`, `loader 13/13`), `default_bench_11/13 = 263,481 / 705,739`, `b4_bench_11/13 = 252,109 / 791,312`.
- **FULL 45-Param Big Tune (`ROUND13_BUILD_REPORT.json`, `build_round13_corrhist.py`, `test_round13_sf38_sf39.py`):** `full_bench13_nodes = 531,909` vs `576,063` base (**`-7.66%`**, `2,700,045` NPS; `cand rc=0`, `base rc=1`). *(Note: reflects the defective `corr_valid` cache path above.)*
- **Elo Status:** **ZERO `fastchess` Elo matches** (`ALL_MATCHES_SCOREBOARD.md` / `matches/`). Queued `SF39_corrhist_minor_plus_major_600g_50k` (`seed=202611496`) in `run_cpu_wave2_queue.py:76` was stopped (`NEON_TO_OPUS.md:770`).

---

## 5. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint** (`nnue_v3.hpp`/`nnue_v3.cpp` vs `search.hpp`/`search.cpp`).
- **vs `SF38_corrhist_major.patch`:** **MUTUALLY EXCLUSIVE (`RC=1` CONFLICT)** across all 7 hunks (`SF39` supersedes `SF38`).
- **vs `SF35`:** Shares read-only context lines `search.hpp:561-563`, editing different lines (`min_line_gap=0`); pairwise sequential `git apply` passes **`RC=0` in both orders**.
- **Combined stack (`V3P -> SF34 -> SF35 -> SF36 -> SF39 -> SF40`):** **ALL `RC=0`**.
