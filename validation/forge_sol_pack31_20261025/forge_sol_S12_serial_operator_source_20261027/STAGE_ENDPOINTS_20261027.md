# Prepared S12 stage endpoints

Each row is one selected finite invocation; all paths/argv/hashes are complete in `OPERATOR_STAGE_SEQUENCE_20261027.json`.

| Stage | Operation | Max s | Required endpoint status | Output basename |
|---|---|---:|---|---|
| Lprime-01 | baseline_Release_reuse_binding | read-only | PASS_BINDING_ONLY | Lprime_baseline_Release_arm.json |
| Lprime-02 | baseline_ASAN_reuse_binding | read-only | PASS_BINDING_ONLY | Lprime_baseline_ASAN_arm.json |
| Lprime-03 | candidate_Release_OFF_build | 900 | PASS_BUILD_ONLY | Lprime_candidate_Release_OFF_build |
| Lprime-04 | candidate_Release_OFF_FIRST_bare11 | 120 | PASS | Lprime_candidate_Release_OFF_build_FIRST |
| Lprime-05 | candidate_Release_OFF_FULL_runtime_OFF | 600 | PASS | Lprime_candidate_Release_OFF_build_FULL |
| Lprime-06 | candidate_Release_OFF_binding | read-only | PASS_BINDING_ONLY | Lprime_candidate_Release_OFF_arm.json |
| Lprime-07 | candidate_Release_ON_build | 900 | PASS_BUILD_ONLY | Lprime_candidate_Release_ON_build |
| Lprime-08 | candidate_Release_ON_FIRST_bare11 | 120 | PASS | Lprime_candidate_Release_ON_build_FIRST |
| Lprime-09 | candidate_Release_ON_FULL_runtime_OFF | 600 | PASS | Lprime_candidate_Release_ON_build_FULL |
| Lprime-10 | candidate_Release_ON_binding | read-only | PASS_BINDING_ONLY | Lprime_candidate_Release_ON_arm.json |
| Lprime-11 | candidate_Release_ON_reviewed_feature | 600 | PASS | Lprime_Release_ON_feature_v2 |
| Lprime-12 | baseline_Release_helpers_build | 180 | PASS_COMPILE_ONLY | Lprime_baseline_Release_helpers |
| Lprime-13 | candidate_Release_helpers_build | 180 | PASS_COMPILE_ONLY | Lprime_candidate_Release_helpers |
| Lprime-14 | baseline_Release_actual_regression_RED | 120 | PASS | Lprime_baseline_Release_actual_RED |
| Lprime-15 | candidate_Release_actual_regression_GREEN | 120 | PASS | Lprime_candidate_Release_actual_GREEN |
| Lprime-16 | candidate_Release_counter_all_five | 900 | PASS | Lprime_Release_counter_all5 |
| Lprime-17 | Release_actual_Worker_bounded_three_arm_parity | 600 | PASS_BOUNDED_ACTUAL_WORKER_PARITY | Lprime_actual_alias_parity |
| Lprime-18 | candidate_ASAN_ON_build | 900 | PASS_BUILD_ONLY | Lprime_candidate_ASAN_ON_build |
| Lprime-19 | candidate_ASAN_ON_FIRST_bare11 | 120 | PASS | Lprime_candidate_ASAN_ON_build_FIRST |
| Lprime-20 | candidate_ASAN_ON_FULL_runtime_OFF | 600 | PASS | Lprime_candidate_ASAN_ON_build_FULL |
| Lprime-21 | candidate_ASAN_ON_binding | read-only | PASS_BINDING_ONLY | Lprime_candidate_ASAN_ON_arm.json |
| Lprime-22 | candidate_ASAN_ON_reviewed_feature | 300 | PASS | Lprime_ASAN_ON_feature_v2 |
| Lprime-23 | baseline_ASAN_helpers_build | 180 | PASS_COMPILE_ONLY | Lprime_baseline_ASAN_helpers |
| Lprime-24 | candidate_ASAN_helpers_build | 180 | PASS_COMPILE_ONLY | Lprime_candidate_ASAN_helpers |
| Lprime-25 | baseline_ASAN_actual_regression_RED | 120 | PASS | Lprime_baseline_ASAN_actual_RED |
| Lprime-26 | candidate_ASAN_actual_regression_GREEN | 120 | PASS | Lprime_candidate_ASAN_actual_GREEN |
| B-01 | baseline_Release_reuse_binding | read-only | PASS_BINDING_ONLY | B_baseline_Release_arm.json |
| B-02 | baseline_ASAN_reuse_binding | read-only | PASS_BINDING_ONLY | B_baseline_ASAN_arm.json |
| B-03 | candidate_Release_OFF_build | 900 | PASS_BUILD_ONLY | B_candidate_Release_OFF_build |
| B-04 | candidate_Release_OFF_FIRST_bare11 | 120 | PASS | B_candidate_Release_OFF_build_FIRST |
| B-05 | candidate_Release_OFF_FULL_runtime_OFF | 600 | PASS | B_candidate_Release_OFF_build_FULL |
| B-06 | candidate_Release_OFF_binding | read-only | PASS_BINDING_ONLY | B_candidate_Release_OFF_arm.json |
| B-07 | candidate_Release_ON_build | 900 | PASS_BUILD_ONLY | B_candidate_Release_ON_build |
| B-08 | candidate_Release_ON_FIRST_bare11 | 120 | PASS | B_candidate_Release_ON_build_FIRST |
| B-09 | candidate_Release_ON_FULL_runtime_OFF | 600 | PASS | B_candidate_Release_ON_build_FULL |
| B-10 | candidate_Release_ON_binding | read-only | PASS_BINDING_ONLY | B_candidate_Release_ON_arm.json |
| B-11 | candidate_Release_ON_reviewed_feature | 600 | PASS | B_Release_ON_feature_v2 |
| B-12 | baseline_Release_helpers_build | 180 | PASS_COMPILE_ONLY | B_baseline_Release_helpers |
| B-13 | candidate_Release_helpers_build | 180 | PASS_COMPILE_ONLY | B_candidate_Release_helpers |
| B-14 | baseline_Release_actual_regression_RED | 120 | PASS | B_baseline_Release_actual_RED |
| B-15 | candidate_Release_actual_regression_GREEN | 120 | PASS | B_candidate_Release_actual_GREEN |
| B-16 | candidate_Release_counter_all_five | 900 | PASS | B_Release_counter_all5 |
| B-17 | Release_actual_Worker_bounded_three_arm_parity | 600 | PASS_BOUNDED_ACTUAL_WORKER_PARITY | B_actual_alias_parity |
| B-18 | candidate_ASAN_ON_build | 900 | PASS_BUILD_ONLY | B_candidate_ASAN_ON_build |
| B-19 | candidate_ASAN_ON_FIRST_bare11 | 120 | PASS | B_candidate_ASAN_ON_build_FIRST |
| B-20 | candidate_ASAN_ON_FULL_runtime_OFF | 600 | PASS | B_candidate_ASAN_ON_build_FULL |
| B-21 | candidate_ASAN_ON_binding | read-only | PASS_BINDING_ONLY | B_candidate_ASAN_ON_arm.json |
| B-22 | candidate_ASAN_ON_reviewed_feature | 300 | PASS | B_ASAN_ON_feature_v2 |
| B-23 | baseline_ASAN_helpers_build | 180 | PASS_COMPILE_ONLY | B_baseline_ASAN_helpers |
| B-24 | candidate_ASAN_helpers_build | 180 | PASS_COMPILE_ONLY | B_candidate_ASAN_helpers |
| B-25 | baseline_ASAN_actual_regression_RED | 120 | PASS | B_baseline_ASAN_actual_RED |
| B-26 | candidate_ASAN_actual_regression_GREEN | 120 | PASS | B_candidate_ASAN_actual_GREEN |
