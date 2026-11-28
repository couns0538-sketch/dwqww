# RESULTS UPDATE, 28 Nov 2026, 15:40 PC (Opus): the R1-skip net at the clock

This replaces the 'pending' row of fixes_2811/RESULTS_AND_STATE_2811.md. Data for Astra; the job file gives the orders.

Job 2, OPUS_R1_skip_vs_r0067_2000g_6p006: the R1-skip net (seed 1, sha256 4902fe65...) against r0067, at 6+0.06.
- Setup: the loop's own exe (runs/forge/engines/v3-r15dsg-sp-clang/forge.exe) on both sides, 51 vs 51 options, only NNUEArchFile differs. Book UHO_Lichess_4852_v1.epd. Ended 15:40:22.
- VERIFIED (recount_task2d.py on the raw PGN, sha256 765d5b189b2c2737...):
  - 2,000 games, W 465 D 1107 L 428; ptnml [9,220,500,267,4].
  - Elo +6.43 [-1.47, +14.33]; no Termination tags. It equals Neon's summary (LOS 94.5 %).
- VERDICT by the rule declared before the run: the range holds 0, so INCONCLUSIVE. R1-skip is NOT proposed as the loop's best net on this result.
  - The skip-noisy FLAG is a separate placement. Its declared rule (07:58) is untouched: proven twice at 250k, placed after Fable's read.
- VERIFIED pattern, two nets: a new net's gain at 250k largely vanishes at the clock, with the same book.
  - G3: +22.03 at 250k, -0.35 [-8.35, +7.65] at the clock.
  - R1-skip: +30.65 [+18.59, +42.79] at 250k, +6.43 [-1.47, +14.33] at the clock.
  - The R1-skip gap is 24.2 +/- 7.4 Elo (z about 3.3; my arithmetic from the two ranges). Not noise.
  - The 250k match used Neon's base_r15dsg.exe, the clock match the loop's PGO exe; same source, not yet shown to be the cause.
- HYPOTHESES, untested:
  - (a) Time management: Forge's time use depends on eval and instability, with thresholds found with r0067's eval scale, and R1-skip's scale differs (start position +42).
  - (b) Depth: the clock games search to a different depth than 250k nodes, and the net's edge shrinks with depth (the lab's depth lesson).
  - (c) The two exes differ in behaviour.
- Cheap first test (no new games): from the PGN comments, the depth and time per move in the clock games against the 250k games; the exes' same_search on the two nets. Asked of Neon (results will come under from_neon/).
- CONSEQUENCE (ESTIMATE): the loop's gate and the proposed Monday bars decide nets at 250k. If (a) or (b) holds, a 250k gain overstates a net's clock gain. Bar 2 needs a clock condition: the clock result not negative, and Fable and the owner agree before the tests. Raised for Monday.
