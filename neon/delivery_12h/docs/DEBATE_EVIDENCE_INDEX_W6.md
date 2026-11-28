# Wave 6 — 3-Model Debate Evidence Index (`Opus / Neon / Astra`)

**Snapshot Timestamp (UTC):** `2026-11-28T07:39:04Z`
**Maintainer:** Wave 6 Milestone 3 (Stream C)
**Scope:** Live-computed SHA-256 master index incorporating all Wave 5 assets plus all post-G3 `Ep 40` diagnostics, `55` unpooled completed `fastchess` matches (`ALL_MATCHES_SCOREBOARD.md`: `25 x 600g @ 50k` screens, `28 x 1,000g @ 50k` confirmations, `2 x 600g @ 250k` decision matches; Wave 6 survey baseline was `51` and `ALL_MATCHES_SCOREBOARD.json` has `47`), V3P 5-surface placement inventory, Stage-2 Filter Quest summary, Server-Day arch suite, and Round 12–14 / parity / Surface-4 patches.

---

## 1. Executive Debate Rules & Evidence Integrity (Rule R5)

1. **Screens vs Confirmations vs Higher-Node Decision Matches Are NEVER Pooled:** All `600g @ 50k` search screens (Table A, `25` runs) are exploratory screening leads only. Only fresh-seed `1,000g @ 50k` (Table B, `28` runs) or `600g @ 250k` / `2,000g @ 6+0.06` equal-time confirmations (Table C, `2` runs) are decision-grade Elo evidence. Example: `SF4b1` scored `+15.06 Elo` (`600g` screen) yet lost `-4.52 Elo` alone and `-15.99 Elo` with `SF8` on `1,000g` confirmations; `SF15` scored `+7.53 Elo` (`600g`) yet `-0.35 Elo` (`1,000g` confirm); `COMBO_v2` (`SF8+SF13+LmrDeeper`) scored `-3.13 Elo` despite individual wins.
2. **Offline Metrics Are Diagnostic Leads Only:** Training loss, `M4` WDL MSE, `SF19` blunder rate, `WDL` calibration `ECE`, and `heldout_syzygy_4k` accuracy never replace `fastchess` playing-strength evidence.
3. **Living-Run Snapshot (`G3_FULL25` Ep 40 Complete):** `G3_FULL25_v3p_1024_cc0_anchored` finished `40/40` epochs (`cand.fnn3`, `train_seconds=9157.4`, `final_train_loss=0.006042`), passed `--full` Master Gates (`hard_pass=true`), beat same-data `r0202` by `+22.27 [+8.64, +35.96]` Elo (`1,000g @ 50k`), scored `+4.86 [-8.49, +18.23]` Elo vs `r0067` (`1,000g @ 50k`), beat `r0067` by **`+22.03 [+5.88, +38.28]` Elo** (`z=+2.675, LOS=99.63%`) at `600g @ 250k` and scored `-0.58 [-16.30, +15.14]` Elo vs `r0202` (`600g @ 250k`) (Table C). Stage-2 `12` matches and clean `6+0.06` PGO confirmation are pending; `HANDOFF_12H_DATA_QUALITY.md` and `ALL_MATCHES_SCOREBOARD.md` remain living documents.
4. **Measurement vs Planning Estimate Separation:** All `V3P_v3` verify/UBSan/multithread checks, `bucketed` dedup throughput, `.fqs.z` compression ratios, and RX 7900 XT training speeds are directly measured; cloud EUR/hr rates and H100/RTX 4090 throughput in `SERVER_DAY_COST_MODEL.json` are planning estimates.

---

## 2. Master Artifact & Live SHA-256 Registry

### 2A. Parity Bias, CC0 Book & Living Documents (13 Files)
| Artifact | Exact Path | Bytes | Live SHA-256 |
|---|---|---:|---|
| `LIVE_LOOP_PARITY_BIAS_AUDIT.json` | `C:\nnue-lab\neon\filter_quest\LIVE_LOOP_PARITY_BIAS_AUDIT.json` | 1,139 | `cc0a0aeed348afa5336bd3b343b1a59cc1cb52297cd0173fe1690b8ca437aa93` |
| `COLOR_AND_OUTCOME_SYMMETRY.json` | `C:\nnue-lab\neon\filter_quest\COLOR_AND_OUTCOME_SYMMETRY.json` | 5,442 | `a3b4d88c3a09a23bab5a64746eb93ae488a2bcb6cd8cf210b3980ac9e80cc790` |
| `PARITY_FIX_PILOT_4K.json` | `C:\nnue-lab\neon\filter_quest\PARITY_FIX_PILOT_4K.json` | 293 | `b4dcbaf6be8b0af4e3e019bfaa45fd5984f4dcc711f7100b030358a368371a7d` |
| `HANDOFF_12H_DATA_QUALITY.md (living)` | `C:\nnue-lab\neon\filter_quest\HANDOFF_12H_DATA_QUALITY.md` | 34,875 | `bae42cb53544dd3560fcc456decd5811d7a8afef4a084cb7ddafd7a293129e6a` |
| `PHASE_B_METHODS_AND_DESIGN.md (living)` | `C:\nnue-lab\neon\filter_quest\PHASE_B_METHODS_AND_DESIGN.md` | 19,634 | `d8c81bc215a59ace988c2d9fd66240600d463193cb5419b44836fd34c0263f6b` |
| `book_cc0_clean.epd` | `C:\nnue-lab\neon\forge_fixes\book_cc0_clean.epd` | 15,793,891 | `d49523f18e004126fca3914ffb92a89cfc3c8b4427ce4c18d4405faeb1102191` |
| `stm_bias_root_cause.json` | `C:\nnue-lab\neon\forge_fixes\stm_bias_root_cause.json` | 7,320 | `aec3965fc204436d5f7032aa9aab7aab1d4d46dfaed03cb7f4b6f43a1bd4f81b` |
| `cc0_book_audit.json` | `C:\nnue-lab\neon\forge_fixes\cc0_book_audit.json` | 994 | `1da807bea16ce832088e1fc0d4dc419ace521d223cbf283f775913228d03f9e0` |
| `book_cc0_clean_meta.json` | `C:\nnue-lab\neon\forge_fixes\book_cc0_clean_meta.json` | 368 | `afe3d8b53c633034c9c05c027004f0628cb4739869d92787fbffabd847615fc4` |
| `pilot_datagen_parity_7_8.json` | `C:\nnue-lab\neon\forge_fixes\pilot_datagen_parity_7_8.json` | 1,243 | `74ce8489278b5aa4970114f86c878551934aca3da5dfebabd85459283eccf61b` |
| `datagen_uci_cc0_parity.patch` | `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_cc0_parity.patch` | 5,372 | `5b8bba1c416bad446437c2415573428b04c8ea5952be1af403cfef3a6ba1726d` |
| `datagen_uci_startpos_only.patch` | `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_startpos_only.patch` | 3,816 | `c0c92cb75a56b8a5e0d9670befd6509e21a912ac6facf2124e62e1734494eba8` |
| `datagen_uci_parity_7_8_minimal.patch` | `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_parity_7_8_minimal.patch` | 5,771 | `184c6d2b8f880a7a22d23667e5b9ab38df53037c9736e14a115c84b9efa556c7` |

### 2B. `G3_FULL25` 3-Cycle Diagnostics, `SF19` Taxonomy, Blunder Probes & `WDL` Calibration (29 Files)
| Artifact | Exact Path | Bytes | Live SHA-256 |
|---|---|---:|---|
| `diag_e6/diag_summary.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e6\diag_summary.json` | 657 | `e4a2403f12104258cc8d1303cc361d0a981511693c3d43f59d4b329408dbc21f` |
| `diag_e6/eval_full.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e6\eval_full.json` | 1,010 | `3d51685bf36921a4e9dd43c3eb6ccee07dcf7504ff06d558a2bef33a9cf1f839` |
| `diag_e6/heldout_syzygy_4k.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e6\heldout_syzygy_4k.json` | 1,192 | `1c0b702a80821cfe9eb4e44bb7f14758669f6ffcad3989116d149a41369c03d8` |
| `diag_e6/net_sanity_v2.txt` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e6\net_sanity_v2.txt` | 1,196 | `fb693b310fffec898c4412f71fd98494d1144cd93a91e53e5a697444d047beaa` |
| `diag_e6/sf19_slice.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e6\sf19_slice.json` | 2,842 | `6463deab6c604379bc795b5fb36cdcbd6a1fd6b3d4aed6a061a02e2ee24ff371` |
| `diag_e6/cand.fnn3` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e6\cand.fnn3` | 12,798,184 | `58c9a5eac649e0158150eeb7cefca78d2cc784a616e17faf77aa2135f883b00c` |
| `diag_e12/eval_full.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e12\eval_full.json` | 963 | `3c74504749478488a929636555d412a2ba3f311e1b5a70fb1a31b816e3920d3e` |
| `diag_e12/heldout_syzygy_4k.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e12\heldout_syzygy_4k.json` | 1,186 | `4d6810219946596efddcf8184df200a00cadf632c81d3995c0de86863b78aa68` |
| `diag_e12/sf19_slice.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e12\sf19_slice.json` | 2,844 | `fa2705202bec8240540d63a373064e0431ca91e7e2398a6d607b7d963046abe4` |
| `diag_e12/swa_meta.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e12\swa_meta.json` | 586 | `e60d7c77edcd25600483a79a145cf46c7acad0ca87b6f0c56f76dbceb9748a61` |
| `diag_e12/cand.fnn3` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e12\cand.fnn3` | 12,798,184 | `f96f772023c59a83740d64231dd042385c8c5a7eeca0ed8273bf9a7863eff6d5` |
| `diag_e24/diag_summary.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\diag_summary.json` | 610 | `eea294f1ed92bb0a8ae77fccf6ef80c9fc74bbcb7c4abc06d4b69f64774b8ab7` |
| `diag_e24/eval_full.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\eval_full.json` | 962 | `ede50e0e3af50840616a8a30e261242478aedf32735c8c02ac36272b11c3d64f` |
| `diag_e24/heldout_syzygy_4k.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\heldout_syzygy_4k.json` | 1,190 | `0a661f06444e022545c8d3a376c86dc8cc1ea829deeb6c57664d404d62990b78` |
| `diag_e24/net_sanity_v2.txt` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\net_sanity_v2.txt` | 1,191 | `73b9e77c043a3d996ee09686e0642b78c27fd5b3b0897e39ae560c7481f9f8b9` |
| `diag_e24/sf19_slice.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\sf19_slice.json` | 2,842 | `f148fb871da27898df8e64720b23d2ce65df6099ec84abe15933561097c889ea` |
| `diag_e24/cand.fnn3` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\diag_e24\cand.fnn3` | 12,798,184 | `f656225c0bd4abfe1255932cd42a319e2828fd47d8e479f90d58db6b4308e6ef` |
| `SF19_ERROR_TAXONOMY.json` | `C:\nnue-lab\neon\forge_fixes\SF19_ERROR_TAXONOMY.json` | 5,487 | `c5005018523204225a2dab4cbeae06710f0ebb5b7baae14b29fea077bc7dee44` |
| `WDL_CALIBRATION_AUDIT.json` | `C:\nnue-lab\neon\filter_quest\WDL_CALIBRATION_AUDIT.json` | 7,758 | `fc603ac498a51b213a2c1733abc9cabbe4785d0974e54b15047da9185160f5ba` |
| `G3_SCALING_TRAJECTORY.json` | `C:\nnue-lab\neon\forge_fixes\G3_SCALING_TRAJECTORY.json` | 2,859 | `b6da207e315114db7677f753feb70f8586520180b04fd5d1e8393f2aa39abc8a` |
| `G3_RESIDUAL_BLUNDER_DIAGNOSIS.json` | `C:\nnue-lab\neon\forge_fixes\G3_RESIDUAL_BLUNDER_DIAGNOSIS.json` | 1,018 | `8f6ab3f92df1eee85b557e53ce37e00f55fc1247a7d0526edd2d3f42928cb4c7` |
| `G3_QUIET_BLUNDER_DEPTH_PROBE.json` | `C:\nnue-lab\neon\forge_fixes\G3_QUIET_BLUNDER_DEPTH_PROBE.json` | 1,352 | `9e14d65f14cd9980e8645bb2c13322b833d486a395098dcb40d07035c1aeeb1a` |
| `baseline_r0067_scorecard.json` | `C:\nnue-lab\neon\forge_fixes\baseline_r0067_scorecard.json` | 914 | `13950486c75e3edc80ec32f4ac960b45d24a6a89b7f5c388fbfd76362e1675c2` |
| `r0067/train/cand.fnn3` | `C:\nnue-lab\runs\forge\r0067\train\cand.fnn3` | 9,463,528 | `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28` |
| `G2_v3p_1024_pairwise_psqt/cand.fnn3` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G2_v3p_1024_pairwise_psqt\cand.fnn3` | 12,798,184 | `6a24996f9057c5b42a489c12c185de1673f30a0318b17e020514efbd647d587f` |
| `anchors/heldout_eval_r0067.json` | `C:\nnue-lab\neon\forge_fixes\anchors\heldout_eval_r0067.json` | 1,142 | `639aad8609d7bcbe06dc39dd1099794a1786c2c475915a174ab7ff0241c70124` |
| `anchors/heldout_eval_G2.json` | `C:\nnue-lab\neon\forge_fixes\anchors\heldout_eval_G2.json` | 1,160 | `7c5007d2a53ad0bd4019ae06fb87c7160b19b972a43e7dbb9f990a03ab081a95` |
| `sf19_slice_r0067.json` | `C:\nnue-lab\neon\forge_fixes\sf19_slice_r0067.json` | 2,790 | `4a2d0a954b2050b7b2af84285b97e597346320f2b08f78f0e72e72d8ed7fded8` |
| `sf19_slice_G1.json` | `C:\nnue-lab\neon\forge_fixes\sf19_slice_G1.json` | 2,819 | `c9e0df8a36a5425e4cbf32398b43fc132ec368ad84db16b0a59d72d7ff5218a6` |

### 2C. `V3P_v3` Fused AVX-512 Kernel Proofs & Engine Safety (9 Files)
| Artifact | Exact Path | Bytes | Live SHA-256 |
|---|---|---:|---|
| `V3P_FUSED_V3_VERIFY_PROOF.json` | `C:\nnue-lab\neon\forge_fixes\V3P_FUSED_V3_VERIFY_PROOF.json` | 766 | `8bdfbb7300a84076b566dd53af5773b1c26013fc216e2266631987ff6c522ade` |
| `UBSAN_STACK_PROOF.json` | `C:\nnue-lab\neon\forge_fixes\UBSAN_STACK_PROOF.json` | 509 | `edaf038fbe39d68022350939db27e965eca66dd3cd53abec46d1b67f041b53f2` |
| `MULTITHREAD_STRESS_PROOF.json` | `C:\nnue-lab\neon\forge_fixes\MULTITHREAD_STRESS_PROOF.json` | 1,054 | `d10a41ccefce83405d1558434c318b29424a63fc2ef6814201ac9271a3b0fa7a` |
| `V3P_FUSED_BITEXACT_PROOF.json` | `C:\nnue-lab\neon\forge_fixes\V3P_FUSED_BITEXACT_PROOF.json` | 1,656 | `de2eeea0e7978f26d68ee9b11980e6ed1f66b4021870820876fd4ad632dc3855` |
| `V3P_FUSED_V3_REPORT.json` | `C:\nnue-lab\neon\forge_fixes\V3P_FUSED_V3_REPORT.json` | 680 | `230faae8b814b0b32ee9765b391fcc776ef839e5e3ae55409e10aff1619ad0eb` |
| `V3P_WIDTH_SCALING.json` | `C:\nnue-lab\neon\forge_fixes\V3P_WIDTH_SCALING.json` | 2,781 | `2077c3adaebd6ac7efd5f015142defc6631dc69e3c0634222ab7756ab9fac740` |
| `V3P_pairwise_psqt_fused_v3.patch` | `C:\nnue-lab\neon\forge_fixes\patches\V3P_pairwise_psqt_fused_v3.patch` | 43,075 | `57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763` |
| `STACK_V3Pv3_SF13_SF8_W2P1.patch` | `C:\nnue-lab\neon\forge_fixes\patches\STACK_V3Pv3_SF13_SF8_W2P1.patch` | 54,707 | `f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8` |
| `superstack_6patch_proof.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\superstack_6patch_proof.json` | 7,572 | `f20a0a4f0b0c9629d3f96e601266637320f0c59583be86a058c278515ca86227` |

### 2D. `kb=16` Feasibility, Diversity, Cross-Split Leakage & Server-Day Cost / Throughput (12 Files)
| Artifact | Exact Path | Bytes | Live SHA-256 |
|---|---|---:|---|
| `V3P_KB16_FEASIBILITY.json` | `C:\nnue-lab\neon\forge_fixes\V3P_KB16_FEASIBILITY.json` | 214 | `9c91cf72b3394fa9b2a3857c51f07bfce2bbb197fb56dae4e0c79bed45da5f04` |
| `OPENING_AND_KB16_DIVERSITY.json` | `C:\nnue-lab\neon\filter_quest\OPENING_AND_KB16_DIVERSITY.json` | 3,614 | `0b24f075f2490a2b4faeaad5352c3010776cad7965bf4914d6653b09cf989c87` |
| `CROSS_SPLIT_LEAKAGE_AUDIT.json` | `C:\nnue-lab\neon\filter_quest\CROSS_SPLIT_LEAKAGE_AUDIT.json` | 2,255 | `7c879c6e0376db5b5b105df56f7588b2d3ed6cc2a7362b8f5caa83dabc9a75ea` |
| `SERVER_DAY_COST_MODEL.json` | `C:\nnue-lab\neon\filter_quest\SERVER_DAY_COST_MODEL.json` | 3,633 | `152cd19e9975d03b2692bb4c5c32a682e9e6287f17e2d66c1ce0a8d843527353` |
| `partition_fqs_buckets_bench.json` | `C:\nnue-lab\neon\filter_quest\results\partition_fqs_buckets_bench.json` | 6,294 | `cbf81bfa3b2d1e72842c516a1303c65a74932a75b09bfb33a18b41fec18acbe5` |
| `final_eval_r0203_w14_w15.plain` | `C:\nnue-lab\neon\filter_quest\eval_sets\final_eval_r0203_w14_w15.plain` | 19,356,333 | `b8ff64590bd511584dbcf603dbedb30dd1a2c54f3b4aae844904bd33cf96175b` |
| `anchors/heldout_syzygy_4k.json` | `C:\nnue-lab\neon\forge_fixes\anchors\heldout_syzygy_4k.json` | 324,677 | `b363d7843ea696008ced1d37699b255469202d9577a0c43f8849bd81979f1429` |
| `anchors/heldout_integrity_verification.json` | `C:\nnue-lab\neon\forge_fixes\anchors\heldout_integrity_verification.json` | 1,380 | `7dfe88d9b537fed19f45ad169cfada6e904aadbc902c1e0b94b5df85e1114adf` |
| `anchors/s5_s7_overlap_audit.json` | `C:\nnue-lab\neon\forge_fixes\anchors\s5_s7_overlap_audit.json` | 2,573 | `7f6bcd378bb64e6e1c8893df68fd9ada63eb566d1702dafe4e22b2f2a45d2fc3` |
| `anchors/dead_draws_20k_s5disjoint.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\dead_draws_20k_s5disjoint.fqs.z` | 125,433 | `7653279511862abc7d5bd856f14e61a594932ba625be09107e168d43e9b775a5` |
| `anchors/won_endings_syzygy_20k.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\won_endings_syzygy_20k.fqs.z` | 154,309 | `c2f51696b886c6cad78da2cca253352d79e6a188778c5ab35526b6321a4a96de` |
| `anchors/opening_ply012_anchors.fqs.z` | `C:\nnue-lab\neon\forge_fixes\anchors\opening_ply012_anchors.fqs.z` | 2,200 | `6703857609240a6cbdf07d85e95d1747d939ccb307b685eb0c6c76675e4540d0` |

### 2E. Supporting Neon & Wave 3–5 Audit / Build JSONs (21 Files)
| Artifact | Exact Path | Bytes | Live SHA-256 | Key Relevance |
|---|---|---:|---|---|
| `ALL_MATCHES_SCOREBOARD.md (living)` | `C:\nnue-lab\neon\forge_fixes\ALL_MATCHES_SCOREBOARD.md` | 8,651 | `da3b6568e7a1148af8285a196b777ae7507e6e9a63a5a200cf794f689187146c` | `54` completed matches (living; `.json` snapshot `47`) |
| `ALL_MATCHES_SCOREBOARD.json (living)` | `C:\nnue-lab\neon\forge_fixes\ALL_MATCHES_SCOREBOARD.json` | 20,331 | `f57ea1995eba481d726b14b9628bf4c633f0177bae250eaabbfa78fb93a7fd0f` | Machine-readable scoreboard (`47` entries) |
| `rescore_depth_curve.json` | `C:\nnue-lab\neon\forge_fixes\rescore_depth_curve.json` | 1,845 | `112162c61fedb4fcc22a5b199689ea2f4623dbde447a42dbba7a2c55aceefca1` | `4k->8k` `-12.34%` MSE, `4k->16k` `-19.22%` MSE |
| `SERVER_DAY_OB_MIX_AUDIT.json` | `C:\nnue-lab\neon\filter_quest\results\SERVER_DAY_OB_MIX_AUDIT.json` | 1,695 | `a18497efac3888069e245fb7a3fa6b585023745ea5637afa3f9235b8b736e993` | CC0+1% anchors `OB0` `0.597x` vs M4 (`KL=0.02233`) |
| `WITHIN_GAME_CORRELATION_AUDIT.json` | `C:\nnue-lab\neon\filter_quest\results\WITHIN_GAME_CORRELATION_AUDIT.json` | 3,664 | `a045c1d720dcac9273c7df9b2735b6fbfbfcbada0812f8ff6785aa367a8a009e` | Lag-1 `rho_wdl=0.9958`, `tau_int=36.592` |
| `audit_cc0_v2_dedup_phase.json` | `C:\nnue-lab\neon\filter_quest\results\audit_cc0_v2_dedup_phase.json` | 1,311 | `09d71c18e89f04b75693e4106b79ee3732ac6bf068d1d3e5cd4f79ffdd10e1fb` | `2,000,004 -> 1,839,070 -> 1,612,164` (`12.34%` exact dup) |
| `audit_neardups_and_correlation.json` | `C:\nnue-lab\neon\filter_quest\results\audit_neardups_and_correlation.json` | 1,955 | `7f09aae7f09121005635e61cfc379d8fa0733bd185bc7cebce4734b142c4a7a1` | `48.95%` rows carry `90%` grad; `28.66%` PK near-dups |
| `audit_r0202.json` | `C:\nnue-lab\neon\filter_quest\results\audit_r0202.json` | 4,383 | `09bbb44f8fcfea324052ec01b31ab6e2e01fbc18753c972721ab17aef13837b7` | `r0202` `14.015%` `|score|>=800`, `14,542` draw-conf/round |
| `audit_val_and_r0203_raw.json` | `C:\nnue-lab\neon\filter_quest\results\audit_val_and_r0203_raw.json` | 23,123 | `f3accfea6db70bb3b4e387910f77362e6a30f573dfa65eb4e1394fcba6f1a6a6` | Legacy `val.plain` vs `r0203` raw audit |
| `cross_round_dedup_r0178_r0202_m64.json` | `C:\nnue-lab\neon\filter_quest\results\cross_round_dedup_r0178_r0202_m64.json` | 7,772 | `898e07e0bd81a5194e52c46dd9886917d1ee22390a390e938bcc41d680f95b62` | `3.145%` cumulative cross-round dup (`r0178..r0202`) |
| `m4_vs_train_shift.json` | `C:\nnue-lab\neon\filter_quest\results\m4_vs_train_shift.json` | 2,483 | `9d820da3b64c4278a296c20485a4cd8779b818cef4dd5f68a235882649b2019b` | `ob0=0.562x`, `ob7=1.663x` vs M4 |
| `offline_eval_table.json` | `C:\nnue-lab\neon\filter_quest\results\offline_eval_table.json` | 24,992 | `e2eef0eecdf6187bd1b9699fbecc2253582a3f48447e4fadb2da01c80fbafa5f` | Offline diagnostic comparison across quest nets |
| `parallel_filter_benchmark.json` | `C:\nnue-lab\neon\filter_quest\results\parallel_filter_benchmark.json` | 737 | `e81633ca15da3aa9ec1c68ad69cdc345e3e59f38c34d082ece532e96493c38c3` | `12w` `.plain -> .fqs.z` `482.5k rec/s` (`10.53 B/kept`) |
| `ROUND10_SEARCH_BUILD_REPORT.json` | `C:\nnue-lab\neon\forge_fixes\ROUND10_SEARCH_BUILD_REPORT.json` | 463 | `83762d41a76f8fbfd37b33be1e80cd3185e4f3c004789e614219844358ab7965` | `SF29`, `SF30`, `SF31` `--quick` `hard_pass=true` |
| `ROUND11_SEARCH_BUILD_REPORT.json` | `C:\nnue-lab\neon\forge_fixes\ROUND11_SEARCH_BUILD_REPORT.json` | 302 | `10bc8c2d964647860e16a43f8e88099781a9c7ff413fe0ed5be3b2d40856487b` | `SF32`, `SF33` `--quick` `hard_pass=true` |
| `ROUND12_BUILD_REPORT.json` | `C:\nnue-lab\neon\forge_fixes\ROUND12_BUILD_REPORT.json` | 1,417 | `12e1739a33235f858559373a602f77562c5549cdca03939973ad263143cb2b81` | `SF34`, `SF35`, `SF36` `--quick` `hard_pass=true` |
| `ROUND13_BUILD_REPORT.json` | `C:\nnue-lab\neon\forge_fixes\ROUND13_BUILD_REPORT.json` | 820 | `510ac18ff3bc0c2abe26564aadf0b2de9e18fb213a52587d1d853d59d0a60da4` | `SF38`, `SF39` `--quick` `hard_pass=true` |
| `proto_7_gate.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_7_gate.json` | 8,916 | `98a2c0f1f37804cf8e24ade78ef428948aa6cfc95c1f6fc37112d7164f9b25ce` | W4 `proto_7` gate proof |
| `proto_8_gate.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamA_search_packets\builds\proto_8_gate.json` | 8,909 | `4bd548cd7c63380763553cad1f362fecdddcd63f584218b361063d4c769789d7` | W4 `proto_8` gate proof |
| `proto_9_corr_complexity_rfp_lmr_gate.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\proto_9_corr_complexity_rfp_lmr_gate.json` | 8,926 | `215cb73d8cf24894ad5c7824caa514482a36ec78d6a8f7b272198df0c0003f76` | W5 `proto_9` gate proof |
| `proto_10_cutnode_history_and_cap_lmr_gate.json` | `C:\nnue-lab\neon\forge_fixes\teamwork_wave5\streamA_search_packets\builds\proto_10_cutnode_history_and_cap_lmr_gate.json` | 8,920 | `2e33a0b015c62b11e3085b7147d03c6827fb98ec1b905db6ea27c73d887cac82` | W5 `proto_10` gate proof |

### 2F. Post-G3 `Ep 40`, Matches, Phase B/C Audits, V3P Placement & Round 12–14 Patches (39 Files)
> **Note on `SF37`:** `SF37` has **no standalone `.patch`** on disk (`builds\SF37_tm_combined_SF17_plus_SF18.exe` is `SF17 + SF18` combined).
| Artifact | Exact Path | Bytes | Live SHA-256 | Key Relevance |
|---|---|---:|---|---|
| `G3_FULL25/cand.fnn3 (Ep 40)` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\cand.fnn3` | 12,798,184 | `7ff7789032491aa732846db17ad24ec7fc95c6cb9ad177490f5a06fcccbb9763` | Final Ep 40 net (`checksum=aaf8ca22cd936daf`) |
| `G3_FULL25/metrics.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\metrics.json` | 3,819 | `5c227a17c17a0173ab7c51548b098f912600baef46b942e6b332e2593bbe37de` | `40` ep, `loss=0.006042`, `int_parity=256/256<=1cp` |
| `G3_FULL25/post_g3_summary.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\post_g3_summary.json` | 7,218 | `c17ed87657eeee881e4839a4bd37e62590674a449d89544be5985a2cbabcfcc5` | `master_gates_ok=true`, `best=cand` |
| `G3_FULL25/master_gate_full_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\master_gate_full_cand.json` | 9,578 | `356f63d9c87c93a25427f5eab8d33b17f4592616089875da2a2b22c7c30f4442` | `PASS_WITH_ADVISORY_FLAGS`, `hard_pass=true`, `37/37` loader |
| `G3_FULL25/eval_full_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\eval_full_cand.json` | 1,021 | `b6d596b4b9acabddf5c018f8872c66a685a7a77786a7ff03c26ab347fdf5beeb` | `m4_wdl_mse=0.0114`, `corr=0.8041`, `cliff=133.0` |
| `G3_FULL25/heldout_syzygy_4k_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\heldout_syzygy_4k_cand.json` | 1,177 | `adec936dd6ce3ccc5be75453be51eac77838824e965ef84607ad5e084c602233` | Draws `med=9.9 cp`, wins `sign=99.6%` |
| `G3_FULL25/sf19_slice_cand.json` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\sf19_slice_cand.json` | 2,836 | `9c7745409c45fc145ab6d52239760c1cda5ccafbd59f3576b9ffe2f57cfc7881` | `wdl_mse=0.052914`, `sev35=13.22%` |
| `G3_FULL25/net_sanity_v2_cand.txt` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\net_sanity_v2_cand.txt` | 1,191 | `eab287868ffd33c8b50e2d8b322964e8837cb73958ed586a03b99b980b4f09a6` | `unit=172.2`, `1 FLAG: S1 -14.5 cp`; `S2..S8` pass |
| `G3_FULL25/heldout_perpos_cand.tsv` | `C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\heldout_perpos_cand.tsv` | 196,559 | `914f344aef8fe8a7dba57c7e7de3a54aa3a8d4e21f730de6d795e3aef792e14c` | Opus TSV: `4,002` lines / `4,000` data rows (referenced, NOT copied into 1.8 MiB bundle) |
| `G3_FULL25_vs_r0067_1000g_50k/summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_1000g_50k\summary.json` | 4,772 | `2acbaa65272ba182bf3d63759b053423654b5169d3ddf909ecd65d27fb5a01b5` | `270-474-256`, `+4.86 +/- 13.35` Elo |
| `G3_FULL25_vs_r0067_1000g_50k/declaration` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_1000g_50k\declaration_20261127_222833.json` | 3,708 | `f7371869469791a87916c1ce1e303776f3604c49d08418cc2a788672c987d474` | `v3p_fused_v3_engine.exe` vs `base_r15dsg.exe` (`seed=202611501`) |
| `G3_FULL25_vs_r0067_1000g_50k/config.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_1000g_50k\config.json` | 14,580 | `9a880e3a75dfa85cadf9296bd917a125edd42f46c0e2bbdb5d4b9d28ba4dcecb` | `UHO_Lichess_4852_v1.epd`, `50k` nodes |
| `G3_FULL25_vs_r0202_1000g_50k/summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_1000g_50k\summary.json` | 4,842 | `bf0b092f06a89cffd444e4ce81ebadcb6f89fdb3b9eeac164213674bb58667e1` | `298-468-234`, `+22.27 +/- 13.64` Elo (`LOS 99.93%`) |
| `G3_FULL25_vs_r0202_1000g_50k/declaration` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_1000g_50k\declaration_20261127_223800.json` | 3,777 | `6166b0ced7d8dacde4ed7b36eef31a945817e503ac396a14a293acd2c4819436` | Same-25r `r0178..r0202` control (`seed=202611505`) |
| `G3_FULL25_vs_r0202_1000g_50k/config.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_1000g_50k\config.json` | 14,579 | `766c24b9fb99e98329e5cf11cce65b5113d617140eaa5d51452fad6fcec366a7` | `UHO_Lichess_4852_v1.epd`, `50k` nodes |
| `G3_FULL25_vs_r0067_600g_250k/summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_600g_250k\summary.json` | 4,816 | `7030b0793828ec0c9b4c33ff64f71c24187d4692828575f282a1c67515d1333c` | `165-308-127`, `+22.03 +/- 16.17` Elo (`LOS 99.63%`) |
| `G3_FULL25_vs_r0067_600g_250k/declaration` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0067_600g_250k\declaration_20261127_224737.json` | 3,751 | `63fa62ee1c5d20ec247fe9615d8fbbe2a9ed6d1cf3da9c608cb6001872fee57d` | Opus Point 3 `250k` decision match vs `r0067` (`seed=202611701`) |
| `G3_FULL25_vs_r0202_600g_250k/summary.json` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_600g_250k\summary.json` | 4,821 | `d4a82130a301daaee903b261232dc7c71f5b4e993d0de0d0b0ec58d3b48abfe0` | `152-295-153`, `-0.58 +/- 15.70` Elo (`LOS 47.12%`) |
| `G3_FULL25_vs_r0202_600g_250k/declaration` | `C:\nnue-lab\neon\forge_fixes\matches\G3_FULL25_vs_r0202_600g_250k\declaration_20261127_230522.json` | 3,756 | `936a86818d39ab2f62e43618c5a9bb267d2a684644ad22dcbb4bb0ecfd4a15a9` | Opus Point 3 `250k` decision match vs `r0202` (`seed=202611702`) |
| `G3_VS_R0067_PGN_DIAGNOSIS.json` | `C:\nnue-lab\neon\forge_fixes\G3_VS_R0067_PGN_DIAGNOSIS.json` | 1,276 | `6516eb180dd7a619ea8a0c065229dd66a52c241cfe01bcb5cd05a98caab805f8` | W `54.0%` (`+40`), B `47.4%` (`-26`), `eg_le10 +21` |
| `G3_STM_TEMPO_BY_SOURCE_AUDIT.json` | `C:\nnue-lab\neon\forge_fixes\G3_STM_TEMPO_BY_SOURCE_AUDIT.json` | 6,017 | `04eba7445196499a56cc64e88933dd430a640c35477ecd9912dac80ad97b6482` | `353,448,538` rows, `mean_final_target_cp=+4.29` |
| `G3_INDIST_TEMPO_AUDIT.json` | `C:\nnue-lab\neon\forge_fixes\G3_INDIST_TEMPO_AUDIT.json` | 933 | `98a3778aeb4183ef1d527e067c1f8da02e3fccdfad01ed58ccdd7370156491e4` | `600` pairs: `G3_e40` `+M` on `99.8%` (`mean=106.27`) |
| `pilot_datagen_parity_7_8_G3_R4.json` | `C:\nnue-lab\neon\forge_fixes\pilot_datagen_parity_7_8_G3_R4.json` | 1,038 | `99a8c85ce551cb310d48a3f1ec36b739f0baa68fd6491e54a9ad76364274b46d` | R4 `200g`: `+86.04 -> +69.99 cp` |
| `PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md` | `C:\nnue-lab\neon\forge_fixes\PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md` | 8,373 | `7ae59122a5c0628b77eda9681668907011a3d2f0f18ae5bf531bb46a72bcde21` | Surfaces 1–5 inventory, `~2.0h->~2.9h` cadence, `0.283%` anchor |
| `V3P_PLACEMENT_PACKAGE_VERIFICATION.json` | `C:\nnue-lab\neon\forge_fixes\V3P_PLACEMENT_PACKAGE_VERIFICATION.json` | 2,346 | `bed11cb8c91772de96e3b3fb4833799bc370f69c379a79b68c6208870c2d72ae` | `all_pass=true` across Surfaces 1–5 |
| `STAGE2_FILTER_QUEST_SUMMARY.md (living)` | `C:\nnue-lab\neon\filter_quest\STAGE2_FILTER_QUEST_SUMMARY.md` | 2,957 | `c17033d8b8a4102b0709fb5b6d62af7cf9a42ef7aa850ce91dffdf01f6eda56d` | `13/13` GPU arms done; `0/12` `1,000g @ 50k` matches done |
| `STAGE2_FILTER_QUEST_SUMMARY.json (living)` | `C:\nnue-lab\neon\filter_quest\STAGE2_FILTER_QUEST_SUMMARY.json` | 6,194 | `5b3df20128271863c8404978243ea55701519a4979f61bea9a1fe39dec9c1d12` | `13` GPU arms + `12` match specs |
| `SERVERDAY_ARCH_SUITE_SUMMARY.json` | `C:\nnue-lab\neon\forge_fixes\SERVERDAY_ARCH_SUITE_SUMMARY.json` | 1,052 | `6e31f3da625c36d1bc6899136b7ceef6073f9c49fb664005ecad50c10ed5efe4` | `768p/kb8`, `1536p/kb8`, `1024p/kb16` all `master_gate_hard_pass=true` |
| `forge_train_v3p_loop_adapter.py` | `C:\nnue-lab\neon\forge_fixes\forge_train_v3p_loop_adapter.py` | 7,880 | `55bc6078392b19df16860d8a93420c9af3b52bfeefe0026ef04888da841b7631` | Surface 3 loop adapter (`train`, `export`, `load_model`) |
| `test_v3p_surface2_format.py` | `C:\nnue-lab\neon\forge_fixes\test_v3p_surface2_format.py` | 4,715 | `c3157540e4cf92804183607bbd338262afd3e271240e8c0dd5cd1a6b60031574` | Surface 2 fail-before / pass-after (`0/50` diffs) |
| `test_v3p_surface4_parity_and_modelcheck.py` | `C:\nnue-lab\neon\forge_fixes\test_v3p_surface4_parity_and_modelcheck.py` | 5,398 | `18f7d8de513c3386c69682b13911bed385b5407645956eb6325db95dd9181528` | Surface 4a/4b fail-before / pass-after |
| `v3p_surface4a_v3_parity.patch` | `C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4a_v3_parity.patch` | 380 | `29d2af4dd4601312889215cbef8f08977d71d9a55d65f0023880b7013b41c777` | Surface 4a `v3_parity.py` `forge_v3p` fallback |
| `v3p_surface4b_v3_model_check.patch` | `C:\nnue-lab\neon\forge_fixes\patches\v3p_surface4b_v3_model_check.patch` | 1,395 | `68572e4546a453def301c8e163ab3470b49ae1dc7af8e40b723f651aa708589c` | Surface 4b `v3_model_check.py` `arch=='v3p'` dispatch |
| `SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF34_tactical_cutoff_quiet_malus_and_prior_refute.patch` | 2,205 | `056b3bae0db5193ebff6d7f4cd0a0d72e6646c8a56fc2fe40c08b3d53946b325` | Round 12 `SF34` (`bench13=835,472`, `hard_pass=true`) |
| `SF35_razoring_d3_quadratic_and_nmp_minply.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF35_razoring_d3_quadratic_and_nmp_minply.patch` | 3,473 | `4cd9f3953d840e249c1a2c397debb5b6fb0cd684f4c45f702e296b40af8aec5a` | Round 12 `SF35` (`bench13=503,542`, `hard_pass=true`) |
| `SF36_threat_quiet_move_ordering.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF36_threat_quiet_move_ordering.patch` | 1,075 | `7a07741e601136ee2fc0c5066e05a677516d4b901df5de93c02e883e748963d6` | Round 12 `SF36` (`bench13=817,101`, `hard_pass=true`) |
| `SF38_corrhist_major.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF38_corrhist_major.patch` | 4,650 | `02cc557e461d40ec2f1cf368230446ab4f522e31cf360012a3b6a02e1b417490` | Round 13 `SF38` (`bench13=510,068`, `hard_pass=true`; excludes `SF39`) |
| `SF39_corrhist_minor_plus_major.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF39_corrhist_minor_plus_major.patch` | 6,265 | `4160fef92c8c4f42b5e4c75f676d66532b6be696d63c60d2c7f9325e62563ee5` | Round 13 `SF39` (`bench13=531,909`, `hard_pass=true`; excludes `SF38`) |
| `SF40_tt_recency_pv_admit_and_pv_conthist.patch` | `C:\nnue-lab\neon\forge_fixes\patches\SF40_tt_recency_pv_admit_and_pv_conthist.patch` | 3,174 | `16dd427a387abb59a828a7eeb545032e1de6166ec691e93fff99b92532115c62` | Round 14 `SF40` (`RC=0`; no `ROUND14_BUILD_REPORT.json` on disk) |

---

## 3. Claim-to-Evidence Index (All 7 Debate Areas)

### Area 1: Live-Loop `random_move_count = 8` `+153 cp / 61.4%` White-Win Bias & Parity Fixes
- **Core Claims & Verified Numbers:**
  - `LIVE_LOOP_PARITY_BIAS_AUDIT.json`: All 4 audited live rounds (`r0180`, `r0190`, `r0200`, `r0202`; `55.5M+` rows) show systemic White-win bias (`white_stm` `50.360%–50.374%`, `mean_white_cp` `+151.39` to `+153.94 cp`, `white_score` `61.21%–61.46%`).
  - `COLOR_AND_OUTCOME_SYMMETRY.json`: `r0202_live` (`1,000,000` sample) has `W/D/L = 41.87% / 39.03% / 19.11%` (`white_score = 61.38%`, `mean_score_white_cp = +152.9`). Pre-target-STM `cc0_v2_nodrawconf` (`1,839,070` rows) showed `white_stm = 49.979%`, `mean_score_white_cp = -22.29`, `white_score = 47.93%`.
  - **Root Cause (`stm_bias_root_cause.json`):** `C:\nnue-lab\pipeline\config.forge.toml` sets fixed EVEN `random_move_count = 8` from `startpos` (ply 7 blind Black random move, ply 8 White's first searched move).
  - **Fixes Verified:** `book_cc0_clean.epd` + `gen_cc0_selfgame_fqs.py` (`20k`-pos `202g`: `white_stm = 49.79%`, `mean_white_cp = +21.87 cp`, `white_score_pct = 53.79%`); live `.plain` parity patches (`datagen_uci_cc0_parity.patch`, `datagen_uci_startpos_only.patch`, and `datagen_uci_parity_7_8_minimal.patch`: `pilot_datagen_parity_7_8.json` cut `200g` `127.12 -> 68.46 cp`, and `pilot_datagen_parity_7_8_G3_R4.json` on `G3_FULL25` cut `+86.04 -> +69.99 cp`, `white_score 58.75% -> 56.75%`, `exact_fen4_repeat 3.85% -> 3.46%`).
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json, hashlib; from pathlib import Path; a=json.loads(Path(r'C:\nnue-lab\neon\filter_quest\LIVE_LOOP_PARITY_BIAS_AUDIT.json').read_text()); r4=json.loads(Path(r'C:\nnue-lab\neon\forge_fixes\pilot_datagen_parity_7_8_G3_R4.json').read_text()); b=Path(r'C:\nnue-lab\neon\forge_fixes\book_cc0_clean.epd').read_bytes(); print('r0202:', a['live_rounds']['r0202'], 'g3_r4:', r4['control_fixed_8']['mean_white_cp'], '->', r4['patched_alt_7_8']['mean_white_cp'], 'book_sha256:', hashlib.sha256(b).hexdigest())"
  ```

### Area 2: `G3_FULL25` Full `Ep 40` Scaling Curve, `SF19` Taxonomy, Blunder Probes & `WDL` Calibration
*(Diagnostic leads only per Rule R5 — never Elo claims.)*
- **Full 4-Cycle Scaling (`r0067 -> G2 -> G3_e6 -> G3_e12 -> G3_e24 -> G3_e40`; `G3_SCALING_TRAJECTORY.json` & `post_g3_summary.json`):**

| Metric | `r0067` (`768w`) | `G2` (`1024w` 12r) | `G3_e6` (`1024w` C1) | `G3_e12` (`1024w` C2) | `G3_e24` (`1024w` C3) | `G3_e40` (`1024w` Final C4) |
|---|---:|---:|---:|---:|---:|---:|
| `net_sanity_v2` Flags | `3` (`S2,S5,S7`) | `2` | `1` (`S1 -12.6 cp`) | `0` | `0` (`S1 +1.9 cp`) | `1` (`S1 -14.5 cp`; `S2..S8` pass) |
| `M4` WDL MSE (`n=4000`) | `0.01302` | `0.01234` | `0.01197` | `0.01185` | `0.01175` | **`0.0114`** (`-12.44%` vs `r0067`) |
| `M4` Correlation | `0.7754` | `0.7864` | `0.7915` | `0.7950` | `0.7984` | **`0.8041`** |
| `M4` Opp-Wing WDL MSE (`n=718`) | `0.01724` | — | `0.01586` | `0.01551` | `0.01464` | **`0.01421`** (`-17.58%` vs `r0067`) |
| `OB0<->OB1` Median Cliff (`cp`) | `143.5` | `129.5` | `123.0` | `125.5` | `128.0` | `133.0` |
| `SF19` Overall WDL MSE (`n=6000`) | `0.057367` | `0.055020` | `0.054138` | `0.053505` | `0.053187` | **`0.052914`** (`-7.76%` vs `r0067`) |
| `SF19` Sign-Flip `>=150 cp` | `6.95%` *(tax)* / `5.10%` *(slice)* | `6.48%` *(tax)* / `4.45%` *(slice)* | `4.45%` *(slice)* | `6.08%` *(tax)* / `4.27%` *(slice)* | `5.90%` *(tax)* / `3.98%` *(slice)* | **`3.98%`** *(slice)* |
| Heldout Syzygy Draws `med \|cp\|` (`n=2000`) | `19.0` (`86.6% <=50cp`) | **`8.9`** (`94.3% <=50cp`) | `10.7` (`92.15% <=50cp`) | `9.2` (`94.30% <=50cp`) | `10.7` (`92.90% <=50cp`) | `9.9` (`93.9% <=50cp`) |
| Heldout Syzygy Wins `sign_ok` (`n=2000`) | `99.35%` | `99.60%` | `99.60%` | `99.65%` | `99.65%` | `99.6%` |
| `r0203` `final_eval` ECE (`10-bin`) | `0.01743` | `0.01653` | — | — | **`0.01458`** | `0.01685` (`wdl_mse=0.053514`) |

- **In-Distribution Tempo & Source Audit (`G3_INDIST_TEMPO_AUDIT.json`, `G3_STM_TEMPO_BY_SOURCE_AUDIT.json`):** Across `600` quiet `val.plain` pairs, `G3_e40` has positive STM tempo on **`99.8%`** (`mean_M_raw=106.27`, matching `r0067` `95.76`). Across the `353,448,538`-row weighted mix, `mean_final_target_as_cp = +4.29`.
- **Residual Blunder & Depth Probe (`G3_RESIDUAL_BLUNDER_DIAGNOSIS.json` live `G3_FULL25_e40`, `G3_QUIET_BLUNDER_DEPTH_PROBE.json`):** `G3_FULL25_e40` cuts `SF19` severe blunders (`>=0.35`) `14.47% (868) -> 13.22% (793)` (`-8.64%`); `63.43%` (`503`) are quiet (`137` opp-castle MG); `400`-node search resolves `26.67%` (`32/120`) while `73.33%` persist structurally; `G3_QUIET_BLUNDER_DEPTH_PROBE.json` (`n=100`): `400n/4k/16k` resolve `27.0% / 36.0% / 40.0%`, MAE `0.5593 -> 0.3724`.
- **Note on `SF19_ERROR_TAXONOMY.json`:** Computed through `G3_FULL25_e24` (`overall 0.053187`, `opp_side_castling 0.071015`, `endgame_le10_pcs 0.017481`); `G3_FULL25_e40` overall `SF19` improved further to `0.052914` (`sf19_slice_cand.json`), with `OB0=0.011963` (`0.0%` flip) and `OB1=0.016922` (`0.0%` flip).
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json; from pathlib import Path; g3=Path(r'C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored'); ev=json.loads((g3/'eval_full_cand.json').read_text()); sf=json.loads((g3/'sf19_slice_cand.json').read_text()); bl=json.loads(Path(r'C:\nnue-lab\neon\forge_fixes\G3_RESIDUAL_BLUNDER_DIAGNOSIS.json').read_text()); print('e40_m4:', ev['m4_wdl_mse'], 'sf19:', sf['overall']['wdl_mse'], 'blunder:', bl['g3_tag'], bl['g3_blunder_count'], bl['g3_blunder_pct'])"
  ```

### Area 3: `V3P_v3` Fused AVX-512 Kernel Proofs, 5-Surface Placement & Combined Stacks
- **Core Claims & Verified Numbers:**
  - `V3P_FUSED_V3_VERIFY_PROOF.json`: `-DFORGE_NNUE_V3_VERIFY=1` across 4 nets: `448,340` live nodes verified, `0` failures.
  - `UBSAN_STACK_PROOF.json`: `STACK_V3Pv3_SF13_SF8_W2P1.patch` UBSan `-fsanitize=undefined -fno-sanitize-recover=all`, `0` errors across `G3_e12` & `r0067`.
  - `MULTITHREAD_STRESS_PROOF.json`: `6` configs x `10` = `60/60` mates (`t4_stop_ms = 0.0`).
  - `G3_FULL25/master_gate_full_cand.json`: `--full` Master Gates `hard_pass=true`, `perft 12/12`, `v3_parity 1120/1120 max_diff_cp=0`, `loader_safety 37/37` + `uci_multi_net_switching=ok`.
  - `PLAN_V3P_LOOP_PLACEMENT_INVENTORY.md` + `V3P_PLACEMENT_PACKAGE_VERIFICATION.json`: `all_pass=true` across Surfaces 1–5 (`~2.0h -> ~2.9h` round cadence, `0.283%` anchor share).
  - `verify_all_patches_w6.py`: `75/75` patches `RC=0` plus isolated stack checks `superstack_6` (`6/6`), `v3p_round12_14_sf38` (`6/6`), and `v3p_round12_14_sf39` (`6/6`).
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json; from pathlib import Path; mg=json.loads(Path(r'C:\nnue-lab\neon\forge_fixes\gpu_runs\G3_FULL25_v3p_1024_cc0_anchored\master_gate_full_cand.json').read_text()); vp=json.loads(Path(r'C:\nnue-lab\neon\forge_fixes\V3P_PLACEMENT_PACKAGE_VERIFICATION.json').read_text()); print('master_gate:', mg['hard_pass'], mg['gates']['v3_parity']['max_diff_cp'], mg['gates']['loader_safety']['passed'], 'v3p_pkg:', vp['all_pass'])"
  ```

### Area 4: `kb=16`, Server-Day Arch Suite (`G5a/G5b/G5c`) & Opening/Bucket Diversity
- **Core Claims & Verified Numbers:**
  - `V3P_KB16_FEASIBILITY.json`: `kb8_mb=12.21`, `kb16_mb=24.39`, `kb16_parity_max_diff_cp=0` (zero C++ changes).
  - `SERVERDAY_ARCH_SUITE_SUMMARY.json`: All 3 Server-Day arch variants trained & master-gated (`hard_pass=true`): `G5a_cc0_768p_kb8` (`9,647,848` B, `31.8s`), `G5b_cc0_1536p_kb8` (`19,098,856` B, `63.5s`), `G5c_cc0_1024p_kb16` (`25,577,704` B, `53.5s`).
  - `OPENING_AND_KB16_DIVERSITY.json` (`n=500,000`): `r0202_live_8rand` `kb16_min_pct=0.895%`, `cc0_v2_book_4k` `kb16_min_pct=0.578%` (`23.12M` perspectives @ 2B).
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json; from pathlib import Path; s=json.loads(Path(r'C:\nnue-lab\neon\forge_fixes\SERVERDAY_ARCH_SUITE_SUMMARY.json').read_text()); print({k:(v['hidden'],v['king_buckets'],v['master_gate_hard_pass']) for k,v in s.items()})"
  ```

### Area 5: Cross-Split Leakage & Syzygy Holdout Integrity
- **Core Claims & Verified Numbers:**
  - `CROSS_SPLIT_LEAKAGE_AUDIT.json`: `train_anchors_all3 vs heldout_syzygy_4k`: `0/4,000`; `train_r0202 vs heldout_syzygy_4k`: `0/4,000`; `train_cc0_v2 vs heldout_syzygy_4k`: `1/4,000` (`0.025%`); `train_cc0_v2 vs final_eval_r0203`: `747/198,073` (`0.3771%`); `train_r0202 vs final_eval_r0203`: `2,716/198,073` (`1.3712%`).
  - `heldout_integrity_verification.json`: `4,000` unique rows, `syzygy_wdl_mismatches=0`. `s5_s7_overlap_audit.json`: `dead_draws_20k_s5disjoint.fqs.z` has `0` heldout and `0` S5/S7 overlap.
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json; from pathlib import Path; l=json.loads(Path(r'C:\nnue-lab\neon\filter_quest\CROSS_SPLIT_LEAKAGE_AUDIT.json').read_text()); print({k:v['overlap_keys'] for k,v in l['train_vs_eval_exact_overlaps'].items()})"
  ```

### Area 6: Server-Day Cost Model, Within-Game Correlation, OB Mix & Bucketed Dedup
- **Core Claims & Verified Numbers:**
  - `SERVER_DAY_COST_MODEL.json` *(planning estimates for cloud EUR/hr & H100/4090 speeds)*: Scenario A (`2.0B, H100, 1024w`): `EUR 72.40`; Scenario B (`1536w`): `EUR 75.25`; Scenario C (`1.5B, hybrid 7900 XT`): `EUR 28.52`; Scenario D (`4090`): `EUR 50.98`.
  - `partition_fqs_buckets_bench.json`: `2,000,004 -> 1,612,164` kept in `2.61s` (`4w`), **`766,285.1 rec/s`**, `0/9` diffs, `< 0.72 GiB/worker` RAM @ 2.0B.
  - `WITHIN_GAME_CORRELATION_AUDIT.json` (`1,555` games, `204,180` pos): lag-1 `rho_white_cp=0.9779`, `rho_white_wdl=0.9958`, `piece_jaccard=0.8413`, `tau_int=36.592`, `N_eff/N=0.0273`.
  - `SERVER_DAY_OB_MIX_AUDIT.json`: `ServerDay_2B_CC0_plus_1pct_anchors` vs `M4` (`OB0=0.597x`, `OB7=1.503x`, `KL=0.02233`); clamped `[0.7, 1.5]` LUT `[1.5, 1.089, 1.167, 0.978, 0.922, 0.883, 0.891, 0.7]`.
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json; from pathlib import Path; w=json.loads(Path(r'C:\nnue-lab\neon\filter_quest\results\WITHIN_GAME_CORRELATION_AUDIT.json').read_text()); o=json.loads(Path(r'C:\nnue-lab\neon\filter_quest\results\SERVER_DAY_OB_MIX_AUDIT.json').read_text()); print('tau_int:', w['tau_int_wdl_lag1_20'], 'kl:', o['kl_M4_vs_dist']['ServerDay_2B_CC0_plus_1pct_anchors'], 'lut:', o['recommended_serverday_ob_weights_clamped_0p7_1p5'])"
  ```

### Area 7: Complete Unpooled Fastchess Scoreboard (`55` Completed: `25` Screens + `28` Confirmations + `2` `250k` Decision Matches)
- **Post-G3 & Stage-2 Status:** `G3_FULL25_vs_r0202_1000g_50k` **`+22.27 [+8.64, +35.96]`** (`z=+3.21, LOS 99.93%`), `G3_FULL25_vs_r0067_1000g_50k` `+4.86 [-8.49, +18.23]` (`+21` net wins in `eg_le10`), `G3_FULL25_vs_r0067_600g_250k` **`+22.03 [+5.88, +38.28]`** (`z=+2.675, LOS 99.63%`), `G3_FULL25_vs_r0202_600g_250k` **`-0.58 [-16.30, +15.14]`** (`z=-0.072, LOS 47.12%`), `G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k` **`+699.72 [+642.27, +784.63]`** (`z=+141.30, LOS 100.0%`), and `G3b_skipnoisy_vs_G3a_eqret_1000g_50k` **`+651.27 [+597.55, +727.83]`** (`z=+115.77, LOS 100.0%`). Stage-2 Filter Quest: `13/13` GPU arms complete, `2/12` declared Stage-2 `1,000g @ 50k` matches complete (`STAGE2_FILTER_QUEST_SUMMARY.md` snapshot still reads `0/12`).
- **1-Line Read-Only Repro Command (`CUDA_VISIBLE_DEVICES=""`, `RC=0`):**
  ```powershell
  $env:CUDA_VISIBLE_DEVICES=""; C:\nnue-lab\venv101\Scripts\python.exe -B -c "import json; from pathlib import Path; md=Path(r'C:\nnue-lab\neon\forge_fixes\ALL_MATCHES_SCOREBOARD.md').read_text(); sb=json.loads(Path(r'C:\nnue-lab\neon\forge_fixes\ALL_MATCHES_SCOREBOARD.json').read_text()); rows=[l for l in md.splitlines() if l.startswith('| ') and l.split('|')[1].strip() not in ('Group','---')]; print('md_rows:', len(rows), 'json_rows:', len(sb), '250k_rows:', sum(1 for r in rows if '250k' in r))"
  ```

---

## 4. Unpooled Fastchess Scoreboard (`ALL_MATCHES_SCOREBOARD.md` / `.json`)

**Live Count Reconciliation:** `ALL_MATCHES_SCOREBOARD.md` records **`55`** completed matches (Wave 6 survey baseline `51` plus newly completed matches including `G3_FULL25_vs_r0067_600g_250k`, `G3_FULL25_vs_r0202_600g_250k`, `G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k`, and `G3b_skipnoisy_vs_G3a_eqret_1000g_50k`), whereas `ALL_MATCHES_SCOREBOARD.json` still holds **`47`** entries (missing the newest post-JSON runs). **`600g @ 50k` screens, `1,000g @ 50k` confirmations, and `600g @ 250k` decision matches are NEVER pooled.**

### Table A: Search Screens (`25 x 600g @ 50k nodes`) — Exploratory Screening Leads Only
| # | Group | Match Name | W–D–L | Elo `[95% CI]` | z | LOS% | Ptnml | Clean | Candidate vs Base |
|---:|---|---|---|---:|---:|---:|---|---|---|
| 1 | `forge_fixes` | `SF13_qs_evasion_pruning_600g_50k` | `169-298-133` | **+20.87** `[+4.86, +36.97]` | +2.56 | 99.5% | `[5, 60, 137, 90, 8]` | OK | `SF13_qs_evasion_pruning.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 2 | `forge_fixes` | `SF8_conthist_6ply` | `163-305-132` | **+17.97** `[+2.21, +33.80]` | +2.23 | 98.7% | `[5, 60, 141, 87, 7]` | OK | `SF8_conthist_6ply.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 3 | `forge_fixes` | `SF4b1_v3_endgame_scale` | `154-318-128` | **+15.06** `[-0.35, +30.54]` | +1.92 | 97.2% | `[3, 60, 156, 70, 11]` | OK | `SF4b1_v3_endgame_scale.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 4 | `forge_fixes` | `COMBO_v1_plus_LmrDeeper_600g_50k` | `148-324-128` | **+11.59** `[-4.52, +27.74]` | +1.41 | 92.1% | `[3, 72, 137, 78, 10]` | OK | `V3P_SF_COMBO_v1.exe` (`r0067`) vs `V3P_SF_COMBO_v1.exe` (`r0067`) |
| 5 | `forge_fixes` | `W2_proto_1_corrhist_minor_600g_50k` | `155-309-136` | **+11.01** `[-4.82, +26.88]` | +1.36 | 91.3% | `[5, 68, 135, 87, 5]` | OK | `proto_1_corrhist_minor.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 6 | `forge_fixes` | `SF6_lmr_fractional_caphist` | `158-302-140` | **+10.43** `[-5.77, +26.67]` | +1.26 | 89.6% | `[7, 65, 138, 83, 7]` | OK | `SF6_lmr_fractional_caphist.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 7 | `forge_fixes` | `SF15_rfp_failsoft_blend_600g_50k` | `151-311-138` | **+7.53** `[-8.65, +23.74]` | +0.91 | 81.9% | `[7, 69, 133, 86, 5]` | OK | `SF15_rfp_failsoft_blend.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 8 | `forge_fixes` | `SF14_lmr_ttpv_cutnode_ext_600g_50k` | `143-323-134` | **+5.21** `[-10.90, +21.34]` | +0.63 | 73.7% | `[7, 69, 138, 80, 6]` | OK | `SF14_lmr_ttpv_cutnode_ext.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 9 | `forge_fixes` | `SF9_minor_corrhist_conservative_600g_50k` | `157-295-148` | **+5.21** `[-12.80, +23.25]` | +0.57 | 71.5% | `[12, 69, 133, 70, 16]` | OK | `SF9_minor_corrhist_conservative.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 10 | `forge_fixes` | `SF1_quiet_checks_tail` | `151-303-146` | **+2.90** `[-14.16, +19.97]` | +0.33 | 63.0% | `[12, 64, 141, 73, 10]` | OK | `SF1_quiet_checks_tail.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 11 | `forge_fixes` | `SF11_quiet_refutation_hist_triple_ext_600g_50k` | `144-315-141` | **+1.74** `[-13.81, +17.30]` | +0.22 | 58.7% | `[4, 75, 140, 76, 5]` | OK | `SF11_quiet_refutation_hist_triple_ext.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 12 | `forge_fixes` | `UCI_TtCutoffHistory1_600g_50k` | `137-328-135` | **+1.16** `[-15.01, +17.33]` | +0.14 | 55.6% | `[8, 69, 143, 73, 7]` | OK | `base_r15dsg.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 13 | `forge_fixes` | `SF4a_sf_rule50_damping` | `160-281-159` | **+0.58** `[-15.55, +16.71]` | +0.07 | 52.8% | `[6, 75, 138, 74, 7]` | OK | `SF4a_sf_rule50_damping.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 14 | `forge_fixes` | `SF12_rfp_corr_safety_600g_50k` | `147-299-154` | **-4.05** `[-19.28, +11.15]` | -0.52 | 30.1% | `[5, 73, 151, 66, 5]` | OK | `SF12_rfp_corr_safety.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 15 | `forge_fixes` | `SF2_no_see_quiet_checks` | `140-313-147` | **-4.05** `[-20.43, +12.30]` | -0.49 | 31.4% | `[9, 74, 138, 73, 6]` | OK | `SF2_no_see_quiet_checks.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 16 | `forge_fixes` | `UCI_AspFailHighReduce1_600g_50k` | `140-313-147` | **-4.05** `[-20.51, +12.38]` | -0.48 | 31.4% | `[8, 78, 133, 75, 6]` | OK | `base_r15dsg.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 17 | `forge_fixes` | `SF3_qs_see_keep_checks_promos` | `136-317-147` | **-6.37** `[-23.21, +10.44]` | -0.74 | 22.9% | `[8, 79, 141, 60, 12]` | OK | `SF3_qs_see_keep_checks_promos.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 18 | `forge_fixes` | `W2_proto_3_lmr_refinements_600g_50k` | `136-317-147` | **-6.37** `[-21.84, +9.08]` | -0.81 | 20.9% | `[6, 76, 145, 69, 4]` | OK | `proto_3_lmr_refinements.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 19 | `forge_fixes` | `W2_proto_4_qs_pruning_600g_50k` | `141-305-154` | **-7.53** `[-24.68, +9.58]` | -0.86 | 19.4% | `[10, 82, 127, 73, 8]` | OK | `proto_4_qs_pruning.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 20 | `forge_fixes` | `SF7_failsoft_futility_caphist_see` | `129-318-153` | **-13.90** `[-30.45, +2.58]` | -1.65 | 4.9% | `[8, 86, 136, 62, 8]` | OK | `SF7_failsoft_futility_caphist_see.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 21 | `forge_fixes` | `UCI_EvasionOrdering_600g_50k` | `135-303-162` | **-15.65** `[-30.99, -0.36]` | -2.01 | 2.2% | `[7, 80, 150, 59, 4]` | OK | `base_r15dsg.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 22 | `forge_fixes` | `SF4b2_v3_endgame_plus_sf_mat` | `140-286-174` | **-19.71** `[-36.22, -3.29]` | -2.35 | 0.9% | `[10, 87, 136, 61, 6]` | OK | `SF4b2_v3_endgame_plus_sf_mat.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 23 | `forge_fixes` | `SF5a_corrhist_gravity_step` | `89-252-259` | **-101.21** `[-119.74, -83.22]` | -11.50 | 0.0% | `[38, 124, 112, 22, 4]` | OK | `SF5a_corrhist_gravity_step.exe` (`none`) vs `base_r15dsg.exe` (`none`) |
| 24 | `forge_fixes` | `SF16_tt_pv_replace_cap_malus_600g_50k` | `154-292-154` | **-0.00** `[-16.17, +16.17]` | +0.00 | 50.0% | `[7, 75, 134, 79, 5]` | OK | `SF16_tt_pv_replace_cap_malus.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 25 | `forge_fixes` | `W2_proto_2_singular_multicut_600g_50k` | `140-320-140` | **-0.00** `[-15.93, +15.93]` | +0.00 | 50.0% | `[6, 77, 131, 83, 3]` | OK | `proto_2_singular_multicut.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |

### Table B: Independent Confirmations & Declared Matches (`28 x 1,000g @ 50k nodes`) — Decision-Grade `50k` Evidence
| # | Group | Match Name | W–D–L | Elo `[95% CI]` | z | LOS% | Ptnml | Clean | Candidate vs Base |
|---:|---|---|---|---:|---:|---:|---|---|---|
| 1 | `forge_fixes` | `G3b_skipnoisy_vs_G3a_keepnoisy_1000g_50k` | `972-21-7` | **+699.72** `[+642.27, +784.63]` | +141.30 | 100.0% | `[0, 0, 7, 21, 472]` | OK | `v3p_fused_v3_engine.exe` (`G3b_cc0_skip_noisy`) vs `v3p_fused_v3_engine.exe` (`G3a_cc0_keep_noisy`) |
| 2 | `forge_fixes` | `G3b_skipnoisy_vs_G3a_eqret_1000g_50k` | `967-20-13` | **+651.27** `[+597.55, +727.83]` | +115.77 | 100.0% | `[0, 0, 13, 20, 467]` | OK | `v3p_fused_v3_engine.exe` (`G3b_cc0_skip_noisy`) vs `v3p_fused_v3_engine.exe` (`G3a_cc0_keep_noisy_eqret`) |
| 3 | `forge_fixes` | `G3_FULL25_vs_r0202_1000g_50k` | `298-468-234` | **+22.27** `[+8.64, +35.96]` | +3.21 | 99.9% | `[16, 98, 217, 144, 25]` | OK | `v3p_fused_v3_engine.exe` (`G3_FULL25_v3p_1024_cc0_anchored`) vs `base_r15dsg.exe` (`r0202`) |
| 4 | `forge_fixes` | `G2_1024p_vs_G1_768_1000g_50k` | `287-470-243` | **+15.30** `[+1.65, +28.99]` | +2.20 | 98.6% | `[12, 120, 204, 140, 24]` | OK | `v3p_engine.exe` (`G2_v3p_1024_pairwise_psqt`) vs `base_r15dsg.exe` (`G1_v3_selfdistill_mix85`) |
| 5 | `filter_quest` | `M_F0_base_vs_min_r203_n50k` | `364-298-338` | **+9.04** `[-8.22, +26.34]` | +1.03 | 84.8% | `[53, 91, 191, 107, 58]` | OK | `forge.exe` (`fq_f0_base_filter`) vs `forge.exe` (`fq_f0_min_integrity`) |
| 6 | `forge_fixes` | `LmrDeeper_alone_vs_base_1000g_50k` | `255-514-231` | **+8.34** `[-4.06, +20.76]` | +1.32 | 90.6% | `[5, 122, 234, 122, 17]` | OK | `base_r15dsg.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 7 | `forge_fixes` | `SF13_confirm_vs_base_1000g_50k` | `256-512-232` | **+8.34** `[-4.39, +21.10]` | +1.28 | 90.0% | `[9, 118, 231, 124, 18]` | OK | `SF13_qs_evasion_pruning.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 8 | `forge_fixes` | `W2_proto_1_corrhist_minor_confirm_1000g_50k` | `260-502-238` | **+7.64** `[-4.34, +19.65]` | +1.25 | 89.4% | `[10, 102, 256, 120, 12]` | OK | `proto_1_corrhist_minor.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 9 | `forge_fixes` | `M_W2_obm4_vs_noteach_1000g_50k` | `279-463-258` | **+7.30** `[-6.54, +21.16]` | +1.03 | 84.9% | `[21, 112, 213, 133, 21]` | OK | `base_r15dsg.exe` (`fq_w_ob_m4`) vs `base_r15dsg.exe` (`r12_noteach`) |
| 10 | `forge_fixes` | `SF8_alone_vs_base_1000g_50k` | `251-512-237` | **+4.86** `[-7.77, +17.51]` | +0.76 | 77.5% | `[9, 125, 222, 131, 13]` | OK | `SF8_conthist_6ply.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 11 | `forge_fixes` | `G3_FULL25_vs_r0067_1000g_50k` | `270-474-256` | **+4.86** `[-8.49, +18.23]` | +0.71 | 76.2% | `[18, 115, 218, 133, 16]` | OK | `v3p_fused_v3_engine.exe` (`G3_FULL25_v3p_1024_cc0_anchored`) vs `base_r15dsg.exe` (`r0067`) |
| 12 | `forge_fixes` | `V3P_SF6b_scaled_SF8_no4b1_vs_base_1000g_50k` | `234-545-221` | **+4.52** `[-8.18, +17.22]` | +0.70 | 75.7% | `[10, 125, 219, 134, 12]` | OK | `V3P_SF6b_scaled_SF8.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 13 | `forge_fixes` | `V3P_SF4b1_SF8_LmrDeeper_vs_base_1000g_50k` | `251-507-242` | **+3.13** `[-10.21, +16.48]` | +0.46 | 67.7% | `[16, 124, 210, 135, 15]` | OK | `V3P_SF4b1_SF8.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 14 | `filter_quest` | `M_W1_soft800_vs_noteach_n50k` | `276-450-274` | **+0.69** `[-13.21, +14.61]` | +0.10 | 53.9% | `[20, 126, 207, 126, 21]` | OK | `forge.exe` (`fq_w_soft800`) vs `forge.exe` (`r12_noteach`) |
| 15 | `forge_fixes` | `COMBO_v1_vs_base_1000g_50k` | `244-511-245` | **-0.35** `[-12.79, +12.10]` | -0.06 | 47.8% | `[8, 134, 218, 131, 9]` | OK | `V3P_SF_COMBO_v1.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 16 | `forge_fixes` | `SF15_confirm_vs_base_1000g_50k` | `238-523-239` | **-0.35** `[-12.75, +12.06]` | -0.06 | 47.8% | `[15, 112, 241, 123, 9]` | OK | `SF15_rfp_failsoft_blend.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 17 | `forge_fixes` | `COMBO_v2_SF8_SF13_LmrDeeper_1000g_50k` | `243-505-252` | **-3.13** `[-15.94, +9.68]` | -0.48 | 31.6% | `[15, 128, 216, 133, 8]` | OK | `COMBO_v2_SF8_SF13.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 18 | `forge_fixes` | `SF4b1_alone_vs_base_1000g_50k` | `234-519-247` | **-4.52** `[-17.04, +7.99]` | -0.71 | 23.9% | `[13, 126, 232, 119, 10]` | OK | `SF4b1_v3_endgame_scale.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 19 | `forge_fixes` | `V3P_SF4b1_SF6b_scaled_SF8_vs_base_1000g_50k` | `241-503-256` | **-5.21** `[-17.81, +7.37]` | -0.81 | 20.8% | `[12, 131, 228, 118, 11]` | OK | `V3P_SF4b1_SF6b_scaled_SF8_combo.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 20 | `filter_quest` | `M0d_cyc40_wd01_vs_ctrl_n50k` | `236-486-278` | **-14.60** `[-28.23, -1.02]` | -2.11 | 1.8% | `[18, 147, 214, 101, 20]` | OK | `forge.exe` (`r12_ablate_cyc40_wd01`) vs `forge.exe` (`r12_control`) |
| 21 | `forge_fixes` | `SF4b1_SF8_noDeeper_vs_base_1000g_50k` | `236-482-282` | **-15.99** `[-29.09, -2.95]` | -2.40 | 0.8% | `[20, 140, 214, 118, 8]` | OK | `SF4b1_SF8.exe` (`r0067`) vs `base_r15dsg.exe` (`r0067`) |
| 22 | `forge_fixes` | `G1_selfdistill_mix85_vs_r0067_1000g_50k` | `233-479-288` | **-19.13** `[-32.65, -5.67]` | -2.79 | 0.3% | `[25, 137, 219, 106, 13]` | OK | `base_r15dsg.exe` (`G1_v3_selfdistill_mix85`) vs `base_r15dsg.exe` (`r0067`) |
| 23 | `forge_fixes` | `G2_1024p_vs_r0067_1000g_50k` | `238-469-293` | **-19.13** `[-33.23, -5.09]` | -2.67 | 0.4% | `[28, 137, 218, 96, 21]` | OK | `v3p_engine.exe` (`G2_v3p_1024_pairwise_psqt`) vs `base_r15dsg.exe` (`r0067`) |
| 24 | `filter_quest` | `M0b_mix65_vs_ctrl_n50k` | `241-457-302` | **-21.22** `[-34.87, -7.64]` | -3.06 | 0.1% | `[25, 142, 217, 101, 15]` | OK | `forge.exe` (`r12_ablate_mix65`) vs `forge.exe` (`r12_control`) |
| 25 | `filter_quest` | `M0a_noteach_vs_ctrl_n50k` | `234-456-310` | **-26.46** `[-40.02, -12.98]` | -3.85 | 0.0% | `[27, 144, 220, 96, 13]` | OK | `forge.exe` (`r12_noteach`) vs `forge.exe` (`r12_control`) |
| 26 | `forge_fixes` | `M_SWA_swa12_24_40_vs_r12ctrl_1000g_50k` | `229-456-315` | **-29.95** `[-43.27, -16.72]` | -4.45 | 0.0% | `[26, 147, 226, 89, 12]` | OK | `base_r15dsg.exe` (`r12_control_swa12_24_40`) vs `base_r15dsg.exe` (`r12_control`) |
| 27 | `filter_quest` | `M0e_r12ctrl_vs_r0067_n50k` | `209-479-312` | **-35.91** `[-49.26, -22.67]` | -5.34 | 0.0% | `[25, 165, 206, 96, 8]` | OK | `forge.exe` (`r12_control`) vs `forge.exe` (`r0067`) |
| 28 | `filter_quest` | `M0c_bundle_r9_vs_ctrl_n50k` | `217-449-334` | **-40.84** `[-55.04, -26.77]` | -5.72 | 0.0% | `[38, 158, 196, 99, 9]` | OK | `forge.exe` (`r12_bundle_r9`) vs `forge.exe` (`r12_control`) |

### Table C: Higher-Node Decision Matches (`2 x 600g @ 250k nodes`) — Opus Point 3 Decision Evidence
| # | Group | Match Name | W–D–L | Elo `[95% CI]` | z | LOS% | Ptnml | Clean | Candidate vs Base |
|---:|---|---|---|---:|---:|---:|---|---|---|
| 1 | `forge_fixes` | `G3_FULL25_vs_r0067_600g_250k` | `165-308-127` | **+22.03** `[+5.88, +38.28]` | +2.68 | 99.6% | `[4, 60, 142, 82, 12]` | OK | `v3p_fused_v3_engine.exe` (`G3_FULL25_v3p_1024_cc0_anchored`) vs `base_r15dsg.exe` (`r0067`) |
| 2 | `forge_fixes` | `G3_FULL25_vs_r0202_600g_250k` | `152-295-153` | **-0.58** `[-16.30, +15.14]` | -0.07 | 47.1% | `[4, 81, 130, 82, 3]` | OK | `v3p_fused_v3_engine.exe` (`G3_FULL25_v3p_1024_cc0_anchored`) vs `base_r15dsg.exe` (`r0202`) |

### Explicitly Excluded Incomplete / Quarantined Match Directories
- `C:\nnue-lab\neon\forge_fixes\matches\SF32_qs_see1_futility_pruning_600g_50k`: Incomplete / no `summary.json`.
- `C:\nnue-lab\neon\forge_fixes\matches\SF5b_corrhist_plus_minor`: Incomplete / no `summary.json`.
- `C:\nnue-lab\neon\filter_quest\matches\M_SWA_ctrl_swa24_40_vs_ctrl_n50k`: Quarantined (failed `v3_model_check` `3.02 cp > 3 cp` on 1 FEN; no `summary.json`).

---

## 5. Open Debate Questions & Escalation Triggers (`HANDOFF_12H_DATA_QUALITY.md` § 12)

1. **Immediate Live-Loop Placement (Atomic 5-Surface Package):** Place `FORGENN3-P` (`V3P_pairwise_psqt_fused_v3.patch` + `forge_v3p.py` + `forge_train_v3p_loop_adapter.py` + `v3p_surface4a/4b` + `datagen_uci_parity_7_8_minimal.patch` + `dead_draws_20k_s5disjoint.fqs.z` + `won_endings_syzygy_20k.fqs.z` + `opening_ply012_anchors.fqs.z`) only after `G3_FULL25` clears Opus Point 3 `250k` & GPU-idle `2,000g @ 6+0.06` PGO confirmation.
2. **Tier-2 Filter Policy (Stage-2 `12` Matches):** Decide from `G3a` vs `G3b` (noisy policy), `G4a` (`--loss-pow 2.5`), `G4b` (`ob_reweight`), `EXP-F1`, `EXP-F2` (`first` vs `avg`), `EXP-W3` (soft weighting, `0` discarded), and `EXP-R1`/`R1b` (`16k` Forge rescoring `--prioritize-opp-castle`).
3. **Server-Day Net Width & King Buckets:** Evaluate `G5a/G5b/G5c` (`768p/kb8`, `1536p/kb8`, `1024p/kb16`) once `G3_FULL25` equal-time `6+0.06` PGO finishes.
4. **Search & TM Composition:** Queue Opus's zero-C++ `LmrDeeperShallower=true` SPRT `[0, 5]`, then place independently confirmed Round 1–14 wins 1-by-1 (respecting `SF38` vs `SF39` mutual exclusion and never stacking unconfirmed combos) followed by post-`G3` SPSA (`POST_G3_SPSA_RECIPE.md`).
5. **Owner-Gated Escalation:** Because `63.43%` (`503/793`) of `G3_FULL25_e40` `SF19` severe errors are quiet and `73.33%` persist at `400` nodes (`40.0%` resolved at `16k`), evaluate cross-architecture self-play + `random_multi_pv` vs external data policy if post-`G3` + search stack blunders remain high.
