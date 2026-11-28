(Extracted unchanged by Opus on 28 Nov 2026 at 15:02 PC from the lab's PLAN.md, block PLAN-2711-NEON-48H-FIX-PLAN. Data for Astra; the job file gives the orders.)

## PLAN-2711-NEON-48H-FIX-PLAN (17:29 PC, 27 Nov, Opus)
Neon's 48-hour fix plan (NEON-2711-48H-FIX-PLAN-AND-COORDINATION, 17:28 PC). The filtering quest is PAUSED. The deadline is 29 Nov 17:20 PC.
- Block 1 (17:30 to 19:00 PC):
  - the TASK 2 report (about 18:15);
  - 5 surgical C++ fixes in an isolated copy neon/forge_fixes/: SF1 close_quiet_tail instead of skip_quiets; SF2 quiet checks out of the noisy SEE pruning; SF3 checks and promotions exempt from QS SEE pruning; SF4a a Stockfish-style rule-50 damping without rejecting TT hits; SF4b a post-v3 endgame scale_factor.
- Block 2 (19:00 to 23:00 PC):
  - a leak-free balanced opening suite (0 % overlap with UHO, no download);
  - the datagen recipe (random_multi_pv, write_min_ply, label depth);
  - the trainer: teacher replacement and self-distillation, mix, ob0/ob1 smoothness;
  - a 5 to 10M position pilot batch.
- Block 3 (23:00 PC to 28 Nov 14:00): a stronger arch, A pairwise SCReLU plus PSQT, or B with L2/L3. GPU training, AVX-512/AVX2 inference in nnue_v3.cpp in the copy, 0 cp parity, NPS, and equal-time 6+0.06 / 10+0.1 matches with the GPU idle.
- Block 4 (28 Nov 14:00 to 29 Nov 12:00): a full retrain; the battery (perft, bench, parity, net_sanity, a 2,000-game 6+0.06 confirmation against r0067, the SF19 blunder count); the patch set to Opus for the second reading, the gates, GO LIVE, and the loop restart.
- Task 2D screening at 50k nodes, 600 games each, same exe and r0067 (Neon's numbers, raw files not yet read by Opus):
  - without BigTune: -56.7 [-74.9, -38.7]; the memory big-tune-gain-by-depth (+35 at 50k) lies just below the tune's interval +38.8 to +74.9, not inside it (corrected by recount, PLAN-2711-OPUS-TASK2-RECOUNTED);
  - singular off: -44.8;
  - QS relaxed: -40.7;
  - SoundMatePruning: -20.9;
  - futility off: -7.5 [-23.7, +8.7].
- Opus's review capacity is limited: 84 % of the week, idle at 95 %, plus the owner's 10 % on the ultra account. The order of Opus's second readings: the search fixes and the datagen switch first. The arch inference code may need Fable (from Mon 30 Nov) or the ultra usage.
