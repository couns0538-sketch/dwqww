# Forge 6.4 original match and experiment evidence audit

Audit date: 2026-10-19. Repository: `couns0538-sketch/dwqww`.

## Scope and immutable sources

- Engine/source commit: [`24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b`](https://github.com/couns0538-sketch/dwqww/commit/24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b), on `cursor/engine-strength-overhaul-66cc`.
- Match branch commit: [`f481fc5afc6bf13b730fe5853fbefaeeb6047162`](https://github.com/couns0538-sketch/dwqww/tree/f481fc5afc6bf13b730fe5853fbefaeeb6047162), on `cursor/match-pgns-66cc`.
- Original experiment ledger: [EXPERIMENTS.md](https://github.com/couns0538-sketch/dwqww/blob/f481fc5afc6bf13b730fe5853fbefaeeb6047162/EXPERIMENTS.md).
- Engine-side validation record: [validation/release-6.0.0/README.md](https://github.com/couns0538-sketch/dwqww/blob/24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b/validation/release-6.0.0/README.md).

This audit independently read the PGNs and checked bytes, results, pair structure and recorded termination reasons. It did not replay moves for legality, run new engine matches, rerun the old SPRTs or authenticate absent runner logs. Statements about options, training, old LLRs and historical adoption are attributed to the original ledger unless explicitly independently verified below.

## What is independently verified

The source commit contains `validation/release-6.0.0/all-match-pgns.zip`:

- Archive SHA-256: `acbd91b4a7f7829092eede5472e2c40de1e34f33e469f6b2927c61b58ad27960`.
- 44 PGNs, 281,063,155 uncompressed bytes, **76,047 games**.
- Recomputed Git blob SHA-1 and size of **every PGN exactly match** the 44 corresponding blobs in the match branch tree at `f481fc5...`. No missing files or mismatches.
- Every PGN result tag agrees with its final movetext result.
- All complete two-game rounds reverse engine colors. Nine stopped SPRT files have one unpaired final game; these are retained in the full-file game counts.
- All 76,047 recorded termination tags are either `normal` (28,225) or `adjudication` (47,822). There are no timeout, illegal-move or crash termination tags. This is evidence about recorded tags, not a new correctness certification.
- Fixed-opening pairs match through the first 16 plies. The start-position OwnBook test and random-EPD test naturally differ after play begins; the paired starting FENs agree in both.

Full per-file W/D/L, SHA-256, Git blob hash, controls, terminations, round counts and pair histograms are in `forge-match-raw-stats.json`. `forge-match-git-tree.json` contains the retrieved immutable Git tree. `audit_forge_match_archive.py` reproduces the audit with Python's standard library.

## The Stockfish claim, corrected precisely

**Forge 6.4's original Stockfish match is 100 games, not 1,000 games.** The 1,120-game total spans nine matches, several Forge versions, two limiter settings and three clocks. There are 500 Stockfish-3000 games across four Forge builds.

All W/L/D numbers in this table were independently counted from raw PGNs, from Forge's perspective:

| Forge build | Opponent label | Clock | Games | W / L / D | Score |
| --- | --- | --- | ---: | --- | ---: |
| 5.31.0 | SF19-2800 | 10+0.1 | 20 | 1 / 17 / 2 | 10.0% |
| 6.0.0, hand-set evaluation | SF19-2800 | 10+0.1 | 100 | 47 / 32 / 21 | 57.5% |
| 6.0.0, shipped tuned table | SF19-2800 | 10+0.1 | 200 | 118 / 42 / 40 | 69.0% |
| 6.0.0, shipped tuned table | SF19-2800 | 30+0.3 | 100 | 79 / 14 / 7 | 82.5% |
| 6.1.0 | SF19-2800 | 10+0.1 | 200 | 134 / 34 / 32 | 75.0% |
| 6.2.0 pre-release | SF19-3000 | 10+0.1 | 200 | 66 / 75 / 59 | 47.75% |
| 6.2.0 | SF19-3000 | 20+0.2 | 100 | 35 / 32 / 33 | 51.5% |
| 6.3.0 | SF19-3000 | 20+0.2 | 100 | 33 / 33 / 34 | 50.0% |
| **6.4.0** | **SF19-3000** | **20+0.2** | **100** | **35 / 30 / 35** | **52.5%** |

All 1,120 SF games record `Termination "normal"`. The 6.4 match has 50 complete color-swapped pairs. Its pair-score histogram at scores 0, 0.5, 1, 1.5, 2 is `[5, 8, 18, 15, 4]` from Forge's perspective.

The original ledger identifies the opponent as official Stockfish 19 (`sf_19`, `stockfish-linux-x86-64-universal`), with `UCI_LimitStrength=true`, `UCI_Elo=2800` or `3000`, `Threads=1`, `Hash=64`; Forge uses Hash64 and default one thread. PGN engine-name tags corroborate Stockfish19 and Forge version identities, but PGNs do not independently prove the UCI option values.

The ledger specifies fastchess alpha1.8.2 `20260726-f618e34`, `-repeat`, `-recover`, `timemargin=200`, `8moves_v3.pgn` from official-stockfish/books, random order, 16 opening plies, no evaluation adjudication for clock matches, and concurrency3–4 on a shared four-core Xeon VM. Source/book/binary hashes and the actual 6.x command/UCI logs are not present for these matches. These are historical setup claims, not values recovered from complete runner logs.

The original 6.4 report gives +17 +/-53 logistic Elo; its interval includes zero. The defensible statement is that Forge 6.4 scored52.5% in this 100-game limited-Stockfish match. It does not establish superiority to unrestricted Stockfish, a3000 FIDE rating, or a1,000-game6.4 result.

Primary6.4 PGN: [forge-6.4.0-vs-sf19-3000-20+0.2.pgn](https://github.com/couns0538-sketch/dwqww/blob/f481fc5afc6bf13b730fe5853fbefaeeb6047162/pgns/forge-6.4.0-vs-sf19-3000-20+0.2.pgn). Git blob: `d2ba8f9e7985256d9f4b6052460b846366767207`.

## The strongest direct evidence for the 6.4 improvement

The residual network was tested against unchanged 6.3, with the following raw-PGN results:

| Candidate | Protocol recorded in ledger | Games | W / L / D | Score | Recorded termination tags |
| --- | --- | ---: | --- | ---: | --- |
| Residual 128 | 20k nodes/move | 500 | 209 / 88 / 203 | 62.1% | 170 normal, 330 adjudication |
| **Residual 128** | **10+0.1, equal clock** | **200** | **49 / 23 / 128** | **56.5%** | **200 normal** |
| Residual 256 | 20k nodes/move | 500 | 218 / 98 / 184 | 62.0% | 147 normal, 353 adjudication |

The equal-clock test has 100 complete color-reversed opening pairs with no first 16-ply mismatches. Its pair histogram for residual 128 is `[0,12,57,24,7]`. PGNs identify both engine versions as6.3.0, with match aliases `res128` and `v63`; the release ledger ties `res128` to the neural-network patch later shipped as 6.4. A version label alone therefore does not identify the evaluated build.

The original ledger reports +45 +/-26 logistic Elo for the equal-clock test and +86 +/-24 for fixed nodes. Those are different protocols and cannot be combined into one Elo estimate. The clock result is useful evidence for the neural network despite its approximately 15% reported NPS cost. The 200-game clock test was a fixed-game threshold gate, **not** an SPRT; it should not be retroactively described as one.

Primary clock PGN: [dev-residual-nnue-128-vs-6.3.0-10+0.1.pgn](https://github.com/couns0538-sketch/dwqww/blob/f481fc5afc6bf13b730fe5853fbefaeeb6047162/pgns/dev-residual-nnue-128-vs-6.3.0-10+0.1.pgn). SHA-256 `85cf152a44ae4963e4ed008cd392ea5e481e071401ffc96e3be0fdf86d8e9559`; Git blob `b03d55a9a358d5896f9d806b7f33d5aec76248bd`.

## What Forge 6.4 inherits

These are source/ledger descriptions; the parent source audit and current build should verify them before modification:

- 6.0: magic-bitboard move generation, modern selective PVS search, pawn correction history, staged move picker, TT prefetch and a regularized Texel-tuned classical evaluation.
- 6.1: Lazy SMP with shared TT and private histories and caches, tunable search constants, evaluation retuning, and NNUE training infrastructure.
- 6.2: embedded 2,616-entry book and Polyglot support, cutoff-count LMR, material correction history, additional tuned evaluation terms, lazy move sorting, evaluation-drop-aware soft time management, and Zen 4 builds.
- 6.3: `LmpBase=4`, `HistoryBonusQuadratic=20`, `HistoryBonusMax=2048`; combined fixed-node SPRT reported H1 at 3,670 games,52.37%,LLR 2.97. Raw PGN verifies 1122W/948L/1600D and1,835 complete pairs.
- 6.4: residual 768 -> 128x2 SCReLU NNUE added to HCE, pure search-score training targets, SSE output layer and `-ffp-contract=off`. No search constant was changed from 6.3. Reported `bench11` signature:417491;6.3:344040;6.2:340241.

Training ledger:13,428,686 positions,128 hidden units, pure search-score targets (`lambda=0`), Adam lr 0.001, batch 16384, epoch 2 selected by validation. The network is a residual on top of the existing classical evaluation, not an HCE replacement. Training data and original training logs are not included in the 44-PGN match archive.

## Experiment disposition to carry forward

The full ledger remains the authority for exact historical settings. All PGN counts/results below can be checked against `forge-match-raw-stats.json`; LLRs are reported by the ledger because original 6.x console logs are missing.

### Historically adopted

| Experiment | Historical evidence | Caution for future work |
| --- | --- | --- |
| Correction history + picker + TT prefetch | 101W/82L/117D at 25k nodes | Bundled300-game test; does not isolate each component |
| Regularized Texel evaluation | 167W/59L/74D at 25k nodes | Strong relative fixed-node result |
| Four threads vs one | 26W/1L/23D at 8+0.08 | Different resource allocation; feature/scaling result |
| Retune on61.5k games | 53.17% book openings and54% randomEPD,300 games each | Small fixed-node screens |
| Additional eval terms + retune | 127W/115L/158D at 20k nodes |51.5%400-game result, uncertain gain |
| Cutoff-count LMR | 894W/726L/1184D,2804 games, reported H1 LLR 2.96 |Fixed20k nodes; not equal-clock release proof |
| Material correction history | 3200-game console50.77%,LLR 0.60; full PGN3213 games 944W/898L/1371D |Explicitly adopted while inconclusive |
| OwnBook defaulton |18W/11L/91D,120 games10+0.1 |From start position; no external opening book in test |
| Lazy move sorting |110W/98L/192D,400 games20k nodes |Adopted for speed; equal-score tie order changes |
| LMP/history combination |1122W/948L/1600D,3670 games,reported H1 LLR 2.97 |Combined pass; the individual8k tests were inconclusive |
| Residual 128 NNUE |62.1% fixed nodes,56.5% equal clock |Preserve shipped net and HCE; fixed-game thresholds, no SPRT |
| SSE output layer codegeneration |Reported same417491bench across targets with faster v2/v3 binaries |Preserve floating-point order and `-ffp-contract=off` |

### Not adopted, superseded or inconclusive; avoid blind repeats

- Unregularized Texel fits were superseded by the regularized table; a second44k-game tuning iteration scored50.2%over500 games.
- First-ply quiet checks in quiescence:50.2%over500 games; additional per-node cost.
- Standalone768x256 NNUE:14W/257L/29D; later standalone 128/256 training also failed held-out loss criteria.
- `NullMoveMinDepth=2`:stopped early; full PGN3081 games 910W/892L/1279D.
- `CaptureFutilityBase=300`:timecap; full PGN5882 games 1709W/1674L/2499D.
- `FailLowContinuationBonus=100`:stopped; full PGN2097 games 576W/562L/959D.
- `TmSoftDivisor=18`:33W/34L/133D at 10+0.1.
- `SingularMargin=1`, `ProbcutDepth=4`, `LmrHistoryDivisor=4000`, `RfpMargin=60`:stopped without standard SPRT bound; results near 50%.
- Pawn-island/candidate-passer terms with retune:110W/115L/175D; lower training loss did not produce measured playing gain.
- `LmpBase=4` alone:8000 games 2261W/2176L/3563D,reported LLR 0.86. History-bonus pair alone:8000 games 2295W/2247L/3458D,LLR 0.10. Both inconclusive separately; combination adopted.
- Before residual net: `FutilityBase=80`/`FutilityMultiplier=130` and `SeeQuietMultiplier=18`:stopped near 50%.
- After residual net: `QsSeeMargin=80`, `HistoryPruneMultiplier=3000`, `NullMoveEvalDivisor=150`:stopped without H0 boundary. No6.4searchconstant change adopted.
- Residual 256 NNUE:62.0% fixed nodes,approximately same result as128; no 256 equal-clock comparison in archive.
- Residual training with result-blended targets (`lambda=0.5`) overfit; `lambda=0.1` first beat same-metric HCE loss, then pure score (`lambda=0`) shipped. Losses at differentlambda/K values are not comparable.
- `SeeNoisyMultiplier=100` and `AspirationDelta=12` runs were killed almost immediately; no records kept.
- Two early nominal SPRTs were actually A/A because fastchess ignored tuning options absent from UCI advertisement. Both were rerun after `FORGE_EXPOSE_TUNABLES`; the original A/A PGNs were overwritten.

The old stopped near 50% experiments are not statistically proven losers. They can be revisited only with a concrete changed hypothesis, interaction or resource reason; they should not be calledSPRT rejections merely because development stopped them.

## Gaps and contradictions to repair going forward

1. **Stale source provenance.** [SOURCE_PROVENANCE.json](https://github.com/couns0538-sketch/dwqww/blob/24cc2cce3eda0e12ddfa4036cd25f7d50e8a3b0b/SOURCE_PROVENANCE.json) still saysrelease 6.0.0 and lists no multithreading, no OwnBook and Windows/Wine untested, contradicting6.4 source/changelog. Do not trust it as current 6.4 metadata.
2. **Runner provenance mismatch.** `tools/match/fastchess-provenance.json` identifies a 20260912-60d7a7a CI build;6.x EXPERIMENTS identifies 20260726-f618e34. These may describe different historical tools. The former hash must not be attributed to the 6.x matches without evidence.
3. **Missing originals.** Neither the match branch nor the 6.4 release ZIP contains the 6.x `console.txt`, exact match command/config, full UCI logs, training datasets or original training logs named by the ledger. Original PGNs are preserved; every original log is not recovered.
4. **Historical nonstandard stopping.** Some tests adopted or rejected by score or time thresholds while standard SPRT bounds were unmet. Preserve the shipped6.4 baseline; use a preregistered fastchess SPRT with equal intended clock/resources for new release acceptance. Budget exhaustion remains inconclusive.
5. **Elo versus normalizedElo.** Early release notes mix logistic and normalizedElo values. EXPERIMENTS explicitly corrects this. Report the model consistently; do not add historical Elo increments as an absolute rating.
6. **Training provenance wording.** CHANGELOG6.4 loosely calls the 82,694-game source a6.3 round set; EXPERIMENTS specifies6.2 era producers and older 6.1 data. Preserve actual generator hashes and a split manifest if recovering/retraining.

## Immediate practical consequence

There is credible original evidence that the 6.4 residual net improved6.3 at a real clock, and substantial retained experiment history. Preserve6.4 as the immutable comparison baseline. Improvement work should start with source-grounded profiling or a reproducible correctness finding, keep every candidate/result, and use the user's requested fastchess SPRT gate for new equal-time strength claims. Neither a model name nor the opponent's 3000 setting establishes that Forge has no remaining improvement opportunities.
