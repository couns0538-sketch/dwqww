# Wave 6 Final `teamwork\` Delivery Manifest (Curated Text-Only Staging Bundle)

> **CRITICAL SAFETY RULE:** **DO NOT COPY ANYTHING INTO `C:\nnue-lab\teamwork\` DURING WAVE 6.**
> Staging into `C:\nnue-lab\teamwork\neon_12h_quest_delivery\` is permitted **ONLY AFTER FULL QUEST COMPLETION** (post-Stage-2 Filter Quest / `6+0.06` PGO freeze and clearing of all `[PENDING` / `[TRAINING` / `[TESTING` markers in `HANDOFF_12H_DATA_QUALITY.md`).

- **Staging Script:** `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\stage_teamwork_delivery_w6.py` (`89,441` B, `sha256=7bbb8de156499d40e4fe11fd7c3d16613588637d493ecb719ac9000849470827`)
- **Default Execution Mode:** `--dry-run` (mutually exclusive `--dry-run` / `--live` / `--verify-debate-index`, defaults to dry-run when omitted; read-only, `C:\nnue-lab\teamwork\` untouched). Optional `--strict-living` fails `RC=1` on any `(living)` file or scoreboard count drift during `--verify-debate-index`.
- **Dual-Gate Live Safety Contract (NO `--allow-unfrozen` escape hatch):** `--live` unconditionally refuses (`RC=2`) unless **BOTH**:
  1. `--confirm-quest-complete YES_COPY_TO_TEAMWORK` is passed verbatim, **AND**
  2. `C:\nnue-lab\neon\filter_quest\HANDOFF_12H_DATA_QUALITY.md` has **zero** `r"\[(?:PENDING|TRAINING|TESTING)[^\]]*(?:\]|$)"` markers (plus `missing=0`, `pending_sibling=0`, `immutable_mismatch=0`, `forbidden_ext=0`, `forbidden_path=0` on both `src` and `dest_rel`, and `total_staged = total_files_bytes + manifest_json_bytes <= 1,887,436`).
- **Bundle Discipline (`<= 1.8 MiB` / `1,887,436` B INCLUDING `MANIFEST_SHA256.json`, Text-Only):** **`217` staged files** (`1,807,973` B) + compact **`MANIFEST_SHA256.json`** (`40,903` B, `separators=(",", ":")`, concise schema `dest_rel`/`bytes`/`sha256`/`category`/`freeze_mutable`) = **`1,848,876` B** (`38,560` B headroom under `1.8 MiB`; exact `DELIVERY_MANIFEST_W6.md` self-size synced below): `22` docs, `31` packets, `49` recommended/active patches, `20` scripts, `6` pytests, `89` JSON/TXT audits. Zero `.exe`, `.pt`, `.fnn3`, `.fqs`, `.z`, `.plain`, `.pgn`, `.npz`, `.binpack`, `.dll`, `.lib`, `.o`, `.obj`, `.pyc`, `.part`, `__pycache__`, `.pytest_cache`, or `_work_*` paths.

---

## 1. Category Byte Budget Summary
| Category | Files | Total Bytes |
|---|---:|---:|
| `docs\` | 22 | 352,190 |
| `packets\` | 31 | 311,771 |
| `patches\` | 49 | 235,081 |
| `scripts\` | 20 | 348,540 |
| `tests\` | 6 | 133,411 |
| `audits\` | 89 | 426,980 |
| **Manifest Files Subtotal** | **217** | **1,807,973** |
| `MANIFEST_SHA256.json` *(compact, generated on `--live`)* | 1 | 40,903 |
| **Total Staged (`--live` Destination Cap)** | **218** | **1,848,876** / `1,887,436` |

---

## 2. Wave 6 New & Upgraded Deliverables Included in Bundle
| Staged Path (`neon_12h_quest_delivery\`) | Source Path | Bytes | Live SHA-256 | Stream |
|---|---|---:|---|---|
| `docs\PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md` | `C:\nnue-lab\neon\forge_fixes\PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md` | 8,373 | `7ae59122a5c0628b77eda9681668907011a3d2f0f18ae5bf531bb46a72bcde21` | Post-G3 / Phase B-C |
| `docs\STAGE2_FILTER_QUEST_SUMMARY.md` | `C:\nnue-lab\neon\filter_quest\STAGE2_FILTER_QUEST_SUMMARY.md` | 2,957 | `c17033d8b8a4102b0709fb5b6d62af7cf9a42ef7aa850ce91dffdf01f6eda56d` | Post-G3 / Phase B-C |
| `scripts\forge_train_v3p_loop_adapter.py` | `C:\nnue-lab\neon\forge_fixes\forge_train_v3p_loop_adapter.py` | 7,880 | `55bc6078392b19df16860d8a93420c9af3b52bfeefe0026ef04888da841b7631` | Post-G3 / Phase B-C |
| `tests\test_v3p_surface2_format.py` | `C:\nnue-lab\neon\forge_fixes\test_v3p_surface2_format.py` | 4,715 | `c3157540e4cf92804183607bbd338262afd3e271240e8c0dd5cd1a6b60031574` | Post-G3 / Phase B-C |
| `tests\test_v3p_surface4_parity_and_modelcheck.py` | `C:\nnue-lab\neon\forge_fixes\test_v3p_surface4_parity_and_modelcheck.py` | 5,398 | `18f7d8de513c3386c69682b13911bed385b5407645956eb6325db95dd9181528` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_post_g3_summary.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\post_g3_summary.json` | 7,218 | `c17ed87657eeee881e4839a4bd37e62590674a449d89544be5985a2cbabcfcc5` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_eval_full_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\eval_full_cand.json` | 1,021 | `b6d596b4b9acabddf5c018f8872c66a685a7a77786a7ff03c26ab347fdf5beeb` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_heldout_syzygy_4k_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\heldout_syzygy_4k_cand.json` | 1,177 | `adec936dd6ce3ccc5be75453be51eac77838824e965ef84607ad5e084c602233` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_sf19_slice_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\sf19_slice_cand.json` | 2,836 | `9c7745409c45fc145ab6d52239760c1cda5ccafbd59f3576b9ffe2f57cfc7881` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_master_gate_full_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\master_gate_full_cand.json` | 9,578 | `356f63d9c87c93a25427f5eab8d33b17f4592616089875da2a2b22c7c30f4442` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_net_sanity_v2_cand.txt` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\net_sanity_v2_cand.txt` | 1,191 | `eab287868ffd33c8b50e2d8b322964e8837cb73958ed586a03b99b980b4f09a6` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_metrics.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\metrics.json` | 3,819 | `5c227a17c17a0173ab7c51548b098f912600baef46b942e6b332e2593bbe37de` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0067_1000g_50k_summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_1000g_50k\summary.json` | 4,772 | `2acbaa65272ba182bf3d63759b053423654b5169d3ddf909ecd65d27fb5a01b5` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0067_1000g_50k_declaration_20261127_222833.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_1000g_50k\declaration_20261127_222833.json` | 3,708 | `f7371869469791a87916c1ce1e303776f3604c49d08418cc2a788672c987d474` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0202_1000g_50k_summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_1000g_50k\summary.json` | 4,842 | `bf0b092f06a89cffd444e4ce81ebadcb6f89fdb3b9eeac164213674bb58667e1` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0202_1000g_50k_declaration_20261127_223800.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_1000g_50k\declaration_20261127_223800.json` | 3,777 | `6166b0ced7d8dacde4ed7b36eef31a945817e503ac396a14a293acd2c4819436` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0067_600g_250k_summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_600g_250k\summary.json` | 4,816 | `7030b0793828ec0c9b4c33ff64f71c24187d4692828575f282a1c67515d1333c` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0067_600g_250k_declaration_20261127_224737.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_600g_250k\declaration_20261127_224737.json` | 3,751 | `63fa62ee1c5d20ec247fe9615d8fbbe2a9ed6d1cf3da9c608cb6001872fee57d` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0202_600g_250k_summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_600g_250k\summary.json` | 4,821 | `d4a82130a301daaee903b261232dc7c71f5b4e993d0de0d0b0ec58d3b48abfe0` | Post-G3 / Phase B-C |
| `audits\G3_FULL25_vs_r0202_600g_250k_declaration_20261127_230522.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_600g_250k\declaration_20261127_230522.json` | 3,756 | `936a86818d39ab2f62e43618c5a9bb267d2a684644ad22dcbb4bb0ecfd4a15a9` | Post-G3 / Phase B-C |
| `audits\G3_VS_R0067_PGN_DIAGNOSIS.json` | `C:\nnue-lab\neon\forge_fixes\G3_VS_R0067_PGN_DIAGNOSIS.json` | 1,276 | `6516eb180dd7a619ea8a0c065229dd66a52c241cfe01bcb5cd05a98caab805f8` | Post-G3 / Phase B-C |
| `audits\G3_STM_TEMPO_BY_SOURCE_AUDIT.json` | `C:\nnue-lab\neon\forge_fixes\G3_STM_TEMPO_BY_SOURCE_AUDIT.json` | 6,017 | `04eba7445196499a56cc64e88933dd430a640c35477ecd9912dac80ad97b6482` | Post-G3 / Phase B-C |
| `audits\G3_INDIST_TEMPO_AUDIT.json` | `C:\nnue-lab\neon\forge_fixes\G3_INDIST_TEMPO_AUDIT.json` | 933 | `98a3778aeb4183ef1d527e067c1f8da02e3fccdfad01ed58ccdd7370156491e4` | Post-G3 / Phase B-C |
| `audits\pilot_datagen_parity_7_8_G3_R4.json` | `C:\nnue-lab\neon\forge_fixes\pilot_datagen_parity_7_8_G3_R4.json` | 1,038 | `99a8c85ce551cb310d48a3f1ec36b739f0baa68fd6491e54a9ad76364274b46d` | Post-G3 / Phase B-C |
| `audits\V3P_PLACEMENT_PACKAGE_VERIFICATION.json` | `C:\nnue-lab\neon\forge_fixes\V3P_PLACEMENT_PACKAGE_VERIFICATION.json` | 2,346 | `bed11cb8c91772de96e3b3fb4833799bc370f69c379a79b68c6208870c2d72ae` | Post-G3 / Phase B-C |
| `audits\STAGE2_FILTER_QUEST_SUMMARY.json` | `C:\nnue-lab\neon\filter_quest\STAGE2_FILTER_QUEST_SUMMARY.json` | 6,194 | `5b3df20128271863c8404978243ea55701519a4979f61bea9a1fe39dec9c1d12` | Post-G3 / Phase B-C |
| `audits\SERVERDAY_ARCH_SUITE_SUMMARY.json` | `C:\nnue-lab\neon\forge_fixes\SERVERDAY_ARCH_SUITE_SUMMARY.json` | 1,052 | `6e31f3da625c36d1bc6899136b7ceef6073f9c49fb664005ecad50c10ed5efe4` | Post-G3 / Phase B-C |
| `packets\PACKET_SURFACE1_V3P_KERNEL_LINEBYLINE.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamA_v3p_placement_packets\PACKET_SURFACE1_V3P_KERNEL_LINEBYLINE.md` | 21,725 | `a01420de4e9288ad2f63617e997f85fb8cad5ec50a8a696b508b10f9d5ae397d` | W6 Stream A |
| `packets\PACKET_SURFACES2_5_LOOP_INTEGRATION.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamA_v3p_placement_packets\PACKET_SURFACES2_5_LOOP_INTEGRATION.md` | 16,543 | `521dc0043b58b6e52b5d5bcbf129b4857c76c22643847cfd1ff6b0e95b2f029c` | W6 Stream A |
| `tests\test_v3p_placement_and_parity_w6.py` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamA_v3p_placement_packets\tests\test_v3p_placement_and_parity_w6.py` | 29,325 | `ec41754ef74762a9f3413ee2497cc3cd5be5681584669d152907246ef0665a81` | W6 Stream A |
| `packets\PACKET_SF34.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF34.md` | 8,622 | `dd1d77a37e9e44d09850b944705556b05c3744e52a9697a0bd1d447ea08fb37a` | W6 Stream B |
| `packets\PACKET_SF35.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF35.md` | 9,981 | `6ecc49faba5c388b54f5830413b9917be45bc5572ffa4eef9b195e6d8b8d3768` | W6 Stream B |
| `packets\PACKET_SF36.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF36.md` | 6,245 | `8ff78fc6e87a137dda8dea2bf920d9307a39e2f1e93c7b179f69fd518af34d74` | W6 Stream B |
| `packets\PACKET_SF37.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF37.md` | 11,825 | `148c96699b40abd2af98975720a19dd8eae7907ee60e44c7380437f5526952ea` | W6 Stream B |
| `packets\PACKET_SF38.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF38.md` | 10,844 | `cc01dc97ad3ddc806653b158d8838419c2242683a5c3842a52f61e9a6ce246ce` | W6 Stream B |
| `packets\PACKET_SF39.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF39.md` | 12,103 | `5d72e0eef27fb1b195049bf30ade87175643160c1ff79c6a574e31508d1ec4fb` | W6 Stream B |
| `packets\PACKET_SF40.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_SF40.md` | 7,998 | `5ef1d11509289ffc7c0aca205530a6695b0c01581ae7197b42b9ca989d0009ee` | W6 Stream B |
| `packets\PACKET_LMR_DEEPER_UCI.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\PACKET_LMR_DEEPER_UCI.md` | 7,959 | `4384994283605df5fedf43344f06eeed5743865f69577a1bf8c74f2132c863ad` | W6 Stream B |
| `scripts\verify_round12_14_orthogonality.py` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\verify_round12_14_orthogonality.py` | 13,437 | `991b4317a55e3106342a14d18cc4fc723b4d41281278fe5dec5fce4f9242052f` | W6 Stream B |
| `audits\round12_14_orthogonality.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamB_round12_14_packets\round12_14_orthogonality.json` | 62,996 | `98a9d33191c95e67b1ab344340639891c83a8ed61e3cea7e5860d8b01a18656c` | W6 Stream B |
| `docs\DEBATE_EVIDENCE_INDEX_W6.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\DEBATE_EVIDENCE_INDEX_W6.md` | 59,166 | `f89388f25bf4472014e04b9c69ba6572644d2847e7932785f49fb1514f4c7062` | W6 Stream C |
| `docs\DELIVERY_MANIFEST_W6.md` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\DELIVERY_MANIFEST_W6.md` | 16,844 | `self` | W6 Stream C |
| `scripts\verify_all_patches_w6.py` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\verify_all_patches_w6.py` | 28,611 | `f3794ff2e5f6045bdc273850ad7baad8c9889bb4ab80e2daf556d9ac4cab4318` | W6 Stream C |
| `scripts\stage_teamwork_delivery_w6.py` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\stage_teamwork_delivery_w6.py` | 89,441 | `7bbb8de156499d40e4fe11fd7c3d16613588637d493ecb719ac9000849470827` | W6 Stream C |
| `audits\verify_all_patches_w6_report.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\verify_all_patches_w6_report.json` | 52,731 | `1d430f287625ee784acccaefd19051537cb7795206de5d024b5bf9643bd07fee` | W6 Stream C |

> Full SHA-256 inventory of all `172` preserved Wave 1–5 files (`docs\`, `packets\`, `patches\`, `scripts\`, `tests\`, `audits\`) is embedded in `stage_teamwork_delivery_w6.py` `MANIFEST` and verified on every `--dry-run` / `--live`.

---

## 3. Excluded, Superseded & Referenced Large Files (Not Copied into `1.8 MiB` Bundle)

1. **Opus Per-Position TSV (Referenced by Exact Path & SHA-256, NOT Copied — `196,559` B):**
   - `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\heldout_perpos_cand.tsv` (`196,559` B, `4,002` lines / `4,000` data rows, `sha256=914f344aef8fe8a7dba57c7e7de3a54aa3a8d4e21f730de6d795e3aef792e14c`).
2. **Superseded Wave 2–5 Interim Docs & Packets (`12` Files, Replaced by Wave 5/6 Equivalents):**
   - `DEBATE_EVIDENCE_INDEX_W5.md`: Superseded by `DEBATE_EVIDENCE_INDEX_W6.md`
   - `DELIVERY_MANIFEST_W5.md`: Superseded by `DELIVERY_MANIFEST_W6.md`
   - `verify_all_patches_w5_report.json`: Superseded by `verify_all_patches_w6_report.json`
   - `FILTER_QUEST_RESUME_BLUEPRINT.md`: Superseded by `HANDOFF_12H_DATA_QUALITY.md` + `STAGE2_FILTER_QUEST_SUMMARY.md`
   - `SERVER_DAY_2B_RUNBOOK.md`: Superseded by `SERVER_DAY_V2_RUNBOOK.md`
   - `SERVER_DAY_QUICKSTART.md`: Superseded by `SERVER_DAY_V2_RUNBOOK.md`
   - `PATCH_AUDIT_MATRIX.md`: Superseded by `PATCH_AUDIT_MATRIX_W4.md` + `verify_all_patches_w6_report.json`
   - `HANDOFF_AUDIT_REPORT.md`: Superseded by `HANDOFF_REAUDIT_W4.md` + `DEBATE_EVIDENCE_INDEX_W6.md`
   - `PACKET_V3P_FUSED_V3.md`: Superseded by Stream A `PACKET_SURFACE1_V3P_KERNEL_LINEBYLINE.md`
   - `PACKET_ROUND12_SF34_SF36.md`: Superseded by Stream B `PACKET_SF34.md`..`PACKET_SF36.md`
   - `PACKET_ROUND13_SF38_SF39.md`: Superseded by Stream B `PACKET_SF38.md`..`PACKET_SF39.md`
   - `packet_LmrDeeperShallower_uci.md`: Superseded by Stream B `PACKET_LMR_DEEPER_UCI.md`
3. **Rejected / Negative-Control / Superseded Patches (`26` Files, `362,040` B):**
   - Preserved in `neon\forge_fixes\patches\` & `teamwork_wave2\` (all `75/75` pass `verify_all_patches_w6.py` `RC=0`), intentionally excluded from `neon_12h_quest_delivery\patches\` (`SF5a`, `SF4b2`, `SF7`, `proto_4`, `proto_3`, `SF3`, `SF4b1`, `SF2`, `SF12`, `SF4a`, `SF16`, `proto_2`, `SF1`, `SF11`, `SF5b`, `7` `SF4b1`-tainted combos, `4` pre-v3 `V3P` patches).
4. **Binary / Large Data Exclusion:** Zero `.exe`, `.pt`, `.fnn3`, `.fqs`, `.z`, `.plain`, `.pgn`, `.npz`, `.binpack`, `.dll`, `.lib`, `.o`, `.obj`, `.pyc`, `.part` files staged.

---

## 4. Verified Dry-Run, Dual-Gate Refusal & Debate-Index Verification Commands

```powershell
$env:HIP_VISIBLE_DEVICES=""; $env:CUDA_VISIBLE_DEVICES=""; $env:ROCR_VISIBLE_DEVICES=""
$py = "C:\nnue-lab\venv101\Scripts\python.exe"
$sc = "C:\nnue-lab\neon\forge_fixes\teamwork_wave6\streamC_final_delivery_w6\stage_teamwork_delivery_w6.py"

& $py -B $sc --dry-run                             # Expected: RC=0, total_staged <= 1887436, missing=0
& $py -B $sc --dry-run --require-siblings          # Expected: RC=0 when Stream A+B complete
& $py -B $sc --live                                # Expected: RC=2 (missing confirmation)
& $py -B $sc --live --confirm-quest-complete YES_COPY_TO_TEAMWORK  # Expected: RC=2 (unfrozen markers)
& $py -B $sc --verify-debate-index --strict-living # Expected: RC=0 (live SHA-256 + unpooled scoreboard + 0 living drift)
& $py -B $sc --verify-debate-index                 # Expected: RC=0 (0 static drift + 0 scoreboard diffs + 0 forbidden words)
```
