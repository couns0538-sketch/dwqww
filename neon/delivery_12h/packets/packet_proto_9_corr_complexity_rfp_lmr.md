# Opus Placement Review Packet: `proto_9_corr_complexity_rfp_lmr`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish `correctionValue` complexity adjustment (`CorrComplexityRefine`, `default 1 min 0 max 1`) using centered `|static_eval - raw_eval|` to widen/tighten Reverse Futility Pruning margins (`[-12, +48]` cp via `rfp_worsening`) and gate quiet LMR reductions (`--r` for high correction `>= 56` cp, `++r` for calm non-PV `depth >= 6` with `<= 8` cp). Verified 100% bit-exact with `base_r15dsg.exe` when `CorrComplexityRefine=0` (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`), passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB), diverges on `8/8` `B4` and `8/8` `FULL` benchmark FENs, and shifts `r0067 Default bench 13` by **`-18.93%`** (`587,886` vs `725,158`), `B4+r0067` by **`+21.35%`** (`767,145` vs `632,195`), and `FULL+r0067` by **`+6.56%`** (`613,852` vs `576,076`). A pre-declared `1,000g @ 50k` match is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\patches\proto_9_corr_complexity_rfp_lmr.patch` (`3,255` B, `61` lines, `SHA-256: 776B26A2B2717EB5C8520ADFEC1CC348C03110F5F2EF8914F26887A0185915F1`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\proto_9_corr_complexity_rfp_lmr.exe` (`2,383,360` B, `SHA-256: C7464BAA2AF89FB99EDCFD75DA59D245986D38BF6E8F4F39A3DE622531DCEB90`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\proto_9_corr_complexity_rfp_lmr_gate.json` (`8,926` B, `275` lines, `SHA-256: 215CB73D8CF24894AD5C7824CAA514482A36EC78D6A8F7B272198DF0C0003F76`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_07_proto_9_uci_ablation_and_behavioral`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -258,6 +258,7 @@
 extern int RfpDepth;
 extern int RfpMargin;
 extern int RfpImproving;
+extern int CorrComplexityRefine; // 0 = off, 1 = centered |static_eval - raw_eval| RFP margin & quiet LMR
 extern int RazorDepth;
 extern int RazorBase;
 extern int RazorMultiplier;
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -107,6 +107,7 @@
 int RfpDepth = 8;
 int RfpMargin = 72;
 int RfpImproving = 40;
+int CorrComplexityRefine = 1;
 int RazorDepth = 2;
 int RazorBase = 150;
 int RazorMultiplier = 350;
@@ -193,6 +194,7 @@
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
         {"RfpDepth", &RfpDepth, 0, 15},                  {"RfpMargin", &RfpMargin, 10, 300},
         {"RfpImproving", &RfpImproving, 0, 200},         {"RazorDepth", &RazorDepth, 0, 6},
+        {"CorrComplexityRefine", &CorrComplexityRefine, 0, 1},
         {"RazorBase", &RazorBase, 0, 1000},              {"RazorMultiplier", &RazorMultiplier, 0, 1000},
         {"FutilityDepth", &FutilityDepth, 0, 15},        {"FutilityBase", &FutilityBase, 0, 500},
         {"FutilityMultiplier", &FutilityMultiplier, 0, 500},
@@ -2082,9 +2084,13 @@
         // Reverse futility pruning.
         // B4 TtPruneV2: when the opponent's static eval fell on their move ("opponent worsening"), the fail high is a
         // third of a margin step cheaper. 0 with the option off, so the condition is r7's.
-        const int rfp_worsening = tt_prune_v2_ && (ss - 1)->static_eval != ValueNone &&
-                                          ss->static_eval + (ss - 1)->static_eval > 2
-                                      ? tune::RfpMargin / 3 : 0;
+        int rfp_worsening = tt_prune_v2_ && (ss - 1)->static_eval != ValueNone &&
+                                    ss->static_eval + (ss - 1)->static_eval > 2
+                                ? tune::RfpMargin / 3 : 0;
+        if (tune::CorrComplexityRefine != 0 && ss->static_eval != ValueNone && ss->raw_eval != ValueNone) {
+            const int corr_abs = std::min(std::abs(ss->static_eval - ss->raw_eval), 256);
+            rfp_worsening -= std::clamp((corr_abs - 24) / 2, -12, 48);
+        }
         if (!bare_king_mode && depth <= tune::RfpDepth &&
             eval - (tune::RfpMargin * depth - tune::RfpImproving * improving - rfp_worsening) >= beta &&
             eval < MateInMaxPly) {
@@ -2418,6 +2424,15 @@
                 ss->raw_eval != ValueNone) {
                 const int correction_cp = ss->static_eval - ss->raw_eval;
                 if (correction_cp != 0) r = apply_lmr_signed_correction(r, correction_cp);
+            }
+            if (tune::CorrComplexityRefine != 0 && quiet && ss->static_eval != ValueNone &&
+                ss->raw_eval != ValueNone) {
+                const int corr_abs = std::min(std::abs(ss->static_eval - ss->raw_eval), 256);
+                if (corr_abs >= 56) {
+                    --r;
+                } else if (corr_abs <= 8 && !pv_node && depth >= 6) {
+                    ++r;
+                }
             }
             // A parent tried after at least six earlier moves is speculative. Its first
             // four replies are the likely refutations, so they lose one ply of reduction.
```

---

## 2. Technical Note & Caveats

- **Mechanism (`include/forge/search.hpp:260+`; `src/search.cpp:109+, 195+, 2085-2087, 2421+`):**
  1. **UCI Parameter (`CorrComplexityRefine`, `default 1 min 0 max 1`):** Registered cleanly after `RfpImproving`, leaving `>= 7` lines of separation from `proto_1`, `proto_7`, `proto_8`, and `proto_10`.
  2. **Centered Correction Complexity RFP Margin (`search.cpp:2085-2087`):** Converts `rfp_worsening` to mutable `int` and, when `tune::CorrComplexityRefine != 0 && ss->static_eval != ValueNone && ss->raw_eval != ValueNone`, sets `corr_abs = std::min(std::abs(ss->static_eval - ss->raw_eval), 256)` and subtracts `std::clamp((corr_abs - 24) / 2, -12, 48)` from `rfp_worsening`. At `corr_abs = 0`, the effective RFP margin tightens by `12` cp; at `24`, neutral (`0` cp); at `>= 120`, the margin widens by `48` cp so RFP avoids pruning positions with large NNUE correction swings.
  3. **Quiet LMR Complexity Adjustment (`search.cpp:2421+`):** Placed immediately after `LmrSignedCorrection`. When `tune::CorrComplexityRefine != 0 && quiet && ss->static_eval != ValueNone && ss->raw_eval != ValueNone`, reduces 1 ply less (`--r`) when `corr_abs >= 56` and reduces 1 ply more (`++r`) on calm non-PV nodes at `depth >= 6` when `corr_abs <= 8`.
  4. **Bit-exactness (`CorrComplexityRefine=0`):** Both guards short-circuit to `false`, producing identical control flow and node counts to `base_r15dsg.exe`.
- **Bounds & Interaction Checks:**
  1. **Overflow & Mate Safety:** `static_eval` and `raw_eval` are clamped to `[-31871, +31871]` (`[-MateInMaxPly + 1, MateInMaxPly - 1]`) inside `Worker::corrected_eval`, so `|static_eval - raw_eval| <= 63742` with zero signed overflow; `eval < MateInMaxPly` (`2090`) and `std::clamp(new_depth - r, 1, new_depth)` (`2426`) remain intact downstream.
  2. **Stack Separation:** Leaves `search.cpp:2088-2091` untouched, so `SF15_rfp_failsoft_blend.patch` (modifying line `2091`) has zero hunk collision. Also disjoint from `proto_10` (`2416+`), `SF29` (`2409`, `2414+`, `2426`), and all 6 Super-Stack patches (`V3P_v3`, `SF33`, `SF8`, `proto_1`, `SF15`, `SF27`).
- **Caveat 1 (No Match Played Yet):** Only deterministic `--quick` Master Gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `proto_9_corr_complexity_rfp_lmr.exe` is non-PGO. Rebuild with PGO if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish `correctionValue` complexity magnitude adjustment for RFP margins and quiet LMR, adapted to Forge's `ss->static_eval - ss->raw_eval` difference and gated by `tune::CorrComplexityRefine`.
- **License Status:** 100% clean-room implementation (`19` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `proto_9_corr_complexity_rfp_lmr.exe` (`C7464BAA...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `291,788 / 822,579` | `-6.74% / -4.61%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `248,930 / 587,886` | `-4.15% / -18.93%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `280,450 / 767,145` | `+49.23% / +21.35%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `173,446 / 613,852` | `-20.59% / +6.56%` |
| Ablation (`CorrComplexityRefine=0`) `B4` / `FULL` | `187,930 / 632,195` \| `218,410 / 576,076` | `187,930 / 632,195` \| `218,410 / 576,076` | Bit-exact `0` diff |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 120/200 balanced FENs, `8/8` KB, `8/8` OB) | `0` differ | `0` differ (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on Target Exes (`FORGE_TEST_EXE=""`)

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

*(Primary `C:\nnue-lab\venv\Scripts\python.exe` lacks `pytest`; run via `unittest discover -s ... -p ...` rather than a bare `.py` path: `C:\nnue-lab\venv\Scripts\python.exe -B -m unittest discover -s C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests -p test_round9_11_and_wave5_search.py -v` — `RC=0`, `9/9 OK` when `FORGE_TEST_EXE=""`; `RC=1`, `7 failed` when `FORGE_TEST_EXE=base_r15dsg.exe`.)*

Observed output (`RC=0`, `9 passed in 36.16s`):
- `test_01_all_patches_apply_cleanly`: **PASSED** (`git -C C:\nnue-lab\forge\r15dsg apply --check` `RC=0` for all 7 patches)
- `test_07_proto_9_uci_ablation_and_behavioral`: **PASSED** (`option name CorrComplexityRefine type spin default 1 min 0 max 1` advertised; `=0` bit-exact `187,930 / 632,195` (`B4`) and `218,410 / 576,076` (`FULL`); `=1` diverges on `8/8` `B4` FENs including `startpos_d9` `c2c4->e2e3`, `bench3_d9` `c4d5->h2h3`, `tactical_d9` `b2b4->c1g5`, `sf32_eq_d9` `d4c5->f1e1`, and `8/8` `FULL` FENs including `startpos_d9` `g1f3->d2d4`, `bench3_d9` `h2h3->c4d5`, `tactical_d9` `b2b4->f1e1`)
- `test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, Mate-in-1 `d1d8`, `go mate 2`, `Qh4+` `g2g3`, `v3_parity 0/200` with planted fault caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

Observed output (`RC=1`, `7 failed, 2 passed in 5.98s`):
- `test_01_all_patches_apply_cleanly`: **PASSED**
- `test_02`..`test_06`: **FAILED** (baseline matches itself on Round 9–11 behavioral FENs)
- `test_07_proto_9_uci_ablation_and_behavioral`: **FAILED** (`AssertionError: 'option name CorrComplexityRefine type spin default 1 min 0 max 1' not found`)
- `test_08_proto_10_uci_ablation_and_behavioral`: **FAILED** (`AssertionError: 'option name CutNodeHistRefine type spin default 1 min 0 max 1' not found`)
- `test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity`: **PASSED**

---

## 6. Opus Placement Checklist

- [ ] Review `include/forge/search.hpp:260+`, `src/search.cpp:2085-2087, 2421+`, and `proto_9_corr_complexity_rfp_lmr.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`proto_9_corr_complexity_rfp_lmr.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
