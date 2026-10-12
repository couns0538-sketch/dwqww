# Release 6.0.0 strength validation

## Reference opponent

Stockfish 19 (official `sf_19` release, `stockfish-linux-x86-64-universal`) with
`UCI_LimitStrength=true`, `UCI_Elo=2800`, `Threads=1`, `Hash=64`. At this setting
Stockfish chooses its move at depth 11 from a MultiPV-4 set with the skill-level
randomisation (`Skill::pick_best`); its Elo scale is anchored to CCRL blitz
ratings. Its playing strength is therefore essentially independent of the time
control, while Forge's is not.

## Match setup

- fastchess 1.8.2-alpha, `-repeat` colour-swapped pairs, `-recover`
- Openings: `8moves_v3.pgn` (official-stockfish/books), random order, 16 plies
- Forge: `Hash=64`, default options, one thread
- Hardware: 4-core Intel Xeon VM shared with the match runner; concurrency 3-4
- No adjudication other than fastchess's rule-based endings; every game in the
  recorded matches terminated normally (no time forfeits)

## Results

| Engine | TC | Games | W / L / D | Score | Elo (fastchess) | Record |
| --- | --- | --- | --- | --- | --- | --- |
| Forge 5.31.0 (baseline) | 10+0.1 | 20 | 1 / 17 / 2 | 10.0 % | -382 | `forge-5.31.0-vs-sf19-2800-10+0.1.pgn` |
| Forge 6.0.0, hand-set evaluation | 10+0.1 | 100 | 47 / 32 / 21 | 57.5 % | +66 +/- 68 | `forge-6.0.0-handset-eval-vs-sf19-2800-10+0.1.pgn` |
| **Forge 6.0.0 (shipped)** | 10+0.1 | 200 | 118 / 42 / 40 | **69.0 %** | +158 +/- 48 | `forge-6.0.0-vs-sf19-2800-10+0.1.pgn` |
| **Forge 6.0.0 (shipped)** | 30+0.3 | 100 | 79 / 14 / 7 | **82.5 %** | +331 +/- 68 | `forge-6.0.0-vs-sf19-2800-30+0.3.pgn` |
| **Forge 6.1.0 (shipped)** | 10+0.1 | 200 | 134 / 34 / 32 | **75.0 %** | +224 +/- 48 | `forge-6.1.0-vs-sf19-2800-10+0.1.pgn` |

All 620 recorded games terminated normally. The 6.0.0 binary's `bench 11`
signature is 513922 nodes and the 6.1.0 binary's is 422451 nodes, identical to
the binaries used in the respective matches. Because the opponent's strength does not scale with time, the margin
grows at longer time controls; Stockfish's `UCI_Elo` calibration itself was done
at 60+0.6.

## Development A/B tests (fixed 25,000 nodes per move, self-play, 8moves_v3)

| Change | Games | Score |
| --- | --- | --- |
| Correction history, sorted move picker, TT prefetch vs initial rewrite | 300 | 53.2 % |
| Texel-tuned table (regularised) vs hand-set table | 300 | 68.0 % |
| Texel-tuned table (unregularised) vs hand-set table | 300 | 64.0 % |
| Second tuning iteration (44k games incl. 22k from the tuned engine) vs shipped table | 500 | 50.2 % (not adopted) |
| Quiet checks in quiescence search vs shipped search | 500 | 50.2 % (not adopted) |
| Retune on 61.5k games incl. 17.5k random-opening games vs 6.0.0 table, 8moves_v3 openings | 300 | 53.2 % (adopted in 6.1.0) |
| Same retune, random EPD openings | 300 | 54.0 % (adopted in 6.1.0) |
| NNUE 768x256 trained on 3.5M positions vs tuned HCE | 300 | 9.5 % (not adopted; overfit) |

## 6.1.0 multi-threading (8+0.08, concurrency 1, four-core VM)

| Match | Games | W / L / D | Score |
| --- | --- | --- | --- |
| Threads=4 vs Threads=1 (same binary) | 50 | 26 / 1 / 23 | 75.0 % |

## Tuning data

22,000 self-play games at 10,000 nodes per move (hand-set evaluation engine),
8moves_v3 openings, draw adjudication from move 40 (8 moves within +/-15 cp),
resign adjudication (4 moves beyond 600 cp). `forge_extract` kept 1,715,952
quiet, non-book positions with the search score; `forge_texel` fitted the table
with Adam (learning rate 1.0 halved every 200 epochs, 600 epochs, lambda 0.5
result/score blend, regularisation 2e-9, rarity threshold 0.5 %).
