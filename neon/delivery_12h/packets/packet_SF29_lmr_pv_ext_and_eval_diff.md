# Opus Placement Review Packet: `SF29_lmr_pv_ext_and_eval_diff`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish Late Move Reductions refinement combining (1) an extra `-1` reduction relief on `ss->tt_pv` nodes when a live TT score beats `alpha` (`tt_hit && tt_score != ValueNone && tt_score > alpha`), (2) `+1` extra reduction on far-below-alpha non-PV quiet moves (`ss->static_eval + 200 < alpha`), and (3) bounded 1-ply LMR extension (`max_lmr_d = new_depth + 1` when `r < 0`) gated by `!pv_node && !root_node && !bare_king_lmr_cap && new_depth < 12`. Passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB on `r0067`), diverges on `8/8` `B4` and `8/8` `FULL` benchmark FENs (flipping `B4` `bench3_d9` `c4d5->h2h3` and `sf32_eq_d9` `d4c5->f1e1`), and expands `bench 13` across all configs (`HCE +23.04%`, `r0067 Default +22.29%`, `B4+r0067 +34.60%`, `FULL+r0067 +10.54%`). **OVERLAP ALERT:** Overlaps `proto_7_ttpv_lmr_and_iir.patch` at `search.cpp:2409`, though orthogonal to the 6-patch Super-Stack (`V3P_v3` + `SF33` + `SF8` + `proto_1` + `SF15` + `SF27`). Zero completed `fastchess` matches exist; a pre-declared `1,000g @ 50k` match is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\patches\SF29_lmr_pv_ext_and_eval_diff.patch` (`2,167` B, `35` lines, `SHA-256: D89DCD817B9930ABAFD43B56256BFB446B76660377C1F45BDAF2C5E66B59679E`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\builds\SF29_lmr_pv_ext_and_eval_diff.exe` (`2,382,848` B, `SHA-256: C16DD099D7EC59E338581E267C8A9FE96ABA940A21E69B236B79B23BEA83457D`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\builds\SF29_lmr_pv_ext_and_eval_diff_gate.json` (`8,882` B, `275` lines, `SHA-256: E96C112F2FB4EFA75B8E53C2A1AE05D8BC95C92D7EBD3CAE3AA6DF270CB17194`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_03_sf29_behavioral_and_bench`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -2406,12 +2406,18 @@
             move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&
             (quiet || !ss->tt_pv || move_count > 4)) {
             int r = reduction(quiet, depth, move_count);
-            if (ss->tt_pv) r -= 1;
+            if (ss->tt_pv) {
+                r -= 1;
+                // SF29 (clean-room Stockfish LMR): live PV TT hit reduces 1 ply less.
+                if (tt_hit && tt_score != ValueNone && tt_score > alpha) r -= 1;
+            }
             if (!improving) r += 1;
             if (cut_node) r += 2;
             if (tt_capture && quiet) r += 1;
             if (gives_check) r -= 1;
             if (in_check) r -= 1;
+            // SF29: far-below-alpha non-PV quiet moves reduce 1 ply more.
+            if (!pv_node && !in_check && quiet && ss->static_eval != ValueNone && ss->static_eval + 200 < alpha) r += 1;
             if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
             if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
             if (tune::LmrSignedCorrection && quiet && ss->static_eval != ValueNone &&
@@ -2423,7 +2429,11 @@
             // four replies are the likely refutations, so they lose one ply of reduction.
             if (tune::LmrLateParentRelief && ss->arrival_index >= 7 && move_count <= 4) --r;
             if (bare_king_lmr_cap) r = std::min(r, 1);
-            const int reduced_depth = std::clamp(new_depth - r, 1, new_depth);
+            // SF29: allow bounded 1-ply LMR extension when r < 0 on non-PV nodes.
+            const int max_lmr_d = (!pv_node && !root_node && !bare_king_lmr_cap && new_depth < 12)
+                                      ? (new_depth + 1)
+                                      : new_depth;
+            const int reduced_depth = std::clamp(new_depth - r, 1, max_lmr_d);
             if (tune::HindsightDepth) (ss + 1)->withheld_plies = new_depth - reduced_depth;
             score = -search_child(board, ss + 1, reduced_depth, -alpha - 1, -alpha, true);
             if (tune::HindsightDepth) (ss + 1)->withheld_plies = 0;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`C:\nnue-lab\forge\r15dsg\src\search.cpp:2406-2435` inside `Worker::search` LMR block):**
  1. **`tt_pv` Score-Gated Relief (`search.cpp:2409`):** Keeps `if (ss->tt_pv) r -= 1;` and adds `if (tt_hit && tt_score != ValueNone && tt_score > alpha) r -= 1;`, reducing 1 ply less when a TT entry on a PV-history node already beats `alpha`.
  2. **Large Negative Eval-Diff Quiet Penalty (`search.cpp:2414+`):** Adds `if (!pv_node && !in_check && quiet && ss->static_eval != ValueNone && ss->static_eval + 200 < alpha) r += 1;` immediately after `if (in_check) r -= 1;`, reducing 1 extra ply on unpromising non-PV quiet moves when static eval trails `alpha` by more than `200` cp.
  3. **Bounded 1-Ply LMR Extension (`search.cpp:2426`):** Replaces `std::clamp(new_depth - r, 1, new_depth)` with `max_lmr_d = (!pv_node && !root_node && !bare_king_lmr_cap && new_depth < 12) ? (new_depth + 1) : new_depth;` and `std::clamp(new_depth - r, 1, max_lmr_d)`, allowing `r < 0` (e.g., `ss->tt_pv` + `tt_score > alpha` + `gives_check`/`in_check` + high history) to extend by at most 1 ply while respecting `board.halfmove_clock() + new_depth < 100` (`2405`) and `bare_king_lmr_cap`.
- **Bounds & Interaction Checks (EXPLICIT OVERLAP WARNING):**
  1. **Direct Overlap with `proto_7_ttpv_lmr_and_iir.patch` (`search.cpp:2409`):** Both `SF29` and Wave 4's `proto_7` rewrite `if (ss->tt_pv) r -= 1;` at `search.cpp:2409` to inspect `tt_score > alpha`. They are mutually conflicting alternatives at line `2409` and cannot be sequentially applied without manual reconciliation.
  2. **Stack Compatibility & LMR Context Proximity:** Completely orthogonal (disjoint hunks) to the 6-patch Super-Stack (`V3P_v3` + `SF33` + `SF8` + `proto_1` + `SF15` + `SF27`), `SF28`, `SF30`, and `SF31`. Inside the LMR block (`2406-2435`), `SF29` shares leading/trailing context near `proto_9` (`2421`) and `proto_10` (`2416`), so verify context lines if combining with Wave 5 LMR prototypes.
  3. **Extension & Overflow Safety:** `ss->static_eval + 200` cannot overflow `int` (bounded within `[-MateInMaxPly + 1, MateInMaxPly - 1]`), and `new_depth < 12` caps LMR extension depth and prevents runaway recursion (`perft 5 = 4,865,609`). Note that when `reduced_depth == new_depth + 1`, `reduced_depth < new_depth` is `false` at line `2430`, so `full_depth_needed` stays `false` and the node does not re-search shallower.
- **Caveat 1 (Tree Expansion):** Because of the extra `-1` `tt_pv` relief and 1-ply LMR extension, `SF29` expands `bench 13` by `+10.54%` (`FULL`) to `+34.60%` (`B4`). Only a `50k` match determines whether the tactical gain outweighs the node expansion.
- **Caveat 2 (No Match Played Yet & Non-PGO):** `ALL_MATCHES_SCOREBOARD.md` has **0 completed matches** for `SF29`, and `SF29_lmr_pv_ext_and_eval_diff.exe` is non-PGO. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish LMR (PV-history TT score above `alpha` reduction relief `ss->tt_pv && tt_score > alpha`, large negative static-eval margin `ss->static_eval + 200 < alpha` extra reduction, and bounded `r < 0` 1-ply LMR extension), implemented cleanly on Forge's `Worker::search` LMR block.
- **License Status:** 100% clean-room implementation (`+12 / -2`, `10` net C++ lines), zero verbatim GPL code copied, zero Stockfish eval labels.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `SF29_lmr_pv_ext_and_eval_diff.exe` (`C16DD099...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `435,924 / 1,061,027` | `+39.33% / +23.04%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `306,729 / 886,772` | `+18.11% / +22.29%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `261,905 / 850,956` | `+39.36% / +34.60%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `256,451 / 636,800` | `+17.42% / +10.54%` |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 120/200 balanced FENs, `8/8` KB, `8/8` OB) | `0` differ | `0` differ (`max_diff_cp = 0`, planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `SF29_lmr_pv_ext_and_eval_diff.exe` (`FORGE_TEST_EXE=""`)

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

*(Primary `C:\nnue-lab\venv\Scripts\python.exe` lacks `pytest`; run via `unittest discover -s ... -p ...` rather than a bare `.py` path: `C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v` — `RC=0`, `9/9 OK` when `FORGE_TEST_EXE=""`; `RC=1`, `7 failed` when `FORGE_TEST_EXE=base_r15dsg.exe`.)*

Observed live output (`RC=0`, `9 passed in 31.38s`):
```text
TestRound911AndWave5Search::test_01_all_patches_apply_cleanly PASSED [ 11%]
TestRound911AndWave5Search::test_03_sf29_behavioral_and_bench PASSED [ 33%]
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
============================= 9 passed in 31.38s ==============================
```
- `test_01_all_patches_apply_cleanly`: **PASSED** (`git -C C:\nnue-lab\forge\r15dsg apply --check` `RC=0` for `SF29` and all 6 peer patches)
- `test_03_sf29_behavioral_and_bench`: **PASSED** (`B4` diverges on `8/8` FENs including bestmove flips on `bench3_d9` `c4d5->h2h3` (`('h2h3', 6, 24243)`) and `sf32_eq_d9` `d4c5->f1e1`; `FULL` diverges on `8/8` FENs including `bench3_d9` `h2h3->c4d5` (`('c4d5', 16, 13962)`); `B4 bench 13` = `850,956` vs `632,195` (`+34.60%`) and `FULL bench 13` = `636,800` vs `576,076` (`+10.54%`))
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
TestRound911AndWave5Search::test_03_sf29_behavioral_and_bench FAILED [ 33%]
...
E           AssertionError: ('c2c4', 22, 4022) == ('c2c4', 22, 4022) : SF29 B4 must diverge from base on startpos_d9
...
TestRound911AndWave5Search::test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity PASSED [100%]
========================= 7 failed, 2 passed in 5.88s =========================
```

---

## 6. Opus Placement Checklist

- [ ] Review `C:\nnue-lab\forge\r15dsg\src\search.cpp:2406-2435` and `SF29_lmr_pv_ext_and_eval_diff.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`), noting the `search.cpp:2409` overlap with `proto_7_ttpv_lmr_and_iir.patch`.
- [ ] Run pre-declared `1,000g @ 50k` match (`SF29_lmr_pv_ext_and_eval_diff.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
