# T12-01-sprt-bounds-caps: SPRT bounds and caps that decide Forge gates (pentanomial, normalised Elo)
Status: COMPLETE

## Source
Fishtest wiki: https://github.com/official-stockfish/fishtest/wiki/Fishtest-mathematics (bounds in normalised Elo,
pentanomial model, GSPRT = MLE for the unknowns, expected length depends only on the bounds) and
https://github.com/official-stockfish/fishtest/wiki/Creating-my-first-test (STC 10+0.1 / LTC 60+0.6, non-regression
<-1.75,0.25>). Numbers below: own Brownian-GSPRT model (MC, 20k reps) on the crew's FORGE_RESULTS.csv (110 gates with
Ptnml); tables in notes/T12/PROTOCOLS.md sections 1-2.

## Licence
fishtest at 5a8a229a52: no root LICENSE file found by tools/licence_at.py (WORKER_RULES list it as GPL-3.0): ideas
only; only the two wiki pages were read, no source file. The model and all numbers are own work.

## Mechanism
With t = nElo * sqrt(2) * ln10 / 800 per game pair, the GSPRT LLR is close to a random walk with drift
dt * (t - t_mid) and variance dt^2 per pair (dt = bound width in t units), stopped at +-ln(19). The length depends
only on the width and the true effect. Pairing: at UHO the pentanomial variance per pair is 0.618 of the
independent-games value (8moves_v3: 0.90), so pairs save ~38 % of the games on UHO.

## Forge fit
Already in use: fastchess 1.8.2 pentanomial GSPRT (forge-gate-stats). Bounds in use: [0,10] nElo on 82 of the 85
undecided gates (model LLR = printed LLR within 0.15). 79 of 110 gates ended "Cap with no decision" (55 at 1,500
games, 14 at 3,000, 9 at 1,000, 1 at 6,000; nElo 10/50/90 % = -9.0 / +7.4 / +18.2), 4 more by the net early stop.
Book scale: UHO 1 Elo = 1.91 nElo (n=6 gates), 8moves_v3 2.10 (n=63). No engine code involved. No gate ran [0,5];
it is read here as nElo (as the brief says). If it meant logistic Elo, it is ~[0,9.5] nElo on UHO: same cost as [0,10].

## Expected gain
No Elo claim: the gain is decided gates per CPU hour. Model (UHO, 497 games/h, games = 2 x pairs):
- [0,10]: true 0 or +10 nElo -> mean 6.6k games (13 h), p90 12.7k; P(decided by 3000) 0.20, by 12000 0.88.
  True +5 -> mean 11.1k, by 12000 0.66.
- [0,5] (the WORKER_RULES route): mean 26k games (53 h) at either end, 44k at +2.5; P(decided by 3000) 0.00, by
  12000 0.21. Not reachable with any cap the queue has used.
- [0,15]: mean 2.95k; P(decided by 6000) 0.91-0.92 at the ends, 0.72 at the midpoint.
- [0,20]: mean 1.65k, p90 3.2k; P(decided by 3000) 0.88-0.89 at the ends.
- Fishtest-size [0,2] or [-1.75,0.25]: mean ~165k games (330 h): out of reach. Forge non-regression [-10,0] = [0,10] cost.
- Truncated rule (decide by the LLR sign at the cap): [0,10] cap 3000 false accept 0.22 / power 0.78; cap 6000
  0.13 / 0.86; cap 12000 0.07 / 0.93. [0,20] cap 3000: 0.07 / 0.93 at +20 nElo, 0.50 at +10.
Forge estimate: with [0,10] and a 12k cap, ~88 % of gates at the bound ends decide instead of ~20 % at 3k. Cost:
mean 6.6k games at the ends and 9-11k near +5 nElo (the capped median is +7.4) vs today's 1,500, i.e. ~4-6x the CPU
per gate - **UNPROVEN** (model, not yet replayed on the gate PGNs).

## Effort
Crew ~1-2 h: a manifest change (bounds, cap) plus one replay of the 85 capped Ptnml profiles with the S44 simulator
(forge-gate-stats, ~75 min for 23 gates single-threaded). CPU: no extra games; gates get longer but end decided.

## Test plan
Pre-gate: replay S44 `run` with each gate's own Ptnml profile under [0,10] cap 12000 and under [0,15] cap 6000; check
that the MC table reproduces the stopping-time spread of the 25 decided gates. Gate route for every candidate stays
the UHO SPRT at STC (bounds [0,10] nElo, cap 12000, or [0,15] cap 6000), then LTC; 8moves_v3 confirm never pooled;
node-identical speed changes = nps ABBA only (T12-02, T12-03).

## OFF-by-default design
Runner/manifest setting only (sprt elo0/elo1, cap_games, cap rule "sign of LLR"); no engine change, lock pins
312866/862329/3024920/12389307/34048354 untouched. Old bounds stay one manifest value away.
