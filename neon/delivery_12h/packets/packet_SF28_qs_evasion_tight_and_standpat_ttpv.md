# Opus Placement Review Packet: `SF28_qs_evasion_tight_and_standpat_ttpv`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish `qsearch` pairing of (1) preserving `tt_pv` on stand-pat `BoundLower` TT stores (`!tt_hit`) and (2) tightening `SF13` quiescence check-evasion pruning from `move_count > 2` to `move_count >= 2` once a non-mated evasion is established (`best_score > -MateInMaxPly`). Passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB on `r0067`), diverges on `7/8` `B4` and `8/8` `FULL` benchmark FENs, and shifts `B4+r0067 bench 13` by **`-10.14%`** (`568,093` vs `632,195`), `HCE Default` by **`-12.20%`** (`757,111` vs `862,329`), `r0067 Default` by **`+11.48%`** (`808,393` vs `725,158`), and `FULL+r0067` by **`+0.16%`** (`577,019` vs `576,076`). **OVERLAP ALERT:** Hunk 2 (`search.cpp:1847-1863`, `move_count >= 2`) **directly overlaps `SF33_qs_overhaul_SF13_plus_SF32`** (Patch #2 of the 6-patch Super-Stack, `search.cpp:1847-1875`); only Hunk 1 (`1826-1834`, stand-pat `tt_pv`) is orthogonal to `SF33`. Zero completed `fastchess` matches exist for `SF28`; a pre-declared `1,000g @ 50k` match (plus PGO confirmation if promoted) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF28_qs_evasion_tight_and_standpat_ttpv.patch` (`2,420` B, `40` lines, `SHA-256: 45252132C8615E269C667B97FC10B1D77C01648FB505723AFEA3AF4E7DEE7B77`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF28_qs_evasion_tight_and_standpat_ttpv.exe` (`2,382,848` B, `SHA-256: 1A90AF3FF9BEB54CCF8C59668DE6092A1F52D1B0FBE74EB6EE8DCED91F94E8DE`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF28_qs_evasion_tight_and_standpat_ttpv_gate.json` (`8,887` B, `275` lines, `SHA-256: 6560938881B4195A14CA5AC413DDC390848840A88B367FC6DC06D798F3D13AF7`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_02_sf28_behavioral_and_bench`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -1826,9 +1826,9 @@
         best_score = eval;
         if (best_score >= beta) {
 #if FORGE_SPD_TT_NOTLS
-            if (!tt_hit) store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
+            if (!tt_hit) store_tt(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, tt_pv, board.halfmove_clock());
 #else
-            if (!tt_hit) shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, false, board.halfmove_clock());
+            if (!tt_hit) shared_.tt.store(tt_probe, board.key(), score_to_tt(best_score, ply), ss->raw_eval, Move::none(), 0, BoundLower, tt_pv, board.halfmove_clock());
 #endif
             return best_score;
         }
@@ -1847,14 +1847,19 @@
     while (!(move = picker.next(false)).is_none()) {
         if (!picker.last_move_known_legal() && !board.is_legal(move)) continue;
         ++move_count;
-        if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {
-            const bool gives_check = board.gives_check(move);
-            // Futility: even winning the captured piece cannot raise alpha.
-            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
-                best_score = std::max(best_score, futility_base + capture_value(board, move));
+        if (mate_moves_ == 0 && best_score > -MateInMaxPly) {
+            if (!in_check) {
+                const bool gives_check = board.gives_check(move);
+                // Futility: even winning the captured piece cannot raise alpha.
+                if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
+                    best_score = std::max(best_score, futility_base + capture_value(board, move));
+                    continue;
+                }
+                if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
+            } else if (move_count >= 2 && !move.is_capture() && !move.is_promotion() &&
+                       !board.gives_check(move) && !board.see_ge(move, 0)) {
                 continue;
             }
-            if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
         }
 #if FORGE_SPD_PREFETCH_EARLY
         std::uint64_t child_key = 0;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:1826-1834, 1847-1863` inside `Worker::qsearch`):**
  1. **Hunk 1 — Stand-Pat `tt_pv` Preservation (`search.cpp:1829, 1831`):** When `best_score >= beta` and `!tt_hit`, `r15dsg` previously stored `false` for the `tt_pv` flag in both the `FORGE_SPD_TT_NOTLS` (`store_tt`) and `#else` (`shared_.tt.store`) branches. `SF28` stores `tt_pv` instead, preventing quiescence stand-pat fail-highs on PV lines from erasing `tt_pv` history for subsequent visits.
  2. **Hunk 2 — Tightened Check-Evasion Pruning (`search.cpp:1847-1863`):** `r15dsg` restricted the quiescence move-pruning block (`1850`) to `!in_check`, expanding every legal check evasion. `SF28` lifts `!in_check` out of the outer guard (`if (mate_moves_ == 0 && best_score > -MateInMaxPly)`) into an `if (!in_check) { ... } else if (...)` split: `!in_check` retains exact `r15dsg` capture futility and `-tune::QsSeeMargin` SEE pruning, while `in_check` prunes quiet non-tactical evasions (`!is_capture() && !is_promotion() && !board.gives_check(move)`) that lose material (`!board.see_ge(move, 0)`) starting at `move_count >= 2` (as soon as move 1 already established `best_score > -MateInMaxPly`).
- **Bounds & Interaction Checks (EXPLICIT OVERLAP WARNING):**
  1. **Direct Overlap with `SF33_qs_overhaul_SF13_plus_SF32` (Super-Stack Patch #2):**
     - `SF28` Hunk 2 (`search.cpp:1847-1863`, `in_check` pruning with `move_count >= 2`) **DIRECTLY OVERLAPS** `SF33` (`search.cpp:1847-1875`, `in_check` pruning with `move_count > 2` plus `SF32` `!in_check` `see_ge(move, 1)` futility pruning), as well as `SF13` (`1847-1859`) and `SF24` (`1847-1859`).
     - Note: multi-file `git apply --check` cannot detect this collision because `git` validates each patch against the untouched baseline; sequential application of `SF28` and `SF33` collides on `search.cpp:1850-1858`.
     - **Important:** `SF33` is already **Patch #2 of the 6-patch Super-Stack** (`superstack_6patch.exe`). Meanwhile, **`SF28` Hunk 1 (`search.cpp:1826-1834`, stand-pat `tt_pv` store) is 100% orthogonal to `SF33`** and all other patches. If `SF28`'s stand-pat `tt_pv` fix is wanted atop `SF33` / the Super-Stack, cherry-pick **only Hunk 1 (`1826-1834`)** or explicitly reconcile `move_count >= 2` vs `move_count > 2` in `in_check` and match-test the merged variant.
  2. **Checkmate & Evasion Safety (`has_non_pawn_material` Disclosure):** Guarded by `mate_moves_ == 0`, `best_score > -MateInMaxPly` (at least one non-mated evasion already searched), `move_count >= 2`, `!is_capture()`, `!is_promotion()`, `!gives_check()`, and `!see_ge(move, 0)`. Same disclosure as `PACKET_SF13`: unlike Stockfish, `SF28` does not gate on `has_non_pawn_material(us)` in pure pawn endings (low risk because `best_score > -MateInMaxPly`, `move_count >= 2`, `!gives_check`, and `see_ge(move, 0)` remain enforced; king moves rarely fail `SEE >= 0`). Verified `Qh4+` check evasion (`bestmove g2g3`, no `score mate -1`), Mate-in-1 (`d1d8`), `go mate 2`, and `perft 5 = 4,865,609`.
- **Caveat 1 (No Match Played Yet):** `ALL_MATCHES_SCOREBOARD.md` records **0 completed `fastchess` matches** for `SF28`. Related predecessor `SF13` (`move_count > 2` without Hunk 1 or `>= 2`) scored `+20.87 [+4.86, +36.97]` Elo in a 600g screen (`169-298-133`, `LOS = 99.5%`) and `+8.34 [-4.39, +21.10]` Elo in a separate 1,000g confirmation (`256-512-232`, `LOS = 90.0%`, reported unpooled). `SF28` itself requires a pre-declared `50k` match before placement.
- **Caveat 2 (Non-PGO Binary):** `SF28_qs_evasion_tight_and_standpat_ttpv.exe` is non-PGO. Rebuild with PGO if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish `qsearch()` stand-pat `tt_pv` preservation (`store_tt(..., tt_pv, ...)`) combined with tightened `SF13` quiescence check-evasion SEE pruning (`move_count >= 2` after `best_score > -MateInMaxPly`), re-implemented cleanly on Forge's `Worker::qsearch` and `board.see_ge`.
- **License Status:** 100% clean-room implementation (`+13 / -8`, `5` net C++ lines), zero verbatim GPL code copied, zero Stockfish eval labels.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `SF28_qs_evasion_tight_and_standpat_ttpv.exe` (`1A90AF3F...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `310,905 / 757,111` | `-0.63% / -12.20%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `259,494 / 808,393` | `-0.08% / +11.48%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `197,118 / 568,093` | `+4.89% / -10.14%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `219,267 / 577,019` | `+0.39% / +0.16%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 120/200 balanced FENs, `8/8` KB, `8/8` OB) | `0` differ | `0` differ (`max_diff_cp = 0`, planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF28_qs_evasion_tight_and_standpat_ttpv.exe` (`FORGE_TEST_EXE=""`)

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

*(Primary `C:\nnue-lab\venv\Scripts\python.exe` lacks `pytest`; run via `unittest discover -s ... -p ...` rather than a bare `.py` path: `C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v` — `RC=0`, `9/9 OK` when `FORGE_TEST_EXE=""`; `RC=1`, `7 failed` when `FORGE_TEST_EXE=base_r15dsg.exe`.)*

Observed live output (`RC=0`, `9 passed in 31.38s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_02_sf28_behavioral_and_bench PASSED [ 22%]
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
============================= 9 passed in 31.38s ==============================
```
- `test_01_all_patches_apply_cleanly`: **PASSED** (`git -C C:\nnue-lab\forge\r15dsg apply --check` `RC=0` for `SF28` and all 6 peer patches)
- `test_02_sf28_behavioral_and_bench`: **PASSED** (`B4` diverges from `base_r15dsg` on `7/8` FENs: `startpos_d9` `4022->4017`, `kiwipete_d8` `8370->8552`, `kiwipete_d10` `(-134, 20623)->(-148, 27755)`, `bench3_d9`, `bench5_d9`, `tactical_d9`, `sf32_eq_d9`; `FULL` diverges on `8/8` FENs; `B4 bench 13` = `568,093` vs `632,195`, delta `-10.14%` inside `[-15%, -5%]`)
- `test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, Mate-in-1 `d1d8`, `go mate 2`, `Qh4+` `g2g3`, `v3_parity 0/200` with planted `king_map[2]` fault caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

Observed live output (`RC=1`, `7 failed, 2 passed in 5.88s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_02_sf28_behavioral_and_bench FAILED [ 22%]
...
E           AssertionError: ('c2c4', 22, 4022) == ('c2c4', 22, 4022) : SF28 B4 must diverge from base on startpos_d9
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
========================= 7 failed, 2 passed in 5.88s =========================
```

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:1826-1834, 1847-1863` and `SF28_qs_evasion_tight_and_standpat_ttpv.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] **Resolve `SF28` vs `SF33` overlap before stacking:** `SF33` is Patch #2 of the 6-patch Super-Stack and collides with `SF28` Hunk 2 (`1847-1863`). Either test `SF28` standalone, cherry-pick only Hunk 1 (`1826-1834` stand-pat `tt_pv`), or test an explicit `move_count >= 2` + `SF32` merge.
- [ ] Run pre-declared `1,000g @ 50k` match (`SF28_qs_evasion_tight_and_standpat_ttpv.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
