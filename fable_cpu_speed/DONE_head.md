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
