# ADVICE: observed search-event frequencies

Search only; board/FEN setup excluded. Zero opportunities are undefined.
A frequency below 0.1% is advisory; it proves neither dead code nor strength.
Corpus limit: the specified 2,000 WAC/STS set is not available (no STS file exists on the PC); this run uses Sol's sealed substitute corpus: 300 WAC + 7 bench + 1,693 synthetic opening positions, 2,000 distinct. It is not a WAC/STS corpus.

## Bench depth 20

| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |
|---|---:|---|---:|---:|---|
| nodes | 12389307 | nodes | 12389307 | 100 | false |
| main_nodes | 7947037 | nodes | 12389307 | 64.144322 | false |
| qs_nodes | 4442270 | nodes | 12389307 | 35.855678 | false |
| eval_requests | 6931060 | nodes | 12389307 | 55.943888 | false |
| hce_computations | 6931060 | eval_requests | 6931060 | 100 | false |
| nnue_forward | 6931060 | eval_requests | 6931060 | 100 | false |
| nnue_refresh | 8 | nnue_forward | 6931060 | 0.00011542246 | true |
| tt_probes | 12369330 | nodes | 12389307 | 99.838756 | false |
| tt_hits | 4928579 | tt_probes | 12369330 | 39.845157 | false |
| tt_misses | 7440751 | tt_probes | 12369330 | 60.154843 | false |
| picker_visits | 38785201 | nodes | 12389307 | 313.05384 | false |
| picker_main_tt | 810282 | picker_visits | 38785201 | 2.0891525 | false |
| picker_generate_captures | 2319089 | picker_visits | 38785201 | 5.9793141 | false |
| picker_good_captures | 3088115 | picker_visits | 38785201 | 7.9620962 | false |
| picker_killer1 | 1696525 | picker_visits | 38785201 | 4.3741555 | false |
| picker_killer2 | 1454950 | picker_visits | 38785201 | 3.7513019 | false |
| picker_counter_move | 1426597 | picker_visits | 38785201 | 3.6781993 | false |
| picker_generate_quiets | 1340912 | picker_visits | 38785201 | 3.4572774 | false |
| picker_quiet_moves | 8231572 | picker_visits | 38785201 | 21.223487 | false |
| picker_bad_captures | 2326074 | picker_visits | 38785201 | 5.9973236 | false |
| picker_qs_tt | 73414 | picker_visits | 38785201 | 0.18928354 | false |
| picker_qs_generate | 2046665 | picker_visits | 38785201 | 5.2769225 | false |
| picker_qs_captures | 5432848 | picker_visits | 38785201 | 14.007528 | false |
| picker_evasion_tt | 159865 | picker_visits | 38785201 | 0.41218041 | false |
| picker_evasion_generate | 585273 | picker_visits | 38785201 | 1.5090111 | false |
| picker_evasions | 7793020 | picker_visits | 38785201 | 20.092767 | false |
| razor_checks | 5903273 | main_nodes | 7947037 | 74.282692 | false |
| razor_searches | 90431 | razor_checks | 5903273 | 1.531879 | false |
| razor_cutoffs | 85947 | razor_searches | 90431 | 95.041523 | false |
| probcut_checks | 2783428 | main_nodes | 7947037 | 35.024727 | false |
| probcut_searches | 61134 | probcut_checks | 2783428 | 2.1963564 | false |
| probcut_cutoffs | 47713 | probcut_searches | 61134 | 78.046586 | false |
| iir_checks | 3260942 | main_nodes | 7947037 | 41.033432 | false |
| iir_reductions | 100757 | iir_checks | 3260942 | 3.0898127 | false |
| lmp_checks | 6739389 | main_nodes | 7947037 | 84.803795 | false |
| lmp_activations | 813424 | lmp_checks | 6739389 | 12.069699 | false |
| futility_checks | 4827843 | main_nodes | 7947037 | 60.750227 | false |
| futility_prunes | 161187 | futility_checks | 4827843 | 3.338696 | false |
| capture_futility_checks | 1911546 | main_nodes | 7947037 | 24.053569 | false |
| history_checks | 4666656 | main_nodes | 7947037 | 58.721961 | false |
| history_prunes | 83218 | history_checks | 4666656 | 1.7832469 | false |
| quiet_see_checks | 4583438 | main_nodes | 7947037 | 57.674804 | false |
| quiet_see_prunes | 600643 | quiet_see_checks | 4583438 | 13.104639 | false |
| noisy_see_checks | 1911546 | main_nodes | 7947037 | 24.053569 | false |
| noisy_see_prunes | 830367 | noisy_see_checks | 1911546 | 43.439551 | false |
| qs_futility_checks | 3662581 | qs_nodes | 4442270 | 82.44841 | false |
| qs_futility_prunes | 1031402 | qs_futility_checks | 3662581 | 28.160524 | false |
| qs_see_checks | 2631179 | qs_nodes | 4442270 | 59.230506 | false |
| qs_see_prunes | 1305696 | qs_see_checks | 2631179 | 49.62399 | false |
| singular_checks | 9755002 | main_nodes | 7947037 | 122.75018 | false |
| singular_searches | 92597 | singular_checks | 9755002 | 0.94922584 | false |
| singular_extensions | 31393 | singular_searches | 92597 | 33.902826 | false |
| singular_double_extensions | 16464 | singular_searches | 92597 | 17.780274 | false |
| singular_cutoffs | 21770 | singular_searches | 92597 | 23.510481 | false |

Not a dead-feature row (disabled by default, so a zero count is expected):
- capture_futility_prunes: count 0 of 1911546 capture_futility_checks; tune::CaptureFutilityBase = 0 in the lock defaults (src/search.cpp); the prune requires CaptureFutilityBase > 0, the opportunity counter runs before that guard

## Corpus fixed work

| Event | Count | Denominator | Opportunities | Percent | Below 0.1% |
|---|---:|---|---:|---:|---|
| nodes | 19878446 | nodes | 19878446 | 100 | false |
| main_nodes | 10807249 | nodes | 19878446 | 54.366669 | false |
| qs_nodes | 9071197 | nodes | 19878446 | 45.633331 | false |
| eval_requests | 12076007 | nodes | 19878446 | 60.749251 | false |
| hce_computations | 12076007 | eval_requests | 12076007 | 100 | false |
| nnue_forward | 12076007 | eval_requests | 12076007 | 100 | false |
| nnue_refresh | 2000 | nnue_forward | 12076007 | 0.016561766 | true |
| tt_probes | 19742382 | nodes | 19878446 | 99.31552 | false |
| tt_hits | 6765190 | tt_probes | 19742382 | 34.267344 | false |
| tt_misses | 12977192 | tt_probes | 19742382 | 65.732656 | false |
| picker_visits | 65170909 | nodes | 19878446 | 327.8471 | false |
| picker_main_tt | 1279259 | picker_visits | 65170909 | 1.9629295 | false |
| picker_generate_captures | 3725358 | picker_visits | 65170909 | 5.7162898 | false |
| picker_good_captures | 5787026 | picker_visits | 65170909 | 8.8797687 | false |
| picker_killer1 | 2585242 | picker_visits | 65170909 | 3.966865 | false |
| picker_killer2 | 2239319 | picker_visits | 65170909 | 3.4360715 | false |
| picker_counter_move | 2209204 | picker_visits | 65170909 | 3.3898622 | false |
| picker_generate_quiets | 2079643 | picker_visits | 65170909 | 3.1910603 | false |
| picker_quiet_moves | 10687397 | picker_visits | 65170909 | 16.39903 | false |
| picker_bad_captures | 3870829 | picker_visits | 65170909 | 5.9395044 | false |
| picker_qs_tt | 96924 | picker_visits | 65170909 | 0.1487228 | false |
| picker_qs_generate | 3982142 | picker_visits | 65170909 | 6.1103061 | false |
| picker_qs_captures | 10065115 | picker_visits | 65170909 | 15.444184 | false |
| picker_evasion_tt | 290664 | picker_visits | 65170909 | 0.44600268 | false |
| picker_evasion_generate | 1036271 | picker_visits | 65170909 | 1.5900822 | false |
| picker_evasions | 15236516 | picker_visits | 65170909 | 23.379321 | false |
| razor_checks | 8362013 | main_nodes | 10807249 | 77.374113 | false |
| razor_searches | 86018 | razor_checks | 8362013 | 1.0286758 | false |
| razor_cutoffs | 81796 | razor_searches | 86018 | 95.091725 | false |
| probcut_checks | 4010704 | main_nodes | 10807249 | 37.111239 | false |
| probcut_searches | 37973 | probcut_checks | 4010704 | 0.94679139 | false |
| probcut_cutoffs | 29214 | probcut_searches | 37973 | 76.933611 | false |
| iir_checks | 5179822 | main_nodes | 10807249 | 47.929145 | false |
| iir_reductions | 95473 | iir_checks | 5179822 | 1.8431714 | false |
| lmp_checks | 11768552 | main_nodes | 10807249 | 108.89498 | false |
| lmp_activations | 1774069 | lmp_checks | 11768552 | 15.074658 | false |
| futility_checks | 8044575 | main_nodes | 10807249 | 74.436843 | false |
| futility_prunes | 250266 | futility_checks | 8044575 | 3.1109909 | false |
| capture_futility_checks | 3723977 | main_nodes | 10807249 | 34.45814 | false |
| history_checks | 7794309 | main_nodes | 10807249 | 72.12112 | false |
| history_prunes | 1108 | history_checks | 7794309 | 0.0142155 | true |
| quiet_see_checks | 7793201 | main_nodes | 10807249 | 72.110867 | false |
| quiet_see_prunes | 1393703 | quiet_see_checks | 7793201 | 17.883576 | false |
| noisy_see_checks | 3723977 | main_nodes | 10807249 | 34.45814 | false |
| noisy_see_prunes | 1624941 | noisy_see_checks | 3723977 | 43.634561 | false |
| qs_futility_checks | 7098661 | qs_nodes | 9071197 | 78.254954 | false |
| qs_futility_prunes | 1175365 | qs_futility_checks | 7098661 | 16.557559 | false |
| qs_see_checks | 5923296 | qs_nodes | 9071197 | 65.297843 | false |
| qs_see_prunes | 2545923 | qs_see_checks | 5923296 | 42.981526 | false |
| singular_checks | 14521209 | main_nodes | 10807249 | 134.36545 | false |
| singular_searches | 39601 | singular_checks | 14521209 | 0.27271145 | false |
| singular_extensions | 26128 | singular_searches | 39601 | 65.978132 | false |
| singular_double_extensions | 7664 | singular_searches | 39601 | 19.353047 | false |
| singular_cutoffs | 5231 | singular_searches | 39601 | 13.209262 | false |

Not a dead-feature row (disabled by default, so a zero count is expected):
- capture_futility_prunes: count 0 of 3723977 capture_futility_checks; tune::CaptureFutilityBase = 0 in the lock defaults (src/search.cpp); the prune requires CaptureFutilityBase > 0, the opportunity counter runs before that guard

