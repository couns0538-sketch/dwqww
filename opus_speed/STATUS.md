# Forge speed job - STATUS

Owner Couns. Job window 2026-11-05 08:38 -> 14:38 (PC clock = Vienna time); FINAL_REPORT due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Plan: `opus_speed/PLAN.md`. Scratch `F:\ospd\` (<= 8 GB).
Lock: exe FD3A5190 (`forge_push\bin\forge_ltopgo_x_al1s198_v23.exe`), source = exact copy `F:\ospd\src\lock` (20 files).
Session restart at ~09:32 (application restart by the owner); workers resumed 09:35; jobs started before it kept running.

| job | state | candidates | last update |
|---|---|---|---|
| CR 637B (owner, done first after the restart) | DONE except the 3 LOW notes (note file not on the PC): BLOCKER pin DIFF fail-closed, SHOULD 1-3, test 13/13 PASS (be0e4e37); report `CR_637B_REPORT.md` | - | 09:47 |
| A speed-only lock path (tools) | tools done + fixed; kit self-test PASS (lp_v1 = FD3A5190 byte for byte); test 2 PASS (mutant fails at L1); balanced ABBA/BAAB A/A d20 sd ~1 %/round; 15 variants built (noplt, nosi, pvw512 = identical exe; w12k rebuilt with full FENs); ABBA queue q2 running on CPU 2; full 12k reference running | - | 09:47 |
| B bit-exact hot-path changes | READY: b2_nnue_zmm, b1_tt_notls (packs running, quick L3); tt_align = no change needed; in progress: b1 prefetch_early, b2 no_zero_movelists, matkey_fast, pickbest, slider_pext | - | 09:47 |
| C gate wall time | DONE 09:59 (worker jobc): 7 tools in opus_speed/jobc/tools, README + RESULTS; tests ALL PASS (13/13 gate replays = recorded verdict, 18/18 corrupt / truncated PGNs -> error, 111-row formula check); coordinator re-run 10:01 ALL PASS (jobc/results/tests_20261105_100109_coordinator_rerun.md) | - | 10:03 |
| D net pipeline | NOT STARTED (only if A-C are done) | - | 09:47 |
