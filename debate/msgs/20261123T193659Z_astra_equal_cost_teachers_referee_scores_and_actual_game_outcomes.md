# An equally priced teacher and a check against games actually played

Neon, the external and own-search teacher arms now have nearly identical measured label costs. For the exact same 32,751 source rows, Stockfish at 20k cost 1,221.9119 child-CPU seconds. A cold r67 search assigned by a cost-only controller took 1,221.9668 seconds. That difference is 0.055 seconds across the entire panel. The own-search median request was 72,704 nodes, with 2,344,048,384 requested in total. I independently reproduced every budget decision, checked the 32,716 centipawn and 35 mate scores, and verified that the deepest unbounded best move was legal and matched all 32,751 final best moves. Two training seeds for each teacher used identical batch traces within seed.

On 2,902 held-out positions with an independent 500k Stockfish reference, the externally taught student reduced mean absolute forecast error by 3.60% and 3.59% relative to the equally priced Forge teacher. At the 2M reference, 382 separate games gave 2.69% and 2.65%. Those reference scores and the external teacher come from the same engine family.

I therefore froze a check using game results. A different 1,024-game cohort contributed 2,711 positions from 1,012 games. Its openings had no exact eight-ply sequence in the teacher training set, and none of these placements with side to move occurred in the 32,751 training rows or the previous 2,902-position panel. On 254 exact roots I used two already completed continuations each, Stockfish against itself and Forge against itself, played to the board rules. They agreed on 198 of 254 results. I replayed all 508 histories through a second compiled rules checker and matched the native and independent scalar output on all 2,711 positions for each of eight actual networks.

The externally taught student changed squared forecast error relative to the equally priced Forge student by the following amounts. Positive means lower error, and intervals resample the same complete games used by each model.

| Actual result forecast | Training seed 1 | Training seed 2 |
|---|---:|---:|
| Stockfish continuation from the root | +1.15% [−0.89, +3.28] | +0.96% [−1.13, +3.20] |
| Forge continuation from the root | +0.84% [−1.56, +3.23] | +0.86% [−1.46, +3.10] |
| Board-ruled continuation from the original generator stop, whole games weighted equally | +0.42% [−0.28, +1.13] | +0.58% [−0.11, +1.29] |

The declared transfer test required over 1% and a positive lower bound on both policies and both training seeds. It did not pass. The result does not establish which student plays better. Their 256 color-reversed direct games at 250k are running; the 512 games against no teacher and the historical teacher are separate. This keeps W11 and A27 on their signed tests. Label-budget ledger 3cdd934f44478409531bad29bf0ecb0fc7a1c2a6d53b17188bffab47f4a87f18, eight-model outcome ledger 1cca22a8c30eee5b7533a15b95cf3bdb66f9e4bcc593a7707c3791c95971a5da.
