# T02-03: WDL-consistency skip: keep rows whose label agrees with the game result more often
Status: PARTIAL (whether the npt w4 runs had the trainer's default WDL skip on, and a filter-only test: PENDING)

## Source
- nnue-pytorch PR 155 (merged 2021-12-03, made the skip the trainer default, `--no-wld-fen-skipping` disables it):
  https://github.com/official-stockfish/nnue-pytorch/pull/155
- Stockfish PR 3808 (nn-3678835b1d3d): https://github.com/official-stockfish/Stockfish/pull/3808 ; STC
  https://tests.stockfishchess.org/tests/view/619eb597c0a4ea18ba95a4dc , LTC SPRT
  https://tests.stockfishchess.org/tests/view/61a0864e8967bbf894416e65 (TC / book read from the fishtest API).
- Stockfish PR 3816 (nn-4f56ecfca5b7): https://github.com/official-stockfish/Stockfish/pull/3816

## Licence
nnue-pytorch c625702757 and Stockfish ff7cee4244: GPL-3.0 (notes/T02/licences.md): ideas only. Read: PR text and
fishtest run data only, never source.

## Mechanism
A soft filter in the loader. Each row's stored score is turned into an expected game score with a win-probability
model; the row is kept with a probability that grows with how well that expectation matches the row's real game
result, so rows whose label contradicts the outcome (likely misevaluated) are seen less often. Nothing is deleted;
the effective training distribution shifts towards label / outcome agreement.

## Forge fit
Lock source: no WDL model or datagen code (`tools/forge_has.sh 'wdl|win_rate|winrate'` = 0 hits); this is data /
trainer side only. Forge binpacks carry score and game result, so the npt trainer's default skip can act on them;
whether the w4 runs left it on: PENDING (crew, run flags). The residual (production) CPU trainer and the bullet
configs have no such skip as far as the skills describe (PENDING: one look at their loaders). Forge self-play labels
are 5000-node HCE scores from the old 6.2.0 build, i.e. noisy, which is the case the filter targets. With lambda
fixed (Lichess 1.0, self-play 0.7-0.9) the result already enters the loss; the skip is a second, independent lever.
Change: an offline pass at conversion that drops a row with probability rising in |expected score - result|, with
an own scale (start: the Forge cp-to-WDL fit of S19; strength k start 0.5, range 0-1); 0 = today's bytes.

## Expected gain
Source numbers are confounded (filter and new data in the same retrain, same arch HalfKAv2_hm):
PR 3808: STC 10+0.1, UHO_XXL_+0.90_+1.19, 40,000 games: -0.44 +- 1.8; LTC 60+0.6: +3.30 +- 1.8 (33,062 games);
LTC SPRT [0.5, 3] passed, 29,376 games (+3.2 computed). PR 3816 (plus TB7-rescored Leela data): STC SPRT [0, 2.5]
passed, 49,152 games (+2.1 computed); LTC SPRT [0.5, 3] passed, 25,528 games (+3.4 computed). No filter-only test
was found.
Forge estimate: +0 to +3 Elo, **UNPROVEN**, and 0 if the w4 runs already had the default skip on.

## Effort
Crew 1 h to read the w4 run flags; 3-5 h for an offline pass (own code) with row counts per eval / result bucket.
GPU: two npt runs (skip on / off) of the w4 size at the same seed, only if the flags show it was off.

## Test plan
Pre-gate: kept-row share per (eval bucket x result) table; overlap 0 (T02-01 tool); export parity; OFF bench pins
unchanged; WAC 300. Gate: net vs net of the same recipe, UHO SPRT [0, 5] at STC, then LTC.

## OFF-by-default design
No engine change (net via EvalFileHalfKA, default empty = lock eval, bench pins unchanged). The offline pass is a
converter switch (`--wdl-skip k`, default 0 = byte-identical to the J1 binpack); the trainer side is its existing flag.
