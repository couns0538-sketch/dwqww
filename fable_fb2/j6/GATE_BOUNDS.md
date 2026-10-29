# GATE_BOUNDS.md — SPRT bounds and caps that decide at this PC's throughput (FB2-J6, 2026-10-28)

Proposal only: nothing here was queued and the gate queue was not edited. Numbers come from
`F:\opus_scratch\fable\fb2\j6\gate_bounds_sim.py` (output `gate_bounds_sim.json`, `gate_bounds_tables.md`); the
formulas are the ones verified on 23 gates (skill forge-gate-stats). Addresses section 7 of
`F:\opus_scratch\r3\GATE_PROPOSALS.md` (R3-3).

## 1. What the PC delivers

| quantity | value | source |
|---|---|---|
| gate format | fastchess 1.8.2, 10+0.1, Threads 1, Hash 16, 8moves_v3 book, concurrency 8, SPRT normalized a = b = 0.05 | RESULT.md settings lines (gates 36-38) |
| throughput | 1500 games in 92-93 min = **about 970 games per hour** (gate36 07:06 -> gate37 08:39 -> gate38 10:11 on 2026-10-27) | RESULT.md start times |
| draw rate / pentanomial profile vs AL1 | Ptnml [8, 113, 483, 135, 11] of 750 pairs (77% draws), pair-score variance var = 0.0268 | gate38 |
| LLR bounds | +-ln 19 = +-2.944 (a = b = 0.05) | fastchess |

## 2. The math (normalized model, pentanomial)

- Pair score a in {0, 1/4, 1/2, 3/4, 1}; Elo = -400 log10(1/a - 1) ~ 695 (a - 1/2) for small differences.
- nElo = (a - 1/2) / sqrt(2 var) x 800/ln 10. With var = 0.0268: **1 classical Elo = 2.16 nElo**, so the bounds in
  the queue are smaller than they look: [0,10] nElo = [0, 4.6] Elo, [0,5] nElo = [0, 2.3] Elo, [-3,1] nElo = [-1.4, 0.5] Elo.
- GSPRT (normal approximation, exact to about 0.1 LLR): LLR = N (mu1 - mu0) (abar - (mu0 + mu1)/2) / var over N pairs,
  mu_i = 1/2 + nElo_i x (ln 10 / 800) x sqrt(2 var). Check: gate38 (abar 0.5093, N 750) gives 1.11, the printed value.
- Expected pairs to reach the H1 bound when the truth is exactly elo1 (Wald): E[N] ~ ln 19 x (1 - 2a) / drift with
  drift = (nElo1 x ln 10 / 800)^2 per pair, i.e. **E[games] ~ 2 x 2.944 x 0.9 / (0.002878 x nElo1)^2**:

| bounds (nElo) | truth at elo1 (Elo) | E[games] to H1 | hours at 970 games/h |
|---|---|---|---|
| [0,5] | +2.3 | 25,600 | 26 |
| [0,10] | +4.6 | 6,400 | 6.6 |
| [0,15] | +6.9 | 2,850 | 2.9 |
| [0,20] | +9.2 | 1,600 | 1.7 |

A 1500-game cap is therefore below the expected sample size of every design with elo1 <= 15 nElo: the queue's runs
end "cap, no decision" for every realistic effect, exactly what R3-3 observed.

## 3. Simulated decision probabilities (4000 runs per cell, the gate38 profile tilted to the true Elo; classical Elo)

P(H1) / P(H0) / P(cap) and expected games:

| design | -10 | -5 | 0 | +3 | +5 | +8 | +10 | +15 |
|---|---|---|---|---|---|---|---|---|
| [0,10] cap 1500 (queue) | 0/.69/.31, 1219 | 0/.22/.78, 1432 | 0/.03/.97, 1491 | .01/0/.99, 1497 | .04/0/.96, 1490 | .14/0/.86, 1459 | .26/0/.74, 1417 | .71/0/.29, 1204 |
| [0,5] cap 1500 (R3-3) | 0/.01/.99 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | .03/0/.97 |
| [0,5] cap 4000 | 0/.90/.10, 2912 | 0/.25/.75, 3832 | 0/0/.99, 3998 | .01/0/.99 | .06/0/.94 | .34/0/.66, 3741 | .63/0/.37, 3427 | .99/0/.01, 2407 |
| [0,10] cap 3000 | 0/.99/.01, 1363 | 0/.80/.20, 2104 | .01/.20/.78, 2825 | .09/.04/.87, 2900 | .25/.01/.74, 2776 | .61/0/.39, 2376 | .83/0/.17, 2026 | .99/0/.01, 1329 |
| **[0,10] cap 6000** | 0/1/0, 1356 | 0/.99/.01, 2267 | .03/.55/.42, 4567 | .28/.11/.60, 5092 | .61/.02/.36, 4367 | .96/0/.04, 2860 | 1/0/0, 2182 | 1/0/0, 1315 |
| [0,10] cap 8000 | 0/1/0 | 0/1/0, 2273 | .04/.70/.27, 5263 | .37/.15/.48, 6185 | .76/.02/.22, 4995 | .99/0/.01, 2897 | 1/0/0 | 1/0/0 |
| [0,20] cap 1500 (nets) | 0/.99/.01, 581 | 0/.91/.09, 811 | .03/.54/.43, 1147 | .11/.28/.61, 1272 | .21/.15/.64, 1290 | .44/.04/.52, 1211 | .61/.01/.37, 1114 | .92/0/.08, 781 |
| [-10,0] non-regression cap 3000 | 0/.83/.17, 2029 | .01/.24/.75, 2784 | .21/.01/.78, 2812 | .57/0/.43, 2445 | .80/0/.20, 2083 | .96/0/.04 | .99/0/.01 | 1/0/0 |
| [-3,1] non-regression cap 3000 | 0/.09/.91 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | .04/0/.96 | .15/0/.85 | .74/0/.26 |
| [-5,5] cap 2000 | 0/.76/.24 | 0/.24/.76 | .02/.02/.96 | .10/0/.89 | .24/0/.76 | .54/0/.47 | .74/0/.26 | .97/0/.03 |

## 4. Recommendation

1. **Search / evaluation features (expected +2..+8 Elo): SPRT [0,10] nElo, cap 6000 games (about 6 h).** It
   accepts a true +8 with 96%, a true +5 with 61%, rejects a true -5 with 99%, and its false-accept rate at 0 is 3%.
   The queue's [0,5]/1500 and [0,10]/1500 cannot decide any of these (P(decision) <= 4% up to +5). If 6 h per entry is
   too much, [0,10] cap 3000 (3 h) still decides a +8 with 61% and rejects a -5 with 80%.
2. **Node-exact speed changes (+0.5..+3% NPS, i.e. +0.2..+1.5 Elo): do not gate for Elo at all.** Even [0,10]/8000
   accepts a true +1.5 with about 12%. Use the quiet-runner paired NPS measurement (R3-2Q, the +2% lower-bound rule)
   plus a **non-regression SPRT [-10,0] nElo, cap 3000** (3 h): it rejects a true -5 with 24% and -10 with 83%, and a
   true 0 reaches H1 ("not worse than -4.6 Elo") 21% of the time, cap otherwise; the cap outcome with Elo +- 8 is the
   acceptable evidence that nothing broke. The rule-book's [-3,1] needs 40,000+ games (not feasible here).
3. **Trained nets (J1 and later): first the holdout, then [0,20] nElo cap 1500 (1.5 h)** as a cheap screen: a net
   that is +10 Elo or better is accepted with 61% and a net that is -5 or worse is rejected with 91%; a cap result
   sends it to design 1. Gate a net only after it beats AL1's exact holdout loss (0.014417 b0.6 on the FB2 holdout).
4. **Net early stop** (>= 750 games, Elo < -8, LLR < -1.5) stays as it is for [0,10]; for [-10,0] use LLR < -1.5
   unchanged (the scale is the same width), and never apply it to [0,20].
5. Keep one design per entry; never pool runs across concurrency or opponent (forge-gate-stats).

## 5. Ranking of the candidates by expected Elo per gate hour (design 1, priors stated)

The expected accepted Elo = sum over the prior of P(H1 | Elo) x max(Elo, 0); hours = expected games / 970.
Priors are my guesses (mean +- sd), stated so that the owner can replace them; the ranking is only as good as they
are, and the J1 prior is wide because the net is still training (it is below AL1 on the holdout at checkpoint 1).

| rank | candidate | prior Elo | P(H1) | E[Elo accepted] | E[hours] | **Elo / gate hour** | note |
|---|---|---|---|---|---|---|---|
| 1 | J1 v3 standalone net (only once it beats AL1 on the holdout; use design 3 first) | -15 +- 25 | 0.20 | 3.70 | 1.2 | 3.12 | huge spread: 1.17x NPS vs AL1 per node (+25 Elo equivalent at equal nets) against a holdout gap of 1.7e-3 (about -80 Elo by S44's 5 Elo per 1e-4); re-rank after each checkpoint |
| 2 | J3 CorrHistV2 | +3 +- 5 | 0.38 | 2.69 | 4.0 | 0.67 | continuation correction history |
| 3 | J3 LmrTableV2 | +1 +- 6 | 0.27 | 2.00 | 3.8 | 0.53 | fitted LMR (wide prior: observational fit) |
| 4 | J3 TtPruneV2 | +2 +- 5 | 0.31 | 2.08 | 4.0 | 0.51 | pruning guards and margins |
| 5 | J3 SingularV2 | +2 +- 5 | 0.31 | 2.08 | 4.1 | 0.51 | triple extensions / multicut |
| 6 | R3 search changes (CorrMargins, CorrExt, CuckooRep, HistRework) | +2 +- 5 each | 0.31 | 2.07 | 4.1 | 0.51 | R3-3 class B |
| 7 | J4 TimeManV2 | +2 +- 4 | 0.29 | 1.67 | 4.3 | 0.39 | fewer hard-deadline overruns at fast TC |
| 8 | R3 O2 AVX2 kernels (+3% NPS on a quiet runner; compiled out in the znver5 PC recipe) | +1.5 +- 1 | 0.12 | 0.23 | 5.1 | 0.05 | speed: use design 2 |
| 9 | R3 NOZERO (+1.6% NPS) | +0.8 +- 0.8 | 0.06 | 0.08 | 5.0 | 0.02 | speed: design 2 |
| 10 | R3 MaterialKeyTable / SPEEDSTACK / LazyAcc (<= +0.5% NPS) | +0.2 +- 0.3 | 0.03 | 0.01 | 4.8 | 0.00 | not worth a gate; keep as free merges after the NPS measurement |
| - | J5 SMP v2 | n/a | - | - | - | - | needs a Threads > 1 runner (R3-3 class C); gate only with Threads 4 on both sides |

Reading: with 6 h per decisive gate and roughly one gate per 4 h average, the PC decides about 4 search entries per
day; the J3/R3 search options are the sensible queue after the J1 net screen, speed entries should be merged on the
quiet-runner NPS evidence with a non-regression gate, and the net should not enter the queue before its holdout loss
is below AL1's.
