# T01B table: net feature levers still open (pairwise, king-map shapes at equal count, per-feature-set data / L1 / nps)

Written from 01:08 PC clock (last clock read while editing: 01:13). "+x" = Elo +- 95 % error as printed by the source. Every Forge-side number is
**UNPROVEN**. V = Viridithas, I = Integral (both from notes/T01/sources.md, not re-read here), SP = Stormphrax,
PC = PlentyChess, Ob = Obsidian. Licences: SP / PC / Ob GPL-3.0, V AGPL-3.0, I none = ideas only (PR / commit text);
bullet MIT; viridithas-networks release text CC0-1.0; forum text has no licence row.

## A. Candidates (idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict)
| # | idea | source + link | licence | logged numbers | Forge has it | verdict |
|---|---|---|---|---|---|---|
| 1 | pairwise clipped product instead of SCReLU, single hidden layer | Ob beaa1374 https://github.com/gab8192/Obsidian/commit/beaa13742e08a40c1e766db74c750e65c4393222 | GPL-3.0 ideas only | STC 6+0.06 +3.18 +- 2.10 (29,514 g, [0,2.5]; "false tc due to broken nps") | no: include/forge/nnue.hpp:11 SCReLU; v2port.patch:21; trainer main.rs:316-317 | card T01B-01 |
| 2 | pairwise inside a new layer stack | SP PR 237 https://github.com/Ciekce/Stormphrax/pull/237 ; V net v92 (notes/T01 row 11) | GPL-3.0 / CC0 text | SP: 25k +41.04, STC +8.15 ([-3,1]), LTC +22.69 +- 6.51 (2,730 g); V v92 LTC +9.44 +- 4.12 (T01) | no L2 in v2 | no card: confounded, layers after L1 are outside T1 |
| 3 | horizontal mirroring at an equal bucket count | SP PR 166 https://github.com/Ciekce/Stormphrax/pull/166 ; Ob d8e8007f https://github.com/gab8192/Obsidian/commit/d8e8007f151b341789ff66e6faaaa88256ce8ec5 ; Leorik https://talkchess.com/viewtopic.php?p=987095 | GPL-3.0 ideas only; forum text | SP (with L1 1536): STC -4.84 +- 4.02 FAILED, LTC +4.90 +- 2.91 (14,550 g); Ob (with 4 buckets, L1 768): STC +10.18 +- 5.92 (6,898 g); Leorik "+20", nps -10 %, no conditions; counterpoint https://talkchess.com/viewtopic.php?p=954027 : 64 squares vs 32 mirrored "not even 1 Elo on UHO", mirrored HalfKA "basically nil" (no TC / games) | partly: v2 flag bit 1 mirror (o30_v2net.py:16, :31; main.rs:214, :280), never trained (o30_v2net.py:8 exact start only unmirrored) | card T01B-02 |
| 4 | unmirrored back-rank-heavy shape at an equal count (own: rank 1 four file pairs, rank 2 halves, ranks 3-4 one, ranks 5-8 one = 8) | own idea; context: bullet examples/progression/3_input_buckets.rs (MIT) 10 mirrored back-rank-heavy buckets; Leorik's 5-bucket edge / centre map | MIT; forum text | none: no source compares shapes at an equal count (web search 00:49 found none); merging rarely visited king squares is called untested in https://talkchess.com/viewtopic.php?p=954027 | no: maps rank4 / x2 / x4 / x8 only (o30_v2net.py:47-59, main.rs:222-249) | no card (no source number); a second arm inside T01B-02, exact lock warm start |
| 5 | factorised king buckets (shared 768 block, zero start, merged at export) | PC PR 202 https://github.com/Yoshie2000/PlentyChess/pull/202 ; bullet 3_input_buckets.rs (MIT); V v99 (T01 row 11) | GPL-3.0 ideas only; MIT | PC STC 8+0.08 +2.84 +- 2.08 (30,054 g, [0,3]), no LTC; V v99 25k nodes +7.81 +- 4.08 (fixed nodes only) | no: 0 hits for "factor" in forge_v2_bullet_o30/src/main.rs, o30_v2net.py | below the T01B card bar (+2.84 STC, no LTC): row only; cheap own offline A/B (training only, exact warm start, ~2-3 crew h) |
| 6 | more king buckets (count) | SP PR 177 https://github.com/Ciekce/Stormphrax/pull/177 ; PC PR 183 / 256 https://github.com/Yoshie2000/PlentyChess/pull/256 | GPL-3.0 ideas only | SP 16 buckets + L1 1280 (after PR 166's L1 1536; the previous count is not stated in the PR, 8 at PR 71): STC +13.72 +- 5.42 (5,296 g); PC first buckets STC +17.07 +- 7.64; PC 7 factorised buckets net STC +4.96 +- 2.96 / LTC +3.95 +- 2.52 (with more training) | yes: KB4-KB32 (forge-o30-v2net skill) | evidence for T01-04 |
| 7 | merged king planes (768 -> 704 per bucket) | V PR 221 (T01 row 8); SP commit 12ddec9f "support networks with merged king planes" | AGPL / GPL ideas only | V non-regression +0.29 +- 1.74 ([-3,0]); SP: no test | no: 768 per bucket (o30_expand_kb.py:27) | drop: under +1 Elo |
| 8 | accumulator refresh cache (finny table) | PC PR 183 | GPL-3.0 ideas only | STC +10.04 +- 5.65 (6,300 g) | yes: v2 per-worker cache (forge-o30-v2net skill, v2port) | no card (has it) |
| 9 | material output buckets | Ob 8361be0d (commit message) | GPL-3.0 ideas only | STC 8+0.08 +6.30 +- 4.50 (11,640 g) | yes: OB8 (o30_expand_kb.py:23; import_v2r.py:37) | no card (has it) |
| 10 | threat inputs with an L1 cut | PC PR 400 https://github.com/Yoshie2000/PlentyChess/pull/400 | GPL-3.0 ideas only | 20k nodes +45.49 +- 2.23; STC 8+0.08 -3.08 +- 2.89 FAILED; LTC +1.78 +- 1.37 (58,474 g) | no (T01-01) | evidence for T01-01: the speed cost shows as the STC fail |
| 11 | dual activation (square one copy, clip both, concat) after the first hidden layer | SP PR 239 https://github.com/Ciekce/Stormphrax/pull/239 | GPL-3.0 ideas only | STC +6.20 +- 3.44 (12,046 g), LTC +12.05 +- 4.69 (5,076 g) | no L2 in v2 | no card: needs a layer stack (outside T1); an FT-level analogue is untested anywhere |
| 12 | wider L1 alone | Ob 132e8653 (hidden 1280) | GPL-3.0 ideas only | STC -5.01 +- 5.23 FAILED, LTC +0.04 +- 5.02 | no (256) | no card: bigger L1 already reported on 30-Oct |
| 13 | regenerated / more data | SP PR 198 (net038 "first net on the regenerated dataset") | GPL-3.0 ideas only | STC +47.53 +- 10.30 (1,574 g) | n/a | no card: data lever (T2), confounded with the net |

## B. Per feature set: data size, L1 size, nps cost (as the sources state them; "missing" otherwise)
| feature set | engine / net | data size | L1 | nps cost | source |
|---|---|---|---|---|---|
| 768 piece-square, no buckets | Forge lock net | missing here (the lock net's own training set is not restated in this job's notes) | 256 | 1.00 (reference) | include/forge/nnue.hpp:11 |
| 768 piece-square, no buckets | V v61 | 963M positions | 768 | missing | notes/T01 row 11 |
| KB4 / KB8 / KB16 / KB32 unmirrored rank maps + OB8 | Forge v2 (30-h) | 304,999,573 rows | 256 | KB8 0.988x, KB16 0.969x, KB32 0.942x of KB4 (identity nets, same trees); gate exe + KB8 soup 0.893x, + KB32 soup 0.849x of the lock exe (different trees) | forge-o30-v2net skill |
| 4 mirrored buckets + 8 output buckets | Ob d8e8007f | missing | 768 | "25% speedup" over the previous net, which used "the 150MB table" | Ob commit message |
| 4 mirrored buckets | V v84 | missing | 1536 | missing | notes/T01 row 11 |
| 5 buckets (edge / centre) + mirroring | Leorik (forum) | "1B positions" of FRC games added; total missing | 640 | mirroring: "nps goes down by 10%" | talkchess p=987095 |
| 7 factorised buckets | PC 0058r | missing | missing | missing | PC PR 256 |
| 8 buckets | SP PR 71 (title) | missing | 1024 | missing | SP commit titles |
| 10 mirrored back-rank-heavy buckets + factoriser + 8 output buckets | bullet example progression 3 | missing (file name only) | 1024 | missing | bullet 3_input_buckets.rs (MIT) |
| 12 buckets | PC before PR 400 | missing | 1792 | missing | PC PR 400 |
| 16 buckets | SP PR 177; V v91; I PR 256 | missing; missing; "hundreds of millions" of games (I README) | 1280; 2048; 768 (README) / 1024 (PR 266) | missing | SP / PC PR text, notes/T01 |
| 16 mirrored buckets (704 merged planes) | SP PR 237 | missing | 1792 + layer stack | missing | SP PR 237 |
| threats (+ 704x16hm) | V PR 425 | missing | 2560 -> 1024 | ~87 % of the old speed (AVX-512) | notes/T01 row 3 |
| threats 60,144 (no king threats) + 704x16hm, layer stack | SP PR 293 | missing | 1792 -> 640 (L2 16 -> 32) | missing; split piece-square / threat accumulators (no threat refresh on a king-bucket change) STC +9.04 +- 4.10 (SP PR 291) | SP PR 291 / 293 |
| threats 79,856 + 768x12 | PC PR 400 | missing | 1792 -> 640 | missing (STC fail at +45 fixed-node Elo implies a large cost) | PC PR 400 |
| threats 59,808 + pawn pairs 4,560 + HMC 11 + 768x16hm | I README / PR 266 | "hundreds of millions" of games | 768 / 1024 | merged threat + piece-square accumulator +6 % | notes/T01 rows 6, 12 |
| pawn pairs 4,560 | V PR 445; SP PR 341 | missing | 1024 (V v107); 640 (SP, after PR 293) | missing (SP tests exclude its threat-inference speed-ups) | notes/T01 row 4; SP PR 341 |
| pairwise activation | Ob beaa1374; bullet advanced; SP PR 237 | missing | not stated (1280 at 132e8653; the later 62f32032 arch is not named); 768; 1792 | missing ("broken nps" on the test machines) | Ob commit, notes/T01 row 1 |
| factoriser (training only) | PC PR 202; bullet example | missing | missing; 1024 | 0 by construction (merged at export) | PC PR 202, bullet |

Gaps: no source states data size per feature set except V v61 (963M) and I ("hundreds of millions" of games); nps is
stated only for V threats (~87 %), I merged accumulator (+6 %), Ob mirrored KB4 (~+25 % vs a different net) and
Leorik mirroring (-10 %). Our own KB nps numbers are the only clean equal-tree bucket costs in this table.

## C. Evidence for existing cards (better or new numbers; no new card)
- T01-05 (pawn pairs): SP PR 341 https://github.com/Ciekce/Stormphrax/pull/341 - 25k nodes +6.36 +- 3.82 (15,470 g),
  STC 8+0.08 +2.08 +- 1.67 (57,208 g, LLR 2.92 [0,3]), LTC 40+0.4 +3.09 +- 2.15 (25,524 g, LLR 2.94 [0,3]) on a threat
  net; the card had only V's unfinished 25k-node test. This now meets "+2 at STC with LTC".
- T01-01 (threats): SP PR 293 https://github.com/Ciekce/Stormphrax/pull/293 - L1 1792 -> 640 with threats: STC +2.73 +-
  2.07 (37,524 g), LTC +9.85 +- 4.24 (6,736 g), 20+0.2 4 threads +13.03 +- 4.94; SP PR 291 split accumulators STC +9.04
  +- 4.10 (7,652 g); PC PR 400 https://github.com/Yoshie2000/PlentyChess/pull/400 - L1 1792 -> 640: 20k nodes +45.49,
  STC -3.08 +- 2.89 FAILED, LTC +1.78 +- 1.37 (58,474 g): the update cost can eat the whole gain at STC.
- T01-04 (more king buckets): SP PR 177 (16 buckets + L1 1280; previous count not stated) STC +13.72 +- 5.42 (5,296 g); PC PR
  256 (7 factorised buckets + longer training) STC +4.96 +- 2.96 / LTC +3.95 +- 2.52; both confounded.
