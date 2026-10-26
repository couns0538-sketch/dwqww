# ADVICE: observed search-event frequencies

Search only; board/FEN setup excluded. Zero opportunities are undefined.
A frequency below 0.1% is advisory; it proves neither dead code nor strength.

## Bench depth 20

| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |
|---|---:|---|---:|---:|---|
| nodes | 11901452 | nodes | 11901452 | 100 | false |
| main_nodes | 6804758 | nodes | 11901452 | 57.175864 | false |
| qs_nodes | 5096694 | nodes | 11901452 | 42.824136 | false |
| eval_requests | 8129843 | nodes | 11901452 | 68.309673 | false |
| hce_computations | 8129843 | eval_requests | 8129843 | 100 | false |
| nnue_forward | 8129843 | eval_requests | 8129843 | 100 | false |
| nnue_refresh | 8 | nnue_forward | 8129843 | 9.8402884e-05 | true |
| tt_probes | 11889035 | nodes | 11901452 | 99.895668 | false |
| tt_hits | 3255106 | tt_probes | 11889035 | 27.37906 | false |
| tt_misses | 8633929 | tt_probes | 11889035 | 72.62094 | false |
| picker_visits | 40835592 | nodes | 11901452 | 343.11437 | false |
| picker_main_tt | 517493 | picker_visits | 40835592 | 1.2672597 | false |
| picker_generate_captures | 2497247 | picker_visits | 40835592 | 6.1153687 | false |
| picker_good_captures | 3438291 | picker_visits | 40835592 | 8.4198388 | false |
| picker_killer1 | 1636741 | picker_visits | 40835592 | 4.0081236 | false |
| picker_killer2 | 1386832 | picker_visits | 40835592 | 3.3961354 | false |
| picker_counter_move | 1360400 | picker_visits | 40835592 | 3.3314076 | false |
| picker_generate_quiets | 1259259 | picker_visits | 40835592 | 3.083729 | false |
| picker_quiet_moves | 6730177 | picker_visits | 40835592 | 16.481154 | false |
| picker_bad_captures | 2703190 | picker_visits | 40835592 | 6.619691 | false |
| picker_qs_tt | 70782 | picker_visits | 40835592 | 0.17333409 | false |
| picker_qs_generate | 2636809 | picker_visits | 40835592 | 6.4571343 | false |
| picker_qs_captures | 7371292 | picker_visits | 40835592 | 18.051145 | false |
| picker_evasion_tt | 96346 | picker_visits | 40835592 | 0.23593634 | false |
| picker_evasion_generate | 554601 | picker_visits | 40835592 | 1.3581314 | false |
| picker_evasions | 8576132 | picker_visits | 40835592 | 21.001611 | false |
| razor_checks | 5652264 | main_nodes | 6804758 | 83.063409 | false |
| razor_searches | 101383 | razor_checks | 5652264 | 1.7936706 | false |
| razor_cutoffs | 94583 | razor_searches | 101383 | 93.292761 | false |
| probcut_checks | 2838547 | main_nodes | 6804758 | 41.714151 | false |
| probcut_searches | 64759 | probcut_checks | 2838547 | 2.2814137 | false |
| probcut_cutoffs | 50025 | probcut_searches | 64759 | 77.24795 | false |
| iir_checks | 3178751 | main_nodes | 6804758 | 46.713652 | false |
| iir_reductions | 101016 | iir_checks | 3178751 | 3.1778519 | false |
| lmp_checks | 7570076 | main_nodes | 6804758 | 111.24681 | false |
| lmp_activations | 943220 | lmp_checks | 7570076 | 12.459848 | false |
| futility_checks | 5239894 | main_nodes | 6804758 | 77.003385 | false |
| futility_prunes | 208137 | futility_checks | 5239894 | 3.9721605 | false |
| capture_futility_checks | 2330182 | main_nodes | 6804758 | 34.243422 | false |
| capture_futility_prunes | 0 | capture_futility_checks | 2330182 | 0 | true |
| history_checks | 5031757 | main_nodes | 6804758 | 73.944687 | false |
| history_prunes | 149929 | history_checks | 5031757 | 2.979655 | false |
| quiet_see_checks | 4881828 | main_nodes | 6804758 | 71.74139 | false |
| quiet_see_prunes | 738910 | quiet_see_checks | 4881828 | 15.135929 | false |
| noisy_see_checks | 2330182 | main_nodes | 6804758 | 34.243422 | false |
| noisy_see_prunes | 1147117 | noisy_see_checks | 2330182 | 49.228644 | false |
| qs_futility_checks | 5145987 | qs_nodes | 5096694 | 100.96716 | false |
| qs_futility_prunes | 1575617 | qs_futility_checks | 5145987 | 30.618363 | false |
| qs_see_checks | 3570370 | qs_nodes | 5096694 | 70.052666 | false |
| qs_see_prunes | 1828209 | qs_see_checks | 3570370 | 51.205029 | false |
| singular_checks | 8842704 | main_nodes | 6804758 | 129.94884 | false |
| singular_searches | 39951 | singular_checks | 8842704 | 0.45179619 | false |
| singular_extensions | 15412 | singular_searches | 39951 | 38.577257 | false |
| singular_double_extensions | 7406 | singular_searches | 39951 | 18.537709 | false |
| singular_cutoffs | 9512 | singular_searches | 39951 | 23.809166 | false |

## Corpus fixed work

| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |
|---|---:|---|---:|---:|---|
| nodes | 19881407 | nodes | 19881407 | 100 | false |
| main_nodes | 10768524 | nodes | 19881407 | 54.163792 | false |
| qs_nodes | 9112883 | nodes | 19881407 | 45.836208 | false |
| eval_requests | 12097858 | nodes | 19881407 | 60.85011 | false |
| hce_computations | 12097858 | eval_requests | 12097858 | 100 | false |
| nnue_forward | 12097858 | eval_requests | 12097858 | 100 | false |
| nnue_refresh | 2000 | nnue_forward | 12097858 | 0.016531852 | true |
| tt_probes | 19744171 | nodes | 19881407 | 99.309727 | false |
| tt_hits | 6743452 | tt_probes | 19744171 | 34.154141 | false |
| tt_misses | 13000719 | tt_probes | 19744171 | 65.845859 | false |
| picker_visits | 65317263 | nodes | 19881407 | 328.53441 | false |
| picker_main_tt | 1280554 | picker_visits | 65317263 | 1.9605139 | false |
| picker_generate_captures | 3725492 | picker_visits | 65317263 | 5.7036866 | false |
| picker_good_captures | 5781671 | picker_visits | 65317263 | 8.8516737 | false |
| picker_killer1 | 2580711 | picker_visits | 65317263 | 3.9510397 | false |
| picker_killer2 | 2232147 | picker_visits | 65317263 | 3.4173921 | false |
| picker_counter_move | 2201897 | picker_visits | 65317263 | 3.3710797 | false |
| picker_generate_quiets | 2070522 | picker_visits | 65317263 | 3.1699461 | false |
| picker_quiet_moves | 10630715 | picker_visits | 65317263 | 16.275506 | false |
| picker_bad_captures | 3856716 | picker_visits | 65317263 | 5.9045891 | false |
| picker_qs_tt | 98418 | picker_visits | 65317263 | 0.15067686 | false |
| picker_qs_generate | 4060188 | picker_visits | 65317263 | 6.2161025 | false |
| picker_qs_captures | 10222316 | picker_visits | 65317263 | 15.650252 | false |
| picker_evasion_tt | 290881 | picker_visits | 65317263 | 0.44533556 | false |
| picker_evasion_generate | 1037187 | picker_visits | 65317263 | 1.5879217 | false |
| picker_evasions | 15247848 | picker_visits | 65317263 | 23.344285 | false |
| razor_checks | 8326665 | main_nodes | 10768524 | 77.324107 | false |
| razor_searches | 87119 | razor_checks | 8326665 | 1.0462652 | false |
| razor_cutoffs | 82641 | razor_searches | 87119 | 94.859904 | false |
| probcut_checks | 4013244 | main_nodes | 10768524 | 37.268283 | false |
| probcut_searches | 37782 | probcut_checks | 4013244 | 0.94143292 | false |
| probcut_cutoffs | 29637 | probcut_searches | 37782 | 78.442115 | false |
| iir_checks | 5179043 | main_nodes | 10768524 | 48.09427 | false |
| iir_reductions | 93969 | iir_checks | 5179043 | 1.8144086 | false |
| lmp_checks | 11725286 | main_nodes | 10768524 | 108.8848 | false |
| lmp_activations | 1759825 | lmp_checks | 11725286 | 15.008802 | false |
| futility_checks | 8014965 | main_nodes | 10768524 | 74.42956 | false |
| futility_prunes | 260434 | futility_checks | 8014965 | 3.2493467 | false |
| capture_futility_checks | 3710321 | main_nodes | 10768524 | 34.455242 | false |
| capture_futility_prunes | 0 | capture_futility_checks | 3710321 | 0 | true |
| history_checks | 7754531 | main_nodes | 10768524 | 72.011085 | false |
| history_prunes | 993 | history_checks | 7754531 | 0.012805417 | true |
| quiet_see_checks | 7753538 | main_nodes | 10768524 | 72.001864 | false |
| quiet_see_prunes | 1382091 | quiet_see_checks | 7753538 | 17.825295 | false |
| noisy_see_checks | 3710321 | main_nodes | 10768524 | 34.455242 | false |
| noisy_see_prunes | 1612467 | noisy_see_checks | 3710321 | 43.458962 | false |
| qs_futility_checks | 7214612 | qs_nodes | 9112883 | 79.169369 | false |
| qs_futility_prunes | 1224194 | qs_futility_checks | 7214612 | 16.968258 | false |
| qs_see_checks | 5990418 | qs_nodes | 9112883 | 65.735706 | false |
| qs_see_prunes | 2581936 | qs_see_checks | 5990418 | 43.101099 | false |
| singular_checks | 14486752 | main_nodes | 10768524 | 134.52867 | false |
| singular_searches | 39092 | singular_checks | 14486752 | 0.26984655 | false |
| singular_extensions | 25864 | singular_searches | 39092 | 66.161875 | false |
| singular_double_extensions | 7510 | singular_searches | 39092 | 19.211092 | false |
| singular_cutoffs | 5058 | singular_searches | 39092 | 12.938709 | false |

