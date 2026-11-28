# Opus Placement Review Packet: `proto_10_cutnode_history_and_cap_lmr`

**Recommendation:** **STAGE FOR `50k` SCREEN & CONFIRMATION MATCH (DO NOT PLACE BEFORE MATCH PROOF)** — Clean-room Stockfish/Stormphrax LMR refinement (`CutNodeHistRefine`, `default 1 min 0 max 1`) adding `+1` reduction ply on cut nodes lacking a TT move (`cut_node && tt_move.is_none()`) and `-std::clamp(history / 6000, -1, 1)` capture-history LMR adjustment on non-losing captures (`picker.last_move_see_nonnegative() || board.see_ge(move, 0)`). Verified 100% bit-exact with `base_r15dsg.exe` when `CutNodeHistRefine=0` (`B4`: `187,930 / 632,195`; `FULL`: `218,410 / 576,076`), passes all `--quick` Master Gates (`hard_pass: true`, `perft 5 = 4,865,609`, `v3_parity 0 cp` max diff across `8/8` OB), diverges on `5/8` `B4` and `8/8` `FULL` benchmark FENs, and reduces `FULL+r0067 bench 13` by **`-11.43%`** (`510,233` vs `576,076`) while shifting `B4+r0067` by `+0.36%` (`634,480`) and `r0067 Default` by `+4.41%` (`757,153`). A pre-declared `1,000g @ 50k` match is owed before placement.

- **Patch File:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\patches\proto_10_cutnode_history_and_cap_lmr.patch` (`1,973` B, `41` lines, `SHA-256: 528028EB7566422D677004CFDF7D049326122CCACAD74F39E675911FFD31BC46`)
- **Build Tested:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\proto_10_cutnode_history_and_cap_lmr.exe` (`2,383,360` B, `SHA-256: F102FC6BF3485EC4735D9C9DB9AD767E3CE11D9569693BEA9CBA05FE15CFE7FB`)
- **Gate JSON:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\proto_10_cutnode_history_and_cap_lmr_gate.json` (`8,920` B, `275` lines, `SHA-256: 2E33A0B015C62B11E3085B7147D03C6827FB98EC1B905DB6EA27C73D887CAC82`, `overall_status: "PASS_WITH_ADVISORY_FLAGS"`, `hard_pass: true`)
- **Fail-Before / Pass-After Test:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py` (`test_08_proto_10_uci_ablation_and_behavioral`, full suite `9/9`)

---

## 1. Verbatim Patch Diff

```diff
--- a/include/forge/search.hpp
+++ b/include/forge/search.hpp
@@ -251,6 +251,7 @@
 extern int LmrQuietDivisor;   // x0.01
 extern int LmrNoisyBase;      // x0.01
 extern int LmrNoisyDivisor;   // x0.01
+extern int CutNodeHistRefine; // 0 = off, 1 = cut-node missing-TT LMR + non-losing capture-history LMR
 extern int NullMoveMinDepth;
 extern int NullMoveBase;
 extern int NullMoveDepthDivisor;
--- a/src/search.cpp
+++ b/src/search.cpp
@@ -100,6 +100,7 @@
 int LmrQuietDivisor = 220;
 int LmrNoisyBase = 10;
 int LmrNoisyDivisor = 340;
+int CutNodeHistRefine = 1;
 int NullMoveMinDepth = 3;
 int NullMoveBase = 3;
 int NullMoveDepthDivisor = 3;
@@ -188,6 +189,7 @@
     static const std::vector<Parameter> table{
         {"LmrQuietBase", &LmrQuietBase, 0, 300},         {"LmrQuietDivisor", &LmrQuietDivisor, 100, 500},
         {"LmrNoisyBase", &LmrNoisyBase, 0, 300},         {"LmrNoisyDivisor", &LmrNoisyDivisor, 100, 800},
+        {"CutNodeHistRefine", &CutNodeHistRefine, 0, 1},
         {"NullMoveMinDepth", &NullMoveMinDepth, 1, 10},  {"NullMoveBase", &NullMoveBase, 1, 6},
         {"NullMoveDepthDivisor", &NullMoveDepthDivisor, 1, 10},
         {"NullMoveEvalDivisor", &NullMoveEvalDivisor, 50, 1000},
@@ -2414,6 +2416,12 @@
             if (in_check) r -= 1;
             if (tune::LmrCutoffThreshold > 0 && (ss + 1)->cutoff_count > tune::LmrCutoffThreshold) r += 1;
             if (quiet) r -= std::clamp(history / tune::LmrHistoryDivisor, -2, 2);
+            if (tune::CutNodeHistRefine != 0) {
+                if (cut_node && tt_move.is_none()) r += 1;
+                if (capture && (picker.last_move_see_nonnegative() || board.see_ge(move, 0))) {
+                    r -= std::clamp(history / 6000, -1, 1);
+                }
+            }
             if (tune::LmrSignedCorrection && quiet && ss->static_eval != ValueNone &&
                 ss->raw_eval != ValueNone) {
                 const int correction_cp = ss->static_eval - ss->raw_eval;
```

---

## 2. Technical Note & Caveats

- **Mechanism (`include/forge/search.hpp:253+`; `src/search.cpp:102+, 190+, 2416+`):**
  1. **UCI Parameter (`CutNodeHistRefine`, `default 1 min 0 max 1`):** Registered cleanly after `LmrNoisyDivisor`, leaving `>= 7` lines of separation from `proto_1`, `proto_7`, `proto_8`, and `proto_9`.
  2. **Cut-Node Missing-TT Extra LMR (`search.cpp:2416+`):** When `tune::CutNodeHistRefine != 0 && cut_node && tt_move.is_none()`, adds `+1` ply reduction on top of `if (cut_node) r += 2;` (`2411`).
  3. **Non-Losing Capture-History LMR (`search.cpp:2416+`):** When `capture && (picker.last_move_see_nonnegative() || board.see_ge(move, 0))`, adjusts `r -= std::clamp(history / 6000, -1, 1)`. At `search.cpp:2235`, `history` is already `capture_history_value(board, move)` for `!quiet` moves (`[-16384, +16384]`), and `picker.last_move_see_nonnegative()` short-circuits `GoodCaptures` at zero extra SEE cost while `MainTT`/`BadCaptures`/`Evasions` fall back to exact `board.see_ge(move, 0)`.
  4. **Bit-exactness (`CutNodeHistRefine=0`):** The `if (tune::CutNodeHistRefine != 0)` guard short-circuits before modifying `r` or invoking `picker.last_move_see_nonnegative()` / `board.see_ge(...)`, producing bit-identical node counts to `base_r15dsg.exe`.
- **Bounds & Interaction Checks:**
  1. **Overflow & Extension Safety:** `CaptureHistory` stores `std::int16_t` clamped to `[-16384, +16384]` (`HistoryMax`), so `history / 6000` is bounded in `[-2, +2]` and clamped to `[-1, +1]`; downstream `std::clamp(new_depth - r, 1, new_depth)` (`2426`) prevents accidental extensions.
  2. **Stack Separation:** Orthogonal to all 6 Super-Stack patches (`V3P_v3`, `SF33`, `SF8`, `proto_1`, `SF15`, `SF27`), `proto_9` (`2421+`), `SF30`, and `SF31`. Note: `2414-2416` is leading context (near `SF20`/`SF23` at `2416` and `SF29` after `2414`); none of `SF20`/`SF23`/`SF29` are in the 6-patch Super-Stack.
- **Caveat 1 (No Match Played Yet):** Only deterministic `--quick` Master Gates and fail-before/pass-after tests have run. A pre-declared `1,000g @ 50k` match on `r0067` + `FULL` options is required before placement.
- **Caveat 2 (Non-PGO Binary):** `proto_10_cutnode_history_and_cap_lmr.exe` is non-PGO. Rebuild with PGO if promoted.

---

## 3. Provenance & License Status

- **Source Inspiration:** Clean-room Stockfish / Stormphrax cut-node missing-TT-move extra LMR reduction paired with non-losing capture-history LMR adjustment (`capture_history_value / 6000`), gated by `tune::CutNodeHistRefine`.
- **License Status:** 100% clean-room implementation (`9` net C++ lines), zero GPL code copied.

---

## 4. Deterministic Gate & `bench 11/13` Table

All checks single-threaded (`Threads=1, Hash=16, OwnBook=false`), `r0067 = C:/nnue-lab/runs/forge/r0067/train/cand.fnn3`.

| Metric | `base_r15dsg.exe` (`5E6F333B...`) | `proto_10_cutnode_history_and_cap_lmr.exe` (`F102FC6B...`) | Delta |
|---|---:|---:|---:|
| `go perft 5` (`Default`, `B4`, `FULL`) | `4,865,609` | `4,865,609` | `0` (PASS) |
| `run_master_gates --quick` (`perft 6/6`, `eval_net_full`, `loader 13/13`) | — | `PASS_WITH_ADVISORY_FLAGS` (`hard_pass: true`) | PASS |
| `HCE Default` (`NNUEArch=false`) `b11 / b13` | `312,866 / 862,329` | `344,506 / 844,733` | `+10.11% / -2.04%` |
| `r0067 Default` (`NNUEArch=true`) `b11 / b13` | `259,695 / 725,158` | `258,182 / 757,153` | `-0.58% / +4.41%` |
| `B4+r0067` `bench 11 / 13` | `187,930 / 632,195` | `192,156 / 634,480` | `+2.25% / +0.36%` |
| `FULL+r0067` `bench 11 / 13` | `218,410 / 576,076` | `225,032 / 510,233` | `+3.03% / -11.43%` |
| Ablation (`CutNodeHistRefine=0`) `B4` / `FULL` | `187,930 / 632,195` \| `218,410 / 576,076` | `187,930 / 632,195` \| `218,410 / 576,076` | Bit-exact `0` diff |
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
- `test_08_proto_10_uci_ablation_and_behavioral`: **PASSED** (`option name CutNodeHistRefine type spin default 1 min 0 max 1` advertised; `=0` bit-exact `187,930 / 632,195` (`B4`) and `218,410 / 576,076` (`FULL`); `=1` diverges on `5/8` `B4` FENs — `kiwipete_d8` `8370->8383`, `kiwipete_d10` `20623->20775` / `-134->-92`, `bench3_d9` `12494->11358`, `bench5_d9` `10472->10448`, `tactical_d9` `17044->17036` — and `8/8` `FULL` FENs)
- `test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity`: **PASSED** (`perft 5 = 4,865,609`, `eval = 87`, Mate-in-1 `d1d8`, `go mate 2`, `Qh4+` `g2g3`, `v3_parity 0/200` with planted fault caught)

### 5.2 Expected Fail on `base_r15dsg.exe`

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""; $env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"; $env:PYTHONDONTWRITEBYTECODE="1"
$env:FORGE_TEST_EXE="C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe"
C:\nnue-lab\venv101\Scripts\python.exe -B -m pytest -p no:cacheprovider -v C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\tests\test_round9_11_and_wave5_search.py
```

Observed output (`RC=1`, `7 failed, 2 passed in 5.98s`):
- `test_01_all_patches_apply_cleanly`: **PASSED**
- `test_02`..`test_06`: **FAILED**
- `test_07_proto_9_uci_ablation_and_behavioral`: **FAILED** (`AssertionError: 'option name CorrComplexityRefine type spin default 1 min 0 max 1' not found`)
- `test_08_proto_10_uci_ablation_and_behavioral`: **FAILED** (`AssertionError: 'option name CutNodeHistRefine type spin default 1 min 0 max 1' not found`)
- `test_09_shared_invariants_perft5_eval_mate_safety_and_v3_parity`: **PASSED**

---

## 6. Opus Placement Checklist

- [ ] Review `include/forge/search.hpp:253+`, `src/search.cpp:2416+`, and `proto_10_cutnode_history_and_cap_lmr.patch` (`git -C C:\nnue-lab\forge\r15dsg apply --check` -> `RC=0`).
- [ ] Run pre-declared `1,000g @ 50k` match (`proto_10_cutnode_history_and_cap_lmr.exe` vs `base_r15dsg.exe` on `r0067` + `FULL` options) before deciding placement.
- [ ] If promoted, rebuild with PGO and re-run `test_round9_11_and_wave5_search.py` and `run_master_gates.py --quick`.
