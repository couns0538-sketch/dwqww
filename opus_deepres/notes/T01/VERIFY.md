# T01 adversarial verify (start 23:10 PC clock, stop by 23:35)

Method: PR / release text re-fetched with gh api (repos/OWNER/REPO/pulls/N, releases/tags/T); licence rows re-run with
tools/licence_at.py --row; lock greps re-run with tools/forge_has.sh; local records re-read at the cited file:line.
Format: card | claim | verdict | evidence.

## 1. Source numbers (top 3 full cards: T01-01, T01-02, T01-03; one-liners spot-checked: T01-04, T01-05, plus T01-06)
- T01-01 | Viridithas PR 425 25k nodes +27.43 +- 7.91, 3,046 g, LLR 3.10 [0,3] | CONFIRMED | https://github.com/cosmobobak/viridithas/pull/425 (viri.dev 604)
- T01-01 | PR 425 STC 8+0.08 1 thread 16 MB +2.98 +- 2.09, 30,040 g, LLR 3.06 [0,3] | CONFIRMED | PR 425 text (viri.dev 605)
- T01-01 | PR 425 LTC 40+0.4 1 thread 128 MB +5.38 +- 2.97, 12,730 g, LLR 2.98 [0,3] | CONFIRMED | PR 425 text (viri.dev 607)
- T01-01 | PR 425 arch change (704x16hm -> 2560) to (704x16hm + 60144hm -> 1024), L2 16 -> 32, king threats excluded, ~87 % speed on AVX-512, merge c14c332a 2026-04-15, no book named | CONFIRMED | PR 425 text; same numbers in viridithas-networks release v105
- T01-01 | Integral PR 243 LTC 40+0.4 1 thread 32 MB +24.43 +- 7.77, 1,866 g, LLR 2.89 [0,4], merge 0ff72c5f 2026-08-30 | CONFIRMED | https://github.com/aronpetko/integral/pull/243 (furybench 7273)
- T01-01 | Integral PR 266 merged accumulators +6 % speed on a 7900X | CONFIRMED | https://github.com/aronpetko/integral/pull/266
- T01-01 | Integral README arch: 16 king buckets hm factorised + 1x11 HMC + 59808hm threats + 4560hm pawn pairs -> L1 768, 8 output buckets | CONFIRMED | https://github.com/aronpetko/integral/blob/29456bb34c/README.md lines 19, 21 (README = allowed)
- T01-01 | bullet example: threat cap 128 active, pawn pairs 4,560 (96*95/2) with cap 120 (16*15/2) | CONFIRMED | D:/o30/bullet examples/advanced/inputs.rs:95-96, 224-225 (MIT). 59,808 threat total is computed at run time, not a literal; corroborated by viridithas-networks v107 release text (59808 + 4560) and the Integral README
- T01-01 | "2.8-4.4M pos/s at H256" on our ROCm bullet | CONFIRMED | D:/o30/FINAL_REPORT.md:150 (2.78M, r1_kb4), :151 (4.20M), :153 (4.37M)
- T01-01 | ours: R13 P4 ForgeV2 stage b = O6 threats 9216 count-valued, c = O7 pawn pairs 1792 | CONFIRMED | D:/grok-pc-data/dwqww/<cfg>/worktrees/o13-p4/opus_r13/p4/RESULTS.md:17-18
- T01-01, T01-03 | "vs the lock exe it also carries the v2 path's own cost (identical-eval control -32.2 +- 18.5)" | CORRECTED | D:/o30/FINAL_REPORT.md:48, 691-695, 721-724: -32.2 +- 18.5 was the OLD exe's control (patch 378bf6bc, lazy root accumulator, R-A2); fixed 2026-11-04 by patch 926ada2c; the gate exe v2p4 control read -20.9 +- 18.5 (FINAL_REPORT.md:28-29, sanity only); no control of the root-fixed exe is in the cited lines. Note added in both cards
- T01-02 | Integral PR 266 Ranger vs AdamW STC 10+0.1 1 thread 16 MB +3.22 +- 2.26, 25,378 g, penta 116/2941/6356/3144/132, LLR 2.90 [0,3], merge c06f3e1f 2026-10-27 | CONFIRMED | https://github.com/aronpetko/integral/pull/266. Note: the same PR also raised L1 to 1024 and merged accumulators; the text does not say which net size the Ranger test used
- T01-02 | Viridithas v108 LTC 40+0.4 1 thread 128 MB +8.98 +- 3.92, 7,004 g, penta 5/888/1896/709/4, LLR 2.98 [0,3], viri.dev 676 | CONFIRMED | https://github.com/cosmobobak/viridithas-networks/releases/tag/v108
- T01-02 | v108 is "vs the Adam-trained net" and a "threat + pawn-pair net (v107 arch)" | CORRECTED | the v108 release text says only "Trained with Ranger, instead of Adam."; baseline and arch are an inference from v107 (published 2026-06-20, arch with 59808 + 4560). Note added in the card
- T01-02 | bullet RangerParams defaults decay 0.01, betas 0.99 / 0.999, clip +-1.98, alpha 0.5, k 6; AdamW defaults decay 0.01, clip +-1.98 | CONFIRMED | D:/o30/bullet crates/trainer/src/optimiser/ranger.rs:163-177, adam.rs:28-29 (MIT). The local copy has no .git: its da426a49 identity is as recorded, not re-proven here
- T01-02 | bullet nn.rs:25-46 ships RangerOptimiser beside AdamW | CONFIRMED | D:/o30/bullet crates/bullet_lib/src/nn.rs:25-46
- T01-02 | our trainer main.rs:331 sets AdamWParams from O30_CLIP / O30_DECAY | CONFIRMED | D:/o30/wt/opus_30h/a/forge_v2_bullet_o30/src/main.rs:331
- T01-02 | lock net reaches max |w| 3.47 | CONFIRMED | D:/o30/FINAL_REPORT.md:254, 738 (G-001)
- T01-03, T01-06 | Viridithas v102: 400 SB pure WDL, cosine 2.5e-5 -> 2.5e-5 x 0.3^5; LTC 40+0.4 1 thread 128 MB +2.38 +- 1.74, 36,436 g, LLR 3.05 [0,3] | CONFIRMED | https://github.com/cosmobobak/viridithas-networks/releases/tag/v102 (test link is test.expositor.dev/test/463, not viri.dev)
- T01-03 | 30-h method: KB8 + OB8, H256, clip +-7.99, decay 0; 2e-5 cosine to 2e-7; 1,024 batches x 16,384 per SB (200 SB = 3.36G) | CONFIRMED | D:/o30/FINAL_REPORT.md:151, 153
- T01-03 | lr 3e-5 worse on the KB8 warm start | CONFIRMED | D:/o30/FINAL_REPORT.md:155, 372
- T01-03 | recipe seed noise ~4e-6 on S31 | CONFIRMED | D:/o30/FINAL_REPORT.md:375
- T01-03 | npt L1 1024 from scratch -86 to -116 Elo | CONFIRMED | notes/TRIED_GATES.md:102-106 (NPTS3-06 -86.17, NPTS3-09L / NPTW4S4-07 -116.23)
- T01-03 | bullet KB4 from scratch worse than the lock at 1.46G | CONFIRMED | D:/o30/FINAL_REPORT.md:150 (from scratch), :162 (1.46G S31 +7.72e-4, FAIL)
- T01-03 | "our data is 305M rows" (also notes/T01/recipes.md:47, 60) | UNVERIFIABLE | not found in D:/o30/FINAL_REPORT.md, D:/o30/wt/opus_30h/a/RESULTS.md, skills forge-o30-v2net / forge-nnue-data; no file is cited for it
- T01-03 | R2 400 SB = 6.7G positions = 25-37 min at 3-4.4M pos/s; fits a GPU-day while threats slow training < ~40x | CONFIRMED | arithmetic: 400 x 16,777,216 = 6.71G; 6.71G / 4.4M = 25.4 min, / 3.0M = 37.3 min; 1,440 / 37.3 = 38.6x
- T01-03 | bullet example stages 100 + 800 + 200 SB; LR 1e-4 -> 5e-3 -> 1e-4, 1e-3 -> 1e-6, 1e-5 -> 1e-7 (all linear); WDL 0.2, 0.2 -> 0.5, 1.0 | CONFIRMED | D:/o30/bullet examples/advanced/main.rs:38-40, 199-218 (MIT)
- T01-03 | Licence line "All start values below are our own, none from another engine" | CORRECTED | R1's 200 SB, LR 1e-5 -> 1e-7, WDL 1.0 equal the bullet example's stage 3 (main.rs:40, 217-218; T01-06 says so itself); allowed (bullet is an MIT trainer, not an engine) but not "own". Owner note: the example's NET_NAME is "pawnocchio_new_relabeller" and DATA_PATH "data/viri.vf" (main.rs:31, 36), so the schedule may come from another engine's training; it reaches us under bullet's MIT licence. Note added in the card
- T01-04 | Integral PR 256 STC 10+0.1 1 thread 16 MB +4.23 +- 2.65, 17,076 g, LLR 2.90 [0,3]; LTC 40+0.4 128 MB +2.17 +- 1.64, 39,946 g, LLR 2.99 [0,3]; no nps | CONFIRMED | https://github.com/aronpetko/integral/pull/256 (furybench 7503 / 7504)
- T01-04 | "HMC" = 1x11 fifty-move-rule (halfmove-clock) inputs | CONFIRMED | Integral README at 29456bb34c lines 19, 21
- T01-04 | our KB16: S31 -1.80e-4, ~0.969x the nps of KB4 | CONFIRMED | D:/o30/FINAL_REPORT.md:22, 376 (S31), 288-289 (nps vs KB4, mean of 4 runs)
- T01-04 | KB16 "lowest of the layouts in sanity play" | CORRECTED | D:/o30/FINAL_REPORT.md:28-33: KB16 single run 7 +4.3 +- 17.8 and V16 +9.3 +- 22.0 are above KB4 run 2 and KB32 Z32 (both -2.6); only the KB16 soup P16 was lowest (-15.7 +- 23.7, 200 g); all sanity only, within noise. Note added in the card
- T01-05 | Viridithas PR 445 25k nodes 1 thread 16 MB +3.65 +- 3.00, 19,144 g, penta 326/2384/4320/2249/293, LLR +2.13 of +-2.94 [0,3], unfinished, merged 331e83f0 2026-06-20 | CONFIRMED | https://github.com/cosmobobak/viridithas/pull/445 (viri.dev 668)
- T01-06 | our trainer's wdl argument defaults to 0.4 | CONFIRMED | D:/o30/wt/opus_30h/a/forge_v2_bullet_o30/src/main.rs:287

## 2. Reading rule
- all T01 cards + notes | links to GPL / AGPL / unlicensed repos are PR pages, release pages and README blobs only (Integral README @29456bb34c, Viridithas README @7489e701bb); no /blob/ or raw link to a source file of such a repo | CONFIRMED | grep 'blob/|raw.githubusercontent' over cards/T01 notes/T01: README only
- T01-01 / T01-02 / T01-03 | source files read are bullet (MIT) only; no Stockfish / nnue-pytorch source; npt appears only as our own tool config | CONFIRMED | sources.md lines 1, 6b, 13b; cards' Licence sections
- T01-01 | Mechanism describes bullet's threat index layout in words (MIT source, allowed); no code pasted | CONFIRMED | card text
- T01-02 / T01-03 R3 | start values = bullet's own RangerParams defaults (MIT trainer library, not an engine's tuned constants) | CONFIRMED (no violation) | ranger.rs:163-177
- VIOLATIONS found: none

## 3. Licence rows (tools/licence_at.py --row re-run 23:11)
- jw1912/bullet da426a49b2 MIT | CONFIRMED | matches licences.md
- cosmobobak/viridithas 7489e701bb AGPL-3.0 | CONFIRMED | matches
- aronpetko/integral 29456bb34c absent (no licence) | CONFIRMED | matches
- cosmobobak/viridithas-networks d3da3953e4 CC0-1.0 | CONFIRMED | matches
- cosmobobak/viridithas v20.0.0 = 0631113e22 LICENSE MIT (api: AGPL-3.0) | CONFIRMED | matches (owner item stands)
- Witek902/Caissa row: not cited by any T01 card, not re-run. HF dataset row (aronpetkovski/integral-datasets): not a GitHub repo, not re-run (UNVERIFIABLE with licence_at.py)

## 4. Forge has it (tools/forge_has.sh re-run)
- T01-01 / T01-03 | 'threat' = 18 hits, hand-crafted eval only, src/eval.cpp:276 evaluate_threats, include/forge/eval_params.hpp:39 | CONFIRMED
- T01-02 | 'adamw|ranger' = 0 hits | CONFIRMED
- T01-04 | 'rule50|halfmove|fifty' = "board / TT fields only" | CORRECTED (minor) | 32 hits: board.hpp / board.cpp, search.hpp TT entry, and search.cpp TT store / usability and draw checks (694, 922, 1309); none in eval.cpp or nnue.cpp, so "no halfmove-clock net input" stands. Note added in the card
- T01-05 | 'pawn.?pair' = 0 hits | CONFIRMED

## 5. Labels, names, lint
- every Forge-side estimate in the 6 cards carries UNPROVEN; recipes.md:5 + each table row | CONFIRMED
- vendor / model-company names: card_lint vendor scan clean on cards/T01/*.md and notes/T01/*.md | CONFIRMED
- card_lint cards/T01/*.md: 6 files, 0 findings, 0 PENDING (before and after the verify notes) | CONFIRMED
