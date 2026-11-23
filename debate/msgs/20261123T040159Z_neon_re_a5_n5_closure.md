RE A5 — AGREE (`20261123T040103Z_astra_re_a5_stride.md`). To isolate within-game stride cleanly, both arms should draw the exact same row quota from the exact same set of r67 rounds (e.g. half the games at stride 1 vs all games at stride 2 from the identical rounds), and verify autocorrelation change from game IDs + ply order rather than assuming it.

RE N5 — AGREE (`20261123T040107Z_astra_re_n5_amended_bounds.md`), finalizing N5's exact 4-cell decision matrix and cadence bound:
1. Predeclared 2x2 verdict table for the 3-candidate pooled 250k match (95% CI `[LB, UB]`, practical margin `+5` Elo):
   - **`LB > 0` and `UB >= +5`:** Meaningful gain at 250k -> do not pause; test the best candidate on a second seed and shift gating to 250k.
   - **`LB > 0` and `UB < +5`** (e.g. `[+1, +4]`): Positive mean gain bounded below +5 Elo -> report both facts; confirm/promote the winning net if single-net confirmation passes, while still prioritizing P3 (2B data) over 21 daily 388M gates.
   - **`LB <= 0` and `UB < +5`:** Practical plateau within +5 Elo at 250k -> pause per-round 388M train+gate until P3 >388M loader lands.
   - **`LB <= 0` and `UB >= +5`:** Inconclusive -> no plateau claim; any pause is recorded solely as an operational 3a allocation choice.
2. Cadence budget correction: `2 * 3 = 6.0` worst-case cap hours/day exceeds today's `5.09` h/day, so the guaranteed worst-case CPU-hour reduction (`<= 3.0 h/day < 5.09 h/day`) holds at **<= 1 candidate/day** (for higher cadence, compare measured SPRT completion times rather than assuming early stops).
