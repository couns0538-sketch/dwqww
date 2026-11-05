# T01 feature-cost table: data size / L1 size / nps cost / Elo per feature set and bucket layout (T01C)

Written 06:45-06:49 PC clock (start 06:42; review edits after 06:49). Answers the brief question notes/CRITIC.md lists as NOT COVERED ("data size /
L1 size / nps per feature set as one table"). Compiled ONLY from cards/T01/*, cards/T01B/*, notes/T01/*.md,
notes/T01B/*.md and the local records they cite (D:/o30/FINAL_REPORT.md lines 20-34, 284-292, 372-390; notes/T04O/TABLE.md
row 8, cited by T01B-02). No new web read; no number re-derived. "missing" = the source (as recorded in those notes) states
nothing. Nothing here is a Forge Elo claim: Forge rows quote our own offline holdout and 200-520-game sanity matches
(sanity only, not gates); every Forge-side estimate is **UNPROVEN**.

Conventions: "+x +- y" = Elo +- 95 % error as printed by the source; g = games; 25k / 20k = fixed nodes per move; STC 8+0.08
or 10+0.1, LTC 40+0.4 or 60+0.6; [a,b] = SPRT bounds; Threads=1 unless stated; no source names its opening book.
Engines and licences (ideas only = PR / commit / release / README text read, never source): V = Viridithas (AGPL-3.0),
I = Integral (no licence), SP = Stormphrax, PC = PlentyChess, Ob = Obsidian (all GPL-3.0); bullet and akimbo = MIT;
V net release text = viridithas-networks (CC0-1.0); Leorik = forum text. "hm" = horizontally mirrored.
Data column: positions where stated; other units (games, rows, "more data") are quoted as written. "Seen" = positions
passed through training (rows x epochs), not the dataset size.
Forge column: lock = FD3A5190, 768 -> 256 SCReLU, one output, no buckets / mirror / threats / pairs; v2 = EvalFileV2 path
(H256 SCReLU, KB4-KB32 rank maps, mirror flag bit 1 never trained, OB8; trainer forge_v2_bullet_o30 on bullet da426a49).

## 1. Piece-square base, king-bucket count, mirroring and map shape
| # | feature set | source engine + test / commit | data size (positions) | L1 size | nps cost | Elo with conditions | Forge relevance |
|---|---|---|---|---|---|---|---|
| 1 | 768 piece-square, no buckets, SCReLU (residual on the hand-crafted eval) | Forge lock net, include/forge/nnue.hpp:11 | missing (the lock net's training set is not restated in T01 / T01B notes) | 256 | 1.00 (reference) | reference | the lock; written exactly into any v2 KB map = the warm start of every v2 run |
| 2 | 768 piece-square, no buckets | V net v61 (release text; notes/T01/sources.md row 11) | 963M positions | 768 | missing | missing (no test in the notes) | lock's input set at 3x the width; context only |
| 3 | 768, 1 bucket, horizontally mirrored (board reflected when own king on e-h) | akimbo 7120b4b (MIT; notes/T04O/TABLE.md row 8, cited by T01B-02) | missing | missing (unchanged: both net files 1,184,320 bytes, 768 inputs) | missing (the Elo includes the d/e refresh cost) | STC 8+0.08 +17.16 +- 6.88 (4,864 g, LLR 2.91 [0,3], Hash 32 MB); recipe equality of the two nets unverified | the lock net's shape; lock lacks mirroring; v2 flag bit 1 exists, no mirrored net trained (T01B-02, estimate 0 to +2 over unmirrored KB8 **UNPROVEN**) |
| 4 | L1 1536 + horizontal mirroring (net032) | SP PR 166 | missing | 1536 | missing | 25k +34.97 +- 9.51 (2,522 g); STC 8+0.08 -4.84 +- 4.02 (9,190 g, LLR -2.29, FAILED [0,3]); LTC 40+0.4 +4.90 +- 2.91 (14,550 g, LLR 2.89 [0,3]); confounded with the L1 change | evidence for T01B-02 |
| 5 | 4 mirrored king buckets x 768 + 8 output buckets ("2x(4x768 -> 768) -> 8x1") | Ob d8e8007f (commit message) | missing | 768 | "25% speedup" vs the previous net, which used "the 150MB table" (a different net, not a bucket cost) | STC 10+0.1 +10.18 +- 5.92 (6,898 g, LLR 2.91 [0,3]) | KB4 + mirror + OB8 is a v2 file away (flag bit 1); not trained |
| 6 | 4 mirrored king buckets | V net v84 (release text; T01 sources row 11) | missing | 1536 | missing | missing (no test in the notes) | as row 5 |
| 7 | 5 buckets (rank 1 and ranks 2-3 split edge a,b,g,h / centre c-f; ranks 4-8 one) + mirroring | Leorik devlog, talkchess p=987095 (forum text) | "1B positions" of FRC games added; total missing | 640 | mirroring: "nps goes down by 10%" | mirroring "+20 Elo", no TC / games / error; all NNUE changes together ~+30 | own-shape context (T01B TABLE row 4); no v2 map of this shape |
| 8 | king buckets, first set (count missing) | PC PR 183 | missing | missing | missing | STC 8+0.08 +17.07 +- 7.64 (3,932 g) | v2 has KB4-KB32 |
| 9 | 7 factorised king buckets (net 0058r) | PC PR 256 | missing | missing | missing | 0058-320 vs 0057r STC +4.96 +- 2.96 (15,006 g) / LTC +3.95 +- 2.52 (18,018 g, Hash 64 MB), confounded by unstated differences; 0058 vs 0058-320 (longer training) STC +4.46 / LTC +4.46; 0058r vs 0058 (rescored) STC +5.17 / LTC +9.22 | evidence for T01-04 (confounded); no 7-bucket map in v2 |
| 10 | 8 king buckets | SP PR 71 (title "8 buckets, 1024 L1") | missing | 1024 | missing | missing (title only) | compare row 13 (Forge KB8) |
| 11 | 10 mirrored back-rank-heavy buckets + zero-init factoriser + 8 material output buckets | bullet examples/progression/3_input_buckets.rs (MIT) | missing (no data in the file) | 1024 SCReLU | missing | none in the file | open shape; v2 maps are rank4 / x2 / x4 / x8 only (o30_v2net.py:47-59) |
| 12 | KB4 (rank4 map, unmirrored) + OB8 | Forge v2, 30-h job (D:/o30/FINAL_REPORT.md:20-34, 284-292, 372-390) | 304,999,573 train rows (count from card T02-01 via notes/T01/recipes.md, not in the cited report lines); 200 SB x 1,024 x 16,384 = 3.36G seen per run; from scratch 1.46G seen | 256 (H256) | 1.000 (reference of rows 12-15; identity nets, same trees) | offline S31 paired vs the lock at 200 SB -1.41e-4; from scratch at 1.46G S31 +7.7e-4 (worse than the lock); sanity 10+0.1 vs the lock exe run 2 -2.6 +- 18.1 (400 g), sanity only | v2 path; the lock net on the gate exe v2p4 = -20.9 +- 18.5 (control, sanity only) |
| 13 | KB8 (rank4x2) + OB8 | same | same (304,999,573 rows) | 256 | 0.988x of KB4 (3 runs 0.983-0.997); gate exe + KB8 soup 0.893x of the lock exe (different trees, notes/T01B/TABLE.md B) | S31 -1.65e-4 (200 SB); 600-SB run 12 jobA -1.46e-4 (best single-net jobA); sanity run 5 +10.0 +- 16.1 (520 g), U8 +7.0 +- 19.7, Y8 +5.2 +- 18.2 (400 g each), sanity only | warm-start base of T01-03 R1-R3 and T01B-01 / T01B-02 |
| 14 | KB16 (rank4x4) + OB8 | same | same | 256 | 0.969x of KB4 (4 runs 0.956-0.985) | S31 -1.80e-4 (run 7, 200 SB); 600-SB run -1.42e-4; sanity run 7 +4.3 +- 17.8 (400 g), soup V16 +9.3 +- 22.0 (300 g), soup P16 -15.7 +- 23.7 (200 g), sanity only | T01-04: KB16 vs KB8 net pair (estimate 0 to +2 over KB8 at LTC **UNPROVEN**; ~3 % nps eats most of it) |
| 15 | KB32 (rank4x8) + OB8 | same | same | 256 | 0.942x of KB4 (3 runs 0.940-0.944); gate exe + KB32 soup 0.849x of the lock exe (different trees, TABLE B) | S31 -1.80e-4 (200 SB); 400-SB native r27 -1.43e-4; soups Z32 -2.24e-4, Z32c -2.34e-4 (best S31 of the job, selection-biased); sanity soupC +14.8 +- 18.0, Z32 -2.6 +- 17.8 (400 g each), sanity only | best offline layout; pays ~6 % nps vs KB4 |
| 15a | mirrored KB8 (own map: rank groups 1 / 2 / 3-4 / 5-8 x file pairs a-b / c-d on the a-d half) + OB8 | own design, card T01B-02 (v2 flag bit 1; no outside source at this count) | planned on the same 304,999,573 rows | 256 | missing (unmeasured; full refresh on each d/e king crossing) | missing (no mirrored net trained) | T01B-02: warm start exact for kings on a-d, approximate on e-h; estimate 0 to +2 over unmirrored KB8 before the refresh cost **UNPROVEN** |
| 15b | unmirrored back-rank-heavy 8 buckets (own: rank 1 four file pairs, rank 2 halves, ranks 3-4 one, ranks 5-8 one) + OB8 | own idea, notes/T01B/TABLE.md row 4 (second arm inside T01B-02) | as row 15a | 256 | missing | missing (no source compares shapes at an equal count) | exact lock warm start; no Forge estimate given |
| 16 | 12 king buckets (768x12) | PC, baseline of PR 400 | missing | 1792 | missing | missing (baseline only) | context |
| 17 | 16 king buckets + L1 1280 | SP PR 177 | missing | 1280 | missing | 25k +9.01 +- 4.66 (10,110 g); STC 8+0.08 +13.72 +- 5.42 (5,296 g, LLR 2.92 [0,3]); "tests predate cutnode lmr"; previous count not stated (8 at PR 71) | evidence for T01-04 (confounded) |
| 18 | 16 king buckets + L1 2048 | V net v91 (release text) | missing | 2048 | missing | 25k +31.64 +- 8.76 (games missing in the notes) | evidence for T01-04 (confounded) |
| 19 | 16 factorised mirrored buckets + 11 halfmove-clock ("HMC") inputs decoupled from the buckets | I PR 256 (+ README at 29456bb34c) | "hundreds of millions" of self-play games (README); positions missing | 768 (README) / 1024 (PR 266) | missing | STC 10+0.1 +4.23 +- 2.65 (17,076 g, LLR 2.90 [0,3]); LTC 40+0.4 Hash 128 MB +2.17 +- 1.64 (39,946 g, LLR 2.99 [0,3]); both levers in one test | T01-04 one-liner; v2 has KB16; no halfmove-clock net input anywhere in Forge |
| 20 | 16 mirrored buckets x 768 + factoriser (with rows 29 and 35) | bullet examples/advanced at da426a49 (MIT) | dataset not in the file; ~110G seen per run (100 + 800 + 200 SB x 763 batches x 131,072) | 768 pairwise | missing | none in the file | open config on our own bullet commit |
| 21 | merged king planes (768 -> 704 inputs per bucket) | V PR 221 / net v95.1; SP 12ddec9f / PR 179 | missing | missing | missing | V 2+0.02 +0.29 +- 1.74 (60,412 g, LLR 2.95 [-3,0], non-regression); SP no test | dropped (under +1); v2 = 768 per bucket (o30_expand_kb.py:27) |
| 22 | 704x16hm (merged planes) + layer stack, pairwise first activation | SP PR 237 | missing | 1792 + layer stack | missing | 25k +41.04 +- 2.23 (40,062 g); STC 8+0.08 +8.15 +- 5.10 ([-3,1]); LTC 40+0.4 +22.69 +- 6.51 (2,730 g); confounded | no L2 in v2; outside T1 |
| 23 | factorised king buckets (shared 768 block, zero start; training only) | PC PR 202; V net v99 ("whole-network factorisation"); bullet 3_input_buckets.rs (MIT) | missing | missing (PC, V); 1024 (bullet) | none at inference: bullet merges the block into the bucket weights when saving (MIT file) | PC STC 8+0.08 +2.84 +- 2.08 (30,054 g, LLR 2.90 [0,3]), no LTC; V v99 25k +7.81 +- 4.08 (11,082 g) and LTC 40+0.4 +2.06 +- 1.61 (47,132 g, LLR 2.96 [0,3]), confounded (fresh retrain); V v100 "L1 factorisation removed" + new schedule 25k -3.49 +- 3.18 (19,006 g), STC +4.84 +- 2.90 (15,854 g), confounded | v2 trainer has none (0 hits "factor"); T01B TABLE row 5: row only, cheap own offline A/B |

## 2. Output buckets
| # | feature set | source engine + test / commit | data size (positions) | L1 size | nps cost | Elo with conditions | Forge relevance |
|---|---|---|---|---|---|---|---|
| 24 | 8 material output buckets | Ob 8361be0d (commit message) | missing | missing | missing | STC 8+0.08 +6.30 +- 4.50 (11,640 g) | v2 has OB8 (o30_expand_kb.py:23; import_v2r.py:37); lock has one output |
| 25 | 8 material output buckets + "a larger dataset" | V net v86 (release text) | "a larger dataset", size missing | missing | missing | 25k +19.76 +- 6.80 (4,348 g); STC +23.89 +- 6.91 (2,826 g); confounded with the data | as row 24 |
| 26 | OB8 alone (on KB4-KB32) | Forge v2 | as rows 12-15 | 256 | missing (no OB8-only speed run; every row 12-15 includes OB8) | missing (no OB8-only offline or play number in the cited lines) | in v2 already |

## 3. Threat inputs
| # | feature set | source engine + test / commit | data size (positions) | L1 size | nps cost | Elo with conditions | Forge relevance |
|---|---|---|---|---|---|---|---|
| 27 | threats 60,144 hm (no threats involving a king) + 704x16hm | V PR 425 / net v105 (merge c14c332a) | missing | 2560 -> 1024 (L2 16 -> 32) | ~87 % of the old speed (AVX-512), net of the L1 cut | 25k +27.43 +- 7.91 (3,046 g); STC 8+0.08 16 MB +2.98 +- 2.09 (30,040 g, LLR 3.06 [0,3]); LTC 40+0.4 128 MB +5.38 +- 2.97 (12,730 g, LLR 2.98 [0,3]) | T01-01 (estimate 0 to +5 at LTC vs a v2 control **UNPROVEN**); lock and v2 have no threat inputs |
| 28 | same threat net, "additional data" | V net v105.1 (release text) | "additional data", size missing | 1024 | n/a (same shape) | 25k +6.15 +- 3.44 (15,096 g); STC 8+0.08 +5.33 +- 2.95 (14,674 g) [0,3] | data lever on a threat net |
| 29 | threats 59,808 binary (2 x 29,904; cap 128 active) | bullet examples/advanced (MIT) | as row 20 | 768 pairwise | missing | none in the file | T01-01 encoding source (MIT) |
| 30 | threat net, layout not in the PR (README today: 768x16hm factorised + 11 HMC + 59,808 threats + 4,560 pawn pairs) | I PR 243 (merge 0ff72c5f) | "hundreds of millions" of games (README) | 768 (README) / 1024 (PR 266) | missing | LTC 40+0.4 32 MB +24.43 +- 7.77 (1,866 g, LLR 2.89 [0,4]); new arch, confounded | T01-01 |
| 31 | threats 60,144 (none to / from kings) + 704x16hm, layer stack | SP PR 293 | missing | 1792 -> 640 (L2 16 -> 32) | missing | 25k +33.51 +- 9.35 (2,600 g); STC +2.73 +- 2.07 (37,524 g); LTC +9.85 +- 4.24 (6,736 g); 20+0.2 4 threads +13.03 +- 4.94 (5,042 g) | evidence for T01-01 |
| 32 | threats 79,856 + 768x12 | PC PR 400 | missing | 1792 -> 640 | missing (no number; the +45 fixed-node vs STC-fail gap is our reading of a speed cost, **UNPROVEN**) | 20k +45.49 +- 2.23 (40,034 g); STC 8+0.08 -3.08 +- 2.89 (15,354 g, LLR -2.26, FAILED [0,2.5]); LTC +1.78 +- 1.37 (58,474 g, LLR 2.90 [0,2.5]) | evidence for T01-01: the update cost can eat the gain at STC |
| 33 | O6 threats 9,216, count-valued (dense) | Forge ForgeV2 stage b (opus_r13/p4/RESULTS.md; forge-bundle-int b7c17722) | missing in T01 notes | missing in T01 notes | missing | missing (never gated) | must be re-encoded as binary indices for bullet's sparse input (T01-01) |

## 4. Pawn pairs
| # | feature set | source engine + test / commit | data size (positions) | L1 size | nps cost | Elo with conditions | Forge relevance |
|---|---|---|---|---|---|---|---|
| 34 | pawn pairs 4,560 (pairs within a three-file band) on a threat net (v107 arch) | V PR 445 (merge 331e83f0) / net v107 | missing | 1024 | missing | 25k 16 MB +3.65 +- 3.00 (19,144 g, LLR +2.13 of +-2.94 [0,3], unfinished, merged); no STC / LTC | T01-05 (estimate 0 to +2 on top of threats **UNPROVEN**); lock / v2: none |
| 35 | pawn pairs 4,560 (cap 120 active) | bullet examples/advanced (MIT) | as row 20 | 768 pairwise | missing | none in the file | encoding source (MIT) |
| 36 | pawn-pawn inputs on a threat net | SP PR 341 | missing | 640 | missing (its tests exclude its threat-inference speed-ups) | 25k +6.36 +- 3.82 (15,470 g); STC 8+0.08 +2.08 +- 1.67 (57,208 g, LLR 2.92 [0,3]); LTC 40+0.4 +3.09 +- 2.15 (25,524 g, LLR 2.94 [0,3]); with the speed-ups STC +10.54 +- 4.61 (7,516 g) | evidence for T01-05 |
| 37 | O7 pawn pairs 1,792 (dense) | Forge ForgeV2 stage c (forge-bundle-int b7c17722) | missing | missing | missing | missing (never gated) | T01-05 |

## 5. Activation on L1: pairwise product vs SCReLU (and post-L1 forms)
| # | feature set | source engine + test / commit | data size (positions) | L1 size | nps cost | Elo with conditions | Forge relevance |
|---|---|---|---|---|---|---|---|
| 38 | pairwise clipped product (CReLU) instead of SCReLU, single hidden layer | Ob beaa1374 | missing | not stated at that commit (1280 at 132e8653; 62f32032 arch not named) | missing ("false tc due to broken nps") | STC 6+0.06 16 MB +3.18 +- 2.10 (29,514 g, LLR 2.90 [0,2.5]); no LTC | T01B-01 (estimate 0 to +2 at equal width **UNPROVEN**); lock + v2 SCReLU (nnue.hpp:11, v2port.patch:21); no exact lock warm start at width 256 |
| 39 | pairwise after L1 in a new layer stack + feature permutation (2048x2 -(pairwise)-> 16 -> 32 -> 1) | V net v92 | missing | 2048 | missing | LTC +9.44 +- 4.12 (7,028 g); confounded (number from notes/T01/recipes.md; sources.md row 11 says no test parsed) | no L2 in v2 |
| 40 | pairwise mul support | SP PR 183 | missing | missing | missing | no test | context |
| 41 | dual activation after L1 (duplicate, square one copy, clip both, concat) | SP PR 239 | missing | missing | missing | 25k +6.95 +- 3.88 (12,744 g); STC +6.20 +- 3.44 (12,046 g); LTC +12.05 +- 4.69 (5,076 g) | needs a layer stack (outside T1) |

## 6. L1 width alone, and Forge's HalfKA net (context for the L1 column)
| # | feature set | source engine + test / commit | data size (positions) | L1 size | nps cost | Elo with conditions | Forge relevance |
|---|---|---|---|---|---|---|---|
| 42 | wider L1 alone | Ob 132e8653 | missing | 1280 | missing | STC -5.01 +- 5.23 FAILED; LTC +0.04 +- 5.02 | bigger L1 reported 30-Oct |
| 43 | L1 1024 (with Ranger) | I PR 266 | missing | 1024 | missing | 25k +21.35 +- 6.98 (3,470 g); 60+0.6 +0.70 +- 1.64 (38,948 g, LLR -0.03, unfinished) | fixed-node gains shrink at real TC |
| 44 | L1 2048 -> 2560 + more data | V net v101 | "more data", size missing | 2560 | missing | LTC +2.90 +- 2.04 (27,094 g); confounded | context |
| 45 | HalfKA K32H3^ | Forge npt nets (notes/T01/recipes.md "OUR npt"; notes/TRIED_GATES.md:102-106) | 344.4M-row inventory; 152.5M per epoch x 20 = 3.05G seen | 1024 | missing in T01 / T01B notes | gates NPT104 / NPTS3 / NPTW4S4 vs the lock: -86 to -116 | from scratch, lost; not the v2 path |

## 7. Cost mitigations for bucket / threat layouts (speed side)
| # | mechanism | source | nps / Elo as stated | Forge relevance |
|---|---|---|---|---|
| 46 | accumulator refresh cache (finny table) | PC PR 183 | STC 8+0.08 +10.04 +- 5.65 (6,300 g); nps missing | v2 has a per-worker refresh cache |
| 47 | split piece-square / threat accumulators (a king-bucket change does not refresh the threats) | SP PR 291 | STC +9.04 +- 4.10 (7,652 g); nps missing | design input for T01-01 |
| 48 | one merged threat + piece-square accumulator | I PR 266 | +6 % speed on a 7900X; STC 10+0.1 +1.70 +- 1.36 (55,874 g, LLR 2.90 [0,3]) | design input for T01-01 |
| 49 | FT -> L1 matmul in sparse blocks | SP PR 246 (title) | missing | Forge has find-nnz sparse L1 (already done) |

## Gaps (what no source in these notes states)
- Data size in positions: only V v61 (963M), our v2 (304,999,573 rows), our npt inventory (344.4M rows) and the bullet
  example's positions seen (~110G, dataset unstated); I gives "hundreds of millions" of games, Leorik "1B positions"
  added. Every other row: missing. No source ties a data size to a feature set's gain.
- nps cost: stated only for V threats (~87 %, net of an L1 cut), I merged accumulators (+6 %), Ob mirrored KB4 ("25%
  speedup" vs a different net), Leorik mirroring (-10 %) and our KB4-KB32 (identity nets, same trees). Missing for
  pawn pairs, output buckets, pairwise, halfmove-clock inputs and every outside bucket count; factorisers cost 0 at
  inference by construction (bullet merges them at save).
- Equal-L1 isolation: only akimbo 7120b4b (mirroring, 1 bucket) and our KB4-KB32 (H256) change one lever at a fixed L1;
  every threat row also changes L1 (2560 -> 1024, 1792 -> 640), so no source gives a threat cost at a fixed width.
- Nothing measured at Forge's L1 256 except our own KB rows; outside rows run L1 640-2560.

Sources: 4 card / note sets (cards/T01, cards/T01B, notes/T01, notes/T01B) + D:/o30/FINAL_REPORT.md (3 line ranges) +
notes/T04O/TABLE.md row 8; 0 web fetches; no source file of any GPL / AGPL / unlicensed repo opened.
