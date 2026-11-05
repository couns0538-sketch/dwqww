# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files).
Session restart at ~09:32 (application restart by the owner); workers resumed 09:35; jobs started before it kept running.

| job | state | candidates | last update |
|---|---|---|---|
| CR 637B (owner, done first after the restart) | DONE except the 3 LOW notes (note file not on the PC): BLOCKER pin DIFF fail-closed, SHOULD 1-3, test 13/13 PASS (be0e4e37); report `CR_637B_REPORT.md` | - | 09:47 |
| A speed-only lock path (tools) | tools done; kit self-test PASS; test 2 PASS (mutant fails at L1); balanced A/A d20 sd ~1 %/round; variant screen: no flag / build mode beats the lock recipe so far (o3 -3.4 %, lto -2.5 %, pgo -1.2 %, znver4 -0.3 %, partial-training -0.4 % cpu medians; noplt, nosi, pvw512 = identical exe); test 1 lock-vs-lock pack re-running (locklock_v1b, builds = FD3A5190); full 12k reference cached (12,000 distinct rows) | - | 10:17 |
| B bit-exact hot-path changes | WINS so far (bit-exact L1-L4 quick + ABBA d20 x 10 vs lock): b1_tt_notls_b cpu +3.69 % [1.0147, 1.0492] (wall noisy, no win); b2_nzm2 (no-zero movelists value 2) wall +3.61 % [1.0161, 1.0606] and cpu +4.26 % [1.0360, 1.0479]. Waiting for ABBA: r14_speed2_b, b1_prefetch_early, b2_pickbest1; pipeline: matkey, slider_pext, nzm1, pickbest2, nnue_zmm_c, locklock_v1c, var_lp_part1. SPEED2 conflicts textually with NZM in generate_quiets -> hand-merged patch r14_speed2_after_nzm.patch; trial stack TT + NZM + SPEED2 applies cleanly (checks running) | b1_tt_notls_b, b2_nzm2 | 10:51 |
| C gate wall time | DONE 09:59 (worker jobc): 7 tools in opus_speed/jobc/tools, README + RESULTS; tests ALL PASS (13/13 gate replays = recorded verdict, 18/18 corrupt / truncated PGNs -> error, 111-row formula check); coordinator re-run 10:01 ALL PASS (jobc/results/tests_20261105_100109_coordinator_rerun.md) | - | 10:03 |
| D net pipeline | NOT STARTED (only if A-C are done) | - | 09:47 |
