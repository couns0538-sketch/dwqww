# Opus Placement Review Packet: `SF22_low_ply_history`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF — NOTE `SF8` HUNK OVERLAP)** — Clean-room `4`-ply root-near butterfly history table (`LowPlyHistory`, `ply 0..3`, `git apply --check RC=0` against base `r15dsg`), passes all deterministic gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and moves `B4+r0067 bench 13` by **`+11.28%`** (`703,535` vs `632,195`) and `FULL+r0067 bench 13` by **`+11.25%`** (`640,887` vs `576,076`). **Overlap warning:** `SF22` edits `src/search.cpp:893, 907, 933, 1620`, which overlap `SF8_conthist_6ply.patch`; sequential stacking with `SF8` requires a small manual merge. A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF22_low_ply_history.patch` (`4,599` B, `86` lines, `SHA-256: 83D26808E1251D2D19AAA7FBF2C31F62B3643EFC9B3CF7B0D7347EE2DA9E6229`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF22_low_ply_history.exe` (`2,382,848` B, `SHA-256: AB61F25A8119F9FEF3E0841449141B4FB962B4D777E94B02B0BA28D9545BD121`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF22_low_ply_history_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf22_low_ply_history.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -394,6 +394,7 @@
 // [side][threat 0..3][from][to]. Threat bit 1: mover attacked by a cheaper enemy.
 // Threat bit 0: the destination square is attacked by a cheaper enemy than the mover.
 using ThreatQuietHistory = std::array<std::array<std::array<std::array<std::int16_t, 64>, 64>, 4>, 2>;
+using LowPlyHistory = std::array<std::array<std::array<std::int16_t, 64>, 64>, 4>;
 // forge/r15: the pawn-structure history is compiled in only with -DFORGE_PAWN_HISTORY=1. Compiled out (the default)
 // its table is not allocated, its reads and updates are not in the code and its four tunables are not offered.
 // Reason: with the tunable off the engine was about 2 % slower than without the code (timing t4, 2026-11-15:
@@ -498,6 +499,7 @@
     int id_ = 0;
     Evaluator evaluator_;
     std::unique_ptr<ButterflyHistory> main_history_;
+    std::unique_ptr<LowPlyHistory> low_ply_history_;
     std::unique_ptr<ThreatQuietHistory> threat_history_;
     std::unique_ptr<PawnHistoryTable> pawn_history_;
     std::unique_ptr<CaptureHistory> capture_history_;
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -893,6 +893,7 @@
         const PieceToHistory* cont1;
         const PieceToHistory* cont2;
         const PieceToHistory* cont4;
+        const std::array<std::array<std::int16_t, 64>, 64>* low_ply;
         const Board& board;
         const Worker& worker;
         const LesserThreatHistory::value_type* rework_side;
@@ -907,6 +908,7 @@
               cont2(ss != nullptr ? (ss - 2)->continuation : nullptr),
               cont4(tune::ContHist4PlyRead && ss != nullptr && !(ss - 4)->current_move.is_none()
                         ? (ss - 4)->continuation : nullptr),
+              low_ply(ss != nullptr && ss->ply >= 0 && ss->ply < 4 ? &(*searcher.low_ply_history_)[static_cast<std::size_t>(ss->ply)] : nullptr),
               board(b),
               worker(searcher),
               rework_side(tune::HistRework != 0 && ss != nullptr
@@ -933,6 +935,7 @@
             if (cont1 != nullptr) value += (*cont1)[p][move.to];
             if (cont2 != nullptr) value += (*cont2)[p][move.to];
             if (cont4 != nullptr) value += (*cont4)[p][move.to] / 2;
+            if (low_ply != nullptr) value += (*low_ply)[move.from][move.to];
             if (use_threat_hist) [[unlikely]] value += worker.threat_quiet_bonus(board, move);
 #if FORGE_PAWN_HISTORY
             value += worker.pawn_history_value(board, piece, move);
@@ -1193,6 +1196,7 @@
     : shared_(shared),
       id_(id),
       main_history_(std::make_unique<ButterflyHistory>()),
+      low_ply_history_(std::make_unique<LowPlyHistory>()),
       threat_history_(std::make_unique<ThreatQuietHistory>()),
 #if FORGE_PAWN_HISTORY
       pawn_history_(std::make_unique<PawnHistoryTable>()),
@@ -1218,6 +1222,7 @@
     stack_dirty_limit_ = MaxPly + 7;
     evaluator_.clear();
     *main_history_ = ButterflyHistory{};
+    *low_ply_history_ = LowPlyHistory{};
     *threat_history_ = ThreatQuietHistory{};
     // No temporary of the table's size on the stack (13.6 MB): fill in place. Untouched while the feature is off.
 #if FORGE_PAWN_HISTORY
@@ -1620,6 +1625,9 @@
         if (tune::ContHist4PlyRead && (ss - 4)->continuation != nullptr && !(ss - 4)->current_move.is_none()) {
             score += (*(ss - 4)->continuation)[p][move.to] / 2;
         }
+        if (ss->ply >= 0 && ss->ply < 4) {
+            score += (*low_ply_history_)[static_cast<std::size_t>(ss->ply)][move.from][move.to];
+        }
     }
     if (tune::ThreatHistory) [[unlikely]] score += threat_quiet_bonus(board, move);
 #if FORGE_PAWN_HISTORY
@@ -1725,6 +1733,7 @@
     }
     const Piece piece = board.moved_piece(move);
     apply_history((*main_history_)[static_cast<std::size_t>(us)][move.from][move.to], bonus);
+    if (ss->ply >= 0 && ss->ply < 4) apply_history((*low_ply_history_)[static_cast<std::size_t>(ss->ply)][move.from][move.to], bonus);
     update_threat_quiet(board, move, bonus);
 #if FORGE_PAWN_HISTORY
     update_pawn_history(board, piece, move, bonus);
@@ -1734,6 +1743,7 @@
         const Move quiet = quiets[i];
         if (quiet == move) continue;
         apply_history((*main_history_)[static_cast<std::size_t>(us)][quiet.from][quiet.to], -bonus);
+        if (ss->ply >= 0 && ss->ply < 4) apply_history((*low_ply_history_)[static_cast<std::size_t>(ss->ply)][quiet.from][quiet.to], -bonus);
         update_threat_quiet(board, quiet, -bonus);
 #if FORGE_PAWN_HISTORY
         update_pawn_history(board, board.moved_piece(quiet), quiet, -bonus);
```

---

## 2. Technical Note & Caveats

- **Mechanism (`include/forge/search.hpp:397, 499`; `src/search.cpp:893-936, 1193-1222, 1620-1627, 1725-1743`):**
  1. Allocates `LowPlyHistory` (`4 x 64 x 64 x int16_t` = `32 KiB` per worker) in `Worker`, zeroed on construction and `Worker::clear()`.
  2. Both `QuietScorer` (`893-936`) and `Worker::quiet_history` (`1625-1627`) add `(*low_ply_history_)[ss->ply][move.from][move.to]` when `0 <= ss->ply < 4`.
  3. `Worker::update_quiet_stats` (`1733, 1743`) updates the same slot with `+bonus` for the cutoff quiet move and `-bonus` for failed quiet moves, biasing move ordering and quiet-history pruning near the root.
- **Bounds & Interaction Checks:**
  1. **Bounds safety:** All accesses are guarded by `ss->ply >= 0 && ss->ply < 4` (plus `ss != nullptr` in `QuietScorer`).
  2. **CRITICAL — Overlap with `SF8_conthist_6ply.patch`:** `SF22` edits `src/search.cpp` at lines `893, 907, 933, 1620`, which are the exact same `QuietScorer` / `quiet_history` lines edited by `SF8_conthist_6ply.patch` (`@@ -893,6`, `@@ -905,8`, `@@ -933,6`, `@@ -1617,8`). Note that `git apply --check SF8.patch SF22.patch` checks each patch independently against base `r15dsg` (`RC=0`), masking the sequential merge conflict! If both `SF8` and `SF22` are placed, `SF22` must be manually rebased onto `SF8` (trivial 4-line insertion after `cont6` instead of `cont4`).
- **Caveat 1 (No Match Played Yet):** Only deterministic gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `SF22_low_ply_history.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish `LowPlyHistory` (`ply < 4` root-near `[ply][from][to]` quiet history table, `32 KiB`) adapted to Forge's `QuietScorer` and `update_quiet_stats` idioms.
- **License Status:** 100% clean-room implementation (`10` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `SF22_low_ply_history.exe` (`ab61f25a...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `290,403 / 925,813` | `-7.18% / +7.36%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `272,131 / 613,455` | `+4.79% / -15.40%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `171,693 / 703,535` | `-8.64% / +11.28%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `193,168 / 640,887` | `-11.56% / +11.25%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF22_low_ply_history.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf22_low_ply_history.py
```

Observed output (`RC=0`):
- `test_1_patch_apply_and_divergence`: **PASSED** (`git apply --check RC=0`; `B4` `3/3` diverge including `startpos d9` flip `c2c4 -> e2e3` (`('e2e3', 29, 5106)`) and `bench5 d9` flip `c4d5 -> a2a3`; `FULL` `4/4` diverge including `startpos` `g1f3 -> d2d4` and `bench3` `h2h3 -> c4b3`)
- `test_2_bench13_delta_vs_base`: **PASSED** (`B4+r0067`: `703,535` vs `632,195`, `+11.28%`; `FULL+r0067`: `640,887` vs `576,076`, `+11.25%`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_sf22_low_ply_history.py
```

Observed output (`RC=1`):
- `test_1_patch_apply_and_divergence`: **FAILED** (`AssertionError: 0 != 3 : Expected 3 B4 divergences, got 0`)
- `test_2_bench13_delta_vs_base`: **FAILED** (`AssertionError: 632195 == 632195 : B4+r0067 bench 13 must differ from base_r15dsg`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `include/forge/search.hpp:394-502`, `src/search.cpp:893-1748`, and `SF22_low_ply_history.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Rebase `QuietScorer` / `quiet_history` hunks onto `SF8_conthist_6ply.patch` if stacking with `SF8`.
- [ ] Run pre-declared `1,000g @ 50k` match (`SF22_low_ply_history.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_sf22_low_ply_history.py --exe <placed_exe>` and `run_master_gates.py --quick`.
