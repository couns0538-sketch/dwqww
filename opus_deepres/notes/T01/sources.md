# T01 sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")

Local read-only context (not counted as web sources): D:/o30/FINAL_REPORT.md lines 82-99 and 370-389 (v2 net
lessons, KB speed cost), forge-nnue-pipeline SKILL.md (npt recipe), forge-o30-v2net SKILL.md (bullet ROCm trainer),
notes/TRIED_GATES.md NPT rows, D:/grok-pc-data/dwqww/.claude/worktrees/o13-p4/opus_r13/p4/RESULTS.md (our bullet
input type ForgeV2 on bullet da426a49: stages a = 768 + OB8, b = + 9216 count-valued threats, c = + 1792 pawn pairs).

1. https://github.com/jw1912/bullet/tree/da426a49b2/examples/advanced (inputs.rs, main.rs) + crates/bullet_lib/src/game/inputs.rs | MIT (copy with notice) | a complete SPARSE threat + pawn-pair training config in bullet itself: threats 59,808 binary inputs (2 sides x 29,904), cap 128 active; pawn pairs 4,560 (3-file band), cap 120; 16 mirrored king buckets x 768 + factoriser; L1 768 pairwise, L2 16 dual (x, x^2), L3 32, 8 material output buckets; batch 131,072, 763 batches/SB (~100M pos/SB); 3 stages 100 + 800 + 200 SB (LR warm-up 1e-4->5e-3->1e-4, then 1e-3->1e-6, then 1e-5->1e-7; WDL 0.2, 0.2->0.5, 1.0); sigmoid 400; no Elo in the file | T01-01, T01-03 (recipe table)
2. https://github.com/cosmobobak/viridithas/releases (release notes v15-v20, read via gh api) | AGPL-3.0, ideas only (release text) | v20.0.0 (2026-06-27) vs v19: +60.84 +- 5.92, 60+0.6 1 thread 128 MB, 3000 games, penta 6/650/702/142/0 - ALL changes since v19 together (activation functions, threat inputs, swedishchef's pawn-pawn inputs, search); v19.0.1 vs v18 +46.12 +- 4.63 (5092 games, "evaluation scaling" net); no per-feature number | T01-01 (context)
