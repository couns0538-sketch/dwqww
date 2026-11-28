# Opus Placement Packet — `SF38_corrhist_major`

**Status:** **HOLD / PLACEMENT BLOCKER (SEMANTIC DEFECT IN `record_move` / `record_null_move`)** — Syntactically orthogonal (`git apply --check RC=0`, stacks cleanly with `V3P + SF34 + SF35 + SF36 + SF40`), quick Master Gates `hard_pass=true`, and `-11.46%` nodes under FULL 45-option Big Tune `bench 13`; however, (1) **`SF38` omits `corr_valid` bit `8U` invalidation/copy in `Worker::record_move` and `Worker::record_null_move`**, causing child nodes to read stale `corr_major_idx` values, (2) **`SF39` (`minor+major`) is a strict superset and conflicts with `SF38`**, and (3) **ZERO `fastchess` Elo matches** have been run (`NEON_TO_OPUS.md:770`).

---

## 1. Live Artifact Inventory & Hashes

| Artifact | Path | Bytes | Lines | Live SHA-256 |
|---|---|---:|---:|---|
| Patch | `C:\nnue-lab\neon\forge_fixes\patches\SF38_corrhist_major.patch` | 4,650 | 96 | `02cc557e461d40ec2f1cf368230446ab4f522e31cf360012a3b6a02e1b417490` |
| Binary | `C:\nnue-lab\neon\forge_fixes\builds\SF38_corrhist_major.exe` | 2,380,800 | — | `6b7b0b9f0b063ae73e4c22fd69a4a786c73b10f547940e1b2e9e949b112f0f55` |
| Gate JSON | `C:\nnue-lab\neon\forge_fixes\gate_SF38_corrhist_major.json` | 7,311 | 220 | `087e4ae4f7172225beb62db1227b25a72585d3581ce2db8cb41904dc794ed6fa` |
| Target HPP | `C:\nnue-lab\forge\r15dsg\include\forge\search.hpp` | 33,146 | 667 | `07af2ca6290fc019be33ebbc2b88cd30ecd56f7ba94eefefa271c83ca01a7e7f` |
| Target CPP | `C:\nnue-lab\forge\r15dsg\src\search.cpp` | 167,417 | 3,426 | `174e07a5211cb1d56ea47105c7d4b847bdf3cd8b1b6ef3d4473405654242abf4` |

Both `r15dsg` targets match `C:\nnue-lab\forge\r15dsg\SOURCE_INPUTS.sha256` (lines 11 and 28) byte-for-byte.

---

## 2. Verbatim Patch Diff (`96` lines, `7` hunks across `2` files)

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -454,6 +454,7 @@
     mutable std::array<std::uint16_t, 2> corr_np_idx{};
     mutable std::uint64_t corr_mat_mix = 0;
     mutable std::uint8_t corr_valid = 0;
+    mutable std::uint16_t corr_major_idx = 0;
 };
 
 // State shared by every worker of one Searcher.
@@ -561,7 +562,8 @@
     // B4 (forge/r9). Allocated with the worker and zeroed by clear(); read and written only while their option is
     // on. Per worker: rework twin 32 KiB, joint correction 128 KiB, continuation correction 6.5 KiB, maps 7.4 KiB.
     std::unique_ptr<LesserThreatHistory> rework_history_;          // HistRework
-    std::unique_ptr<CorrectionHistory> joint_correction_;          // HistRework
+    std::unique_ptr<CorrectionHistory> joint_correction_;
+    std::unique_ptr<CorrectionHistory> major_correction_;          // HistRework
     std::unique_ptr<ContinuationCorrection> continuation_correction_;  // CorrHistV2
     std::array<b4::LesserThreats, MaxPly + 8> threat_maps_{};      // HistRework: maps of the node at each ply
     bool tt_prune_v2_ = false;                                     // TtPruneV2: this search's snapshot
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -258,6 +258,23 @@
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
 [[nodiscard]] int score_to_tt(int score, int ply) {
     if (score >= MateInMaxPly) return score + ply;
     if (score <= -MateInMaxPly) return score - ply;
@@ -1208,6 +1225,7 @@
       non_pawn_black_correction_(std::make_unique<CorrectionHistory>()),
       rework_history_(std::make_unique<LesserThreatHistory>()),
       joint_correction_(std::make_unique<CorrectionHistory>()),
+      major_correction_(std::make_unique<CorrectionHistory>()),
       continuation_correction_(std::make_unique<ContinuationCorrection>()) {
     clear();
 }
@@ -1233,6 +1251,7 @@
     // B4 (forge/r9): cleared here like every other table, so no game inherits another game's statistics.
     *rework_history_ = LesserThreatHistory{};
     *joint_correction_ = CorrectionHistory{};
+    *major_correction_ = CorrectionHistory{};
     *continuation_correction_ = ContinuationCorrection{};
     threat_maps_ = {};
     for (SearchStack& ss : stack_) ss = SearchStack{};
@@ -1469,6 +1488,19 @@
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
     return std::clamp(raw_eval + correction / CorrectionGrain, -MateInMaxPly + 1, MateInMaxPly - 1);
 }
 
@@ -1499,6 +1531,13 @@
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
     }
     // B4 CorrHistV2: the two continuation entries take the same step as the tables above.
     if (tune::CorrHistV2 && ss != nullptr) {
```

---

## 3. CRITICAL PLACEMENT-BLOCKER DEFECTS & Target Methods

- **Enclosing scopes & methods:**
  - `include/forge/search.hpp:454-457` (`struct SearchStack`, `418-457`), `561-567` (`class Worker`, `469-620`).
  - `src/search.cpp:258-261` (anonymous namespace `253-1263`), `1192-1213` (`Worker::Worker`), `1217-1239` (`Worker::clear`), `1412-1473` (`Worker::corrected_eval`), `1475-1514` (`Worker::update_correction`).
- **CRITICAL DEFECT #1 — Missing `corr_valid` bit `8U` Invalidation/Copy in `record_move` & `record_null_move`:**
  - `SF38` caches `ss->corr_major_idx` under bit `8U` (`1 << 3`) of `ss->corr_valid` inside `Worker::corrected_eval` (`1488-1497`) and reads it inside `Worker::update_correction` (`1531-1538`).
  - However, `SF38` **never modifies `Worker::record_move` (`src/search.cpp:1336-1352`)** or **`Worker::record_null_move` (`src/search.cpp:1394-1398`)**:
    - In `record_move`: `std::uint8_t keep = ss->corr_valid;` only clears/copies bits `1U`, `2U`, and `4U`, then sets `child->corr_valid = keep;` (`1351`). Bit `8U` is **preserved unconditionally** onto `child` while `child->corr_major_idx` is **never copied** from `ss` and **never cleared** when a King, Rook, Queen, promotion, or capture of R/Q changes the major-piece configuration!
    - In `record_null_move`: `child->corr_valid = ss->corr_valid;` (`1398`) preserves bit `8U` without copying `child->corr_major_idx = ss->corr_major_idx;`.
  - **Consequence:** Once bit `8U` is set at any ancestor ply (e.g., ply 0), every child ply sees `(ss->corr_valid & 8U) != 0U` and silently reads whatever stale `corr_major_idx` remained in `stack_[ply + 1]` from prior search branches (or `0` on the first visit), corrupting both `corrected_eval()` lookups and `update_correction()` writes.
  - **Required fix before screening/placement:**
    - In `Worker::record_move`: clear bit `8U` (`keep &= static_cast<std::uint8_t>(~8U);`) whenever the moved piece is `King`/`Rook`/`Queen`, or `move.is_promotion()`, or the captured piece is `Rook`/`Queen`; otherwise copy `child->corr_major_idx = ss->corr_major_idx;`.
    - In `Worker::record_null_move`: add `child->corr_major_idx = ss->corr_major_idx;`.
- **DEFECT #2 — Table Size & Option-Gate Note:**
  - `PACKET_ROUND13_SF38_SF39.md:11` describes `major_correction_` as `64 KiB`, whereas `CorrectionHistory = std::array<std::array<std::int32_t, 16384>, 2>` (`search.hpp:407`) is `2 * 16384 * 4 = 131,072` bytes = **`128 KiB` per worker** (same size as `joint_correction_` noted at `search.hpp:562`).
  - Despite the `// HistRework` comment at `search.hpp:565`, `major_correction_` is **unconditionally active** in `corrected_eval` and `update_correction` (NOT gated on `tune::HistRework != 0` or `tune::NonPawnCorrection`).

---

## 4. Gate & Benchmark Evidence (ZERO `fastchess` Elo Matches Run)

- **Quick Master Gates (`gate_SF38_corrhist_major.json`, `r0067`):** `hard_pass = true` (`perft 5 = 4,865,609` `6/6`, `v3_parity 120/120` `0 cp`, `loader 13/13`), `default_bench_11/13 = 241,227 / 677,027`, `b4_bench_11/13 = 250,847 / 597,615`.
- **FULL 45-Param Big Tune (`ROUND13_BUILD_REPORT.json`, `build_round13_corrhist.py`, `test_round13_sf38_sf39.py`):** `full_bench13_nodes = 510,068` vs `576,063` base (**`-11.46%`**, `2,698,772` NPS; `cand rc=0`, `base rc=1`). *(Note: these node counts reflect the defective `corr_valid & 8U` cache path above.)*
- **Elo Status:** **ZERO `fastchess` Elo matches** (`ALL_MATCHES_SCOREBOARD.md` / `matches/`). Queued `SF38_corrhist_major_600g_50k` (`seed=202611495`) in `run_cpu_wave2_queue.py:74-75` was stopped (`NEON_TO_OPUS.md:770`).

---

## 5. Overlap & Orthogonality Matrix (`round12_14_orthogonality.json`)

- **vs `V3P_pairwise_psqt_fused_v3.patch` (`sha256=57f3455f...`):** **100% file-disjoint** (`V3P` touches `nnue_v3.hpp`/`nnue_v3.cpp`; `SF38` touches `search.hpp`/`search.cpp`).
- **vs `SF39_corrhist_minor_plus_major.patch`:** **MUTUALLY EXCLUSIVE (`RC=1` CONFLICT)** at `include/forge/search.hpp:454, 561` and `src/search.cpp:258, 1208, 1233, 1469, 1499` (`SF39` is a strict superset containing `major_correction_` + `minor_correction_`).
- **vs `SF35`:** Shares read-only context lines `search.hpp:561-563`, editing different lines (`min_line_gap=0`); pairwise sequential `git apply` passes **`RC=0` in both orders**.
- **Combined stack (`V3P -> SF34 -> SF35 -> SF36 -> SF38 -> SF40`):** **ALL `RC=0`**.
