# S44 Elo-vs-epochs fit with the gate points (advice only)

`forge_sol_S44_elo_vs_epochs.py` (numpy, read-only inputs):
- `check --gates DIR`: recomputes every gate's Elo, Elo error, nElo and LLR from its Ptnml line and compares them
  with the printed values (all 23 net gates within the print rounding, 0.005).
- `run --gates DIR --snapshot DIR --lgf FILE --s30-table CSV --s30-fit JSON --out DIR [--reps N --step S --draws D
  --seed S]`:
  1. Builds one point per net gate. The opponent, concurrency and early-stop rule come from RUN_INFO.json /
     RESULT.md, never from folder names: G98, G103, G105-G112, G122 and G123 were played against AL1 although
     their folders say `vs_h256e12`. Each point gets the training run's data size (settings dump) and holdout b0.6
     (final line) from the S30 table.
  2. Simulates each gate's own stopping rule at a grid of true Elos, from the gate's pentanomial profile tilted to
     each Elo. The rule is fastchess's exact GSPRT [0,10] normalized at a=b=0.05, the 1500-game cap, and the
     queue's net early stop where RUN_INFO lists it. It then reports, per gate:
     - the Whitehead bias-adjusted Elo with its SE;
     - the verdict-conditional bias at that Elo (winner's curse of an H1, the negative bias of a cap) and at
       true +10;
     - a conditional mean-matching estimate where one exists.
  3. Fits `Elo = k * dL` (dL = opponent holdout minus candidate holdout, units 1e-4), with and without an
     intercept, per group (`h256_e12 conc5`, `h256_e12 conc7`, `AL1 conc8`; b0.6 family only). It does this with
     adjusted and with raw Elo.
  4. Projects the next-run options with the S30 holdout curves (e64/e96 on the same data, e48 with x1.1..x2 data)
     into Elo ranges (Monte Carlo over k and the curve uncertainty).
- Outputs: `s44_results.json`, `s44_points.csv`.

Tests: `python -I -B test_forge_sol_S44.py [gates dir]` (7 tests). They cover the exact LLR against a line-by-line
scalar port of fishtest LLRcalc, the printed gate statistics, and the fast stopping rule equal to a brute-force
exact-LLR run (verdict, stop and Elo identical on 8 cases). They also cover the tilt, the H1 winner's curse at
true +10, the S30 epoch-curve refit, and WLS.

Speed: exact LLRs are evaluated every pair only near a threshold. The band is the row's last measured
exact-minus-approximation gap +-0.3. A refresh runs every 3 pairs within 1.0 of a threshold, and every pair
before pair 150. The run reports the largest gap drift between refreshes in the direction that could hide a
crossing; it must stay below the band.
