# Memory file of astra

Rule 5 of `debate/README.md`: update and push this file about every 10 minutes and whenever your context is nearly
full. Every time in it comes from the command `date -u +%Y-%m-%dT%H:%M:%SZ`, never from your head.
If you lost your context: read `debate/README.md`, this file, `debate/BOARD.md`, then the messages newer than
"Last update" below.

## Who I am
- Name in this debate: astra
- Model: OpenAI Codex (Astra)
- Started: 2026-11-23T03:39:46Z
- Last update: 2026-11-23T11:29:40Z
- Phase: 4 addendum

## What I have read to the end (tick a file only when you reached its last line; 26 source files, 11,566 lines)
- [x] debate/README.md
- [x] debate/PLAN.md
- [x] debate/STATE.md
- [x] debate/READ_CHECK.md (answered in my read-check message)
- [x] loop/LOOP_OPTIONS.txt
- [x] source/R65_NOTE.txt
- [x] source/src/search.cpp (3,426 lines)
- [x] source/src/board.cpp (1,811 lines)
- [x] source/src/uci.cpp (1,314 lines)
- [x] source/src/nnue_v3.cpp (993 lines)
- [x] source/src/eval.cpp (659 lines)
- [x] source/src/nnue.cpp (557 lines)
- [x] source/src/bitboard.cpp (207 lines)
- [x] source/src/book.cpp (193 lines)
- [x] source/src/eval_params.cpp (89 lines)
- [x] source/src/forge65.cpp (61 lines)
- [x] source/include/forge/search.hpp (667 lines)
- [x] source/include/forge/board.hpp (353 lines)
- [x] source/include/forge/nnue_v3.hpp (299 lines)
- [x] source/include/forge/bitboard.hpp (224 lines)
- [x] source/include/forge/b4.hpp (109 lines)
- [x] source/include/forge/nnue.hpp (105 lines)
- [x] source/include/forge/eval_params.hpp (103 lines)
- [x] source/include/forge/eval.hpp (90 lines)
- [x] source/include/forge/tm_node_share.hpp (69 lines)
- [x] source/include/forge/book.hpp (58 lines)
- [x] source/include/forge/clock_plan.hpp (52 lines)
- [x] source/include/forge/uci_clock.hpp (43 lines)
- [x] source/include/forge/tm_finish.hpp (39 lines)
- [x] source/include/forge/forge65.hpp (22 lines)
- [x] source/include/forge/uci_output.hpp (12 lines)
- [x] source/include/forge/uci.hpp (11 lines)

## What I found (each with file and line, or with the figures I recomputed)

READY. All 26 source files (11,566 lines) and the rule-1 documents were read to their ends. My source read-check scored 12/12. Earlier detailed memory is preserved in the branch history, including 6e4672b13514c782a01bdf3403ff82e7c9dbf8a6 and the 10:57Z revision. This memory is the current status; Git order governs across the three different clocks.

## Scope and clock

I am Astra on my own machine. Native shared-branch pushes were denied, as reported in my first fallback message. Only my public Markdown goes to debate/forge-plan-20261123-astra with nondestructive pushes and server byte verification. Fable copies it and alone owns BOARD and FINAL_PLAN. The three original ballots are finished. The owner's separate six-hour research window is 06:35:35–12:35:35 UTC on 23 November (22:35–04:35 Pacific); only confirmed Neon credit exhaustion can end it early. Both peers replied. No confirmed exhaustion. Deliver the final complete change summary and exact final chat line after a verified final push, no later than 12:35:35Z. Owner updates already delivered 08:35:35Z and 10:35:35Z. The existing two-hour automation handles the final status as well; avoid duplicates. Fable's final look at 12:40Z will be after our stop. Distinguish jointly agreed messages from actual changes in the shared plan.

## Original decision

Fable's original FINAL_PLAN at a281365300d062f99a9a95ba8b1828067cddb490 has six testing rules and 16 ordered tasks, drawn from 37 proposals A1–A15, N1–N16 and F1–F6: 32 accepted changes and five deferred measurements with bars. All three ballots agree on all items, no dissent. My ballot 062329Z, fallback 01589eebccf513b40037cf6739e2141cae080dc2; Neon 062351Z, Fable 132211Z. Work order covers tune, Windows match/recovery, sequential judging, deep checks, Linux CPU rehearsal/worker/transport, paid card training and full resume, breadth and filters, disk feeder and qualification games, wider network parity, teacher/recipe/target ablations, 2B data then wider net, held-out search tuning and regressions. A7 retains current geometrically meaningful EP, past legal EP and reversible history; A14 requires the PC's postgame WDL correction. Local and PC stock pins defaults 312866/862329/perft4865609; all 24 loop options+r67 226187/616966. Soft 2k has hard 8k cap (uci.cpp:489–497; search.cpp:2659–2665).

## Issued addendum and ballots

Through Fable's fourth batch 4d0e89f / 171554Z, **15 entered**, eight current requirements and seven future projects. Current A16 durable pair/game identity, A17 source-game sampling within batches, N17 live evaluator, A18 cold liveness with one positive pulse, A20 fresh 40-pass mixing, A22 detect a single replayed pass after resume, A23 bind actual worker bytes and return to the immutable opening reservation, N23 classify final-value SEE plateaus/depth censoring before resetting a tuned value. Future A19 equal-generation-cost deeper labels, N18 qualified multithread search, N19 clock changes/forced moves, N20 stronger-reference and opening-suite bridge, N21 stage widths/buckets with integer safety, A21 second training seed for a repeatable winning recipe, N22 retune deep search only after the new net shows a regime change. Fable previously entered A22/N22 in 5a6c724, and reproduced all 360 stock searches on Windows. N22 working panel had 82 deep-null verification events in 2/120 positions at 20k vs 80,465 in 119/120 at 1M. PC N23 real steps 12/3 cross narrow SEE plateaus, but SingularDepth 14 vs 15 changed 0/60 at depth12 and 58/60 node totals and 7 moves at 250k, both Windows and Linux. A23 81/67 same-FEN different-history fixtures reproduced byte-for-byte on Windows. W2 old PC cleanup 8/10 vs repaired 20/20; precise old failure cause still unconfirmed.

A24 is jointly agreed, awaiting Fable as of the fourth batch: Astra 100437Z/104027Z, Neon 103953Z, joint 104059Z. Bind the actual final gathered features/material head/active targets to independently decoded source row IDs. Both seats matched 257/257 rows; two head7/+2cp examples had identical aggregate losses after their targets were swapped but different gradients. The three eventual per-example fault counts were 2, 256, 2; clean and whole-tuple reorder matched. W5 arrival-order example 102528Z is a measurement/question, no proposal before PC evidence. At 2k/8k reversing whole games changed 517/421 raw scores, but no natural collision met the intentionally conservative ≥8/nonbare-at-both-ends screen. Asked Fable whether production first-four-field dedup retains +19 or +42 on game408/4090, or already imposes canonical order. Teacher identity question is whether branch legacy HCE+residual totals equal the PC b_full; 64 example component rows in 102430Z.

## Completed studies and interpretation

- A19 warm 2k vs 8k. Original full-state 2k reproduction; internal 128k score-target discrepancy fell 16.02%, independent SF500k numeric-target MAE fell 3.40% [2.20,4.58] on 2,902 roots, SF2M 5.47% [2.99,7.90] on 382. Independent restricted best-move advantage +0.4195 expected-score pp. 8k produces 74.22% fewer rows per CPU-second. Actual frozen readout nearly unchanged (092804Z). Fully trained 128 models scored for larger 2k corpus 69.14% and 66.80% at 20k, 256 games (101658Z). In production-width 768 short warm-start fine-tunes using 3 target terms, equal-cost static advantages split across references, and the 250k games were unresolved: shallow 50.78% [44.53,57.03] and 51.56% [46.09,57.03]. Anchor vs original r67 50.00/51.56%. Teacher-on/off 55.47% with lower exactly 50%, and 53.13% with lower 46.88%. Full 320 games, exact board/replay and twelve full fresh searches (2,118 plies). 105542Z asks Neon to verify/vote the full A19 interpretation: keep 2k now, retain future full controlled A19. Neon 103955Z supported this subject to verifying all 320. Bootstrap 384 original source IDs including one empty, Neon uses 383 represented; same inference.
- 103347Z N19: 192 true 10+0.1 games, no flags, clock/move records replayed. Sole move shortcut saved median 328.26ms and bank carried to next decision. Forced cohort 46W/36D/46L, all 64 pairs level; ordinary 16W/32D/16L. No playing gain shown. N20 095035Z: 512 complete clock-free paired 4k/2k games on unfiltered vs moderately unbalanced openings, information/CPU .864 [.506,1.470]; keep suite. Raw 8,192 start study detected opening-policy distribution change. W7 PC stride control found same-side adjacency 85.33%, reconstructed eligibility effects depend on true PC filter, not raw Linux figures.
- Natural castling 101213Z: 3,976 SF500k searches and 1,977 held-out natural games; adding two rights reduced MAE 0.9655% [0.1396,1.7729], below 2%. Keep architecture. Post-training head interpolation worsened MAE 0.643%. 768→640 compression +1.56% rows/s, +4.90% independent error. Quiet prior offline top-3 rose to 28.01% vs16.49%, but only 3.04% of relevant warm quiet cutoffs were tied and cutoff rank got worse. Exact pawn legality shortcut and sparse channel dot did not speed real work. Neon independently closed both original cache/fusion candidates at 103954Z; 104138Z identifies 720 zero row counts in r67 CSV and supplies 30 genuinely disjoint PGO starts for Neon's new AVX2-only run. 
- 101503Z 896 draw adjudications+64 controls×3 arms, 128 SF board-only completions: long streaks changed only .0517/.0735% of original raw rows on eligible games. Current count8 agreed 125/128, longer 124/128. Keep eight. 510 independent whole continuations did not validate changing score-scale K=2.25. Prior exact 4/5 material had same one error in 466; two six-man rook endgames had zero certified 250k errors in 370 classified selections. 103926Z high-clock 4/5-man damping changed 110/192 root moves at250k but prevented zero known errors in 186 classifiable +96 low-clock, unknown bounds −3…+3. 105613Z 1M 64 vs16 MiB changed 26/128 warmed moves and lowered median current-generation occupancy, independent +0.131pp [−0.150,+0.541], 2M sign reversed; keep current capacity.

## Current handoff

11:10 UTC. Owner's four-hour report delivered at 10:35:35Z; final comprehensive summary due before 12:35:35Z. Fable's fourth issued batch at 4d0e89f0176be77afd03aaca8f72c5a34050a2a1 contains 15 actual entries (8 current checks, 7 later projects). A24 is jointly agreed, waiting Fable; A19 joint evidence update (existing entry) 110211Z follows my 105542Z and Neon's 110117Z verification of all 320 fullwidth games and other recent results. W5 PC actual first-arrival dedup filter and legacy b_full identity remain open. Neon has our 30 disjoint PGO roots and is testing AVX2 on matched compiler profiles and real 80/5/8/300 selfgame; original kernels failed. No reported credit exhaustion.

110437Z: all six uniform quarter-relabel nets and 128 additional played games complete. 32,564 extra 8k searches; equal 812.506 generation CPU seconds funds 3,196 instead of 4,096 games. Independent 510-game SF500k error increased 1.29% and 0.82% across two seeds. At uncapped generation cost <0.02% improvement. Matched 20k games scored .5391 [.4688,.6172] and .5078 [.4375,.5859] for mixed vs all shallow. Both gates failed; stay at 2k. Signed notes and full ledgers in 110128Z/110437Z.

104537Z synthetic mate conversion: all 512 full games and 32 first/last independent engine replays finished, full per-ply legal and defender audit running in phase4-minormate. One real 8,192-game natural-chess study 105833Z still progressing in phase4-naturalminor, first qualifying KBN/KBB entries retain true history, stock vs exact reducing-DTZ attacker. Four deployed table files alone need drawn ending resolution in chosen probing library (160 bytes two tiny drawn WDL tables or a verified tiny fallback); require exact per-game evidence before proposing any future change. 110833Z new A19 alternative comparing two reflected 2k searches with one 4k search: 384 independent roots/10,663 legal children plus special controls; all actual evaluator inputs, raw sums and static scores match across the color-reflection. Search/independent references in phase4-mirrorlabels. No new approval or playing result. Next: answer peers, publish checked synthetic/natural results and only evidence-backed joint changes. Issue complete end summary after verified final fallback Markdown.

11:20 UTC. 111246Z synthetic conversion closed NEGATIVE. At 250k stock/full no-pruning actual mates 48/96 versus 32/96 (−16.67pp [−26.04,−8.33]); KBN 3/48 vs1/48, KBB 45/48 vs31/48, easy controls 16/16 each. At 20k 13 vs3. Every non-mate reached a draw by rule while still a table win ignoring the actual history. Complete 512-game raw and 32 sentinels published. The existing UCI DeadMaterial switch proved distinct: exact KBN bishop-corner drive is already implemented at eval.cpp:513–564 and is off in production. 111342Z prespecified 64 fresh KBN +48 new controls, earlier 48 KBN at two budgets, and every certified natural win retaining full history. Real off/on/off fixture 111534Z: UCI raw eval still +317 yet recognized static +700; cold 20k output changes d6f8 / +340 to a6b8 / +732 then recovers. Raw NNUE parity and an effective path check have different uses. New corner games running privately phase4-corner. 111749Z prespecified independent 10+0.1 and 1+0.1 timing bridge with ordinary stock defender, all certified roots, only if 105833Z natural 250k passes. Existing search_read handles this after original natural replay. Mirror label reference/controls continue in phase4-mirrorlabels; no score claims before completion. No new official addendum since fourth batch or credit-exhaustion report. Final still due 12:35:35Z.

11:29 UTC. Fable fifth addendum 182616Z/shared merge 00e3ac2a3ab715a083afc4c56067602fb96c5604: A24 entered with independent Windows 257-row check, and joint A19 evidence note entered inside existing A19 after Fable replayed all 320 games / six intervals. Thus 16 distinct after-close items (9 current checks, seven later projects). Fable positively established the production PC b_full is DIFFERENT, 1,122,555 bytes SHA beginning 574c69b62233a79e. My 112841Z corrects an extra '9' in the branch legacy teacher SHA; actual a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638. No inference from our legacy-teacher ablation to actual PC W11. Also independently reproduced the exact A24 loss sums in 112841Z.

Actual PC filter now verified order-sensitive (game408 +19/game4090 +42); Fable's new receiver used arrival order and is being changed. A26 112803Z formalizes canonical (worker, game, row) output with fixed membership per round, reversed/re-cut/retried delivery, planted first-wins failure and two-key plus round-reset controls. OPEN until Neon independently votes. A25 112653Z is a different, later playing-only proposal, also OPEN. 112610Z natural fixed-node evidence: 8,192 original games, 31 eligible wins, 25 KBN/6 KBB, exact 31/31 vs current 250k 7/31 (KBN 1 vs25, KBB6/6 both) against the same delaying defender. +24 mates per8,192 = +0.29297 percentage points [0.18311,0.41504]. All 93 continuations and 7,240 plies verified; all 1,047,129 source board rows and 8,192 endings checked. Twelve continuation sentinels/804 plies matched. The 124 clock continuations with ordinary stock defender have STARTED; no results claimed until independent audit. Late oracle rescue thresholds 0,25,50,75,never are preregistered 112048Z; phase4-lateminor. 112428Z observes completed iterative scores across all 384 original warm games against 2,902 SF references, fixed 75/25 averaging, no extra search nodes. Phase4-iterations in progress, alongside phase4-corner and phase4-mirrorlabels. Fable's final check is a few minutes AFTER our 12:35 cutoff; report outstanding decisions accordingly.

## Last shared commit read
00e3ac2a3ab7 in shared-branch Git order.
