# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files).
Session restart at ~09:32 (application restart by the owner); workers resumed 09:35; jobs started before it kept running.

| job | state | candidates | last update |
|---|---|---|---|
| CR 637B (owner, done first after the restart) | DONE except the 3 LOW notes (note file not on the PC): BLOCKER pin DIFF fail-closed, SHOULD 1-3, test 13/13 PASS (be0e4e37); report `CR_637B_REPORT.md` | - | 09:47 |
| A speed-only lock path (tools) | tools done + tested (kit self-test, mutant, move-order mutant, CR tests); 12k reference deterministic (lock copy 12000/12000); variant screen vs lock (cpu medians): o3 -3.4 %, lto -2.5 %, pgo -1.2 %, znver4 -0.3 %, ppt -0.4 %, af64 +0.4 %, ipapta +0.7 %, part1 +0.8 %, pvw256 -0.7 % (no WIN); noplt / nosi / pvw512 = identical exe; PGO workload with the net OFF: -29.4 % (cpu) with the net loaded; wmix / w12k timing pending; test 3: var_lp_part1 full pack bit-exact (12k L3), ABBA queued; test 1: locklock_v1c queued | var_lp_part1 | 11:14 |
| B bit-exact hot-path changes | ABBA d20 x 10 vs lock (bit-exact L1-L4 quick first): WIN b2_nzm2 wall +3.61 % [1.0161, 1.0606] cpu +4.26 % [1.0360, 1.0479]; WIN r14_speed2_b wall +3.15 % [1.0165, 1.0443] cpu +2.87 % [1.0157, 1.0425]; WIN(cpu) b1_tt_notls_b cpu +3.69 % [1.0147, 1.0492]; WIN(cpu, narrow) b1_prefetch_early cpu +1.52 % [1.0026, 1.0288]; NO-WIN b2_pickbest1 (+1.1 %, intervals include 1). Stack stack_w2 (TT + NZM2 + SPEED2) bit-exact quick, ABBA queued, full 12k L3 running; trial_w3 (+ prefetch_early) applies cleanly. Pending: matkey, slider_pext, nzm1, pickbest2, nnue_zmm_c | b2_nzm2, r14_speed2_b, b1_tt_notls_b, b1_prefetch_early, stack_w2 | 11:14 |
| C gate wall time | DONE 09:59 (worker jobc): 7 tools in opus_speed/jobc/tools, README + RESULTS; tests ALL PASS (13/13 gate replays = recorded verdict, 18/18 corrupt / truncated PGNs -> error, 111-row formula check); coordinator re-run 10:01 ALL PASS (jobc/results/tests_20261105_100109_coordinator_rerun.md) | - | 10:03 |
| D net pipeline | NOT STARTED (only if A-C are done) | - | 09:47 |
