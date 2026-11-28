# Patch Audit Matrix (Teamwork Wave 4 — Stream C)

> Verified via `C:\nnue-lab\neon\forge_fixes\teamwork_wave4\streamC_handoff_reaudit\verify_all_patches_w4.py` (plain `git apply --check` across all **5** patch folders against clean base trees, zero live modifications).

## Summary

- **Total Patches Verified:** `63/63` (`RC=0`) — `+10` new patches in `forge_fixes/patches` since the early 53-patch survey (`53 -> 63`), and `+19` total since Wave 3's 3-folder `44/44` audit (`+15` in `forge_fixes/patches`, `+2` in `wave3`, `+2` in `wave4`).
- **`forge_fixes/patches`:** `47/47` PASS (`RC=0`)
- **`wave2/streamA_search/patches`:** `9/9` PASS (`RC=0`)
- **`wave3/streamA_search_packets/patches`:** `2/2` PASS (`RC=0`)
- **`wave4/streamA_search_packets/patches`:** `2/2` PASS (`RC=0`)
- **`filter_quest/patches`:** `3/3` PASS (`RC=0`)
- **`datagen_uci_startpos_only.patch` Temp-Copy Test:** **PASS** (isolated `_work_patchtest_*` copy inside `streamC_handoff_reaudit\`, cleaned up in `finally:`)
- **5-Patch Stacked Check (`V3P_pairwise_psqt_fused + SF8 + SF20 + proto_7 + proto_8`):** **PASS** (direct `git apply --check RC=0` AND sequential isolated `_work_stacktest_*` `git apply` `5/5 RC=0`, cleaned up in `finally:`)

## Complete Patch Verification Matrix (63 Patches)

| # | Group | Patch File | Lines | Bytes | Git Root | Target Files | Full SHA-256 | `git apply --check` |
|---:|---|---|---:|---:|---|---|---|---|
| 1 | `forge_fixes/patches` | `COMBO_v2_SF8_SF13.patch` | 84 | 4697 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `98840d3606ef5f77a3555e69fd6f19fecee9682cb07aa470f58f17968cc6ae5d` | PASS (`RC=0`) |
| 2 | `forge_fixes/patches` | `datagen_uci_cc0_parity.patch` | 105 | 5372 | `C:\nnue-lab` | `pipeline/nnloop/datagen_uci.py` | `5b8bba1c416bad446437c2415573428b04c8ea5952be1af403cfef3a6ba1726d` | PASS (`RC=0`) |
| 3 | `forge_fixes/patches` | `datagen_uci_startpos_only.patch` | 78 | 3816 | `C:\nnue-lab` | `pipeline/nnloop/datagen_uci.py` | `c0c92cb75a56b8a5e0d9670befd6509e21a912ac6facf2124e62e1734494eba8` | PASS (`RC=0`) |
| 4 | `forge_fixes/patches` | `SF11_quiet_refutation_hist_triple_ext.patch` | 21 | 1193 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `769a4f7a5c8786c70a9d40507b77e3918623d5aceb2cd8dbd58e4084f9cd5478` | PASS (`RC=0`) |
| 5 | `forge_fixes/patches` | `SF12_rfp_corr_safety.patch` | 14 | 856 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `45d0f67a09b9cedea4e0793bbb10b72cef3e2276c15e74f06070d5e951512f29` | PASS (`RC=0`) |
| 6 | `forge_fixes/patches` | `SF13_qs_evasion_pruning.patch` | 28 | 1584 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `63eb3288af4712a7d641035177e561448e6fc94041d8ee916776ab3fced6b6e4` | PASS (`RC=0`) |
| 7 | `forge_fixes/patches` | `SF14_lmr_ttpv_cutnode_ext.patch` | 21 | 1180 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `8b2208d07d14090dfe5759126c0870a87fb4faa6036ce84c8fce7a61da29830d` | PASS (`RC=0`) |
| 8 | `forge_fixes/patches` | `SF15_rfp_failsoft_blend.patch` | 11 | 501 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `826e49e15407ee62e528c86e41297d964c97d55ae88f58f8f2e2948669863b81` | PASS (`RC=0`) |
| 9 | `forge_fixes/patches` | `SF16_tt_pv_replace_cap_malus.patch` | 36 | 2280 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `54e26991d3fdaa476de541bee9d95044f07b092af379eddc0de44ce177aae240` | PASS (`RC=0`) |
| 10 | `forge_fixes/patches` | `SF17_tm_bestmove_avg_eval.patch` | 68 | 3434 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `d7aaf51cde99336b021a87f38bab7b119a702f5cb96cd036d8bedd8ccfb7b88c` | PASS (`RC=0`) |
| 11 | `forge_fixes/patches` | `SF18_tm_ply_curve.patch` | 34 | 1712 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `4b87a33856f12c14336323e102fbb62ea42ef2497873065c1f4b86cfe4f2f041` | PASS (`RC=0`) |
| 12 | `forge_fixes/patches` | `SF19_capture_history_see_prune.patch` | 12 | 638 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `e4ee3e9039d0b5c1110e1788938ee11e732828bfb2d820a49f135cb91e3deb3f` | PASS (`RC=0`) |
| 13 | `forge_fixes/patches` | `SF1_quiet_checks_tail.patch` | 20 | 1164 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `30da31c1b310fdfa4911bed823c2e1e43689807aeff3ca6a4521913a84caedd3` | PASS (`RC=0`) |
| 14 | `forge_fixes/patches` | `SF20_killer_lmr_relief.patch` | 15 | 830 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `44b74785d72c119a5f22d09b33a63226379d08c36d5fec0542f71d088246c825` | PASS (`RC=0`) |
| 15 | `forge_fixes/patches` | `SF21_corrhist_gravity_clean.patch` | 11 | 669 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `157a5407d4b029ffc967c470c3c4b8c0e3bd00986a4c27def1c3c7b796712a72` | PASS (`RC=0`) |
| 16 | `forge_fixes/patches` | `SF22_low_ply_history.patch` | 86 | 4599 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `83d26808e1251d2d19aaa7fbf2c31f62b3643efc9b3cf7b0d7347ee2da9e6229` | PASS (`RC=0`) |
| 17 | `forge_fixes/patches` | `SF23_capture_hist_badcap_lmr.patch` | 36 | 1912 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `a9f015d28ba40fb0bd262f68ebc2fc77cb744338e173872654860d6b7da66698` | PASS (`RC=0`) |
| 18 | `forge_fixes/patches` | `SF24_qs_evasion_pruning.patch` | 29 | 1693 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `0d7fedfd0a7c8324fd6db421db3c2026070e1c13d08025a2916bb0659b3d5a8c` | PASS (`RC=0`) |
| 19 | `forge_fixes/patches` | `SF25_faillow_prior_move_hist.patch` | 34 | 2168 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `4617216e6cddb66052ba5b01174a19600e714b0195f75b345efa1a7c1cdb1996` | PASS (`RC=0`) |
| 20 | `forge_fixes/patches` | `SF26_cutoff_surprise_hist_depth.patch` | 18 | 1118 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `20875f4e37743df312274458ef07e20fb1c3018ef24f9fec7bf1a687c106fdf9` | PASS (`RC=0`) |
| 21 | `forge_fixes/patches` | `SF27_goodcap_caphist_see_threshold.patch` | 51 | 2306 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `342e838e44a7326b550b4be75998104926fa9e794d65c896ccb45c0fa4106826` | PASS (`RC=0`) |
| 22 | `forge_fixes/patches` | `SF28_qs_evasion_tight_and_standpat_ttpv.patch` | 40 | 2420 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `45252132c8615e269c667b97fc10b1d77c01648fb505723afea3af4e7dee7b77` | PASS (`RC=0`) |
| 23 | `forge_fixes/patches` | `SF29_lmr_pv_ext_and_eval_diff.patch` | 35 | 2167 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `d89dcd817b9930abafd43b56256bfb446b76660377c1f45bdaf2c5e66b59679e` | PASS (`RC=0`) |
| 24 | `forge_fixes/patches` | `SF2_no_see_quiet_checks.patch` | 11 | 569 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `246bafa8c8d378c980253c4082b3ae6651bd8d9257fa59a56045c06901e458b3` | PASS (`RC=0`) |
| 25 | `forge_fixes/patches` | `SF30_probcut_tt_and_corrhist_promo_fix.patch` | 28 | 1814 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `092f8f2145eb5cabf916baeb495afdd995fbcb0d737c310ba8c55eca1cc3960f` | PASS (`RC=0`) |
| 26 | `forge_fixes/patches` | `SF31_singular_triple_ext_and_neg_ext.patch` | 33 | 1629 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `51dd9dcc0736019018246cadb7d196dbf034e90f85a91dee4a2c1a5fd5358e03` | PASS (`RC=0`) |
| 27 | `forge_fixes/patches` | `SF32_qs_see1_futility_pruning.patch` | 16 | 991 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `57ed10e7cf383d2345fdab6c41214ddda938f53d32bfdd374483d78e16a31b7b` | PASS (`RC=0`) |
| 28 | `forge_fixes/patches` | `SF33_qs_overhaul_SF13_plus_SF32.patch` | 40 | 2236 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `6c6a32a6347692ba39f42fde1c010cee04ee0a52d724767f6fa56ba016c9a92e` | PASS (`RC=0`) |
| 29 | `forge_fixes/patches` | `SF3_qs_see_keep_checks_promos.patch` | 11 | 457 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `2cac0b9fa820facc0c1a54594e7fc0f1aab68cfb4b2f77cd704450f4b9de4365` | PASS (`RC=0`) |
| 30 | `forge_fixes/patches` | `SF4a_sf_rule50_damping.patch` | 30 | 1410 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `5a08258ad32b9cf007de9535aa108a51b41c38d0c2bce3e4ab0cfb486f26d339` | PASS (`RC=0`) |
| 31 | `forge_fixes/patches` | `SF4b1_v3_endgame_scale.patch` | 61 | 2335 | `C:\nnue-lab\forge\r15dsg` | `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `c518784783300ff3b094eecd67bcc78b339eb3dd158ae8d08a74979e232037c7` | PASS (`RC=0`) |
| 32 | `forge_fixes/patches` | `SF4b2_v3_endgame_plus_sf_mat.patch` | 67 | 2827 | `C:\nnue-lab\forge\r15dsg` | `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `dc4f53f51dfe36fab0d0800cf993a1f05446b3822a8fc3c7b7d36484d5369e24` | PASS (`RC=0`) |
| 33 | `forge_fixes/patches` | `SF5a_corrhist_gravity_step.patch` | 61 | 3650 | `C:\nnue-lab\forge\r15dsg` | `include/forge/b4.hpp`, `include/forge/search.hpp`, `src/search.cpp` | `4d12f624b6e11f3455b1e6162b8b0b18fc49c96d905461534d7bfebc3477665f` | PASS (`RC=0`) |
| 34 | `forge_fixes/patches` | `SF5b_corrhist_plus_minor.patch` | 119 | 6786 | `C:\nnue-lab\forge\r15dsg` | `include/forge/b4.hpp`, `include/forge/search.hpp`, `src/search.cpp` | `77200c932b07625cd4838e017a839e86fc42d5ad8a69146f6cc7ee4b303524b5` | PASS (`RC=0`) |
| 35 | `forge_fixes/patches` | `SF6_lmr_fractional_caphist.patch` | 74 | 4100 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `41f598471de6bf600fee0e837bd907ba32e5db5370207ff489f48b1aa4d74337` | PASS (`RC=0`) |
| 36 | `forge_fixes/patches` | `SF7_failsoft_futility_caphist_see.patch` | 20 | 1141 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `03ee6325036e77a9b8d94965c992c9e74b3cefea88ff401405afcbf34e2333ec` | PASS (`RC=0`) |
| 37 | `forge_fixes/patches` | `SF8_conthist_6ply.patch` | 58 | 3155 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `62dcf1f3da0ac212a3807e59eb61e144b3705ea2a8a716b70a391e81af4c8779` | PASS (`RC=0`) |
| 38 | `forge_fixes/patches` | `SF9_minor_corrhist_conservative.patch` | 70 | 3683 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `2e79f0c92e188e3b178c78b1219c62086e660977422003f1199aaace7413caca` | PASS (`RC=0`) |
| 39 | `forge_fixes/patches` | `STACK_V3Pv3_SF13_SF8_W2P1.patch` | 896 | 54707 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `include/forge/search.hpp`, `src/nnue_v3.cpp`, `src/search.cpp` | `f441957d44396bd022bbdb0dc723416af23d0921c5230d3aa3926431bccff0d8` | PASS (`RC=0`) |
| 40 | `forge_fixes/patches` | `V3P_pairwise_psqt.patch` | 494 | 28982 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp` | `061fdb2a012023350b35b6a83ebe8bc1e1baf4f6eec85452b7d9a1db97cfb36a` | PASS (`RC=0`) |
| 41 | `forge_fixes/patches` | `V3P_pairwise_psqt_fused.patch` | 681 | 45469 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp` | `fd4de7de9df6f0b3fa7a85a25dc35328feb75c3ea580098fe447d30ab86fa8be` | PASS (`RC=0`) |
| 42 | `forge_fixes/patches` | `V3P_pairwise_psqt_fused_v3.patch` | 679 | 43075 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp` | `57f3455f185463cfa7859727da9c6a91bcaadb3934da4492a6e78029dcaac763` | PASS (`RC=0`) |
| 43 | `forge_fixes/patches` | `V3P_SF4b1_SF6_SF8.patch` | 683 | 38488 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `e4b5847de48258d91ba40fc01864a36da02d9e14ce16890bb47fbf6474155ca4` | PASS (`RC=0`) |
| 44 | `forge_fixes/patches` | `V3P_SF4b1_SF8.patch` | 611 | 34430 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `ad0a57091a281b437fff2ee18549dfacfc1aae033710aa5906017e4f5789f9a1` | PASS (`RC=0`) |
| 45 | `forge_fixes/patches` | `V3P_SF6b_scaled_SF8.patch` | 617 | 35884 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `src/search.cpp` | `fdc4d3244a16c20aabf7d10f07068e05e7a67a9f9e5bbfad2bafaa985fcb273f` | PASS (`RC=0`) |
| 46 | `forge_fixes/patches` | `V3P_SF8.patch` | 552 | 32137 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `src/search.cpp` | `2d2385838ded31aa4a2590870edc2835ea044b5b770245ff0dc4c35755c02c34` | PASS (`RC=0`) |
| 47 | `forge_fixes/patches` | `V3P_SF_COMBO_v1.patch` | 728 | 40958 | `C:\nnue-lab\forge\r15dsg` | `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp`, `include/forge/search.hpp` | `c3fbffd857130df9dd9354151714446d05268435f6582d86d309e38c2427adb1` | PASS (`RC=0`) |
| 48 | `wave2/streamA_search/patches` | `proto_1_corrhist_minor.patch` | 139 | 7602 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `e1cd152b4d78cd7880f55dd8967eb561fe246fe5773232ce22825df5b2071b14` | PASS (`RC=0`) |
| 49 | `wave2/streamA_search/patches` | `proto_2_singular_multicut.patch` | 81 | 4321 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `77a6fdf61657158b35523d2476b395d3f2e3e808c939e3035f328a47b659b014` | PASS (`RC=0`) |
| 50 | `wave2/streamA_search/patches` | `proto_3_lmr_refinements.patch` | 99 | 5833 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `d037dceef60e95894f13d9c8c1506471f3e818c68708af0347e4429875907126` | PASS (`RC=0`) |
| 51 | `wave2/streamA_search/patches` | `proto_4_qs_pruning.patch` | 55 | 2995 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `f36c9c990c70eb607252bb583fa4c0e63ee494420a9e07e1781827a1c39e99e3` | PASS (`RC=0`) |
| 52 | `wave2/streamA_search/patches` | `SF4b1_SF6b_quiet_only_SF8_combo.patch` | 196 | 10229 | `C:\nnue-lab\forge\r15dsg` | `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `4aebad3c42abfb8ddd2617643a486cd409b0baeeed8b5a0216548f6439c44d47` | PASS (`RC=0`) |
| 53 | `wave2/streamA_search/patches` | `SF4b1_SF6b_scaled_SF8_combo.patch` | 196 | 10242 | `C:\nnue-lab\forge\r15dsg` | `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `19dbfd32888eb61cbe097332c5d287a7411e272cc98a419fdb75e0bdbf4225c2` | PASS (`RC=0`) |
| 54 | `wave2/streamA_search/patches` | `SF4b1_SF8.patch` | 123 | 6051 | `C:\nnue-lab\forge\r15dsg` | `include/forge/eval.hpp`, `src/eval.cpp`, `src/search.cpp` | `f15348e7e533991de27cf2295cd9417642ad13349c876fc3baf2e454a597d62f` | PASS (`RC=0`) |
| 55 | `wave2/streamA_search/patches` | `SF6b_quiet_only.patch` | 76 | 4271 | `C:\nnue-lab\forge\r15dsg` | `src/search.cpp` | `56feb2fd7a7815c19b8bbadd809211a8061cfc73957c1eec41c5101d6b8f182d` | PASS (`RC=0`) |
| 56 | `wave2/streamA_search/patches` | `V3P_SF4b1_SF6b_scaled_SF8_combo.patch` | 694 | 41353 | `C:\nnue-lab\forge\r15dsg` | `include/forge/eval.hpp`, `include/forge/nnue_v3.hpp`, `src/eval.cpp`, `src/nnue_v3.cpp`, `src/search.cpp` | `c2408f84447fa7a3457b4d434bb22ca044949b11e80b39429f68437b1a1455be` | PASS (`RC=0`) |
| 57 | `wave3/streamA_search_packets/patches` | `proto_5_hist_malus_lmp.patch` | 116 | 6149 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `c4d9336f1e347894056269cf7418520e65304ca874ffcec62c5d303044cf8be8` | PASS (`RC=0`) |
| 58 | `wave3/streamA_search_packets/patches` | `proto_6_nmp_probcut_refine.patch` | 88 | 5357 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `9a7a0bf51b9548f07ba4ee670b6353fd02e053f2686ed2129f248a5478a4b824` | PASS (`RC=0`) |
| 59 | `wave4/streamA_search_packets/patches` | `proto_7_ttpv_lmr_and_iir.patch` | 75 | 4172 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `6f08b20178def1d47c4c5c40cd1fd983426331d7d64a8b02cc86835dd9cb7bcb` | PASS (`RC=0`) |
| 60 | `wave4/streamA_search_packets/patches` | `proto_8_eval_lmp_and_capfut.patch` | 71 | 4958 | `C:\nnue-lab\forge\r15dsg` | `include/forge/search.hpp`, `src/search.cpp` | `1862cea0b89387be43bef0a74be9cda2bbf2a41ab6e3921406f93b385e62af63` | PASS (`RC=0`) |
| 61 | `filter_quest/patches` | `cache_key_t149.patch` | 46 | 2164 | `C:\nnue-lab` | `pipeline/forge_train.py` | `21180473548d5a15e640882de745239968689fc9f0e17274cec3939c55699088` | PASS (`RC=0`) |
| 62 | `filter_quest/patches` | `filterqc_integrity_telemetry.patch` | 122 | 5361 | `C:\nnue-lab` | `pipeline/nnloop/filterqc.py` | `0ade663d66a1f95fb5b34cf7a6c0fca5d4a94ddae37ae1530ccac591cf00546d` | PASS (`RC=0`) |
| 63 | `filter_quest/patches` | `selfgame_skipcheck_optin.patch` | 36 | 1258 | `C:\nnue-lab` | `forge/r15dsg/src/uci.cpp` | `424190468df17483519dd388afdd26d538cb4446923858b900300bd7808dc1c7` | PASS (`RC=0`) |

## Isolated Temp-Copy Verification: `datagen_uci_startpos_only.patch`

- **Patch:** `C:\nnue-lab\neon\forge_fixes\patches\datagen_uci_startpos_only.patch`
- **`git apply --check` (temp copy):** `RC=0`
- **`git apply` (temp copy):** `RC=0`
- **Check 1 — Fixed `sp_k=4` (never `k=0`!):**
  - With `startpos_random_move_count=4`: `{'startpos_games': 198, 'of_games': 2000, 'k_counts': {4: 198}}`
  - With `startpos_random_move_count` omitted (`rng.choice((3, 4))`): `{'startpos_games': 214, 'of_games': 2000, 'k_counts': {3: 105, 4: 109}}`
- **Check 2 — Zero legacy RNG drift when `startpos_frac=0` (and omitted):** `PASS (100/100 exact draws + rng.getstate() equal across legacy_k8, cc0_k2_sp0, legacy_k8_omitted)`
- **Check 3 — `selfgame_ok()` acceptance for fixed `k=2` CC0:** `{'cc0_k2_result': '', 'noncontiguous_guard': 'rejected', 'multipv_guard': 'rejected'}`

## 5-Patch Stacked Compatibility Check

- **Stack:** `V3P_pairwise_psqt_fused.patch + SF8_conthist_6ply.patch + SF20_killer_lmr_relief.patch + proto_7_ttpv_lmr_and_iir.patch + proto_8_eval_lmp_and_capfut.patch`
- **Touched Files (`C:\nnue-lab\forge\r15dsg`):** `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp`, `src/search.cpp`, `include/forge/search.hpp`
- **Direct `git -C C:\nnue-lab\forge\r15dsg apply --check`:** `RC=0`
- **Sequential Isolated `_work_stacktest_*` `git apply` Steps:**
  - `V3P_pairwise_psqt_fused.patch`: `check_rc=0`, `apply_rc=0`
  - `SF8_conthist_6ply.patch`: `check_rc=0`, `apply_rc=0`
  - `SF20_killer_lmr_relief.patch`: `check_rc=0`, `apply_rc=0`
  - `proto_7_ttpv_lmr_and_iir.patch`: `check_rc=0`, `apply_rc=0`
  - `proto_8_eval_lmp_and_capfut.patch`: `check_rc=0`, `apply_rc=0`

## Summary CLI Output (`verify_all_patches_w4.py`)

```text
PATCH_SUMMARY: 63/63 passed `git apply --check` (RC=0)
  - forge_fixes/patches: 47/47 PASS
  - wave2/streamA_search/patches: 9/9 PASS
  - wave3/streamA_search_packets/patches: 2/2 PASS
  - wave4/streamA_search_packets/patches: 2/2 PASS
  - filter_quest/patches: 3/3 PASS
DATAGEN_STARTPOS_TEMP_TEST: PASS | apply_check_rc=0 apply_rc=0 | sp_k4_default={'startpos_games': 214, 'of_games': 2000, 'k_counts': {3: 105, 4: 109}} | sp_k4_explicit={'startpos_games': 198, 'of_games': 2000, 'k_counts': {4: 198}} | rng_drift=0 | selfgame_ok_k2=''
V3P_STACK_CHECK: PASS | direct_rc=0 | sequential=5/5 RC=0
```
