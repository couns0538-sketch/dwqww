# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files).
Session restart at ~09:32 (application restart by the owner); workers resumed 09:35; jobs started before it kept running.

| job | state | candidates | last update |
|---|---|---|---|
| CR 637B (owner, done first after the restart) | DONE except the 3 LOW notes (note file not on the PC): BLOCKER pin DIFF fail-closed, SHOULD 1-3, test 13/13 PASS (be0e4e37); report `CR_637B_REPORT.md` | - | 09:47 |
| A speed-only lock path (tools) | DONE: tools + tests (kit self-test, test 1 lock-vs-lock pack inside the A/A band, test 2 mutant, test 3 lp_part1 full pack NO-WIN, CR 13/13, move-order mutant 3/3); variant screen complete (no flag beats the lock recipe; net-off PGO workload -29 %); independent review: no BLOCKER, SHOULD 1-4 + LOW 1-11 fixed (REVIEW_FIXES.md); protocol verdict = wall (cpu advisory) | var_lp_part1, locklock_v1c | 12:08 |
| B bit-exact hot-path changes | HEADLINE stack_w2 = TT_NOTLS + NO_ZERO_MOVELISTS=2 + SPEED2: BIT-EXACT L1-L4 + full 12k L3 12000/12000, ABBA vs lock wall +11.48 % [1.0734, 1.1217], cpu +11.34 % [1.0990, 1.1191] = WIN / WIN; its switch-0 build = FD3A5190 byte for byte. stack_w3 (+ prefetch_early): full 12k 12000/12000, wall +11.42 % / cpu +11.83 % WIN / WIN. Singles (protocol = wall): WIN b2_nzm2 (+3.6 %), r14_speed2_b (+3.2 %); cpu-only WIN b1_tt_notls_b (wall +4.2 % noisy), b1_prefetch_early; NO-WIN pickbest1/2, matkey_fast, slider_pext (+1.4 %, low end 0.9993), nnue_zmm_c (+2.0 %, low end 0.9999). Running 12:19: 16-round re-times of TT / slider / prefetch / zmm, stack_w1 (wall winners only: NZM2 + SPEED2) ABBA + full 12k, b2_nzm1 ABBA, trial_w6 (all six ON, ceiling, switch-0 = FD3A5190) pack + full 12k | stack_w2 (QA first) | 12:18 |
| C gate wall time | DONE 09:59 (worker jobc): 7 tools in opus_speed/jobc/tools, README + RESULTS; tests ALL PASS (13/13 gate replays = recorded verdict, 18/18 corrupt / truncated PGNs -> error, 111-row formula check); coordinator re-run 10:01 ALL PASS (jobc/results/tests_20261105_100109_coordinator_rerun.md) | - | 10:03 |
| D net pipeline | DONE 11:54 (worker jobd, plans + read-only log tools only, no GPU): opus_speed/jobd/PLAN.md; D1 owner item (coordinator re-checked): the GPU guard drops HWiNFO rows with a one-digit day since 2026-11-01 and throttles on the ADLX fallback (run_frac 0.33-0.64 vs 0.90-1.00 in October); D2 RAM-floor aborts repeat epochs | - | 12:08 |
