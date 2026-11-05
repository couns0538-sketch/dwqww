# T06-02-hce-residual-rebalance: re-weight HCE vs residual net when piece material is level
Status: COMPLETE

## Source
- Stockfish commit text + fishtest logs (no source): https://github.com/official-stockfish/Stockfish/commit/a2f01c07eb
  "Sometimes change the (materialist, positional) balance" (PR 3492), STC
  https://tests.stockfishchess.org/tests/view/60a82df9ce8ea25a3ef0408f , LTC
  https://tests.stockfishchess.org/tests/view/60a8bbf9ce8ea25a3ef04101

## Licence
Stockfish GPL-3.0 (Copying.txt at d212e663bb): ideas only - commit text and fishtest logs read, never source.

## Mechanism
Stockfish's net of that time produced two output values, read as a material part and a positional part, summed with
equal weights. The patch shifts weight from the material part to the positional part only when piece material is
equal between the two sides, and keeps equal weights once one side is at least an exchange up.
Forge already has the two parts as separate numbers: the final eval is the HCE plus the residual net (the residual is
"what the HCE gets wrong"). Own Forge form: if the non-pawn material of the two sides differs by less than an
exchange (rook minus minor, from Forge's own PieceValueMg), final = (1 - h) HCE + (1 + r) residual; otherwise the
lock's plain sum. h and r are signed per-mille options; SPSA picks them (no Stockfish ratio carried over). Applied
inside static_evaluate, so the rebalanced sum is the raw value the TT stores (deterministic per position); E3's own
post-steps, when ON, still run on it afterwards.

## Forge fit
Lock src/search.cpp:620 returns clamp(HCE_runtime + network): both parts exist there, nothing is re-weighted. E3 does
not touch the split. FORGE_IDEA_BOARD rules out drawish scaling of the residual (double count, per the E3 README);
this is a level-material re-weighting, not a drawishness scale, and it is OFF-default - the crew decides whether the
board rule covers it. Change: one branch at search.cpp:620 (or at E3's raw-eval entry).

## Expected gain
Stockfish a2f01c0 (fishtest STC / LTC, TC not in the commit text; Elo from W/L/D): STC +3.4 (15,936 games,
{-0.5,2.5}, LLR 2.93), LTC +2.7 (13,904 games, {0.5,3.5}, LLR 2.94). Stockfish 13/14 era with a two-output net;
no newer number found.
Forge estimate: 0 to +3 Elo **UNPROVEN**.

## Effort
Crew: ~1.5 h code (two options, threshold from PieceValueMg) + ~2 h proofs. CPU: one 2-parameter SPSA (~3,000 STC
pairs = 6,000 games, ~14 h at the measured ~437 games/h of uhoE3a r6k) + one STC and one LTC SPRT. GPU: none.

## Test plan
Pre-gate: OFF bench / perft = lock pins; ON bench differs; from the FIT_RECIPE step-1 extraction (per-side material
columns) count the share of gate positions with level piece material (it decides how often the branch fires). SPSA on (h, r) from (0, 0), then
UHO SPRT [0,5] at STC vs the lock, then LTC.

## OFF-by-default design
UCI `EvalHceLevelW` and `EvalResidLevelW`, signed -150..150 per mille, default 0. With both 0 the branch returns the
lock's sum unchanged, so OFF is node-identical (bench pins).
