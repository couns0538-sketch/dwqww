# Opus Placement Review Packet: `SF33_qs_overhaul_SF13_plus_SF32`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room unified quiescence-search overhaul combining `SF13` (`in_check` losing quiet-evasion SEE pruning at `move_count > 2`) with `SF32` (`!in_check` equal/losing-exchange fail-soft futility pruning when `futility_base <= alpha && !board.see_ge(move, 1)`). **Already integrated as Patch #2 of the 6-patch Super-Stack** (`superstack_6patch.exe`: `6/6` clean sequential apply `RC=0`, `hard_pass: true` across `768w r0067` + `1024w G3_e24` + `1024w G2`, `0` Clang UBSan errors). Standalone `SF33` passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB on `r0067`), diverges on `8/8` `B4` and `8/8` `FULL` benchmark FENs (flipping `B4` `bench5_d9` `c4d5->f1e2` and `FULL` `bench3_d9` `h2h3->c4d5`), and shifts `B4+r0067 bench 13` by **`+33.20%`** (`842,063` vs `632,195`), `r0067 Default` by **`+4.85%`** (`760,322`), `HCE Default` by **`-4.55%`** (`823,074`), and `FULL+r0067` by **`+0.40%`** (`578,404`). **OVERLAP ALERT:** Directly overlaps `SF28` Hunk 2 (`search.cpp:1847-1863`, `move_count >= 2`), whereas `SF28` Hunk 1 (`1826-1834`, stand-pat `tt_pv`) is orthogonal to `SF33`. Zero completed `fastchess` matches exist for `SF33` itself; a pre-declared `1,000g @ 50k` match is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF33_qs_overhaul_SF13_plus_SF32.patch` (`2,236` B, `40` lines, `SHA-256: 6C6A32A6347692BA39F42FDE1C010CEE04EE0A52D724767F6FA56BA016C9A92E`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF33_qs_overhaul_SF13_plus_SF32.exe` (`2,382,848` B, `SHA-256: 346998256E4BA7C36BCCCA9488BDBD201C580462C89134E4D217466741836F15`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF33_qs_overhaul_SF13_plus_SF32_gate.json` (`8,879` B, `275` lines, `SHA-256: 228AD86D859266EE80895D9A8FBAD888FD1092BBC487DC838744996EB3CEFE55`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_06_sf33_behavioral_and_bench`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -1847,14 +1847,29 @@
     while (!(move = picker.next(false)).is_none()) {
         if (!picker.last_move_known_legal() && !board.is_legal(move)) continue;
         ++move_count;
-        if (mate_moves_ == 0 && !in_check && best_score > -MateInMaxPly) {
-            const bool gives_check = board.gives_check(move);
-            // Futility: even winning the captured piece cannot raise alpha.
-            if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
-                best_score = std::max(best_score, futility_base + capture_value(board, move));
-                continue;
-            }
-            if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
+        if (mate_moves_ == 0 && best_score > -MateInMaxPly) {
+            if (in_check) {
+                // SF13 (clean-room Stockfish QS evasion pruning): after a non-mate evasion is found,
+                // skip late quiet evasions that lose material on SEE.
+                if (move_count > 2 && !move.is_capture() && !move.is_promotion() &&
+                    !board.gives_check(move) && !board.see_ge(move, 0)) {
+                    continue;
+                }
+            } else {
+                const bool gives_check = board.gives_check(move);
+                // SF32 (clean-room Stockfish qsearch futility): equal/losing exchange when futility_base <= alpha.
+                if (!gives_check && !move.is_promotion() && !is_mate_score(alpha) &&
+                    futility_base <= alpha && !board.see_ge(move, 1)) {
+                    best_score = std::max(best_score, futility_base);
+                    continue;
+                }
+                // Futility: even winning the captured piece cannot raise alpha.
+                if (!gives_check && !move.is_promotion() && futility_base + capture_value(board, move) <= alpha) {
+                    best_score = std::max(best_score, futility_base + capture_value(board, move));
+                    continue;
+                }
+                if (!board.see_ge(move, -tune::QsSeeMargin)) continue;
+            }
         }
 #if FORGE_SPD_PREFETCH_EARLY
         std::uint64_t child_key = 0;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:1847-1875` inside `Worker::qsearch`):**
  1. **`in_check` Branch (`SF13`, `search.cpp:1851-1857`):** Lifts `!in_check` out of `if (mate_moves_ == 0 && best_score > -MateInMaxPly)`. When `in_check` and at least two legal evasions have been tried (`move_count > 2`) with a non-mated score already proven (`best_score > -MateInMaxPly`), prunes late quiet non-capture, non-promotion, non-checking evasions that lose material (`!board.see_ge(move, 0)`).
  2. **`!in_check` Branch (`SF32` + Existing QS Futility/SEE, `search.cpp:1858-1871`):** Before `capture_value` futility, checks `if (!gives_check && !move.is_promotion() && !is_mate_score(alpha) && futility_base <= alpha && !board.see_ge(move, 1))` and prunes equal/losing exchanges (`SEE <= 0`) when `futility_base <= alpha`, raising `best_score = std::max(best_score, futility_base)` for fail-soft soundness. Previously, `r15dsg` computed `futility_base + capture_value(board, move) <= alpha`, so down-material positions failed to prune defended equal Queen/Rook trades (`SEE == 0`) because `capture_value(Q)` inflated the sum above `alpha`. Existing `capture_value` futility and `!board.see_ge(move, -tune::QsSeeMargin)` remain intact below it.
- **Bounds & Interaction Checks (EXPLICIT OVERLAP WARNING & SUPER-STACK STATUS):**
  1. **6-Patch Super-Stack Integration:** `SF33` is **Patch #2 of the 6-patch Orthogonal Super-Stack** (`V3P_pairwise_psqt_fused_v3` + `SF33` + `SF8` + `proto_1` + `SF15` + `SF27` -> `builds\superstack_6patch.exe`). Verified `6/6` sequential `git apply` (`RC=0`), `hard_pass: true` across `r0067` (`768w`), `G3_FULL25 diag_e24` (`1024w`), and `G2` (`1024w`), and `0` Clang UBSan errors on all 3 nets (`SUPERSTACK_6PATCH_PROOF.md`).
  2. **Direct Overlap with `SF28` Hunk 2 (`search.cpp:1847-1863`):** `SF33` (`search.cpp:1847-1875`, `move_count > 2` + `SF32`) **DIRECTLY OVERLAPS** `SF28_qs_evasion_tight_and_standpat_ttpv` Hunk 2 (`search.cpp:1847-1863`, `move_count >= 2`), as well as standalone `SF13`, `SF24`, and `SF32` (since `SF33` supersedes `SF13 + SF32`). By contrast, **`SF28` Hunk 1 (`search.cpp:1826-1834`, stand-pat `tt_pv` store) is completely orthogonal to `SF33`** and can be cherry-picked cleanly alongside `SF33`.
  3. **Mate & Endgame Safety (`has_non_pawn_material` Disclosure):** Both branches sit inside `mate_moves_ == 0 && best_score > -MateInMaxPly`, and `SF32` adds `!is_mate_score(alpha)`, `!gives_check`, `!move.is_promotion()`, and `std::max(best_score, futility_base)`. Carries the same `PACKET_SF13` disclosure: does not gate `in_check` on `has_non_pawn_material(us)` (low risk because `move_count > 2`, `best_score > -MateInMaxPly`, `!gives_check`, and `see_ge(move, 0)` guard pawn-ending evasions). Verified `Qh4+` evasion (`g2g3`, no `score mate -1`), Mate-in-1 (`d1d8`), `go mate 2`, and `perft 5 = 4,865,609`.
- **Caveat 1 (No Match Played Yet for `SF33`):** `ALL_MATCHES_SCOREBOARD.md` records **0 completed `fastchess` matches** for `SF33` (and `SF32`). Related predecessor `SF13` scored `+20.87 [+4.86, +36.97]` Elo in a 600g screen (`169-298-133`, `LOS = 99.5%`) and `+8.34 [-4.39, +21.10]` Elo in a separate 1,000g confirmation (`256-512-232`, `LOS = 90.0%`, reported unpooled). `SF33` itself requires a pre-declared `1,000g @ 50k` match before placement.
- **Caveat 2 (Non-PGO Binary):** `SF33_qs_overhaul_SF13_plus_SF32.exe` is non-PGO. Rebuild with PGO if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish `qsearch()` check-evasion SEE pruning (`SF13`: `move_count > 2`, non-tactical `SEE < 0` evasions) combined with clean-room Stockfish `qsearch()` fail-soft futility pruning (`SF32`: `futility_base <= alpha && !board.see_ge(move, 1)`), implemented cleanly on Forge's `Worker::qsearch`.
- **License Status:** 100% clean-room implementation (`+23 / -8`, `15` net C++ lines), zero verbatim GPL code copied, zero Stockfish eval labels.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `SF33_qs_overhaul_SF13_plus_SF32.exe` (`34699825...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `300,750 / 823,074` | `-3.87% / -4.55%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `263,968 / 760,322` | `+1.65% / +4.85%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `206,491 / 842,063` | `+9.88% / +33.20%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `211,546 / 578,404` | `-3.14% / +0.40%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 120/200 balanced FENs, `8/8` KB, `8/8` OB) | `0` differ | `0` differ (`max_diff_cp = 0`, planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF33_qs_overhaul_SF13_plus_SF32.exe` (`FORGE_TEST_EXE=""`)

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

*(Primary `C:\nnue-lab\venv\Scripts\python.exe` lacks `pytest`; run via `unittest discover -s ... -p ...` rather than a bare `.py` path: `C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v` — `RC=0`, `9/9 OK` when `FORGE_TEST_EXE=""`; `RC=1`, `7 failed` when `FORGE_TEST_EXE=base_r15dsg.exe`.)*

Observed live output (`RC=0`, `9 passed in 31.38s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_06_sf33_behavioral_and_bench PASSED [ 66%]
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
============================= 9 passed in 31.38s ==============================
```
- `test_01_all_patches_apply_cleanly`: **PASSED** (`git -C C:\nnue-lab\forge\r15dsg apply --check` `RC=0` for `SF33` and all 6 peer patches)
- `test_06_sf33_behavioral_and_bench`: **PASSED** (`B4` diverges on `8/8` FENs including bestmove flip on `bench5_d9` `c4d5->f1e2` (`('f1e2', -315, 10120)`) and `kiwipete_d8` `8370->5322`; `FULL` diverges on `8/8` FENs including `bench3_d9` `h2h3->c4d5` (`('c4d5', 3, 9446)`); `B4 bench 13` = `842,063` vs `632,195` (`+33.20%`))
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
TestRound911AndWave5Search::test_06_sf33_behavioral_and_bench FAILED [ 66%]
...
E           AssertionError: ('c2c4', 22, 4022) == ('c2c4', 22, 4022) : SF33 B4 must diverge from base on startpos_d9
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
========================= 7 failed, 2 passed in 5.88s =========================
```

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:1847-1875` and `SF33_qs_overhaul_SF13_plus_SF32.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`), noting it supersedes `SF13`/`SF32`, is Patch #2 of the 6-patch Super-Stack, and overlaps `SF28` Hunk 2 (`1847-1863`, whereas `SF28` Hunk 1 `1826-1834` is orthogonal).
- [ ] Run pre-declared `1,000g @ 50k` match (`SF33_qs_overhaul_SF13_plus_SF32.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
