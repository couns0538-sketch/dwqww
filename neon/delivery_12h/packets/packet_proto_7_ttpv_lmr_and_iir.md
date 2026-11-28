# Opus Placement Review Packet: `proto_7_ttpv_lmr_and_iir`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish `tt_pv` LMR refinement (TT score/depth gated relief + upper-bound non-`tt_pv` cut-node tightening) paired with deeper non-`tt_pv` non-TT-move IIR (`TtPvLmrIirRefine`, `default 1 min 0 max 1`), verified bit-exact with `base_r15dsg.exe` when `TtPvLmrIirRefine=0` (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`), stacks cleanly (`RC=0`, builds cleanly) with `V3P_pairwise_psqt_fused + SF8 + SF20 + proto_8` (preserving `search.cpp:2412` as an untouched buffer before `SF20`), passes all `--quick` Master Gates (`perft 5 = 4,865,609`, `v3_parity 0 differ` across `8/8` KB and `8/8` OB on `r0067`), and shrinks `B4+r0067 bench 13` by **`-24.80%`** (`475,386` vs `632,195`) and `FULL+r0067 bench 13` by **`-23.84%`** (`438,736` vs `576,076`). A pre-declared `1,000g @ 50k` match (plus `6+0.06` PGO confirmation) is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\patches\proto_7_ttpv_lmr_and_iir.patch` (`4,172` B, `75` lines, `SHA-256: 6F08B20178DEF1D47C4C5C40CD1FD983426331D7D64A8B02CC86835DD9CB7BCB`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_7_ttpv_lmr_and_iir.exe` (`2,383,360` B, `SHA-256: A37BC49D7D61A74913B661DC34C0C6B19DF68481840D2217F66BCE57422AFB31`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_7_gate.json` (`overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_proto_7_ttpv_lmr_and_iir.py`

---

## 1. Verbatim Patch Diff

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -272,6 +272,7 @@ extern int SeeNoisyMultiplier;
 extern int SingularDepth;
 extern int SingularMargin;
 extern int IirDepth;
+extern int TtPvLmrIirRefine;       // 0 = off, 1 = tt_pv LMR refinement + deeper non-TT-move IIR
 extern int ProbcutDepth;
 extern int ProbcutMargin;
 extern int QsFutilityMargin;
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -121,6 +121,7 @@ int SeeNoisyMultiplier = 150;
 int SingularDepth = 7;
 int SingularMargin = 2;
 int IirDepth = 4;
+int TtPvLmrIirRefine = 1;
 int ProbcutDepth = 5;
 int ProbcutMargin = 180;
 int QsFutilityMargin = 160;
@@ -202,6 +203,7 @@ const std::vector<Parameter>& parameters() {
         {"SeeNoisyMultiplier", &SeeNoisyMultiplier, 0, 1000},
         {"SingularDepth", &SingularDepth, 2, 20},        {"SingularMargin", &SingularMargin, 0, 10},
         {"IirDepth", &IirDepth, 1, 20},                  {"ProbcutDepth", &ProbcutDepth, 1, 20},
+        {"TtPvLmrIirRefine", &TtPvLmrIirRefine, 0, 1},
         {"ProbcutMargin", &ProbcutMargin, 0, 1000},      {"QsFutilityMargin", &QsFutilityMargin, 0, 1000},
         {"QsSeeMargin", &QsSeeMargin, 0, 500},           {"AspirationDelta", &AspirationDelta, 4, 200},
         {"HistoryBonusQuadratic", &HistoryBonusQuadratic, 0, 100},
@@ -2181,11 +2183,18 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
     }
 
     // Internal iterative reduction: no hash move suggests a less important node.
-    if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;
-    // B4 TtPruneV2: a cut node whose TT move failed low before (upper bound) is unlikely to cut: reduce it too.
-    // (Exclusive with the IIR above: that one needs no TT move, this one a TT move; mate search left alone as above.)
-    else if (tt_prune_v2_ && mate_moves_ == 0 && !in_check && depth >= tune::IirDepth + 2 && cut_node &&
-             !tt_move.is_none() && tt_bound == BoundUpper && !ss->tt_pv) --depth;
+    if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none()) {
+        if (pv_node || cut_node) --depth;
+        // Clean-room Stockfish: deeper IIR on non-tt_pv nodes lacking a TT move.
+        if (tune::TtPvLmrIirRefine != 0 && !ss->tt_pv &&
+            ((!(pv_node || cut_node) && depth >= tune::IirDepth + 2) ||
+             (cut_node && depth >= tune::IirDepth + 3))) {
+            --depth;
+        }
+    } else if (tt_prune_v2_ && mate_moves_ == 0 && !in_check && depth >= tune::IirDepth + 2 && cut_node &&
+               !tt_move.is_none() && tt_bound == BoundUpper && !ss->tt_pv) {
+        --depth;
+    }
 
     // B4 HistRework: lesser-attacker maps of this node, read by the quiet scores and the history updates below.
     if (tune::HistRework != 0) threat_maps_[static_cast<std::size_t>(ply)] = b4::lesser_threats(board);
@@ -2406,7 +2415,17 @@ int Worker::search(Board& board, SearchStack* ss, int depth, int alpha, int beta
             move_count > 1 + (root_node ? 1 : 0) && !bare_king_mode &&
             (quiet || !ss->tt_pv || move_count > 4)) {
             int r = reduction(quiet, depth, move_count);
-            if (ss->tt_pv) r -= 1;
+            if (tune::TtPvLmrIirRefine != 0) {
+                // Clean-room Stockfish: gate tt_pv LMR relief by TT score/depth and tighten upper-bound cut nodes.
+                if (ss->tt_pv) {
+                    if (!(tt_hit && tt_score != ValueNone && tt_score <= alpha && tt_depth >= depth)) r -= 1;
+                    if (tt_hit && tt_score != ValueNone && tt_score > alpha && tt_depth >= depth) r -= 1;
+                } else if (cut_node && tt_hit && tt_bound == BoundUpper && tt_depth >= depth - 2) {
+                    r += 1;
+                }
+            } else if (ss->tt_pv) {
+                r -= 1;
+            }
             if (!improving) r += 1;
             if (cut_node) r += 2;
             if (tt_capture && quiet) r += 1;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`include/forge/search.hpp:274+`; `src/search.cpp:123+, 204+, 2184-2188, 2409`):**
  1. **Deeper non-TT-move IIR (`search.cpp:2184-2188`):** When `TtPvLmrIirRefine != 0 && !ss->tt_pv && tt_move.is_none()`, extends IIR by 1 ply onto ALL-nodes at `depth >= IirDepth + 2` and applies a second `-1` ply on deep non-`tt_pv` cut nodes (`cut_node && depth >= IirDepth + 3` after the first `--depth`). The `tt_prune_v2_` `else if` branch (`!tt_move.is_none()`) is preserved identically.
  2. **Refined `tt_pv` LMR (`search.cpp:2409`):** When `ss->tt_pv`: withholds the `-1` relief if a deep TT entry already failed low (`tt_hit && tt_score != ValueNone && tt_score <= alpha && tt_depth >= depth`), and grants an extra `-1` relief when a deep TT entry beat `alpha` (`tt_score > alpha && tt_depth >= depth`). When `!ss->tt_pv && cut_node && tt_hit && tt_bound == BoundUpper && tt_depth >= depth - 2`: adds `+1` reduction, keeping tree size tight (`-24.80%` B4 / `-23.84%` FULL) rather than inflating like `SF14`.
  3. **Bit-exactness (`TtPvLmrIirRefine=0`):** Falls back identically to `if (pv_node || cut_node) --depth;` and `if (ss->tt_pv) r -= 1;`.
- **Bounds & Interaction Checks:**
  1. **Extension safety:** `search.cpp:2426` (`std::clamp(new_depth - r, 1, new_depth)`) remains untouched, preventing unintended search extensions.
  2. **Stack separation (`V3P_pairwise_psqt_fused + SF8 + SF20 + proto_7 + proto_8`):** Verified both via `git apply --check` AND sequential `git apply` + `build_fast.py` smoke compile (`RC=0`, `6.1s`). `search.cpp:2410-2412` remain completely untouched, leaving `search.cpp:2412` as a clean buffer before `SF20`'s `2413-2419` hunk.
- **Caveat 1 (No Match Played Yet):** Only deterministic `--quick` Master Gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `proto_7_ttpv_lmr_and_iir.exe` is non-PGO. Rebuild with `PGO` if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish `tt_pv` LMR score/depth gating, upper-bound cut-node reduction, and deeper non-`tt_pv` non-TT-move IIR adapted to Forge's `tune::TtPvLmrIirRefine` spin parameter (`0/1`).
- **License Status:** 100% clean-room implementation (`23` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5e6f333b...`) | `proto_7_ttpv_lmr_and_iir.exe` (`a37bc49d...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `292,457 / 649,751` | `-6.52% / -24.65%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `260,150 / 651,160` | `+0.18% / -10.20%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `183,614 / 475,386` | `-2.30% / -24.80%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `210,039 / 438,736` | `-3.83% / -23.84%` |
| Ablation (`TtPvLmrIirRefine=0`) `B4` / `FULL` | `187,930 / 632,195` \| `218,410 / 576,076` | `187,930 / 632,195` \| `218,410 / 576,076` | Bit-exact `0` diff |
| `r0067` `startpos` `eval` | `87` | `87` | `0` |
| `v3_parity` (`r0067`, 200 balanced FENs, `8/8` KB, `8/8` OB) | `0/200 differ` | `0/200 differ` (planted fault caught) | PASS |

---

## 5. Reproducible Fail-Before / Pass-After Test Outputs

### 5.1 Pass on `proto_7_ttpv_lmr_and_iir.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE=""
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_proto_7_ttpv_lmr_and_iir.py
```

Observed output (`RC=0`):
- `test_1_uci_gate_patch_and_bit_exact_ablation`: **PASSED** (`git apply --check RC=0`; `TtPvLmrIirRefine` advertised `default 1 min 0 max 1`; `=0` bit-exact `187,930 / 632,195` (`B4`) and `218,410 / 576,076` (`FULL`))
- `test_2_behavioral_divergence_and_bench_bounds`: **PASSED** (`5/5` B4 positions diverge: `startpos d9` `4022 -> 4342`, `kiwipete d8` `8370 -> 9060`, `bench3 d9` `12494 -> 10447`, `bench5 d9` `10472 -> 10285`, `bench8 d9` `6302 -> 6721`; `B4` `-24.80%`, `FULL` `-23.84%`, both in `[-25%, +10%]`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, `v3_parity 0/200`, planted bug caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\tests\test_proto_7_ttpv_lmr_and_iir.py
```

Observed output (`RC=1`):
- `test_1_uci_gate_patch_and_bit_exact_ablation`: **FAILED** (`AssertionError: 'option name TtPvLmrIirRefine type spin default 1 min 0 max 1' not found`)
- `test_2_behavioral_divergence_and_bench_bounds`: **FAILED** (`AssertionError: 0 != 5 : Expected all 5 positions to diverge from base, got 0`)
- `test_3_gates_perft5_eval_and_v3_parity`: **PASSED** (shared baseline invariants)

---

## 6. Opus Placement Checklist

- [ ] Review `include/forge/search.hpp:274+`, `src/search.cpp:2184-2188, 2409`, and `proto_7_ttpv_lmr_and_iir.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`proto_7_ttpv_lmr_and_iir.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_proto_7_ttpv_lmr_and_iir.py --exe <placed_exe>` and `run_master_gates.py --quick`.
