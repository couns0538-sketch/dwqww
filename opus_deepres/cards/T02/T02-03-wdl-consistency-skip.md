# T02-03: WDL-consistency skip: keep rows whose label agrees with the game result more often
Status: COMPLETE (the w4 run flags were read: skip OFF, lambda 1.0; no filter-only source test exists - stated below)

## Source
- nnue-pytorch PR 155 (merged 2021-12-03, made the skip the trainer default, `--no-wld-fen-skipping` disables it):
  https://github.com/official-stockfish/nnue-pytorch/pull/155
- Stockfish PR 3808 (nn-3678835b1d3d): https://github.com/official-stockfish/Stockfish/pull/3808 ; STC
  https://tests.stockfishchess.org/tests/view/619eb597c0a4ea18ba95a4dc , LTC SPRT
  https://tests.stockfishchess.org/tests/view/61a0864e8967bbf894416e65 (TC / book read from the fishtest API).
- Stockfish PR 3816 (nn-4f56ecfca5b7): https://github.com/official-stockfish/Stockfish/pull/3816
- Own records: the npt adapter's logged trainer command of the best w4 run,
  `D:\forge_nnue_train\runs\npt_k32h3_l1024_bs16k_e8x152m5_g072_lam10_w4_s41.log` (2026-11-03 18:48).

## Licence
nnue-pytorch c625702757 and Stockfish ff7cee4244: GPL-3.0 (notes/T02/licences.md): ideas only. Read: PR text and
fishtest run data only, never source. Caissa (counter-evidence below): MIT, commit message only.

## Mechanism
A soft filter in the loader. Each row's stored score is turned into an expected game score with a win-probability
model; the row is kept with a probability that grows with how well that expectation matches the row's real game
result, so rows whose label contradicts the outcome (likely misevaluated) are seen less often. Nothing is deleted;
the effective training distribution shifts towards label / outcome agreement.

## Forge fit
Lock source: no WDL model or datagen code (`tools/forge_has.sh 'wdl|win_rate|winrate'` = 0 hits); data / trainer side
only. The w4 runs pass `--start-lambda 1.0 --end-lambda 1.0 --no-filtered --no-wld-filtered` on the J1 binpack only:
the skip was OFF (review fix, second vote: documented, not inferred - trainer PR 405 "Use Tyro for CLI Args", merged
2026-02-25, renamed `--no-wld-fen-skipping` to `--wld-filtered` / `--no-wld-filtered`, help text "If disabled,
WLD-based fen skipping is turned off. (default: True)") and, with lambda 1.0, the result never entered training at all. The labels are 5000-node HCE
scores of the old 6.2.0 build - the noisy case this filter targets. Not checked here: the residual CPU trainer and
the bullet configs. With the decided lambda for the next runs (self-play 0.7-0.9) the result enters the loss; the
skip is then a second, overlapping lever, so test it at that lambda.
Change: none to code for npt - drop `--no-wld-filtered` (trainer default). Optional offline variant for other
trainers: drop a row with probability rising in |expected score - result| (own scale: the Forge cp-to-WDL fit of
S19; strength k start 0.5, range 0-1; 0 = today's bytes).
Counter-evidence (MIT, Caissa 71f434458f): a decisive-score skip plus two other loader filters lost about 11 Elo (no
TC / games given); Stockfish's stronger skip (f12035c88c) came with an optimizer change: test one filter at a time.
(review fix, second vote: Caissa's `--decisiveSkip` drops rows whose decisive score AGREES with the result - the opposite direction of this skip, so it is weak evidence only; f12035c88c ran lambda 1.0 -> 0.7, so the skip was used below lambda 1.0 too (supports testing at the decided lambda); PR 3808 ran it at lambda 1.0 = the w4 setting, so a lambda-1.0 skip on / off pair is the closest source match if GPU time allows.)

## Expected gain
Source numbers are confounded (filter and new data in the same retrain, same arch HalfKAv2_hm):
PR 3808: STC 10+0.1, UHO_XXL_+0.90_+1.19, 40,000 games: -0.44 +- 1.8; LTC 60+0.6: +3.30 +- 1.8 (33,062 games);
LTC SPRT [0.5, 3] passed, 29,376 games (+3.2 computed). PR 3816 (plus TB7-rescored Leela data): STC SPRT [0, 2.5]
passed, 49,152 games (+2.1 computed); LTC SPRT [0.5, 3] passed, 25,528 games (+3.4 computed). No filter-only test
was found in any source.
Forge estimate: +0 to +3 Elo for the next npt net of the w4 size, **UNPROVEN** (the skip was off in every w4 run).

## Effort
Crew 0.5 h (one flag in the adapter call, a kept-row table). GPU: two npt runs of the w4 recipe (8 x 152.5M
positions) at the same seed, skip on / off, both at the decided lambda. CPU: none beyond the usual export checks.

## Test plan
Pre-gate: kept-row share per (eval bucket x result) table; overlap 0 (T02-01 tool); export parity; OFF bench pins
unchanged; WAC 300 (card T02-04 method). Gate: net vs net of the same recipe, UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
No engine change (net via EvalFileHalfKA, default empty = lock eval, bench pins unchanged). Trainer side: the adapter
keeps `--no-wld-filtered` as its default and gets a switch to drop it; the offline variant is a converter switch
(`--wdl-skip k`, default 0 = byte-identical to the J1 binpack).
