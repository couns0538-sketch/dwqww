# T06C-02-residual-retrain-after-refit: fine-tune the residual net on the re-fitted HCE (second alternation step)
Status: COMPLETE

## Source
- Ethereal 8d02577, net retrained 4 days after the HCE re-tune b552e36 (OpenBench 7644 / 7645):
  https://github.com/AndyGrant/Ethereal/commit/8d02577b5f , http://chess.grantnet.us/test/7644/ , .../test/7645/
- Order of Ethereal's hybrid period (commit titles and dates): net added 513a93c (2020-09-19) -> net retrained c8b7199
  (09-24) -> HCE re-tune b552e36 (09-24) -> net retrained 8d02577 (09-28) -> full NNUE b9b8463 (2021-05-29).
  https://github.com/AndyGrant/Ethereal/commit/c8b7199c3e
- Confounded: 8d02577 also changed the net output to an S(MG, EG) pair and trained with mirroring; its number is for
  that change, which followed the HCE re-tune. Whether its offset used the re-tuned HCE is not stated. No isolated
  "retrain the net on the re-fit HCE" number was found.

## Licence
Ethereal GPL-3.0 (LICENSE at b552e36f88): ideas only - commit text and test pages read, never source.

## Mechanism
Own recipe: the second half of one block-coordinate round. After T06C-01 picks a new table T1, the residual target
moves (the lock net was fit to the errors of the lock table T0). Regenerate the .hce of the training rows with T1,
warm-start from the lock net and fine-tune with the unchanged residual loss (K 2.25, blend b 0.6, same rows, same
013/014 holdout exclusion), so the net re-fits to the errors of T1. Stop at the first holdout plateau; one round only
(a second table refit after it is a new candidate). Risk, both halves: the T06C-01 step can only lower the training
loss with the net fixed, but its room is what the net left uncorrected; after this fine-tune the sum can drift back
to the lock's total eval (the net re-absorbs what the refit moved) unless T1 + net reaches a better joint optimum. The
holdout shows which, before any game.

## Forge fit
Residual loss pred = sigmoid((net_cp + hce_cp) 2.25 / 400) with hce_cp read from per-row .hce files made by hce_dump
(skill forge-nnue-data, "Training facts", "R11 sources"); hce_dump must be rebuilt with T1. In-tree residual mode:
tools/tune/nnue_train.cpp:15-18, :48 (output layer starts at zero = the HCE's loss). Warm-started CPU fine-tune
trainer: skill forge-o30-v2net. Measured 2026-10-28: standalone and residual nets reach the same holdout loss per
position seen (skill forge-nnue-train-cpu), so the HCE only shifts what the net must learn. The lock net is compiled
in (src/nnue_weights.inc); a fine-tuned net needs the EvalFileV2 path (skill forge-o30-v2net) or a separate build.

## Expected gain
Ethereal 8d02577: STC +4.72 +- 3.63 (10+0.1s, Threads 1, SPRT [0,5], LLR 2.95, 14,640 games), LTC +2.71 +- 2.17
(60+0.6s, LLR 2.98, 29,072 games) - confounded, see Source.
Forge estimate: 0 to +2 Elo on top of T06C-01 **UNPROVEN**; run only after T06C-01 passes its holdout filter.

## Effort
Crew ~6 h: hce_dump rebuild with T1 and .hce regeneration for train + holdout ~1.5 h, fine-tune setup, export, parity
(int 0 mismatches) and pins ~3 h, packaging ~1.5 h. CPU: .hce regeneration one pass over ~305M rows (rate not
measured here; own guess 1-3 h); fine-tune ~10 CPU h per 1G position presentations at ~95M per CPU hour
(a full retrain at the lock's ~7.4G presentations would be ~78 CPU h; own arithmetic from skill numbers); STC SPRT
~13-15 h, LTC ~3x per game. GPU optional (R11 pipeline), not required.

## Test plan
Holdout first (b0.6, holdout_013_014_s16, S31 scorer): T1 + fine-tuned net vs T1 + lock net vs lock; drop unless it
beats T1 + lock net. Export parity, OFF bench / perft = lock pins, ON bench differs, smoke. Gate after T06C-01 and
separately (never a bundle before its parts): UHO SPRT [0,5] at STC vs the T06C-01 candidate (or vs the lock if
T06C-01 was adopted), then LTC.

## OFF-by-default design
`HceParamsFile` (T06C-01) plus the EvalFileV2 net option, both empty by default = lock table + compiled lock net ->
OFF node-identical (bench pins). The pair must load together (a T1-fit net on the T0 table double-counts): own design,
the exporter writes the table file's sha256 next to the net and the option pair refuses a mismatch over UCI.
