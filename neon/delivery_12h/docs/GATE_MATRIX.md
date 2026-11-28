# Forge Master Gate Matrix (`M1_master_gates`)

All checks executed single-threaded (`Threads=1`, `HIP_VISIBLE_DEVICES="" CUDA_VISIBLE_DEVICES="" ROCR_VISIBLE_DEVICES=""`) via `C:\nnue-lab\venv\Scripts\python.exe` after `mem_room.py 2` GO.

---

## 1. Summary & Wall-Clock Timing Breakdown (`<15s` Budget Verification)

| Run / Pair | Mode | Overall Status | Hard Pass | Total (s) | Perft (s) | Bench (s) | `v3_parity` (s) | `net_sanity` v2 (s) | `eval_net_full` (s) | `loader_safety` (s) | JSON Artifact |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| **Pair 1:** `base_r15dsg.exe` + `r0067` | `--quick` | `PASS_WITH_ADVISORY_FLAGS` | **PASS** | **4.419** | 0.085 | 0.737 | 1.534 | 0.153 | 1.643 | 0.265 | `gate_pair1_base_r0067.json` |
| **Pair 2:** `base_r15dsg.exe` + `G1` *(vs `base_r15dsg`)* | `--quick` | `PASS_WITH_ADVISORY_FLAGS` | **PASS** | **5.250** | 0.082 | 1.458 | 1.591 | 0.208 | 1.649 | 0.261 | `gate_pair2_base_G1.json` |
| **Pair 3:** `V3P_SF_COMBO_v1.exe` + `r0067` *(vs `base_r15dsg`)* | `--quick` | `PASS_WITH_ADVISORY_FLAGS` | **PASS** | **5.797** | 0.093 | 1.807 | 1.651 | 0.194 | 1.750 | 0.300 | `gate_pair3_combo_r0067.json` |
| **Pair 4:** `V3P_SF4b1_SF8.exe` + `r0067` *(vs `base_r15dsg`)* | `--quick` | `PASS_WITH_ADVISORY_FLAGS` | **PASS** | **5.510** | 0.086 | 1.539 | 1.618 | 0.238 | 1.661 | 0.367 | `gate_pair4_sf4b1_sf8_r0067.json` |
| **Full Audit:** `V3P_SF4b1_SF8.exe` + `r0067` *(vs `base_r15dsg`)* | `--full` | `PASS_WITH_ADVISORY_FLAGS` | **PASS** | **13.957** | 2.744 | 1.528 | 6.772 | 0.165 | 1.737 | 1.008 | `gate_full_sf4b1_sf8_r0067.json` |
| **V3P Synthetic Check:** `V3P_SF4b1_SF8.exe` + `v3p_valid_64.fnn3` | `--quick` | `PASS_WITH_ADVISORY_FLAGS` | **PASS** | **8.414** | 0.085 | 6.185 | 0.097 | 0.132 | 1.659 | 0.254 | `gate_v3p_sf4b1_sf8_v3p64.json` |

- **Budget check:** All 4 required `--quick` pairs run in **4.42s – 5.80s** (including `--baseline-exe` bench comparison in Pairs 2–4), well under the `<15.0s` target. Even `--full` (`12/12` perft, `1,120` FEN parity, `37/37` loader + multi-net switching) completes in **13.96s**, and the untrained random-weight `FORGENN3-P` check (`8.66M`-node bench 13) completes in **8.41s**.

---

## 2. Gate-by-Gate Pass/Fail Matrix

| Gate | Pair 1 (`base + r0067`) | Pair 2 (`base + G1`) | Pair 3 (`COMBO_v1 + r0067`) | Pair 4 (`SF4b1_SF8 + r0067`) | Full (`SF4b1_SF8 + r0067`) | V3P Synthetic (`SF4b1_SF8 + v3p64`) |
|---|---|---|---|---|---|---|
| **a. Perft** | PASS (`4865609`, `6/6`) | PASS (`4865609`, `6/6`) | PASS (`4865609`, `6/6`) | PASS (`4865609`, `6/6`) | PASS (`4865609`, `12/12`) | PASS (`4865609`, `6/6`) |
| **b. Bench 11/13** | PASS | PASS (`+0.0%` vs self) | PASS | PASS | PASS | PASS |
| **c. `v3_parity`** | PASS (`0 cp`, `8/8` OB, `120` FENs) | PASS (`0 cp`, `8/8` OB, `120` FENs) | PASS (`0 cp`, `8/8` OB, `120` FENs) | PASS (`0 cp`, `8/8` OB, `120` FENs) | PASS (`0 cp`, `8/8` OB, `1,120` FENs) | PASS (`0 cp`, `2/2` OB, `120` FENs) |
| **d. `net_sanity` v2** | `ADVISORY_FLAGS` (`rc=1`, 3 flags; Hard PASS) | `ADVISORY_FLAGS` (`rc=1`, 3 flags; Hard PASS) | `ADVISORY_FLAGS` (`rc=1`, 3 flags; Hard PASS) | `ADVISORY_FLAGS` (`rc=1`, 3 flags; Hard PASS) | `ADVISORY_FLAGS` (`rc=1`, 3 flags; Hard PASS) | `ADVISORY_FLAGS` (`rc=1`, 6 flags; Hard PASS; random weights) |
| **e. `eval_net_full`** | PASS (all finite) | PASS (all finite) | PASS (all finite) | PASS (all finite) | PASS (all finite) | PASS (all finite) |
| **f. `loader_safety`** | PASS (`13/13`, `v3p=False`) | PASS (`13/13`, `v3p=False`) | PASS (`15/15`, `v3p=True`) | PASS (`15/15`, `v3p=True`) | PASS (`37/37` + multi-net switch) | PASS (`15/15`, `v3p=True`) |

*(Note: `base_r15dsg.exe` + `v3p_valid_64.fnn3` was additionally verified in `test_master_gates.py` to fail loudly with `rc=2` / `ERROR NNUE v3: ... unknown flag bits` and hard-fail `v3_parity`, `bench`, and `net_sanity` without falling back to HCE.)*

---

## 3. Raw Metrics

### 3.1 Perft & Bench 11 / 13 (Default & B4) with Deltas vs `base_r15dsg.exe`

B4 UCI options: `CuckooRep=true HistRework=2 TtPruneV2=true CorrHistV2=true` (`Threads=1, Hash=16, OwnBook=false`).

| Pair | `perft 5` | Default `bench 11` (delta vs base) | Default `bench 13` (delta vs base) | B4 `bench 11` (delta vs base) | B4 `bench 13` (delta vs base) |
|---|---:|---:|---:|---:|---:|
| **Pair 1:** `base_r15dsg + r0067` | `4,865,609` | `259,695` (ref) | `725,158` (ref) | `187,930` (ref) | `632,195` (ref) |
| **Pair 2:** `base_r15dsg + G1` | `4,865,609` | `224,682` (`+0`, `+0.000%`) | `719,700` (`+0`, `+0.000%`) | `235,075` (`+0`, `+0.000%`) | `790,118` (`+0`, `+0.000%`) |
| **Pair 3:** `V3P_SF_COMBO_v1 + r0067` | `4,865,609` | `265,821` (`+6,126`, `+2.359%`) | `711,363` (`-13,795`, `-1.902%`) | `252,988` (`+65,058`, `+34.618%`) | `773,964` (`+141,769`, `+22.425%`) |
| **Pair 4:** `V3P_SF4b1_SF8 + r0067` | `4,865,609` | `254,160` (`-5,535`, `-2.131%`) | `784,059` (`+58,901`, `+8.123%`) | `233,585` (`+45,655`, `+24.294%`) | `565,442` (`-66,753`, `-10.559%`) |
| **Full:** `V3P_SF4b1_SF8 + r0067` | `4,865,609` | `254,160` (`-5,535`, `-2.131%`) | `784,059` (`+58,901`, `+8.123%`) | `233,585` (`+45,655`, `+24.294%`) | `565,442` (`-66,753`, `-10.559%`) |
| **V3P Check:** `V3P_SF4b1_SF8 + v3p64` | `4,865,609` | `1,322,975` (N/A) | `8,662,760` (N/A) | `1,373,400` (N/A) | `5,938,549` (N/A) |

### 3.2 `v3_parity` (C++ `uci eval` vs `forge_v3p.reference_eval`)

- **Quick Fixture (`parity_fens_8ob.json`):** `120` FENs (`15` per bucket `OB0..OB7`), all `17` edge piece counts (`2,3,5,6,9,10,13,14,17,18,21,22,25,26,29,30,32`), `w:64 / b:56`, `quiet:91 / capture:24 / promotion:5`, `ep:7`, `castling:27`, STM king buckets `0..7` = `{0:6, 1:24, 2:11, 3:22, 4:16, 5:14, 6:10, 7:17}`.
- **Full Parity (`V3P_SF4b1_SF8 + r0067`):** `1,120` FENs (`120` fixture + `1,000` `val.plain`), `OB0..OB7` counts = `{0:109, 1:188, 2:183, 3:145, 4:121, 5:110, 6:132, 7:132}` (`min=109`).
- **Results across all 6 runs:** `max_diff_cp = 0`, `hce_nonzero = 0`, `nnue_ne_total = 0`, `mismatch_count = 0`.
  - `r0067` (`FORGENN3`, `768w`, `kb=8, ob=8`): `8/8` OB covered (`15/bucket` quick, `>=109/bucket` full), `0 cp` diff on `base_r15dsg`, `V3P_SF_COMBO_v1`, and `V3P_SF4b1_SF8`.
  - `G1` (`FORGENN3`, `768w`, `kb=8, ob=8`): `8/8` OB covered (`15/bucket`), `0 cp` diff on `base_r15dsg`.
  - `v3p_valid_64.fnn3` (`FORGENN3-P`, `64w`, `kb=4, ob=2`, `pairwise+psqt`): `2/2` OB covered (`60/bucket`), `0 cp` diff on `V3P_SF4b1_SF8`.

### 3.3 `net_sanity.py` v2 & `eval_net_full.py` Metrics

| Net | `net_sanity` v2 Unit | `net_sanity` v2 Flags (`rc=1`) | `m4_wdl_mse` | `m4_corr` | `m4_opp_wing_wdl_mse` | `ob0_ob1_cliff_median_jump_cp` | `m4_mid20_26_ols_piece_cp` |
|---|---|---|---:|---:|---:|---:|---|
| **`r0067`** (`cand.fnn3`) | `189.6 raw (1.90 raw/cp)` | `S2 start vs 1.e4, side-to-move part` (`M +29.8 cp`), `S5 dead draws` (`KNN-K +53 cp`), `S7 won endings` (`KR-K +233 cp`) | `0.01302` | `0.7754` | `0.01724` | `143.5 cp` | `P:51.5, N:135.7, B:167.0, R:202.1, Q:307.3, tempo:18.8` |
| **`G1`** (`cand.fnn3`) | `199.2 raw (1.99 raw/cp)` | `S2 start vs 1.e4, side-to-move part` (`M +21.6 cp`), `S5 dead draws` (`KNN-K +85 cp`), `S7 won endings` (`KR-K +301 cp`) | `0.01267` | `0.7629` | `0.01648` | `129.0 cp` | `P:48.8, N:133.0, B:163.1, R:194.5, Q:285.4, tempo:17.1` |
| **`v3p_valid_64`** *(synthetic random)* | `2.1 raw (0.02 raw/cp)` | `S1`, `S2`, `S2w`, `S5`, `S6`, `S8` (6 flags — untrained random weights) | `0.07357` | `-0.0322` | `0.08774` | `55.5 cp` | `P:-19.6, N:5.0, B:-13.9, R:4.5, Q:-67.8, tempo:-131.3` |

*(Engine invariance confirmed: `r0067` yields bit-identical `net_sanity` v2 and `eval_net_full` numbers across `base_r15dsg`, `V3P_SF_COMBO_v1`, and `V3P_SF4b1_SF8` because `uci eval` invokes `v3::evaluate_reference` without search scaling.)*

### 3.4 `loader_safety` Coverage

- **`base_r15dsg.exe` (`v3p_supported=False`, `--quick`):** `13/13` PASS (`missing_file`, `empty_0B`, `trunc_7B`, `trunc_192B`, `trunc_minus1B`, `trailing_plus4B`, `bad_magic`, `bad_version`, `unknown_flag`, `bad_checksum`, `residual_refused`, `oob_w2_128`, `oob_acc_32768`).
- **`V3P_SF_COMBO_v1.exe` & `V3P_SF4b1_SF8.exe` (`v3p_supported=True`, `--quick`):** `15/15` PASS (all 13 universal probes + `pairwise_h32` + `oob_psqt_261121`).
- **`V3P_SF4b1_SF8.exe` (`--full`):** `37/37` PASS + `uci_multi_net_switching` PASS (`r0067` -> `valid_legacy_32` -> `<empty>/NNUEArch false` -> `r0067`, exact `eval` and `bestmove` parity against fresh processes).

---

## 4. CLI Usage Examples

```powershell
# 1. Default --quick gate (<15s) on an engine + net pair
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamC_gates\run_master_gates.py `
  --exe C:\nnue-lab\neon\forge_fixes\builds\V3P_SF4b1_SF8.exe `
  --net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3

# 2. --quick gate with baseline node delta comparison & JSON report
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamC_gates\run_master_gates.py `
  --exe C:\nnue-lab\neon\forge_fixes\builds\V3P_SF4b1_SF8.exe `
  --net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 `
  --baseline-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe `
  --quick `
  --json-out C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamC_gates\gate_report.json

# 3. --full deep audit (12/12 perft, 1120-FEN parity, 37 loader cases + multi-net switching)
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamC_gates\run_master_gates.py `
  --exe C:\nnue-lab\neon\forge_fixes\builds\V3P_SF4b1_SF8.exe `
  --net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 `
  --baseline-exe C:\nnue-lab\neon\forge_fixes\builds\base_r15dsg.exe `
  --full `
  --json-out C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamC_gates\gate_full_report.json

# 4. Strict net sanity mode (treats net_sanity.py v2 rc=1 advisory flags as HARD FAIL)
C:\nnue-lab\venv\Scripts\python.exe C:\nnue-lab\neon\forge_fixes\teamwork_wave2\streamC_gates\run_master_gates.py `
  --exe C:\nnue-lab\neon\forge_fixes\builds\V3P_SF4b1_SF8.exe `
  --net C:\nnue-lab\runs\forge\r0067\train\cand.fnn3 `
  --strict-net-sanity
```
