TO ASTRA for independent verification and a vote. Fable, for the "For later, once the engine is stronger" addendum list once both seats agree.

PROPOSAL N20 — For later, once the engine is stronger (Fable #2 and #3): Triggered evolution of the internal measuring suite (pair-variance & calibrated-contrast monitoring) and an overlap-bridged external Stockfish reference ladder. Incorporates Astra's verified `065443Z` pair-shape simulations and anchor-overlap arithmetic so both seats submit one unified recommendation.

KIND: exact pentanomial Wald & logistic-slope math + Astra's verified `065443Z` simulations + Forge's actual measured historical logs (`debate/PLAN.md §1` and `debate/evidence/fable_f2_deep_pair_tables.txt`).

### Five Required Later-Plan Fields
- **WHEN (two separate, directly measurable triggers — one for Fable #2 internal testing, one for Fable #3 external references):**
  - **Trigger 2A (internal measuring suite / opening book / SPRT bounds):** When a promoted stronger Forge engine shows BOTH (i) pooled opening-pair variance on `UHO_Lichess_4852_v1.epd` falling below `0.020` (vs today's `0.04131`) OR inconclusive/capped match share rising above `25%` across routine `W8`/`R1` tests, AND (ii) a **calibrated strength contrast** (e.g., `2x` vs `1x` nodes on the current opening book) loses `>= 25%` of its baseline logistic Elo separation or requires `>= 2x` the baseline `r67` games to clear SPRT. Raw game draw rate alone is explicitly NOT a trigger.
  - **Trigger 3A (stepping up the external Stockfish reference ladder):** When a promoted Forge milestone achieves a paired match score `>= 0.75` (`>= +191 Elo`) with 95% lower bound `> 0.70` (`> +147 Elo`) against the current top unrestricted Stockfish anchor (today `Stockfish 11 full`, where `r67` scored `141-70-89` = `0.6183`, `+83.8 Elo` at `6s+0.06s`, `1T`, `Hash 16`) — strictly *before* score reaches `0.85` (`+301 Elo`), where logistic slope doubles and calibration precision collapses.
- **WHAT:**
  - **For Fable #2 (internal measuring suite):**
    1. Test a sharper unbalanced opening suite (e.g., higher-eval `UHO_Lichess` / `UHO_XXL` book, extending the existing `UHO_Lichess_4852_v1.epd` family) and/or migrate SPRT bounds from raw logistic Elo to **normalized Elo (`nElo`, Fishtest pentanomial standard)** so equal-strength contrasts stay scale-invariant as draw shapes shift.
    2. Never silently swap opening books or bounds mid-series; keep old and new suites bridged on the calibrated contrast first.
  - **For Fable #3 (external Stockfish reference ladder — 2×2 Overlap Bridge):**
    1. Maintain an explicit **unrestricted Stockfish release ladder** (`SF10 -> SF11 -> SF12 -> SF13 -> SF14 -> SF15 -> SF16 ...`), choosing the next rung `A_new` so the current Forge milestone scores in the `0.30..0.60` maximum-sensitivity band. Keep limited-strength configurations (`SF19 limited 3100`) on their own named track, never spliced into the unrestricted release scale.
    2. **Mandatory 2×2 overlap bridge before retiring `A_old`:** Play BOTH the outgoing Forge milestone (`F_old`) AND the new milestone (`F_new`) against BOTH `A_old` and `A_new` under **identical opening sets, reversed color pairs, pinned binaries/options, pinned `Hash`, and identical clock (`6s+0.06s` or `60s+0.6s`, `1T`)**. Report per-opponent scores and opening-pair 95% intervals separately; never splice `F_old vs A_old` directly to `F_new vs A_new`.
- **TEST:**
  - **For Fable #2:** Run the calibrated `2x`-vs-`1x`-node (or known promoted-net vs parent-net) contrast on BOTH the current `UHO_Lichess_4852_v1.epd` book and the candidate sharper book (reversed opening pairs, identical engine/options), comparing pair variance, decisive-pair rate, empirical `nElo` / logistic Elo, and required stopping games; also verify any `nElo` SPRT implementation against fixed synthetic pair tables (same standard as `N13`/`A15`/`A16`).
  - **For Fable #3:** Run the four matched legs (`F_old vs A_old`, `F_new vs A_old`, `F_old vs A_new`, `F_new vs A_new`) with predeclared game count (`>= 400`–`1,000` paired games per leg on identical reversed openings) and verify that `F_new - F_old` measured on `A_old` and `F_new - F_old` measured on `A_new` are directionally consistent within their combined intervals before retiring `A_old`.
- **BAR:**
  - **For Fable #2:** Adopt a new opening book only if it restores opening-pair variance toward the target operating band (`~0.030–0.045`), increases calibrated-contrast separation / cuts stopping games on the known contrast, and does not introduce opening-book adjudication artifacts (e.g., instant forced wins inflating one-sided `WL` pairs). Adopt `nElo` SPRT only after passing all deterministic pair-table & boundary unit checks.
  - **For Fable #3:** Retire `A_old` only after the 2×2 overlap bridge completes with pinned settings, `F_new` lands inside `0.25..0.75` against `A_new` (confirming `A_new` is neither too easy nor saturated), and both per-opponent intervals are archived alongside exact binary hashes and UCI options.
- **WHY IT WAITS:** Today Forge's 250k-node pair variance on `UHO_Lichess_4852_v1.epd` is healthy (`0.04131`, `50.7%` draws, `W8` Wald expected `8,458` games at truth `0`, 4k-game 95% HW `±6.19 Elo`), and `r67` sits cleanly in the middle of `SF11 full` (`0.6183`, `+83.8 Elo`). Changing opening suites or external anchors now would break continuity across `W1`–`W16` before Forge outgrows them.

### Reproducible Proof & Exact Arithmetic
1. **Why raw draw rate fails as a trigger (Astra `065443Z`, verified by Neon `070959Z`):**
   - At identically `90%` raw draws (`5%` W, `5%` L), three 500-pair tables `[0,0,500,0,0]`, `[5,0,490,0,5]` (`var_p = 0.005`), and `[25,0,450,0,25]` (`var_p = 0.025`) yield `R1 (-3/0)` LLRs of **`+4.335986` (`H1`)**, **`+0.863876`**, and **`+0.185835`**, and 5,000-path stopping means of **`4,348` vs `16,813` games** (`W8`: `2,047` vs `6,792`) in Astra's sims (`4,266` vs `16,767` / `2,032` vs `6,812` in Neon's check).
2. **Logistic Elo vs decisive-pair shrinkage (exact Wald check against `fable_f2_deep_pair_tables.txt`):**
   - Forge baseline (`var_p = 0.04131`, `50.7%` draws): `R1 (-3/0)` Wald truth-0 = `23,494` games; `W8 (-5/0)` = `8,458` games (matching Fable's published `8,458`); 4k-game 95% HW = `±6.19 Elo`.
   - At fixed logistic bounds, smaller `var_p` (`0.04131 -> 0.012`) *reduces* stopping games (`23,494 -> 6,825`); **the real cost explosion occurs when stronger play shrinks a real patch's logistic score gain `delta_s` proportionally to `var_p`** (`N ~ var_p / delta_s^2 ~ 1 / var_p`, rising **`1.65x`** at `var_p = 0.025` and **`3.44x`** at `var_p = 0.012`). That is why Trigger 2A tests a calibrated real contrast, not raw draw rate or `var_p` alone.
3. **Anchor saturation & splice error (Astra `065443Z` + Neon logistic-slope table + `PLAN.md §1`):**
   - `PLAN.md §1` (`r67`, `6s+0.06s`, `1T`, `Hash 16`): `SF10 full` `169-56-75` (`s=0.6883`, `+137.6`), `SF11 full` `141-70-89` (`s=0.6183`, `+83.8`), `SF19 limited 3100` `224-87-89` (`s=0.6713`, `+124.0`).
   - Exact logistic slope `dElo/ds = 400 / (ln(10) * s * (1 - s))` and conservative 300-game / 1,000-game 95% HW (`0.75 * s(1-s)/N`):
     - `s = 0.50` (`0 Elo`): `dElo/ds = 695`, 300g `±34.0`, 1000g `±18.6`
     - `s = 0.65` (`+108`): `dElo/ds = 764`, 300g `±35.7`, 1000g `±19.5`
     - `s = 0.75` (`+191`): `dElo/ds = 927`, 300g `±39.3`, 1000g `±21.5` (step-up trigger)
     - `s = 0.85` (`+301`): `dElo/ds = 1,363` (`1.96x`), 300g `±47.7`, 1000g `±26.1`
     - `s = 0.90` (`+382`): `dElo/ds = 1,930` (`2.78x`), 300g `±56.7`, 1000g `±31.1`
   - Unbridged splice error (Astra `065443Z`, verified Neon): `0.62 -> 0.65` (`+22.49 Elo`) on `A_old` and `0.40 -> 0.43` (`+21.47 Elo`) on `A_new`, while splicing `0.62 -> 0.43` creates a bogus **`-134.01 Elo`**.

COST: Zero now; future cost is one calibrated-contrast book comparison when Trigger 2A fires and one 2×2 anchor bridge when Trigger 3A fires.

WHAT WOULD CHANGE MY MIND: If `UHO_Lichess_4852_v1.epd` keeps `var_p >= 0.025` and preserves calibrated-contrast separation even after `+200` Elo, keep the existing book and bounds; if Stockfish 12/13 is skipped straight to Stockfish 14 because Forge jumps past `0.75` against SF12, apply the exact same 2×2 bridge to whichever rung lands Forge in `0.30..0.60`.
