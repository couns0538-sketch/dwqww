# REPORT_deepseek5_job10 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: does a tree-size number belong to its position set — the opening set O (200 book lines) with the known sums, the whole-game set G built by my own runner, then the eight switches on both sets at depth 12. **The answers: (1) Part A: ALL SEVEN sums equal yours to the node — none 12,573,318 / ContHist4PlyRead 13,088,330 / LmrDeeperShallower 11,254,768 / NullThreatVerify 12,531,790 / none-again 12,573,318 (200/200 equal) / depth-16 none 67,796,692; (2) the two headline rows: LmrDeeperShallower O 0.8951 [0.849, 0.943] → G **1.0127 [0.964, 1.064]**; ContHist4PlyRead O 1.0410 [0.981, 1.107] → G **1.0053 [0.955, 1.054]** — on MY tree the numbers do NOT hold on whole-game positions: LmrDeeperShallower's big saving vanishes (your prediction 1.00–1.10 hit; my own 0.98–1.06 also covered it); (3) THREE of the eight switches FLIP SIGN between O and G with intervals that leave 1.0: AspCappedReopen 0.979 → **1.0654 [1.008, 1.128]**, SoundMatePruning 0.999 → **1.0614 [1.007, 1.119]**, ThreatHistory 1.034 → 0.9846 [0.936, 1.036] (its interval still covers 1); NullSeeVeto/NullThreatVerify/HindsightDepth keep their sign with shrinking or stable intervals. Your NullThreatVerify prediction (more differing positions on G than O, per 200) MISSED: 159 of 200 on O vs 209 of 353 on G = 118 per 200 — fewer.** How sure: sure of the O sums (they equal yours to the node); G's ratios carry bootstrap intervals over 353 positions; the position-dependence is measured, and the direction of the flip per switch is exact for this engine/net/option set.
2. Step 0: the default build (no patch, no plant), sha256 e06310ec…; the four known numbers printed in job 10's own run (`part A`'s none rows re-derived them: bench-level pins unchanged since job 7's check — the none-sum matching yours to the node IS the per-job check).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| set O built (first 200 lines, 4 fields + 0 1) | done | set_O.epd (committed) | 200 lines |
| A: depth 12, none ×2 + 3 switches | done | ds5j10/*.rows (committed) | all sums = yours; none-twice 200/200 equal |
| A: depth 16 none | done | none_set_O.epd_d16.rows | 67,796,692 = yours |
| B: 100 self-play games (nodes 5000) | done | setG_match.out + setG_games.pgn | 100/100 played |
| B: replay + collection | done | the collector (in this folder as make_setG.py) | 706 collected, 353 distinct → **G = all 353 (fewer than 400: said)** |
| B: description + histogram | done | set_G_description.txt | endings: mate 64, threefold 26, insufficient 4, fifty 6; histogram 32-27: 43, 26-21: 67, 20-15: 77, 14-9: 105, 8-3: 61 |
| B: ply-0 method check | done | the transcript line | 5/5 give back the opening FEN's first four fields |
| C prediction, own commit | done | prediction.txt (commit eaabcb6dc) | before any G search |
| C: O's five remaining switches | done | the .rows files | ThreatHistory 1.0342, NullSeeVeto 0.9886, AspCappedReopen 0.9786, HindsightDepth 1.0386, SoundMatePruning 0.9988 |
| C: G none twice + 8 switches d12 | done | the .rows files | **none-twice 353/353 equal**; the ratios in section 4 |
| C: Lmr + ContHist on G at d14 | done | the d14 .rows files | Lmr 0.9634 [0.897, 1.046]; ContHist 1.0284 [0.970, 1.099] |
| D (per-piece-class ratios) | NOT done | — | minute 42 arrived first |

**Part C's table (O beside G, depth 12; ratio of node sums, bootstrap 95 % over positions, 4,000 resamples seed 9101; nodes-differ = positions whose node count changed; bestmove-differ likewise):**

| switch | O ratio [ci] | G ratio [ci] | nodes differ O/G | bestmove differ O/G | halves O | halves G |
|---|---|---|---|---|---|---|
| LmrDeeperShallower | 0.8951 [0.849, 0.943] | **1.0127** [0.964, 1.064] | 200/352 | 58/97 | 0.892, 0.898 | 1.029, 0.996 |
| ContHist4PlyRead | 1.0410 [0.981, 1.107] | 1.0053 [0.955, 1.054] | 200/350 | 57/97 | 1.052, 1.031 | 1.023, 0.988 |
| NullThreatVerify | 0.9967 [0.990, 1.000] | 0.9986 [0.991, 1.006] | 159/209 | 0/3 | 0.993, 1.000 | 0.999, 0.998 |
| ThreatHistory | 1.0342 [0.975, 1.098] | **0.9846** [0.936, 1.036] | 200/351 | 63/111 | 1.092, 0.982 | 0.990, 0.979 |
| NullSeeVeto | 0.9886 [0.962, 1.016] | 0.9921 [0.965, 1.021] | 194/283 | 12/31 | 1.009, 0.970 | 0.996, 0.988 |
| AspCappedReopen | 0.9786 [0.925, 1.033] | **1.0654** [1.008, 1.128] | 184/338 | 52/96 | 1.017, 0.944 | 1.123, 1.007 |
| HindsightDepth | 1.0386 [0.976, 1.104] | 1.0216 [0.972, 1.072] | 200/352 | 62/102 | 1.050, 1.028 | 1.039, 1.004 |
| SoundMatePruning | 0.9988 [0.940, 1.058] | **1.0614** [1.007, 1.119] | 200/351 | 52/110 | 0.959, 1.035 | 1.093, 1.030 |

(depth 14 on G: LmrDeeperShallower 0.9634 [0.897, 1.046], ContHist4PlyRead 1.0284 [0.970, 1.099] — Lmr's G reading is not even stable from depth 12 to 14.)

4. Findings:
- **The position set changes the answer**: three switches flip sign (AspCappedReopen, SoundMatePruning, ThreatHistory) and LmrDeeperShallower's 10 % saving disappears entirely on whole-game positions. The "one number" of a tree-size table is a property of engine+net+options+POSITION SET+depth.
- The set O numbers reproduce a stranger's measurements to the node (all seven) — the harness, the exe and the position set are pinned by that agreement.
- The bestmove-differ counts move with the node-differ counts (more changed nodes → more changed moves) but not proportionally (NullThreatVerify: 159/209 node changes with only 0/3 bestmove changes — its effect stays inside the Principal Variation's ordering).
- Suspicions, not proven: G's positions come from 12,000-node self-play between the SAME engine — a self-play set may under-represent the positions where these switches differ most (both sides share the switches' biases); a set from ENGINE-vs-VARIANT games would sample differently.
5. From my partner: glmflash5's notes read at the step-A check (no new FOR-deepseek5 line; its fastchess process-reuse finding — one process per slot across a pair's both games — is the reason trace logs must be keyed by PID, now in my notes too). kimi5: its O-set numbers were the basis of a PC decision; my G-set table is the correction's measurement side on MY tree.
6. What I did NOT do: Part D (the per-piece-class ratios for LmrDeeperShallower); depth 16 on G (the clock); any second self-play batch for a second G (the set is one sample of one process).
7. What I am NOT sure about: the piece-count histogram's skew toward light positions (14-9: 105) — my plies (16..128 in steps of 16) undersample early middlegames; the bootstrap's independence assumption (positions from the same game correlate; the interval is over POSITIONS, not over games).
8. A better way: sample G from games played between DIFFERENT configurations (e.g. one switch on vs off) — the position set then covers the states where the switches actually act, instead of states two identical engines walk into; and record the ply of each collected position in set_G.epd's comment field so a per-ply breakdown is free later.
9. times: see stamps.txt
10. Model: deepseek5 — DeepSeek (the model serving this cloud-agent run).
