# S44 Elo vs epochs (and data) with the new gate points — advice only

**Question (spec S44):** fit every net gate as an unpooled effect-size point (not evidence) and say whether the
next PC run should be e64/e96 on the same data or more data at e48, with the expected gain as a range.

**Short answer:** **More data at e48.** On the conc-5 Elo scale (k = 5.0 ± 1.5 Elo per 1e-4 holdout b0.6, through the origin):
- e64 on the same data: +0.3 Elo (95% +0.1 .. +0.9) for 1.33× the compute;
- e96: +0.6 (+0.25 .. +2.1) for 2×;
- e48 with 1.25× the data: +2.7 (+1.1 .. +4.4); 1.5×: +4.9 (+2.0 .. +8.0); 2×: +8.5 (+3.4 .. +13.7).

At equal compute, data gives about 14× the Elo of extra epochs. Details and the other two groups' scales are under "Answer". Advice only; no Elo claim.

## Method
1. **Points.** One point per net gate, with nothing pooled; confirm gates are separate points. The PC's own
   RESULT.md and RUN_INFO.json give W/L/D, Ptnml, Elo, LLR and verdict, and the opponent, concurrency, cap and
   early-stop rule. Read-only copies are in `F:\opus_scratch\sol_S44\inputs\gates` with their sha256 in
   `s44_points.csv`.
   - The training run's data size comes from its settings dump and its holdout b0.6 from its final line (S30
     table, `train_where` = log line 6 of each run log), never from run names.
   - Citations: gates in the 2026-10-25 13:35 snapshot cite their row line in
     `LA/7_history/gate_results/gate_results_20261025_1335/GATE_RESULTS.csv|md|html`. Later gates cite
     `LATEST_GATE_FACTS_20261026.md` and the sha256 of their RESULT.md.
2. **Groups, kept apart.** Folder names are stale: G98, G103, G105-G112, G122 and G123 say `vs_h256e12` but were
   played against AL1 (RUN_INFO `base.name` = `base_AUTOLOCK_1_gate120_e32f003rec_s198`, exe sha256 833C47F3).
   The groups are:
   - **h256_e12 conc 5:** G90, G95, G100, G100r, G102, G104, G104c, G119;
   - **h256_e12 conc 7:** G120, G120c;
   - **AL1 conc 8:** G98, G103, G105, G106, G107, G109, G111, G112, G122, G123, G124, G124c, G125.
   Conc 5 and conc 7/8 are never pooled or ranked together (S48's comparability rule).
3. **Bias correction.** Each gate's own stopping rule is simulated from its own pentanomial profile, tilted to a
   grid of true Elos:
   - the rule: fastchess 1.8.2 SPRT [0,10] normalized, a = b = 0.05, with the exact GSPRT LLR. The tool
     reproduces all 23 printed LLRs to +-0.005; the Gaussian approximation is up to 0.1 off at H1 stops. Plus the
     1500-game cap and the queue's net early stop (>= 750 games, Elo < -8, LLR < -1.5) where RUN_INFO lists it;
   - the outputs: the **Whitehead bias-adjusted Elo** (solves E[Elo at stop | true Elo] = observed, over all
     outcomes) with its SE, used in the fits because every gate enters the fit whatever its verdict; and the
     **verdict-conditional bias** at that Elo (the winner's curse of an H1 or H0-early stop, the small negative
     bias of a cap), for information.
4. **Fits.** `Elo = k * dL`, where dL = opponent holdout b0.6 minus candidate holdout b0.6 in units of 1e-4.
   - For the e12 groups the fit goes through the origin (a net equal to e12 scores 0 against it); for AL1 conc 8
     it is fitted with and without an intercept. Weights are 1/SE^2, inflated by sqrt(chi2/dof) when above 1.
   - Only the b0.6 family is fitted (f-series and the s197/s198 reseeds). G90 (b0.8), G95 (b0.5) and G98 (b0.4
     e12rec) are listed but excluded: their b0.6 holdout does not measure them on their own target.
5. **Projection.** S30's holdout curves become Elo through k, by Monte Carlo over k's SE and the curve
   uncertainty:
   - the fixed-data epoch curve `L(E) = Linf + A E^-alpha`, refit with leave-one-out (L64 reproduced to 1e-12),
     for e64/e96 on the same data;
   - the e48 data curve `b06 = c + s ln(positions)` (-1.68e-4 per doubling, 95% CI -1.84..-1.41e-4, 23 runs)
     for more data at e48.

### Gate points (one per gate, unpooled)

| gate | group | net run (epochs, data) | holdout b0.6 | dL vs opp (1e-4) | games | verdict | Elo ± 95% | bias-adjusted Elo ± SE | verdict-cond. bias at adj | citation |
|---|---|---|---:|---:|---:|---|---:|---:|---:|---|
| G102 | h256_e12 conc5 | e24_f005_bs16k_lr10e4_b06_s24_fb8k (e24, 137.4M) | 0.014357 | +1.77 | 1500 | cap | +1.85 ± 9.28 | +1.90 ± 4.90 | +0.07 | snapshot csv:6 md:12 html:18; RESULT.md 9cd20850 |
| G100 | h256_e12 conc5 | e32_f003_bs16k_lr14e4_b06_s22_fb8k (e32, 127.4M) | 0.014371 | +1.63 | 1500 | cap | +8.34 ± 8.45 | +8.19 ± 4.51 | -1.16 | snapshot csv:7 md:13 html:19; RESULT.md 2420e0bb |
| G100r | h256_e12 conc5 | e32_f003_bs16k_lr14e4_b06_s22_fb8k (e32, 127.4M) | 0.014371 | +1.63 | 1500 | cap | +10.89 ± 8.38 | +10.41 ± 4.51 | -1.94 | snapshot csv:5 md:11 html:17; RESULT.md 49fe6466 |
| G119 | h256_e12 conc5 | e32_f003rec_s197_b06_fb8k (e32, 151.9M) | 0.014320 | +2.14 | 1500 | cap | +9.50 ± 8.84 | +9.13 ± 4.73 | -1.12 | snapshot csv:3 md:9 html:15; RESULT.md 7b953622 |
| G104 | h256_e12 conc5 | e48_f006_bs16k_lr10e4_b06_s25_fb8k (e48, 137.4M) | 0.014341 | +1.93 | 698 | H1 | +29.44 ± 13.23 | +27.88 ± 6.79 | +1.59 | snapshot csv:4 md:10 html:16; LGF:9; RESULT.md 9533e4db |
| G104c | h256_e12 conc5 | e48_f006_bs16k_lr10e4_b06_s25_fb8k (e48, 137.4M) | 0.014341 | +1.93 | 1500 | cap | +7.18 ± 8.49 | +6.96 ± 4.43 | -0.51 | LGF:10; RESULT.md 44982ffe |
| G95 | h256_e12 conc5 | e12_f (e12, 95.4M) (b05, not fitted) | 0.014666 | -1.32 | 1500 | cap | +0.23 ± 8.53 | +0.25 ± 4.49 | +0.27 | snapshot csv:8 md:14 html:20; RESULT.md fd7bcf2f |
| G90 | h256_e12 conc5 | e16_m_lr7e4_b08_s10 (e16, 127.4M) (b08, not fitted) | 0.014497 | +0.37 | 1360 | H0 | -10.48 ± 9.06 | -9.43 ± 5.14 | -4.83 | snapshot csv:9 md:15 html:21; RESULT.md a97a3d68 |
| G120 | h256_e12 conc7 | e32_f003rec_s198_b06_fb8k (e32, 151.9M) | 0.014311 | +2.23 | 928 | H1 | +23.62 ± 11.90 | +22.01 ± 6.22 | +2.37 | snapshot csv:2 md:8 html:14; LGF:7; RESULT.md 906f1cad |
| G120c | h256_e12 conc7 | e32_f003rec_s198_b06_fb8k (e32, 151.9M) | 0.014311 | +2.23 | 1418 | H1 | +14.46 ± 8.61 | +13.53 ± 4.82 | +4.89 | snapshot csv:33 md:85 html:79; LGF:8; RESULT.md 0cc1c5da |
| G103 | AL1 conc8 | e16_f004_bs16k_lr14e4_b06_sol_s23_fb8k (e16, 132.8M) | 0.014407 | -0.96 | 1500 | cap | +6.49 ± 8.63 | +6.47 ± 4.66 | -0.43 | LGF:16; RESULT.md e777d11d |
| G105 | AL1 conc8 | e16_f007_bs16k_lr14e4_b06_s26_fb8k (e16, 137.4M) | 0.014367 | -0.56 | 1500 | cap | +3.94 ± 8.77 | +4.06 ± 4.67 | +0.27 | LGF:19; RESULT.md 8671721f |
| G107 | AL1 conc8 | e16_f009_bs16k_lr14e4_b06_s28_fb8k (e16, 137.4M) | 0.014390 | -0.79 | 1500 | cap | +0.46 ± 8.49 | +0.96 ± 4.62 | +0.76 | RESULT.md ccba9d7c |
| G109 | AL1 conc8 | e16_f010_bs16k_lr12e4_b06_s29_fb8k (e16, 137.4M) | 0.014389 | -0.78 | 760 | H0-early | -11.43 ± 12.28 | -10.20 ± 6.13 | -1.78 | RESULT.md b43b8323 |
| G111 | AL1 conc8 | e16_f012_bs16k_lr14e4_b06_sol_s31_fb8k (e16, 142.8M) | 0.014390 | -0.79 | 1500 | cap | +4.86 ± 8.55 | +4.96 ± 4.56 | -0.03 | RESULT.md 387b4a34 |
| G106 | AL1 conc8 | e20_f008_bs16k_lr12e4_b06_sol_s27_fb8k (e20, 142.8M) | 0.014389 | -0.78 | 1500 | cap | +8.80 ± 8.57 | +8.48 ± 4.47 | -1.05 | RESULT.md 943eaf08 |
| G112 | AL1 conc8 | e20_f014_bs16k_lr10e4_b06_s33_fb8k (e20, 147.4M) | 0.014345 | -0.34 | 762 | H0-early | -13.23 ± 12.10 | -12.36 ± 6.24 | -0.13 | RESULT.md ba0867f0 |
| G122 | AL1 conc8 | e48_f030_bs16k_lr10e4_b06_s49_fb8k (e48, 161.9M) | 0.014271 | +0.40 | 1500 | cap | +4.86 ± 9.25 | +4.99 ± 4.86 | +0.06 | LGF:11; RESULT.md 98b006a8 |
| G123 | AL1 conc8 | e48_f031_bs16k_lr10e4_b06_s331_fb8k (e48, 161.9M) | 0.014284 | +0.27 | 1500 | cap | +9.04 ± 8.54 | +8.78 ± 4.68 | -1.24 | LGF:12; RESULT.md f6f2f336 |
| G124 | AL1 conc8 | e48_f034_bs16k_lr10e4_b06_s334_fb8k (e48, 171.9M) | 0.014275 | +0.36 | 1432 | H1 | +14.81 ± 8.89 | +13.81 ± 4.89 | +5.08 | LGF:13; RESULT.md 71acba3c |
| G124c | AL1 conc8 | e48_f034_bs16k_lr10e4_b06_s334_fb8k (e48, 171.9M) | 0.014275 | +0.36 | 1500 | cap | +11.35 ± 8.95 | +10.73 ± 4.92 | -1.86 | LGF:14; RESULT.md 068538a1 |
| G125 | AL1 conc8 | e48_f042_bs16k_lr10e4_b06_s342_fb8k (e48, 181.9M) | 0.014252 | +0.59 | 1500 | cap | +6.02 ± 8.94 | +6.00 ± 4.61 | -0.25 | LGF:15; RESULT.md 0c94758a |
| G98 | AL1 conc8 | e12rec_b04_s200_fb8k (e12, 127.4M) (b04, not fitted) | 0.014780 | -4.69 | 1500 | cap | +6.25 ± 9.20 | +6.18 ± 4.89 | -0.16 | LGF:17; RESULT.md a43fa044 |

### Stopping-rule simulation checks

| gate | reps per Elo | Elo grid | exact LLR rows | max crossing-hiding drift (band 0.3) | degenerate rows | cap-cond. bias at true +10 |
|---|---:|---|---:|---:|---:|---:|
| G102 | 4000 | -22..+16 (20) | 3,499,872 | 0.100 | 0 | -1.50 |
| G100 | 4000 | -14..+24 (20) | 3,692,591 | 0.127 | 0 | -1.85 |
| G100r | 4000 | -12..+26 (20) | 3,708,385 | 0.150 | 0 | -1.73 |
| G119 | 4000 | -14..+24 (20) | 2,552,823 | 0.105 | 0 | -1.45 |
| G104 | 4000 | +6..+40 (18) | 4,043,825 | 0.203 | 2 | +8.47 |
| G104c | 4000 | -16..+22 (20) | 2,454,865 | 0.099 | 116 | -1.53 |
| G95 | 4000 | -22..+16 (20) | 3,646,467 | 0.134 | 0 | -1.64 |
| G90 | 4000 | -34..+10 (21) | 4,048,014 | 0.136 | 10 | — |
| G120 | 4000 | +0..+38 (20) | 3,799,557 | 0.159 | 0 | +9.37 |
| G120c | 4000 | -8..+30 (20) | 3,072,325 | 0.167 | 0 | +7.56 |
| G103 | 4000 | -16..+22 (20) | 2,443,763 | 0.114 | 0 | -1.60 |
| G105 | 4000 | -20..+18 (20) | 2,099,418 | 0.112 | 0 | -1.49 |
| G107 | 4000 | -22..+16 (20) | 2,049,610 | 0.114 | 0 | -1.59 |
| G109 | 4000 | -34..+10 (21) | 2,338,181 | 0.181 | 3 | — |
| G111 | 4000 | -18..+20 (20) | 2,278,839 | 0.132 | 0 | -1.65 |
| G106 | 4000 | -14..+24 (20) | 2,555,860 | 0.108 | 0 | -1.61 |
| G112 | 4000 | -36..+10 (21) | 2,415,205 | 0.113 | 0 | — |
| G122 | 4000 | -18..+20 (20) | 2,135,871 | 0.109 | 0 | -1.40 |
| G123 | 4000 | -14..+24 (20) | 2,598,373 | 0.123 | 0 | -1.68 |
| G124 | 4000 | -8..+30 (20) | 3,085,889 | 0.150 | 0 | +7.86 |
| G124c | 4000 | -12..+26 (20) | 2,668,223 | 0.139 | 1 | -1.53 |
| G125 | 4000 | -16..+22 (20) | 2,366,625 | 0.098 | 0 | -1.51 |
| G98 | 4000 | -16..+22 (20) | 2,307,657 | 0.090 | 0 | -1.29 |

### Fits: Elo = (c +) k * dL, dL in 1e-4 holdout b0.6 (b0.6 family only)

| group | Elo used | model | n | k (Elo per 1e-4) ± SE | c ± SE | chi2/dof | SE inflation |
|---|---|---|---:|---:|---:|---:|---:|
| AL1 conc8 | adjusted | c + k dL | 12 | +4.25 ± 3.20 | +6.03 ± 2.03 | 17.6/10 | 1.33 |
| AL1 conc8 | adjusted | k dL | 12 | +0.50 ± 3.85 | +0.00 ± 0.00 | 33.2/11 | 1.74 |
| AL1 conc8 | raw | c + k dL | 12 | +4.71 ± 3.35 | +6.36 ± 2.11 | 21.0/10 | 1.45 |
| AL1 conc8 | raw | k dL | 12 | +0.80 ± 4.07 | +0.00 ± 0.00 | 40.0/11 | 1.91 |
| h256_e12 conc5 | adjusted | c + k dL | 6 | +4.88 ± 16.54 | +0.27 ± 30.36 | 10.0/4 | 1.58 |
| h256_e12 conc5 | adjusted | k dL | 6 | +5.02 ± 1.52 | +0.00 ± 0.00 | 10.0/5 | 1.41 |
| h256_e12 conc5 | raw | c + k dL | 6 | +4.92 ± 17.03 | +0.47 ± 31.23 | 11.6/4 | 1.70 |
| h256_e12 conc5 | raw | k dL | 6 | +5.18 ± 1.57 | +0.00 ± 0.00 | 11.6/5 | 1.52 |
| h256_e12 conc7 | adjusted | k dL | 2 | +7.49 ± 1.84 | +0.00 ± 0.00 | 1.2/1 | 1.08 |
| h256_e12 conc7 | raw | k dL | 2 | +7.90 ± 1.95 | +0.00 ± 0.00 | 1.5/1 | 1.22 |

### Next-run options (projections from the adjusted-Elo fits)

**AL1 conc8 | adjusted | c + k dL**

| option | compute vs e48 on same data | holdout gain (1e-4) | Elo central | Elo p10 / p50 / p90 | Elo 95% |
|---|---:|---|---:|---|---|
| e64 same data | x1.33 | 0.057 (range 0.035..0.142) | +0.24 | +0.01 / +0.33 / +0.82 | -0.17 .. +1.13 |
| e96 same data | x2.00 | 0.116 (range 0.063..0.336) | +0.49 | +0.03 / +0.72 / +1.89 | -0.38 .. +2.63 |
| e48 data x1.10 | x1.10 | 0.231 (95% 0.201..0.261) | +0.98 | +0.03 / +0.98 / +1.94 | -0.47 .. +2.46 |
| e48 data x1.25 | x1.25 | 0.541 (95% 0.471..0.611) | +2.30 | +0.08 / +2.29 / +4.54 | -1.10 .. +5.76 |
| e48 data x1.50 | x1.50 | 0.983 (95% 0.856..1.111) | +4.18 | +0.15 / +4.15 / +8.24 | -2.01 .. +10.45 |
| e48 data x2.00 | x2.00 | 1.681 (95% 1.464..1.899) | +7.15 | +0.25 / +7.10 / +14.11 | -3.42 .. +17.88 |

**AL1 conc8 | adjusted | k dL**

| option | compute vs e48 on same data | holdout gain (1e-4) | Elo central | Elo p10 / p50 / p90 | Elo 95% |
|---|---:|---|---:|---|---|
| e64 same data | x1.33 | 0.057 (range 0.035..0.142) | +0.03 | -0.39 / +0.04 / +0.49 | -0.69 .. +0.81 |
| e96 same data | x2.00 | 0.116 (range 0.063..0.336) | +0.06 | -0.88 / +0.08 / +1.11 | -1.59 .. +1.87 |
| e48 data x1.10 | x1.10 | 0.231 (95% 0.201..0.261) | +0.11 | -1.02 / +0.11 / +1.26 | -1.64 .. +1.88 |
| e48 data x1.25 | x1.25 | 0.541 (95% 0.471..0.611) | +0.27 | -2.40 / +0.26 / +2.94 | -3.84 .. +4.39 |
| e48 data x1.50 | x1.50 | 0.983 (95% 0.856..1.111) | +0.49 | -4.36 / +0.47 / +5.34 | -6.98 .. +7.95 |
| e48 data x2.00 | x2.00 | 1.681 (95% 1.464..1.899) | +0.84 | -7.45 / +0.81 / +9.15 | -11.91 .. +13.61 |

**h256_e12 conc5 | adjusted | c + k dL**

| option | compute vs e48 on same data | holdout gain (1e-4) | Elo central | Elo p10 / p50 / p90 | Elo 95% |
|---|---:|---|---:|---|---|
| e64 same data | x1.33 | 0.057 (range 0.035..0.142) | +0.28 | -1.41 / +0.37 / +2.38 | -2.65 .. +3.80 |
| e96 same data | x2.00 | 0.116 (range 0.063..0.336) | +0.57 | -3.14 / +0.79 / +5.40 | -6.11 .. +8.77 |
| e48 data x1.10 | x1.10 | 0.231 (95% 0.201..0.261) | +1.13 | -3.75 / +1.11 / +6.04 | -6.41 .. +8.69 |
| e48 data x1.25 | x1.25 | 0.541 (95% 0.471..0.611) | +2.64 | -8.79 / +2.59 / +14.12 | -14.97 .. +20.33 |
| e48 data x1.50 | x1.50 | 0.983 (95% 0.856..1.111) | +4.80 | -16.00 / +4.71 / +25.64 | -27.21 .. +36.86 |
| e48 data x2.00 | x2.00 | 1.681 (95% 1.464..1.899) | +8.20 | -27.32 / +8.06 / +43.88 | -46.48 .. +63.09 |

**h256_e12 conc5 | adjusted | k dL**

| option | compute vs e48 on same data | holdout gain (1e-4) | Elo central | Elo p10 / p50 / p90 | Elo 95% |
|---|---:|---|---:|---|---|
| e64 same data | x1.33 | 0.057 (range 0.035..0.142) | +0.29 | +0.20 / +0.42 / +0.74 | +0.13 .. +0.91 |
| e96 same data | x2.00 | 0.116 (range 0.063..0.336) | +0.58 | +0.40 / +0.93 / +1.72 | +0.25 .. +2.14 |
| e48 data x1.10 | x1.10 | 0.231 (95% 0.201..0.261) | +1.16 | +0.71 / +1.16 / +1.62 | +0.47 .. +1.88 |
| e48 data x1.25 | x1.25 | 0.541 (95% 0.471..0.611) | +2.72 | +1.65 / +2.71 / +3.80 | +1.09 .. +4.41 |
| e48 data x1.50 | x1.50 | 0.983 (95% 0.856..1.111) | +4.94 | +3.00 / +4.91 / +6.90 | +2.00 .. +7.99 |
| e48 data x2.00 | x2.00 | 1.681 (95% 1.464..1.899) | +8.45 | +5.14 / +8.40 / +11.82 | +3.41 .. +13.69 |

**h256_e12 conc7 | adjusted | k dL**

| option | compute vs e48 on same data | holdout gain (1e-4) | Elo central | Elo p10 / p50 / p90 | Elo 95% |
|---|---:|---|---:|---|---|
| e64 same data | x1.33 | 0.057 (range 0.035..0.142) | +0.43 | +0.31 / +0.63 / +1.07 | +0.23 .. +1.29 |
| e96 same data | x2.00 | 0.116 (range 0.063..0.336) | +0.87 | +0.63 / +1.41 / +2.49 | +0.43 .. +3.02 |
| e48 data x1.10 | x1.10 | 0.231 (95% 0.201..0.261) | +1.73 | +1.17 / +1.72 / +2.30 | +0.88 .. +2.62 |
| e48 data x1.25 | x1.25 | 0.541 (95% 0.471..0.611) | +4.06 | +2.74 / +4.04 / +5.39 | +2.07 .. +6.13 |
| e48 data x1.50 | x1.50 | 0.983 (95% 0.856..1.111) | +7.37 | +4.99 / +7.33 / +9.79 | +3.76 .. +11.13 |
| e48 data x2.00 | x2.00 | 1.681 (95% 1.464..1.899) | +12.60 | +8.53 / +12.54 / +16.75 | +6.43 .. +19.06 |

S30 epoch-curve refit: L64 0.014334782805 vs S30 0.014334782805

## Reading the points
- **The H1 gates barely move after the Whitehead adjustment.** G104 goes 29.4 → 27.9, G120 23.6 → 22.0,
  G120c 14.5 → 13.5 and G124 14.8 → 13.8. The adjustment answers "what true Elo makes this gate's estimate
  unbiased over all its outcomes". At those strengths H1 is the usual outcome, so the overall bias is small.
- **The winner's curse is large.** It answers "given that the gate said H1, how much too high is the estimate".
  At true +10 it is +7.6 to +9.4 Elo for the H1 gates (G104 +8.47, G120 +9.37, G120c +7.56, G124 +7.86), as
  Sol's S48 found (+8.17). At the adjusted strength it is +1.6 (G104, where H1 is nearly certain) to +5.1
  (G120c, G124).
- **Caps lean the other way.** A capped gate is the run that did not reach H1, so its estimate leans low: the
  cap-conditional bias at true +10 is −1.3 to −1.9 Elo (G100r −1.73, G119 −1.45; Sol's S48: −1.76, −1.62).
- **G104 vs G104c.** The same f006 net gave +27.9 (H1 at 698 games) and +7.0 (confirm cap). The gap of 20.9
  with SEs 6.8 and 4.4 is z ≈ 2.6, unusual but possible among 23 gates. Both stay in the fit as separate points.
- **Elo vs epochs, directly** (no holdout bridge):
  - Against AL1 at conc 8, the e16/e20 nets (data 133-147M) average +1.2/−1.9 and the e48 nets (162-182M)
    average +8.9 (adjusted).
  - Against e12 at conc 5, e24 f005 is +1.9, e32 f003/s197 +8.2/+10.4/+9.1 and e48 f006 +27.9/+7.0.
  - In both groups epochs and data rise together (the e48 runs also have more data), so the direct view
    cannot separate them. The holdout bridge below can.
- **AL1 conc 8 has an offset.** Its intercept is +6.0 ± 2.0: a net with AL1's own holdout loss scores about +6
  Elo against AL1 at conc 8 (12 b0.6 nets, χ²/dof 1.8). Possible reasons are not separated here: conc 8 time
  pressure, AL1's net (s198) being luckier in holdout than in play, or a recipe difference (AL1 is an e32 reseed,
  the candidates are e16/e20/e48 f-series). The through-origin fit is rejected there (χ²/dof 3.0).

## Answer: next PC run
| option (same recipe, e48 unless stated) | compute vs e48 on today's data | expected Elo, conc-5 scale (k = 5.0 ± 1.5 / 1e-4) | conc-7 scale (k = 7.5 ± 1.8) | AL1 conc-8 fit (k = 4.3 ± 3.2) |
|---|---:|---|---|---|
| e64 on the same data | ×1.33 | +0.3 (95% +0.1 .. +0.9) | +0.4 (+0.2 .. +1.3) | +0.2 (−0.2 .. +1.1) |
| e96 on the same data | ×2.00 | +0.6 (95% +0.25 .. +2.1) | +0.9 (+0.4 .. +3.0) | +0.5 (−0.4 .. +2.6) |
| e48, data ×1.10 | ×1.10 | +1.2 (95% +0.5 .. +1.9) | +1.7 (+0.9 .. +2.6) | +1.0 (−0.5 .. +2.5) |
| e48, data ×1.25 | ×1.25 | +2.7 (95% +1.1 .. +4.4) | +4.1 (+2.1 .. +6.1) | +2.3 (−1.1 .. +5.8) |
| e48, data ×1.50 | ×1.50 | +4.9 (95% +2.0 .. +8.0) | +7.4 (+3.8 .. +11.1) | +4.2 (−2.0 .. +10.5) |
| e48, data ×2.00 | ×2.00 | +8.5 (95% +3.4 .. +13.7) | +12.6 (+6.4 .. +19.1) | +7.2 (−3.4 .. +17.9) |

- **More data at e48 is the better next run.** At equal compute (×2), doubling the data is expected to give about
  14× the Elo of e96 (+8.5 vs +0.6 on the conc-5 scale). Even +10% data beats e96, and e64 is worth about a third
  of an Elo point.
- **Why:**
  - The fixed-data epoch curve (S30, 137.4M positions) is nearly flat after e48: L(48) = 0.014341,
    L(64) = 0.014335, L(96) ≈ 0.014329 (leave-one-out ranges in the tables).
  - The e48 data curve keeps falling, −1.68e-4 b0.6 per doubling over 23 runs from 137M to 222M positions.
  - The fitted Elo per 1e-4 is 4-7.5 in all three groups.
- **The ranges are model ranges, not gate predictions.** k comes from 6 (conc 5), 2 (conc 7) and 12 (conc 8)
  unpooled, noisy points. The holdout→Elo slope is assumed constant across recipes and data sizes, and the epoch
  curve is fitted at 137M positions (it may bend differently with more data).
- **Gate resolution.** A 1500-game gate resolves about ±8.5 Elo (95%). The e64/e96 gains are far below that, so
  an SPRT [0,10] would mostly cap. Only a ×1.5-×2 data step reaches the edge of what one gate can see.
- **Practical advice:**
  - Keep e48 and grow the training set with fresh self-play. The PC's queue already adds about 10M positions per
    step (f029→f070: 162M→222M).
  - Gate a candidate only after a step of at least ×1.5 since the last gated net, or pool the evidence by
    gating against the same opponent at the same concurrency.
  - Advice only; no claim.

## Checks of the method
- **Printed statistics:** all 23 net gates reproduce exactly (Elo, error, nElo, LLR within the 0.005 print
  rounding; `logs/step1_check.log`). The exact GSPRT matches a line-by-line scalar port of fishtest LLRcalc to
  1e-9 (tests).
- **Simulation:**
  - The fast stopping rule equals a brute-force exact-LLR run on 8 cases (identical verdicts, stop pairs and Elo;
    tests).
  - In the full run the largest crossing-hiding gap drift was 0.203 (G104), below the 0.3 band that guarantees no
    missed crossing (the run warns above 0.15).
  - A few rows fell back to the approximate LLR because the exact constrained MLE does not exist for degenerate
    cell counts: 116 rows of G104c's 2.45M, at most 10 elsewhere.
- **Replicates:** 4000 per true Elo, step 2 Elo, common random numbers across the grid; seeds in
  `s44_results.json`.
- **S30 epoch curve:** the refit reproduces S30's L64 to 1e-12.

## UNVERIFIED / limits
- No new games; every number comes from existing gates and logs. No Elo claim, advice only.
- The pentanomial tilt keeps each gate's draw profile and moves only the mean. True profiles at other strengths
  may differ.
- G105 and G120c were still running in the snapshot (G120c 360 games) or in LATEST_GATE_FACTS (G105 764 games);
  their points use the final RESULT.md, cited by sha256.
- The holdout b0.6 is not the play target of the b0.4/b0.5/b0.8 nets (G90, G95, G98), so they are listed but not
  fitted.
- The conc-8 offset is unexplained. More AL1 gates at conc 8 with nets of known holdout (a cross-recipe check)
  would separate a scale effect from luck.
