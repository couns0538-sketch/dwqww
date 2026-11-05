# T12 protocols for Forge gates, tuning and speed proofs (UNPROVEN planning numbers, no Elo claim)

Inputs: crew FORGE_RESULTS.csv (110 gates with Ptnml, read-only), the UHO gate settings of
F:/forge_push/uhoE3a_evalmatscale12_r6k_vs_AL1lp (fastchess 1.8.2, 10+0.1, Threads=2, Hash 16, conc 4, CPUs 4-15,
UHO_Lichess_4852_v1.epd, random start), gate rate ~497 games/h (forge-gate-summary). Model script: scratchpad
t12/sprt_plan.py (own code; Brownian approximation of the GSPRT, 20k Monte-Carlo walks per row).

## 1. SPRT bounds, normalised vs logistic Elo, expected games
- Normalised Elo: nElo = (a - 0.5) / sqrt(2 var) * 800/ln10 with a and var the mean and variance of the pair score
  (forge-gate-stats). In t units per pair, t = nElo * sqrt(2) * ln10 / 800 = 0.004070 * nElo.
- LLR model: per pair, drift dt * (t - (t0+t1)/2), variance dt^2, dt = (nElo1 - nElo0) * 0.004070; stop at
  +-ln(19) = +-2.944 (alpha = beta = 0.05). Mean pairs at either bound end = 0.9 * 2.944 / (dt^2 / 2); at the
  midpoint = 2.944^2 / dt^2. Depends only on the width (fishtest wiki: independent of draw ratio and book).
- Unit check on Forge's own gates: assuming [0,10], the model LLR = pairs * dt * (t_hat - t_mid) matches the printed
  LLR of 82 of 85 capped gates within 0.15 (mean diff -0.05). The 3 others: R5D-MF ([-10,0] non-regression), G101
  and R7-PFE (other bounds).
- Logistic vs normalised on Forge's books (median of gates with |Elo| > 3): UHO nElo = 1.91 x Elo (6 gates, range
  1.87-1.95), 8moves_v3 2.10 x Elo (63 gates, 1.90-2.40). So [0,10] nElo = about [0, 5.2] Elo on UHO and
  [0, 4.8] Elo on 8moves_v3; [0,5] nElo = about [0, 2.6] Elo on UHO.

| bounds nElo | true nElo | P(H1) | mean games | median | p90 | P(dec. <= 3000) | <= 6000 | <= 12000 | mean h | p90 h |
|---|---|---|---|---|---|---|---|---|---|---|
| [0,5] | 0 | 0.051 | 26,439 | 21,350 | 50,960 | 0.00 | 0.03 | 0.21 | 53.2 | 102.5 |
| [0,5] | +2.5 | 0.507 | 44,030 | 33,600 | 90,650 | 0.00 | 0.01 | 0.11 | 88.6 | 182.4 |
| [0,5] | +5 | 0.955 | 26,237 | 20,860 | 50,750 | 0.00 | 0.03 | 0.22 | 52.8 | 102.1 |
| [0,10] | 0 | 0.049 | 6,639 | 5,310 | 12,762 | 0.20 | 0.57 | 0.88 | 13.4 | 25.7 |
| [0,10] | +5 | 0.507 | 11,061 | 8,388 | 22,734 | 0.11 | 0.35 | 0.66 | 22.3 | 45.7 |
| [0,10] | +10 | 0.956 | 6,578 | 5,256 | 12,654 | 0.21 | 0.57 | 0.88 | 13.2 | 25.5 |
| [0,10] | +15 | 0.997 | 3,594 | 3,114 | 6,228 | 0.47 | 0.89 | 1.00 | 7.2 | 12.5 |
| [0,15] | 0 | 0.049 | 2,951 | 2,360 | 5,672 | 0.64 | 0.91 | 1.00 | 5.9 | 11.4 |
| [0,15] | +7.5 | 0.507 | 4,916 | 3,728 | 10,104 | 0.40 | 0.72 | 0.94 | 9.9 | 20.3 |
| [0,15] | +15 | 0.956 | 2,924 | 2,336 | 5,624 | 0.64 | 0.92 | 1.00 | 5.9 | 11.3 |
| [0,20] | 0 | 0.050 | 1,654 | 1,336 | 3,164 | 0.88 | 0.99 | 1.00 | 3.3 | 6.4 |
| [0,20] | +10 | 0.505 | 2,715 | 2,052 | 5,636 | 0.68 | 0.92 | 0.99 | 5.5 | 11.3 |
| [0,20] | +20 | 0.954 | 1,636 | 1,304 | 3,148 | 0.89 | 0.99 | 1.00 | 3.3 | 6.3 |
| [-10,0] | -10 / 0 | 0.049 / 0.956 | 6,639 / 6,578 | | 12,762 / 12,654 | 0.20 / 0.21 | 0.57 | 0.88 | 13.3 | 25.6 |
| [-1.75,0.25] or [0,2] | ends | 0.048 / 0.956 | ~165,000 | ~132,000 | ~320,000 | 0.00 | 0.00 | 0.00 | ~333 | ~644 |

Truncated SPRT (at the cap, accept H1 if LLR > 0, else H0): P(accept H1) at true 0 / midpoint / upper bound:
[0,5] cap 3000: 0.35 / 0.50 / 0.66; cap 12000: 0.21 / 0.50 / 0.78. [0,10] cap 3000: 0.22 / 0.50 / 0.78; cap 6000:
0.13 / 0.50 / 0.86; cap 12000: 0.07 / 0.50 / 0.93. [0,20] cap 3000: 0.07 / 0.50 / 0.93; cap 6000: 0.05 / 0.50 / 0.95.

What the capped gates were: 85 of 110 gates with Ptnml ended at a cap (median 1,500 games); their nElo 10/50/90 %
quantiles -12.9 / +6.6 / +17.8; 52 % had |nElo| <= 10 - exactly the zone where [0,10] is slowest (the midpoint +5
needs 11k games on average). A 3,000-game cap decides about 1 in 5 of [0,10] runs at the bound ends.

Options that decide (pick one per queue; numbers above):
1. Keep [0,10] nElo, cap 12,000 games (~24 h): 88 % decided at the ends, 66 % at +5; sign rule at the cap gives
   0.07 false accept / 0.93 power. Mean cost ~6.6k games (13 h) at the ends.
2. [0,15] nElo (= ~[0, 7.9] Elo UHO), cap 6,000 (~12 h): 91-92 % decided at the ends, 72 % at +7.5.
3. Screen + confirm: [0,20] cap 3,000 (~6 h; 88 % decided at the ends; sign rule 0.07 / 0.93 at +20) for wide
   searches, then [0,10] cap 12k on the 8moves_v3 confirm for survivors.
- [0,5] (written in WORKER_RULES as the route) needs ~26k games at the ends (53 h, 0 % decided by 3,000): use it only
  as the LTC/confirm bound of a candidate that already passed [0,10], or not at all at this gate rate.
- Stopping bias (forge-gate-stats S44): an H1 stop overstates Elo (winner's curse +7.6..+9.4 at true +10); report the
  Whitehead-adjusted value with any H1.

## 2. Pentanomial statistics (why pairs)
- A pair = the same opening played with both colours by both engines (fastchess -repeat, -games 2). Opening and colour
  bias largely cancel inside a pair, so the pair score has less variance than two independent games.
- Forge numbers (median over gates with >= 1,000 games): pair-score variance / (per-game variance / 2) = 0.618 on UHO
  (10 gates, range 0.589-0.656) and 0.90 on 8moves_v3 (84 gates, 0.51-0.995). UHO pairs therefore need ~38 % fewer
  games than a trinomial (per-game) test of the same power; 8moves_v3 ~10 %. Draw ratio UHO 0.56, 8moves_v3 0.75.
- Pair-score sd (median): UHO 0.185, 8moves_v3 0.167 per pair. fastchess 1.8.2 already uses the pentanomial GSPRT
  (forge-gate-stats); keep -repeat and never split a pair across a cap (fastchess counts complete pairs only).
- The trinomial/pentanomial gap also measures opening bias (fishtest wiki: "accounting identity", RMS book bias):
  UHO books are deliberately unbalanced, which is why the gap is large there.

## 3. Book and TC choice
PENDING

## 4. SPSA plan for 20 search parameters
PENDING

## 5. nps protocol for 1 % effects
PENDING
