# Release 6.0.0 strength validation

## Reference opponent

Stockfish 19 (official `sf_19` release, `stockfish-linux-x86-64-universal`) with
`UCI_LimitStrength=true`, `UCI_Elo=2800` (6.0.0 and 6.1.0 matches) or
`UCI_Elo=3000` (6.2.0 matches), `Threads=1`, `Hash=64`. At these settings
Stockfish chooses its move at a limited depth from a MultiPV-4 set with the
skill-level randomisation (`Skill::pick_best`); its Elo scale is anchored to
CCRL blitz ratings. Its playing strength is therefore essentially independent
of the time control, while Forge's is not.

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

### Stockfish 19 at `UCI_Elo=3000`

| Engine | TC | Games | W / L / D | Score | Elo (fastchess) | Record |
| --- | --- | --- | --- | --- | --- | --- |
| Forge 6.2.0 pre-release build (before the move-picker change; `bench 11` = 335062) | 10+0.1 | 200 | 66 / 75 / 59 | 47.75 % | -16 +/- 42 | `forge-6.2.0pre-vs-sf19-3000-10+0.1.pgn` |
| **Forge 6.2.0 (shipped)** | 20+0.2 | 100 | 35 / 32 / 33 | **51.5 %** | +10 +/- 60 | `forge-6.2.0-vs-sf19-3000-20+0.2.pgn` |
| **Forge 6.3.0 (shipped)** | 20+0.2 | 100 | 33 / 33 / 34 | **50.0 %** | 0 +/- 54 | `forge-6.3.0-vs-sf19-3000-20+0.2.pgn` |

All 1020 recorded games terminated normally. The 6.0.0 binary's `bench 11`
signature is 513922 nodes, the 6.1.0 binary's is 422451 nodes, the 6.2.0
binary's is 340241 nodes and the 6.3.0 binary's is 344040 nodes, identical to
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

## 6.2.0 development tests (fixed 20,000 nodes per move, self-play, 8moves_v3)

SPRT runs use fastchess with `elo0=0 elo1=5 alpha=0.05 beta=0.05` (normalized
model) against the same binary with default options.

| Change | Games | Score | LLR | Decision |
| --- | --- | --- | --- | --- |
| Cutoff-count LMR (`LmrCutoffThreshold=3`) | 2804 | 53.0 % (894W 726L 1184D) | 2.96, H1 accepted | adopted (+21 Elo) |
| Material correction history (`MaterialCorrectionWeight=100`) | 3200 | 50.8 % | 0.60 | kept (inconclusive) |
| Null-move pruning from depth 2 (`NullMoveMinDepth=2`) | 3000 | 50.2 % | -0.06 | not adopted |
| Capture futility pruning (`CaptureFutilityBase=300`) | 5800 | 50.35 % (1686W 1645L 2469D) | 0.22 (60-minute cap) | not adopted |
| Fail-low continuation bonus (`FailLowContinuationBonus=100`) | 2000 | 50.5 % (555W 536L 909D) | 0.17 | not adopted |
| Lazy move picker vs previous picker (400-game match, no SPRT) | 400 | 51.5 % (110W 98L 192D) | - | adopted (speed-up; same node budget) |
| Opening book on vs. off (10+0.1, 60 pairs, no SPRT) | 120 | 52.9 % (18W 11L 91D) | - | book shipped on by default |
| `TmSoftDivisor=18` vs 22 (10+0.1, 100 pairs, no SPRT) | 200 | 49.75 % (33W 34L 133D), no time forfeits | - | not adopted |

## 6.3.0 development tests (fixed 20,000 nodes per move, self-play, 8moves_v3)

SPRT runs as above (`elo0=0 elo1=5 alpha=0.05 beta=0.05`, normalized model,
test build with the listed options vs the same binary with the 6.2.0
defaults). Runs marked "stopped" were ended under the pre-stated rule
"reject at or below 50.5 % after 1500 games"; "limit" means the run reached
fastchess's 8000-game maximum without hitting a bound.

| Change | Games | Score | LLR | Decision |
| --- | --- | --- | --- | --- |
| `LmpBase=4` + `HistoryBonusMax=2048` + `HistoryBonusQuadratic=20` | 3670 | 52.37 % (1122W 948L 1600D) | 2.97, H1 accepted | adopted (+16 +/- 8 Elo) |
| `LmpBase=4` alone | 8000 (limit) | 50.53 % (2261W 2176L 3563D) | 0.86 | inconclusive alone; adopted in the combination |
| `HistoryBonusMax=2048` + `HistoryBonusQuadratic=20` alone | 8000 (limit) | 50.30 % (2295W 2247L 3458D) | 0.10 | inconclusive alone; adopted in the combination |
| `SingularMargin=1` | 1600 (stopped) | 49.84 % (462W 467L 671D) | -0.26 | not adopted |
| `ProbcutDepth=4` | 3800 (stopped) | 49.92 % (1060W 1066L 1674D) | -0.51 | not adopted |
| `LmrHistoryDivisor=4000` | 1800 (stopped) | 50.39 % (506W 492L 802D) | 0.09 | not adopted |
| `RfpMargin=60` | 1600 (stopped) | 49.91 % (437W 440L 723D) | -0.23 | not adopted |
| Pawn islands + candidate passer evaluation terms, table refitted (400-game match vs 6.2.0, no SPRT) | 400 | 49.4 % (110W 115L 175D) | - | not adopted (reverted) |
| NNUE 768x256 retrained on 9.4M positions | - | best validation loss 0.0333 vs 0.0294 for the hand-crafted evaluation | - | not played; no weights shipped |

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
