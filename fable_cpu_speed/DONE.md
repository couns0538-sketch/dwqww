# DONE: verdict per item, with the evidence each one rests on

Job fable4cpu, branch `fable52-cpu-20261110`, base `16833ecc03b425586f91f4c8834dea8807bf4c22`. Logs are under `evidence/logs/`; their MD5 is in the list at the end of this file.

Words used: **DONE** = fully executed with committed evidence. **PASS** = the full planned count ran and nothing differed. **FAIL** = a reproduced defect or a failed required gate. **INCOMPLETE** = partial count. **BLOCKED** = a permission, capability or input is missing. **NOT RUN**. **UNVERIFIED** = claimed without committed evidence. **NO WIN** = no qualifying speed candidate.

## Items

| Item | Verdict | Planned and completed | Evidence |
|---|---|---|---|
| C0 preflight | DONE | per-CPU load and processes recorded before any build; heavy work started on the CPUs found free; no process of mine seen outside mask 0x707F | `preflight_001.txt`, `UTILIZATION.log`, `STATUS.md` |
| C1 build and freeze | DONE, pins MATCH | 13 of 13 pins; every freeze check OK; rebuild code-and-data identical to the lock exe | `freeze.log`, `clone.json`, `build_c29ctl.log`, `pins_c29ctl.log`, `bytecmp_lock_vs_c29ctl_r2.log` |
| C2 dup check | DONE for local sources; branch history UNVERIFIED | not a complete duplication check (no fetch allowed) | `DUPCHECK.md` |
| C3 profile | DONE | 2 of 2 valid runs, 20,265 samples, shares add to 100 %; second measurement under load, 21,545 samples | `profile_bench22_neton_quiet.log`, `profile_bench22_neton.log`, `profile_call_counts.log`, `nnue_update_codegen_excerpt.log`, `PROFILE.md` |
| C4 speed lane | NO WIN | four candidates built and timed; none at or above +2.0 % | tables below |
| C5 ASan | PASS | fixtures 8 of 8 as expected; full bench 10 of 10, node counts equal the pins, no report | `san_fixtures_r2.log`, `san_build_asan_r2.log`, `san_bench_asan_r2.log` (first link attempt: `san_build_asan.log`) |
| C5 UBSan | PASS | fixtures 8 of 8; full bench 10 of 10, node counts equal the pins, no report | `san_fixtures.log`, `san_build_ubsan.log`, `san_bench_ubsan.log` |
| C5 TSan | BLOCKED | the compiler refuses `-fsanitize=thread` for this target | `san_fixtures.log`, `san_fixtures_r2.log` |
| C5 determinism | PASS | 13,000 of 13,000 row comparisons equal (cold 8,000, warm 4,000, reset 1,000) | the eight `cmp_det_*.log` |
| C5 table stress | PASS | 480 of 480 row comparisons equal; ASan run 240 of 240 searches, no report | `cmp_tt_lock_on_1__vs__tt_lock_on_2.log`, `cmp_tt_lock_off_1__vs__tt_lock_off_2.log`, `ttstress_asan_on_1.rows.tsv` |
| Extra, not TSan | DONE | multi-thread fixed-node searches, Threads 2-9: 600 of 600, legal best moves, no report | `mt_asan_r2.log`, `mt_ubsan.log`, `mt_release_lock.log` |
| Checker self-tests | PASS | 10 of 10 bad or control fixtures handled as expected | `selftest_checkers.log` |
| C6 | NOT RUN | no permitted reader to test against | `README.md` |
| C7 | NOT RUN | no HalfKA source or s135 net available locally | `README.md` |

## C4 candidates

"12,000-position static-eval parity against the lock" is **BLOCKED (unobservable on the release exe)** for every candidate: the lock exe has no static-eval command. The harness comparison below is separate evidence from a test binary; it compares 12,000 positions x (flag 0, flag on) x (net on, net off) = 48,000 rows with the lock source's.

| Candidate, flag value timed | Applies on `16833ecc` | Pins flag 0 / flag on (net on and net off) | Flag-0 build vs lock rebuild | Harness | Screening vs lock: median of 12 pairs (min, max) | Release rows vs the real lock exe (extra) | Outcome |
|---|---|---|---|---|---|---|---|
| `FORGE_SPD_NNUE_FUSE_EVAL=1` | PASS, `patch_NNUE_FUSE_EVAL_apply.log` | 13 of 13 / 13 of 13, `pins_fuse_off.log`, `pins_fuse_on.log` | code-and-data identical, `bytecmp_c29ctl_vs_fuse_off.log` | 48,000 of 48,000 equal, `cmp_harness_fuse_*` | **+0.93 %** (-0.99, +4.60), `timing_fuse_1.log`; repeat +1.46 % (-1.62, +6.13), `timing_fuse_2_followup.log` | 48,000 of 48,000 equal, `cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_*` | stopped: below +2.0 % |
| `FORGE_SPD_PREFETCH_PICK=1` | PASS, `patch_PREFETCH_PICK_apply.log` | 13 of 13 / 13 of 13, `pins_pick_off.log`, `pins_pick_on.log` | code-and-data identical, `bytecmp_c29ctl_vs_pick_off.log` | 48,000 of 48,000 equal, `cmp_harness_pick_*` (does not exercise this patch) | **+0.72 %** (-2.17, +4.57), `timing_pick_1.log` | 48,000 of 48,000 equal, `cmp_release_lock_exe_vs_PREFETCH_PICK_*` | stopped: below +2.0 % |
| `FORGE_SPD_EVAL_PIPELINE=2` | PASS, `patch_EVAL_PIPELINE_apply.log` | 13 of 13 / 13 of 13, `pins_pipe_off.log`, `pins_pipe_on.log` | code-and-data identical, `bytecmp_c29ctl_vs_pipe_off.log` | 48,000 of 48,000 equal, `cmp_harness_pipe_*` | -1.53 % (-3.47, +1.12), `timing_pipe_1.log` | not run | stopped: slower |
| `FORGE_SPD_NNUE_WPREFETCH=16` | PASS, `patch_NNUE_WPREFETCH_apply.log` | 13 of 13 / 13 of 13, `pins_wpf_off.log`, `pins_wpf_on16.log` | code-and-data identical, `bytecmp_c29ctl_vs_wpf_off_r2.log` | 48,000 of 48,000 equal, `cmp_harness_wpf_*` | -4.42 % (-9.18, -2.21), `timing_wpf16_1.log` | not run | stopped: slower |

Noise floor: lock against lock by the same method, 11 valid pairs of 12 planned, median -0.30 %, min -5.19 %, max +7.68 % (`timing_null_1.log`). All timings are screening numbers taken while other work ran on the PC.

The harness catches a planted fault: 9,619 of 12,000 rows differ with the net on (`cmp_harness_mutant_capture_column_vs_ctl_neton.log`); with the net off it shows nothing, correctly, because the fault is in network code.

Patch and exe identities (exes are on the PC under `D:\forge_jobs_20261110\fable4cpu\out\build\<tag>\m2use\forge_m2use.exe`; tags `fuse_on`, `fuse_off`, `pick_on`, `pick_off`, `pipe_on`, `pipe_off`, `wpf_on16`, `wpf_off`):

| Candidate | Patch MD5 | Exe, flag on: MD5 / SHA256 | Exe, flag 0: MD5 / SHA256 |
|---|---|---|---|
| `NNUE_FUSE_EVAL` | `dad1b1623e5fe215301b448195b3aaa9` | `154cd9c12ba9d73f2fad23412ab6191a` / `1e38bfbb77b976de7d47660bc4a2faef993c7ac383a16bf0f6d8ad6829b2dcf0` | `9e17e53c069185e6888c97ef83b5560d` / `e1ff72b6183b0280d37fa7bbe718d991fbd3bf82de18a33c69ae49ea9af97406` |
| `PREFETCH_PICK` | `40f47e7096e50c3f6dd2dd734daa24c3` | `93f625857dd80f4c01c209e8b2c75078` / `f4b203a77fa169c320857a619f86c49211880aaadc4733ef5079d37530be1bd4` | `f4860a8241624ee84c3a7e018b19cca2` / `a0b9365b1dd65666f76e96a0f4ba5e67c38f81dc61e780bed54765a0013559ff` |
| `EVAL_PIPELINE` | `6955bd19231c1ea94232115d84e3f1b7` | `158e887523d3002ca6cc19293f6f0f50` / `c2cbf273d09d558311767b870d4b523b6d5eaf69040054d02c2eedb604b73742` | `bd5f29724d3c4054b395beaa032d0b39` / `1ecbc5f2e668cf6c11c17ac734f1d253ba002c49c31488c8020bffadcbf96f26` |
| `NNUE_WPREFETCH` | `4cff3d338ce774e4e689d8b77caf7415` | `e61cfa9c655b2b91ca83212c23ea8152` / `93d64bd0beba348c543b2ccf7f6802e19f89d8de94986494c5c42dff80c890af` | `3a78e2317b29cc5a452efc601b9b098d` / `b3e53fb301c9af41237197246d52c57dae8e77110b7efb1a94706e95379c7415` |

## Bug hunt (extra)

No defect found. Counts are what ran, not a pre-registered plan; details and five non-defect observations are in `README.md`.

| Part | Completed | Result | Evidence |
|---|---|---|---|
| UCI edge-case battery, 130 cases on 4 exes | 520 of 520 runs | no crash, hang, illegal move or sanitizer report; 7 flags judged: 6 by design, 1 my test's fault | `bughunt_uci_battery.log`, `bughunt_uci_battery_hard.log` |
| Book files that are not books, odd move notations, 15 cases on 2 exes | 30 of 30 runs | no flag | `bughunt_book_and_moves.log` |
| Hardened build (assertions, checked indexing, ASan + UBSan): full bench | 10 of 10 | node counts equal the pins, no report | `san_build_hard.log`, `san_bench_hard.log` |
| Hardened build: Threads 2-9 fixed-node searches | 200 of 200 | legal best moves, no report | `mt_hard.log` |
| Hardened build vs lock exe, 2,000 positions at depth 13, net on and off | 4,000 of 4,000 rows equal | nothing on stderr | `cmp_lock_vs_hard_cold_on.log`, `cmp_lock_vs_hard_cold_off.log` |
| Hardened build vs lock exe, positions 2001-12000 at depth 10, net on and off | 20,000 of 20,000 rows equal | nothing on stderr | the six `cmp_lock_exe_vs_hardened_build_wide_*.log` |
| Answer time of clocked searches | 380 of 380 searches | inside the budget except by under half a millisecond at 1 ms budgets | `bughunt_latency_threads1.log` |

## Superseded logs, kept on purpose

`bytecmp_lock_vs_c29ctl.log` and `bytecmp_c29ctl_vs_wpf_off.log` say DIFFERENT because the first version of my comparer misjudged the debug record; the `_r2` logs replace them. `san_build_asan.log` records the failed first ASan link. `cmp_harness_mutant_capture_column_vs_ctl_netoff.log` says PASS, which is the correct outcome for a fault in network code.

## Payload files with MD5

Every file under `fable_cpu_speed/` except `DONE.md` itself and `MANIFEST.tsv` (explicit exclusions, so that no hash depends on itself). `MANIFEST.tsv` lists the same files plus `DONE.md`, with MD5 and SHA256, and excludes itself.

| File | MD5 |
|---|---|
| `DONE_head.md` | `966b616fe677fafb5306010059248639` |
| `DUPCHECK.md` | `fd5b489ab2a0af46e7bde6aef82e17d5` |
| `PREREG.md` | `9e5ee8f76484ff1a1cb1ae0932d12963` |
| `PROFILE.md` | `d47f61c2a2d13c70cdc727f50d8990aa` |
| `README.md` | `8e5d9313f93349afdd99b77ee4e63954` |
| `REVIEW_LOG.md` | `037f3832b50ff7035ca9b524f3561f12` |
| `STATUS.md` | `83f4f58c90772322c1e815cf30b3fd78` |
| `UTILIZATION.log` | `996e4745dae731b738c85fa8949af133` |
| `evidence/logs/bughunt_book_and_moves.log` | `f662a37d4f2ea0ceb7c349882b19bc32` |
| `evidence/logs/bughunt_latency_threads1.log` | `0d9874585ff89ac7d33a3c83fe53987f` |
| `evidence/logs/bughunt_uci_battery.log` | `3afaff3d5ec1b78fd2a7146eaa91f896` |
| `evidence/logs/bughunt_uci_battery_hard.log` | `7ad36ed586943edd3b1993b45ebb6118` |
| `evidence/logs/build_c29ctl.log` | `7710eaa3ff3f150b97e9162fd712591e` |
| `evidence/logs/build_fuse_off.log` | `0e2e38ea96301be9235dd6118b1c34ea` |
| `evidence/logs/build_fuse_on.log` | `6f7d6cf441b51718b7a75e0540854e43` |
| `evidence/logs/build_pick_off.log` | `4eada60133bb5636d8124736b68ae7d9` |
| `evidence/logs/build_pick_on.log` | `c8003c38294efac63af3b822382160d6` |
| `evidence/logs/build_pipe_off.log` | `8e99545d35eb417fbbd46c6de4b2e00b` |
| `evidence/logs/build_pipe_on.log` | `a709b1b394f34733efc26b927f769def` |
| `evidence/logs/bytecmp_c29ctl_vs_fuse_off.log` | `9699304cf00b950ab79decef04af9c43` |
| `evidence/logs/bytecmp_c29ctl_vs_pick_off.log` | `6717154902b765b9d6c3ad3d060d9b9f` |
| `evidence/logs/bytecmp_c29ctl_vs_pipe_off.log` | `539874ced517fe9acdde6bd70bf47b10` |
| `evidence/logs/bytecmp_c29ctl_vs_wpf_off.log` | `0921472ed74cd7fbd1c2c4b3349f2d33` |
| `evidence/logs/bytecmp_c29ctl_vs_wpf_off_r2.log` | `9f9f0b670312c997aeb7575590e314d2` |
| `evidence/logs/bytecmp_lock_vs_c29ctl.log` | `030b59bd78dd9c7e0adfbc090650a99f` |
| `evidence/logs/bytecmp_lock_vs_c29ctl_r2.log` | `eb7ae91cd3e0e6cbd925ec4417f37850` |
| `evidence/logs/clone.json` | `04dd2e2effab4cd5e82da4ad6b14d75b` |
| `evidence/logs/cmp_det_cold_off_1__vs__det_cold_off_2.log` | `3dcca55d8baa1a862cf54cea22a11945` |
| `evidence/logs/cmp_det_cold_off_1__vs__det_cold_off_3.log` | `ec1b958ea86efd1929517eb05b573f1c` |
| `evidence/logs/cmp_det_cold_on_1__vs__det_cold_on_2.log` | `b31c6e8edbd7f551794c6ed0fb4b3464` |
| `evidence/logs/cmp_det_cold_on_1__vs__det_cold_on_3.log` | `3e41f162d54472f35d71942abd83f759` |
| `evidence/logs/cmp_det_reset_off__vs__det_reset_off_second.log` | `d084e35ac00a3ffe7d2cc5de7c66dd32` |
| `evidence/logs/cmp_det_reset_on__vs__det_reset_on_second.log` | `a38474087e75d49499e011e332334c41` |
| `evidence/logs/cmp_det_warm_off_1__vs__det_warm_off_2.log` | `cc8cc5bb0e2c0336b0b486fa535c1c51` |
| `evidence/logs/cmp_det_warm_on_1__vs__det_warm_on_2.log` | `b9b57a987741165038a918b6e43611df` |
| `evidence/logs/cmp_harness_fuse_off_vs_ctl_netoff.log` | `ab9f652e99d8627056a8dc29a79157b9` |
| `evidence/logs/cmp_harness_fuse_off_vs_ctl_neton.log` | `204a9f47a2fc4bc44c70c497742bad54` |
| `evidence/logs/cmp_harness_fuse_on_vs_ctl_netoff.log` | `56e8b7f7e12fd71d367ec64d3a9c933f` |
| `evidence/logs/cmp_harness_fuse_on_vs_ctl_neton.log` | `0f8178a355293582ffecbae2ab175d1f` |
| `evidence/logs/cmp_harness_mutant_capture_column_vs_ctl_netoff.log` | `1b41daedf6b991b55bf59e79b93e8b0b` |
| `evidence/logs/cmp_harness_mutant_capture_column_vs_ctl_neton.log` | `8a48607fb56bab3cd620a81eff09152b` |
| `evidence/logs/cmp_harness_pick_off_vs_ctl_netoff.log` | `b289819ae5460cbb62325c3c75568dc0` |
| `evidence/logs/cmp_harness_pick_off_vs_ctl_neton.log` | `e2a823c4bfb0337518d4708b508ee9a3` |
| `evidence/logs/cmp_harness_pick_on_vs_ctl_netoff.log` | `1d03c6e6faa981fae160fabee516911d` |
| `evidence/logs/cmp_harness_pick_on_vs_ctl_neton.log` | `d07fd6096046ece12befe769d3fb2595` |
| `evidence/logs/cmp_harness_pipe_off_vs_ctl_netoff.log` | `2d504e030508c3c5931534739b69ddbb` |
| `evidence/logs/cmp_harness_pipe_off_vs_ctl_neton.log` | `52b28a512bcfabe477810a6ee61610e8` |
| `evidence/logs/cmp_harness_pipe_on_vs_ctl_netoff.log` | `feca7af1be9a41da38ae4de2d1068b56` |
| `evidence/logs/cmp_harness_pipe_on_vs_ctl_neton.log` | `a261dfcd41e6dd805e199ada972c16eb` |
| `evidence/logs/cmp_harness_wpf_off_vs_ctl_netoff.log` | `30465fd235dd2d0a3390f27fe94099b9` |
| `evidence/logs/cmp_harness_wpf_off_vs_ctl_neton.log` | `8e9d3adbce42a54f6aaf22229dca2ceb` |
| `evidence/logs/cmp_harness_wpf_on16_vs_ctl_netoff.log` | `fb34c3a47a9e607563f3e947cc67126b` |
| `evidence/logs/cmp_harness_wpf_on16_vs_ctl_neton.log` | `64e75114a25ab2aa0a22cff3628cf8b9` |
| `evidence/logs/cmp_lock_exe_vs_hardened_build_wide_net_off_shard1.log` | `bb81d8676f49c4b5947988540c00d55f` |
| `evidence/logs/cmp_lock_exe_vs_hardened_build_wide_net_off_shard2.log` | `eab300308947c0fb12cfb8e9fe804905` |
| `evidence/logs/cmp_lock_exe_vs_hardened_build_wide_net_off_shard3.log` | `2ddf7744063b08322933f00c917543ab` |
| `evidence/logs/cmp_lock_exe_vs_hardened_build_wide_net_on_shard1.log` | `4627f7183d97ac987d7468830408f5af` |
| `evidence/logs/cmp_lock_exe_vs_hardened_build_wide_net_on_shard2.log` | `ce4a232d6cc1bc9a777fc2a84a4808d9` |
| `evidence/logs/cmp_lock_exe_vs_hardened_build_wide_net_on_shard3.log` | `9373f26e59ed4f7673f37b64f10b3cb1` |
| `evidence/logs/cmp_lock_vs_hard_cold_off.log` | `b794652d2ae0fef244d6d7d72ccbcc47` |
| `evidence/logs/cmp_lock_vs_hard_cold_on.log` | `9d31c698cec6c7132a04fdb9d1cd0f07` |
| `evidence/logs/cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_flag0_net_off.log` | `63f71e2f57609c8501422663c2e36b85` |
| `evidence/logs/cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_flag0_net_on.log` | `452e3523dbfc7053d43e82c129db5b35` |
| `evidence/logs/cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_flag1_net_off.log` | `6c4fb22d15cdecaf24b1fb5f1b58c1d3` |
| `evidence/logs/cmp_release_lock_exe_vs_NNUE_FUSE_EVAL_flag1_net_on.log` | `911adbd69bebd3c189802e441743a7ce` |
| `evidence/logs/cmp_release_lock_exe_vs_PREFETCH_PICK_flag0_net_off.log` | `466131a41653734753f07ac00d5d4f66` |
| `evidence/logs/cmp_release_lock_exe_vs_PREFETCH_PICK_flag0_net_on.log` | `a5fa9dffc8fcca16a2bc2c28f30991af` |
| `evidence/logs/cmp_release_lock_exe_vs_PREFETCH_PICK_flag1_net_off.log` | `956c7fa053fe4c29c49134c036c3a9d7` |
| `evidence/logs/cmp_release_lock_exe_vs_PREFETCH_PICK_flag1_net_on.log` | `a29919ade86b1487700a72de8c0bbc9a` |
| `evidence/logs/cmp_tt_lock_off_1__vs__tt_lock_off_2.log` | `5ba1d7f47b4cbfaee9776e44cd4f6920` |
| `evidence/logs/cmp_tt_lock_on_1__vs__tt_lock_on_2.log` | `9600090a2fa5109309c365cc645d5b75` |
| `evidence/logs/freeze.log` | `45d14cad2d3fe5887a32ed87db620605` |
| `evidence/logs/mt_asan_r2.log` | `84665e8fe7a683f8f547ba5c0e9af411` |
| `evidence/logs/mt_hard.log` | `bd02b9e43779eafe34bf71d2c525c727` |
| `evidence/logs/mt_release_lock.log` | `97f18868984756f9d3097b22de60f7cc` |
| `evidence/logs/mt_ubsan.log` | `d7652de841e89f271122f78af1a4e073` |
| `evidence/logs/nnue_update_codegen_excerpt.log` | `3dd6f9b6c901afd3a7ea4d2054366c1e` |
| `evidence/logs/patch_EVAL_PIPELINE_apply.log` | `47d1c6918499bb8ed875327e800729f0` |
| `evidence/logs/patch_NNUE_FUSE_EVAL_apply.log` | `be53287fbc9ebe1eaacab9af33883106` |
| `evidence/logs/patch_NNUE_WPREFETCH_apply.log` | `93eac96d41c5f53299cc65626a9adac1` |
| `evidence/logs/patch_PREFETCH_PICK_apply.log` | `fbe3f72b0384d44ca888062f4888ad52` |
| `evidence/logs/pins_c29ctl.log` | `55b92366368fdfe07a3fe22f8a49463e` |
| `evidence/logs/pins_fuse_off.log` | `5c7545cee4d6867ec287cabb73e0d2d1` |
| `evidence/logs/pins_fuse_on.log` | `7226b7a56d918152a64d37d4c739ec65` |
| `evidence/logs/pins_pick_off.log` | `39725c08cd19a08a5c527f62ac7d2274` |
| `evidence/logs/pins_pick_on.log` | `904ad06d76edef620f98410ce571ea3e` |
| `evidence/logs/pins_pipe_off.log` | `efe63cad907c7987ee373fd23fd63725` |
| `evidence/logs/pins_pipe_on.log` | `95adb3eba9cb82ee7c407242d60ca5a7` |
| `evidence/logs/pins_wpf_off.log` | `638042549a65645d1e6e70db490f4282` |
| `evidence/logs/pins_wpf_on16.log` | `854b1ab4f57a2f2e6b2ee7e3ed9ee422` |
| `evidence/logs/preflight_001.txt` | `d59aeb2e58e1080a7b1014e03c4e3f99` |
| `evidence/logs/probe_w1_alignment.log` | `bd3dd5931d13d27cf9734d34f36eec1c` |
| `evidence/logs/profile_bench22_neton.log` | `84d0779780cc7b02b00dcc276674945c` |
| `evidence/logs/profile_bench22_neton_quiet.log` | `4e9eef3b271817847484df1455f0b367` |
| `evidence/logs/profile_call_counts.log` | `c1c9ef35f8a63d2b80b98913a88fd01e` |
| `evidence/logs/san_bench_asan_r2.log` | `4aa50f9bbf35ac24ed6c1e945a77a7f1` |
| `evidence/logs/san_bench_hard.log` | `d5d6275cf6412d0fb97e478b7502428f` |
| `evidence/logs/san_bench_ubsan.log` | `2b94e85cee650908085494ba1c040898` |
| `evidence/logs/san_build_asan.log` | `8f288cdd0debc044c90e5f2acbad4466` |
| `evidence/logs/san_build_asan_r2.log` | `9d783cee82cc022f033516d09ac17e47` |
| `evidence/logs/san_build_hard.log` | `a92bfb59d687bd909e5ae66dde926d46` |
| `evidence/logs/san_build_ubsan.log` | `9bedb0f33e63fa670f3fd4220266ce2b` |
| `evidence/logs/san_fixtures.log` | `14735a3a6f924bcf1d2749b4804df5b8` |
| `evidence/logs/san_fixtures_r2.log` | `a6d123991b8c822b4fda2ffbbdcb2894` |
| `evidence/logs/selftest_checkers.log` | `67b14856f22dfad97950b5f5b2fc527f` |
| `evidence/logs/timing_fuse_1.log` | `009d27b7c2d8e489b89ad61c88de4f68` |
| `evidence/logs/timing_fuse_2_followup.log` | `b935fb9dc3b280dad91f3b60b539b6fc` |
| `evidence/logs/timing_null_1.log` | `aae033c0ff2ed9cc2380758522b35baf` |
| `evidence/logs/timing_pick_1.log` | `f239eb2821f5773436a41a59026be3d2` |
| `evidence/logs/timing_pipe_1.log` | `cace6cc66bcac3f5d30cf7b689fd63fa` |
| `evidence/logs/timing_wpf16_1.log` | `4286061a3d3992de0ea996b0318c29bc` |
| `evidence/logs/ttstress_asan_on_1.rows.tsv` | `8271cdd05ffcbd4ef5c729bf89bcd910` |
| `evidence/logs/verify_done.log` | `b5e08c7b18a8c70a41b4fd6076e48c9e` |
| `patches/EVAL_PIPELINE.patch` | `6955bd19231c1ea94232115d84e3f1b7` |
| `patches/NNUE_FUSE_EVAL.patch` | `dad1b1623e5fe215301b448195b3aaa9` |
| `patches/NNUE_WPREFETCH.patch` | `4cff3d338ce774e4e689d8b77caf7415` |
| `patches/PREFETCH_PICK.patch` | `40f47e7096e50c3f6dd2dd734daa24c3` |
| `tests/evaldump.cpp` | `27a06dfd108484049b890f5590a424ea` |
| `tests/fake_engine.py` | `f47fb13ace71565835f6dfe1d3239131` |
| `tests/fake_exit3.cmd` | `b38d4d48f101b4e106e8c09fb0879998` |
| `tests/fake_ok.cmd` | `093933e9b9f83546688cf5dede92b7f0` |
| `tests/fens_12k_v2.txt` | `e7dbf2c8151188c03ef52054557a531e` |
| `tests/san_fixtures.cpp` | `ae857592337a9a9e746c836a0a6e839e` |
| `tools/abba.py` | `57e52f9f1db9c95098d057af06618d96` |
| `tools/bughunt.py` | `da3753ad6ebd52f2cf06106a5d43fb7e` |
| `tools/bughunt_book.py` | `6350858a69f7754bbf86104ac3f551ec` |
| `tools/build.ps1` | `593373177e0c432be38c9fb96bbd5e24` |
| `tools/bytecmp.py` | `48eecf6ce2dd66831411c07ef1f0fa2f` |
| `tools/cand.py` | `f39fb786acbb16fa9d0214d7ac714db8` |
| `tools/cand_ladder.ps1` | `6e827c4b65739bc14489f486c6fdb2bc` |
| `tools/freeze.ps1` | `3baca49c46f6e2b0f7ec2cda8cf9e0c3` |
| `tools/harness.py` | `67c8159d42787d45f7168f905080701e` |
| `tools/latency.py` | `7433b191d15c895146fbb588d8e1eb49` |
| `tools/make_manifest.py` | `14b2727c63a1e57df152447d99e6f80d` |
| `tools/pin.ps1` | `3a2c11c2a9dc08d0688683dcb52d8878` |
| `tools/pins.py` | `a55f920d5c09c94b5778075ba2897f23` |
| `tools/rip_sampler.py` | `5c98cd177f513fd0640494d489416dda` |
| `tools/rows.py` | `89c65cbfb38871035d722bcccfc415ca` |
| `tools/run_determinism.ps1` | `fe8c07e4ce5c5be05e4bebd7db48c14e` |
| `tools/run_harness_set.ps1` | `92cf17b2a2a5e9c4077c1a63bde3a796` |
| `tools/run_parallel.ps1` | `e8a68ea41da537346431e8701531677e` |
| `tools/run_san_chain.ps1` | `0b56d279069d8204192699aae465ec5d` |
| `tools/san.py` | `6327a82dd8ea0f9d70926a845f5a8e6f` |
| `tools/selftest_checkers.py` | `5a55906f9c77042e96f2739336173945` |
| `tools/ttstress.py` | `0c8975ae7cf0fabb19b88594d90b44cb` |
| `tools/uci_common.py` | `c2619f0171209c0ab0115af91ed3c1a8` |
| `tools/utillog.ps1` | `bf0093404452bea166b7311c72ef0b67` |
| `tools/verify_done.py` | `1c7109cd4330c0ea0c5d48adc6ddacb5` |
