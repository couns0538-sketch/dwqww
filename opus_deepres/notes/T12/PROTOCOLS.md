# T12 protocols for Forge gates, tuning and speed proofs (UNPROVEN planning numbers, no Elo claim)

Inputs: crew FORGE_RESULTS.csv (110 gates with Ptnml, read-only), the UHO gate settings of
F:/forge_push/uhoE3a_evalmatscale12_r6k_vs_AL1lp (fastchess 1.8.2, 10+0.1, Threads=2, Hash 16, conc 4, CPUs 4-15,
UHO_Lichess_4852_v1.epd, random start), gate rate ~497 games/h (forge-gate-summary). Model script and raw output:
notes/T12/sprt_model.md (own code; Brownian approximation of the GSPRT, 20k Monte-Carlo walks per row).

## 1. SPRT bounds, normalised vs logistic Elo, expected games
- Normalised Elo: nElo = (a - 0.5) / sqrt(2 var) * 800/ln10 with a and var the mean and variance of the pair score
  (forge-gate-stats). In t units per pair, t = nElo * sqrt(2) * ln10 / 800 = 0.004070 * nElo.
- LLR model: per pair, drift dt * (t - (t0+t1)/2), variance dt^2, dt = (nElo1 - nElo0) * 0.004070; stop at
  +-ln(19) = +-2.944 (alpha = beta = 0.05). Mean pairs at either bound end = 0.9 * 2.944 / (dt^2 / 2); at the
  midpoint = 2.944^2 / dt^2. Depends only on the width (fishtest wiki: independent of draw ratio and book).
- Unit check on Forge's own gates: assuming [0,10], the model LLR = pairs * dt * (t_hat - t_mid) matches the printed
  LLR of 82 of the 85 undecided gates (|LLR| < 2.9) within 0.15 (mean diff -0.05). The 3 others: R5D-MF ([-10,0] non-regression), G101
  and R7-PFE (other bounds).
- Logistic vs normalised on Forge's books (median of gates with |Elo| > 3): UHO nElo = 1.91 x Elo (6 gates, range
  1.87-1.95), 8moves_v3 2.10 x Elo (63 gates, 1.90-2.40). So [0,10] nElo = about [0, 5.2] Elo on UHO and
  [0, 4.8] Elo on 8moves_v3; [0,5] nElo = about [0, 2.6] Elo on UHO.
- Fishtest's own bounds (Stockfish commit 5c617e579c): STC <0.00,2.00>, LTC <0.50,2.50>, non-regression
  <-1.75,0.25> (fishtest wiki), all width 2 nElo -> ~165k games at the ends (table, last row): affordable only
  for a fleet; at 497 games/h one such test is ~2 weeks. Forge's widths must be 5-10x wider.

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

What the capped gates were: 79 of 110 gates with Ptnml ended "Cap with no decision" (55 at 1,500 games, 14 at
3,000, 9 at 1,000, 1 at 6,000; 4 more stopped by the net early-stop rule, 1 NOT CLEAN, 1 TRIAL-ONLY). Their nElo
10/50/90 % quantiles -9.0 / +7.4 / +18.2; 53 % had |nElo| <= 10 - exactly the zone where [0,10] is slowest (the
midpoint +5 needs 11k games on average). A 3,000-game cap decides about 1 in 5 of [0,10] runs at the bound ends.

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
- Books (official-stockfish/books README @a804a97e70, CC0-1.0): UHO_Lichess_4852_v1.epd has 2,632,036 openings
  (1,457,270 white / 1,174,766 black to move, 2-16 plies); 8moves_v3.pgn has 34,700 (16 plies). A 12k-game cap with
  -repeat uses 6,000 openings: 0.2 % of UHO, 17 % of 8moves_v3. Random start (as the queue does) keeps gates
  unpooled and seeds different.
- Forge numbers: UHO draw ratio 0.56 vs 0.75 on 8moves_v3. Pairing removes 38 % of the variance on UHO vs 10 % on
  8moves_v3. nElo/Elo = 1.91 vs 2.10.
- Which book decides a given patch faster depends on the nElo the patch shows on each book. Forge has no same-patch
  pair with enough games to tell: Sf26Bundle=14 read -8.5 nElo (8moves_v3) vs -6.6 (UHO) at 1,500 games each, both
  +-17. A paired study needs ~6k games per book. Until then keep the current rule: UHO is the STC gate book,
  8moves_v3 the separate confirm, never pooled.
- TC: fishtest STC 10+0.1, LTC 60+0.6 (6x), tuning at "normal TC", Hash 16 at 20+0.2 and 64 at 60+0.6 (fishtest
  wiki). Forge's gate is 10+0.1 with Threads=2, ~497 games/h. Rate scales about 1/TC: 30+0.3 ~166 games/h, 60+0.6
  ~83 games/h (UNPROVEN, linear in TC).
- LTC plan: only for candidates that passed STC. 30+0.3 at [0,15] nElo, cap 6,000: mean ~2.95k games at the ends
  = ~18 h, cap ~36 h. 60+0.6 at [0,10] would need a mean ~6.6k games = ~80 h: not routine. Use Hash 32-64 at LTC.

## 4. SPSA plan for 20 search parameters
Mechanics (fishtest wiki, OpenBench wiki SPSA-Tuning-Workloads, R9/O30 tuners already built):
- Engines theta+c_k*delta and theta-c_k*delta play a pair. Update theta += a_k/c_k * (W-L) * delta, with
  c_k = c0/(1+k)^gamma, a_k = a0/(A+1+k)^alpha, r_k = a_k/c_k^2 (fishtest wiki). c0 and a0 are set so that c_k and
  r_k reach c_end and r_end at the last iteration (R9: c0 = c_end N^gamma, a0 = r_end c_end^2 (A+N)^alpha). Defaults alpha 0.602,
  gamma 0.101, A = 0.1 N (OpenBench; R9 uses the same). r_end "ideal 0.0020" (OpenBench). c_end ~ 1/20 of the
  reasonable range and >= 0.5 for ints (OpenBench). The fishtest rule: c "large enough to have a measurable Elo
  difference".
- Own power model (UHO profile, per-pair W-L variance v = 16 x 0.0345 = 0.55): if theta+ beats theta- by e logistic
  Elo along one parameter, its z after N pairs is about sqrt(N) x 0.0077 x e. The other 19 parameters add almost no
  variance; their Elo effects are tiny against game noise.
  For z = 2: N = 66,700 / e^2 pairs. e = 1 -> 133k games; e = 2 -> 33k; e = 3 -> 15k; e = 4 -> 8.3k; e = 5 -> 5.3k.
  On 8moves_v3 (v = 0.45) the same e needs ~20 % fewer pairs, but tune on the gate book.
- Check against R9: 832 pairs at 8+0.08 (8moves_v3) found 0 of 16 beyond 2 sigma. The model says 832 pairs resolve
  only e >= 8-9 Elo swings, which matches "only far-off parameters show".

Budget and wall time (20 parameters, UNPROVEN rates):
| target swing e | pairs | games | h at 497 g/h (gate slot, Threads 2) | h at ~1,000 g/h (Threads 1, conc 8, CPUs 4-15) |
|---|---|---|---|---|
| 4 Elo | 4,170 | 8,340 | 17 | 8 |
| 3 Elo | 7,410 | 14,820 | 30 | 15 |
| 2 Elo | 16,680 | 33,350 | 67 | 33 |
The ~1,000 g/h figure is 10 CPUs x ~100 games/h per CPU (forge-o30-spsa: ~100 games/h at 10+0.1, conc 1, one CPU)
and is not measured. SMT siblings share a core, so it may be ~30 % lower.
Recommended run: 16,680 pairs (33k games). 8 pairs per point (OpenBench: "8 seems to work well for LTC") = 2,085
iterations, A = 208. 10+0.1 (or 8+0.08, ~1.2x faster), Threads=1, Hash 16, UHO, random start.

Step sizes (own, not other engines' values): c_end = max(range/20, 1 unit) so that +-c_end is worth ~2 Elo. Forge's
steep gates show a 20-25 % change of a history / SEE scale moves 7-17 nElo (TRIED_GATES: HistMalusPct=125 -15.6,
ContHist4Pct=45 +16.9 / 85 -10.9, CaptSeeDiv=80 +7.0 / 120 -8.8). So c_end ~ 8-10 % of the value suits scales.
Margins in cp: c_end ~ 1/20 of the range. LMR terms in 1/1024 ply: c_end >= 1024, whole plies only (forge-o30-spsa:
half-ply steps round away), or leave them out. r_end 0.002 for 16k pairs (R9's 0.012 was for 832 pairs).

How to pick the 20 (from the 63 exposed: 41 lock + 22 o30_expose):
1. Live: each moves bench at +-c_end (pin_check / r9_option_check).
2. Frequent: acts at most nodes. LMR base/divisor, RFP margin/depth, NMP base/divisor/eval terms, LMP base, futility
   margin, SEE quiet/capture thresholds, history bonus/malus scale and offset, continuation weight, aspiration delta
   and grow, singular margin/depth, probcut margin, qsearch futility margin.
3. Steep: single-option gates moved >= 5 nElo (list above) -> include.
4. Leave out: time-management constants (separate tune), the Sf26 bits already tuned locally, booleans, and
   parameters that rarely fire. Keep coupled pairs (base + divisor) in the same run.
5. More than 20 candidates: two runs of 10-12, steepest first.
Reading: z vs the null-gradient sigma per parameter (R9 report). Package only |z| >= 2 (O30Tuned switch). Gate: tuned
set vs lock at defaults, UHO SPRT [0,10] cap 12k at STC, then the 8moves_v3 confirm, then LTC. Never act on a
mid-run z (R9).

## 5. nps protocol for 1 % effects at 2-5 % A/A noise
1. Identity first (T12-03 levels 1-3 at least). A speed number for two programs that search differently is void.
2. Machine: one logical CPU of a physical core whose SMT sibling is idle (LLVM: "Disable the SMT pair"). On the
   9850X3D, CPUs 2k / 2k+1 share a core; CPUs 2-3 = one core (forge-opus-tools). No gate, trainer or self-play mask
   may include either sibling during the run. Idle/BelowNormal priority. Free RAM >= 4 GB.
3. Boost/thermal: either (a) PERFBOOSTMODE = 0 (Disabled, Microsoft docs) on the active plan for the window, only with
   the owner's OK and no gate running (it slows every process), or (b) boost on, short tightly interleaved runs, and a
   log of effective clock and temperature per run (HWiNFO keeper log). Drop a block whose A and B halves differ by
   more than 2 % in mean clock. Record which one was used.
4. Layout: a fresh byte copy of the exe for every run (new file -> new cached pages and a new per-boot ASLR base).
   This turns the per-file bias (R12: -3.0 % exe vs own copy) into random noise. Copies are kept (no deletes):
   ~2 MB each.
5. Design: fresh process per run. `bench 16` (~3.0M nodes, ~2-3 s). Bench-window CPU time and engine nps, warm-up
   run discarded. Palindromic order of arms A, B, A' (A' = fresh copies of A): A B A' A' B A, ...
6. Run count: pilot 20 pairs -> s (sd of the per-pair log ratio, in %). Then n = 8.6 x s^2 pairs for 90 % power to
   show a true +1 % at one-sided 95 % (s 2 % -> 35, 3 % -> 78, 5 % -> 215 pairs; 215 pairs ~25 min). Showing
   ">= 0.5 %" needs 4x.
7. Statistics: geometric mean of per-pair ratios, Student-t 95 % CI on log ratios (abba.py). A/A' must contain 0.
   B/A lower bound > 0 and point estimate >= 1 % -> keep. Report median, CI, A/A, load lines, boost mode. Replicate
   once on another day (or after a reboot) before calling it.
8. Source scale: fishtest says 1 % speed-ups pass its SPRT with 85 % chance and ~0.25 % gives 50 % at STC (wiki).
   LLVM reaches < 0.1 % run variation on an isolated Linux core. Forge's Windows box with crew load will not; the run
   count rule above absorbs it.
