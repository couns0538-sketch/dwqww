# Opus Placement Review Packet: `proto_8_eval_lmp_and_capfut`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish/Stormphrax eval-margin LMP tightening (`3/4` when `static_eval + 120 + 60*depth <= alpha`) + improving-aware capture futility (`+/-35 cp` shift on `FULL` where `CaptureFutilityBase > 0`, and non-improving `40 + 180*lmr_depth` at `lmr_depth <= 3` on `B4`/Default, `EvalLmpRefine`, `default 1 min 0 max 1`), verified bit-exact with `base_r15dsg.exe` when `EvalLmpRefine=0` (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`), stacks cleanly (`RC=0`, builds cleanly) with `V3P_pairwise_psqt_fused + SF8 + SF20 + proto_7`, passes all `--quick` Master Gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and moves `B4+r0067 bench 13` by **`+1.19%`** (`639,724` vs `632,195`) and `FULL+r0067 bench 13` by **`-1.45%`** (`567,725` vs `576,076`). A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\patches\proto_8_eval_lmp_and_capfut.patch` (`4,958` B, `71` lines, `SHA-256: 1862CEA0B89387BE43BEF0A74BE9CDA2BBF2A41AB6E3921406F93B385E62AF63`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_8_eval_lmp_and_capfut.exe` (`2,382,848` B, `SHA-256: B0AADE3D8132957F4215B2408E79AA66E7569554B722EC82409011B70D6E5C22`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_8_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_proto_8_eval_lmp_and_capfut.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -298,6 +298,7 @@ extern int TmMinFactorPercent;    // lower bound of the combined soft-limit fact
 extern int CaptureFutilityBase;   // futility pruning of captures: base margin (0 = off)
 extern int CaptureFutilityMultiplier;
 extern int CaptureFutilityDepth;
+extern int EvalLmpRefine;          // 0 = off, 1 = eval-margin LMP tightening + improving-aware capture futility
 extern int FailLowContinuationBonus; // x0.01 of the history bonus given to the parent move on fail low (0 = off)
 extern bool ContHist4PlyRead;        // read 4-ply-back continuation history in quiet scoring (false = off)
 extern bool NonPawnCorrection;       // per-color non-pawn static-eval correction history (false = off)
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -146,6 +146,7 @@ int TmMinFactorPercent = 45;
 int CaptureFutilityBase = 0;
 int CaptureFutilityMultiplier = 250;
 int CaptureFutilityDepth = 6;
+int EvalLmpRefine = 1;
 int FailLowContinuationBonus = 0;
 // packc28 (ported into forge/r12 on 2026-11-15, see forge/tools/make_r12_e.py): three ideas, all 0 = off.
 int AspFailHighReduce = 0;      // 1: after a root fail-high the re-search is one ply shallower per fail-high in a row
@@ -218,6 +219,7 @@ const std::vector<Parameter>& parameters() {
         {"TmFallingEvalPercent", &TmFallingEvalPercent, 0, 400}, {"TmMinFactorPercent", &TmMinFactorPercent, 10, 100},
         {"CaptureFutilityBase", &CaptureFutilityBase, 0, 1000},  {"CaptureFutilityMultiplier", &CaptureFutilityMultiplier, 0, 1000},
         {"CaptureFutilityDepth", &CaptureFutilityDepth, 0, 15},  {"FailLowContinuationBonus", &FailLowContinuationBonus, 0, 300},
+        {"EvalLmpRefine", &EvalLmpRefine, 0, 1},
         {"AspFailHighReduce", &AspFailHighReduce, 0, 1},         {"AspFailHighMaxReduce", &AspFailHighMaxReduce, 1, 6},
         {"EvalSwingMult", &EvalSwingMult, 0, 64},                {"EvalSwingMax", &EvalSwingMax, 50, 400},
         {"TtCutoffHistory", &TtCutoffHistory, 0, 1},
@@ -2269,7 +2271,12 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
                     if (is_mate_score(alpha)) ++tune::sound_prune_trace.quiet_check_on_mate_alpha;
                 }
             };
-            if (quiet && !skip_quiets && move_count >= lmp_threshold(depth, improving)) skip_quiets = true;
+            int lmp_lim = lmp_threshold(depth, improving);
+            if (tune::EvalLmpRefine != 0 && !in_check && ss->static_eval != ValueNone &&
+                !is_mate_score(alpha) && depth <= 6 && ss->static_eval + 120 + 60 * depth <= alpha) {
+                lmp_lim = std::max(2, lmp_lim * 3 / 4);
+            }
+            if (quiet && !skip_quiets && move_count >= lmp_lim) skip_quiets = true;
             const int lmr_depth = std::max(0, depth - reduction(quiet, depth, move_count));
             // B4 TtPruneV2: the TT move is never pruned by futility / history / SEE (it carried a bound before);
             // quiet futility needs a wider margin when improving; history pruning starts at 3/4 of the threshold
@@ -2304,12 +2311,21 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
             } else if (prunable) {
                 // Futility pruning for captures: even winning the piece cannot
                 // bring the position back to alpha.
-                if (tune::CaptureFutilityBase > 0 && capture && !in_check && !gives_check &&
-                    lmr_depth <= tune::CaptureFutilityDepth &&
+                const int cap_fut_base =
+                    tune::CaptureFutilityBase > 0
+                        ? (tune::CaptureFutilityBase + (tune::EvalLmpRefine != 0 ? (improving ? 35 : -35) : 0))
+                        : (tune::EvalLmpRefine != 0 && !improving ? 40 : 0);
+                const int cap_fut_mult =
+                    tune::CaptureFutilityBase > 0 ? tune::CaptureFutilityMultiplier : 180;
+                const int cap_fut_depth =
+                    tune::CaptureFutilityBase > 0 ? tune::CaptureFutilityDepth : 3;
+                if ((tune::CaptureFutilityBase > 0 || (tune::EvalLmpRefine != 0 && !improving)) &&
+                    capture && !in_check && !gives_check &&
+                    lmr_depth <= cap_fut_depth &&
 #if defined(FORGE_MATE_ALPHA_GUARD) && FORGE_MATE_ALPHA_GUARD
                     (!tune::MateAlphaGuard || !is_mate_score(alpha)) &&
 #endif
-                    ss->static_eval + tune::CaptureFutilityBase + tune::CaptureFutilityMultiplier * lmr_depth +
+                    ss->static_eval + cap_fut_base + cap_fut_mult * lmr_depth +
                             capture_value(board, move) + history / 8 <= alpha) {
                     trace_case();
                     continue;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`include/forge/search.hpp:300+`; `src/search.cpp:148+, 220+, 2272, 2307-2313`):**
  1. **Eval-margin LMP tightening (`search.cpp:2272`):** When `EvalLmpRefine != 0 && !in_check && ss->static_eval != ValueNone && !is_mate_score(alpha) && depth <= 6 && ss->static_eval + 120 + 60 * depth <= alpha`, tightens `lmp_lim = std::max(2, lmp_lim * 3 / 4)` before setting `skip_quiets = true`.
  2. **Improving-aware capture futility (`search.cpp:2307-2313`):** Under `FULL` (`CaptureFutilityBase=45 > 0`), shifts the base margin by `+35` when `improving` and `-35` when `!improving`. Under `B4`/Default (`CaptureFutilityBase=0`), activates conservative non-improving capture futility (`40 + 180 * lmr_depth` for `lmr_depth <= 3`), preserving `prunable`, `!in_check`, `!gives_check`, and `MateAlphaGuard`.
  3. **Bit-exactness (`EvalLmpRefine=0`):** `lmp_lim == lmp_threshold(depth, improving)`, and capture futility reduces identically to `CaptureFutilityBase > 0` with `CaptureFutilityBase + CaptureFutilityMultiplier * lmr_depth`.
- **Bounds & Interaction Checks:**
  1. **Mate-score / check safety:** Both LMP tightening and capture futility preserve `!in_check` and `!is_mate_score(alpha)` (`MateAlphaGuard`).
  2. **Stack separation (`V3P_pairwise_psqt_fused + SF8 + SF20 + proto_7 + proto_8`):** Verified via both `git apply --check` AND sequential `git apply` + `build_fast.py` smoke compile (`RC=0`, `6.1s`). `>= 16` lines separation from `proto_7` in `parameters()` and `>= 84` lines in `Worker::search`.
- **Caveat 1 (No Match Played Yet):** Only deterministic `--quick` Master Gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `proto_8_eval_lmp_and_capfut.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish / Stormphrax eval-margin LMP tightening and improving-aware capture futility adapted to Forge's `tune::EvalLmpRefine` spin parameter (`0/1`).
- **License Status:** 100% clean-room implementation (`23` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `proto_8_eval_lmp_and_capfut.exe` (`b0aade3d...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `297,435 / 904,823` | `-4.93% / +4.93%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `275,663 / 725,537` | `+6.15% / +0.05%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `187,255 / 639,724` | `-0.36% / +1.19%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `218,657 / 567,725` | `+0.11% / -1.45%` |
| Ablation (`EvalLmpRefine=0`) `B4` / `FULL` | `187,930 / 632,195` \| `218,410 / 576,076` | `187,930 / 632,195` \| `218,410 / 576,076` | Bit-exact `0` diff |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `proto_8_eval_lmp_and_capfut.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_proto_8_eval_lmp_and_capfut.py
```

Observed output (`RC=0`):
- `test_1_uci_gate_patch_and_bit_exact_ablation`: **PASSED** (`git apply --check RC=0`; `EvalLmpRefine` advertised `default 1 min 0 max 1`; `=0` bit-exact `187,930 / 632,195` (`B4`) and `218,410 / 576,076` (`FULL`))
- `test_2_behavioral_divergence_and_bench_bounds`: **PASSED** (`6/6` B4 positions diverge: `kiwipete d8` `8370 -> 8311`, `kiwipete d10` `20623 -> 20380`, `bench3 d9` `12494 -> 12452`, `bench5 d9` `10472 -> 10466`, `bench8 d9` `6302 -> 6295`, `tactical_checks d9` `17044 -> 16953`; `B4` `+1.19%`, `FULL` `-1.45%`, both in `[-25%, +10%]`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_proto_8_eval_lmp_and_capfut.py
```

Observed output (`RC=1`):
- `test_1_uci_gate_patch_and_bit_exact_ablation`: **FAILED** (`AssertionError: 'option name EvalLmpRefine type spin default 1 min 0 max 1' not found`)
- `test_2_behavioral_divergence_and_bench_bounds`: **FAILED** (`AssertionError: 0 != 6 : Expected all 6 positions to diverge from base, got 0`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `include/forge/search.hpp:300+`, `src/search.cpp:2272, 2307-2313`, and `proto_8_eval_lmp_and_capfut.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`proto_8_eval_lmp_and_capfut.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_proto_8_eval_lmp_and_capfut.py --exe <placed_exe>` and `run_master_gates.py --quick`.
