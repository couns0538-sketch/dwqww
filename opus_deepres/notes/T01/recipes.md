# T01 recipes: side-by-side table and ranked bullet configs (written 22:54 PC clock, updated as sources come in)

## Side-by-side table
WDL = weight of the game result in the target (0 = pure eval score, 1 = pure result); npt "lambda" is the opposite
(lambda 1.0 = pure eval score). Sigmoid scale = the cp divisor inside the sigmoid of the loss.

| recipe | source / licence | inputs | net | data | batch | length | LR schedule | WDL (schedule) | sigmoid scale | init | result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OUR npt (R11 "full" = owner's line-104 recipe) | own, on nnue-pytorch (GPL-3.0, run as a tool) | HalfKA K32H3^ | L1 1024, npt default layers after L1 | 344.4M rows inventory; 152.5M per epoch | 16,384 | 20 epochs = 3.05G positions | lr 8.75e-4, trainer's default per-epoch decay (not set in the profile) | lambda 1.0 start and end = WDL 0 | trainer default (not set in the profile) | from scratch | gates NPT104 / NPTS3 / NPTW4S4: -86 to -116 Elo vs the lock (notes/TRIED_GATES.md) |
| OUR bullet v2 (30-h job, window 2) | own trainer on bullet da426a49 (MIT) | 768 piece-square x king buckets KB4 / 8 / 16 / 32 (rank maps), OB8 output buckets; residual on the hand-crafted eval | H256 hidden, SCReLU, one output per bucket | train = 304,999,573 rows (FPOS / FHCE 001-039 minus holdout 013 / 014) | 16,384 | 200 SB x 1,024 batches = 3.36G positions (also 300 / 400 / 600 SB) | cosine 2e-5 -> 2e-7 (1e-5 .. 3e-5 tried; 3e-5 worse) | 0.4 constant | eval_scale 400 / 2.25 = 177.8 cp | warm start = lock net written exactly into the layout; AdamW clip +-7.99, decay 0 | S31 paired vs the lock KB4 -1.41e-4 .. KB32 -1.80e-4; play within noise (sanity 200-400 g); bullet sb08 early stop -11.9 +- 13.6 (760 g, owner's note) |
| bullet examples/advanced at da426a49 | bullet (MIT) | 16 mirrored king buckets x 768 + factoriser; sparse threats 59,808 (cap 128 active); pawn pairs 4,560 (cap 120) | L1 768 pairwise, L2 16 dual (x, x^2), L3 32, 8 material output buckets | PENDING (not in the file; reads Viridithas-format data) | 131,072 | 3 stages: 100 + 800 + 200 SB x 763 batches (~100M positions per SB) = ~110G positions | stage 1 warm-up 1e-4 -> 5e-3 -> 1e-4; stage 2 1e-3 -> 1e-6; stage 3 1e-5 -> 1e-7 | 0.2; 0.2 -> 0.5; 1.0 | 400 | from scratch | no Elo in the file |

## Ranked bullet configs (each ~1 GPU-day on one RX 7900 XT, offline holdout check vs the current net before any SPRT)
PENDING (written after the remaining sources; see cards/T01/T01-03-*).
