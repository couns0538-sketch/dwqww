# Stream A: Time-Manager Root Cause of the `250k` vs `6+0.06` (`+24.2 Elo`) Clock Gap

> **Evidence Scope:** Measured single-threaded on `C:\nnue-lab\runs\forge\engines\v3-r15dsg-sp-clang\forge.exe` with exact live `v3_uci_options` across the first `40` UHO positions (`C:\nnue-lab\tools\book\UHO_Lichess_4852_v1.epd`). Diagnostic timing/node numbers explain time allocation behavior only; any match strength impact requires declared `6+0.06` `fastchess` games.

---

## 1. Control Check: `time_managed_` vs `go movetime`

| Probe (`40` UHO positions) | `r0067` Mean (Median) | `R1-skip` Mean (Median) | `R1-skip` vs `r0067` Diff |
|---|---:|---:|---:|
| `go wtime 6000 btime 6000 winc 60 binc 60` | `209.92 ms` (`178.13 ms`) | `269.99 ms` (`207.55 ms`) | **`+60.07 ms` (`+28.6%`)** / med **`+16.5%`** |
| `go wtime 2500 btime 2500 winc 60 binc 60` | `114.06 ms` (`92.76 ms`) | `141.12 ms` (`108.15 ms`) | **`+27.06 ms` (`+23.7%`)** / med **`+16.6%`** |
| `go movetime 210` (bypasses `time_managed_`) | `200.25 ms` (`200.18 ms`) | `200.20 ms` (`200.19 ms`) | **`-0.05 ms` (`-0.02%`)** |

**Conclusion:** `go movetime 210` eliminates the gap (`-0.05 ms`), proving **100%** of the `+24–29%` time-per-move excess originates in `time_managed_` iteration-level stopping (`search.cpp:3156-3226`) and the lack of a mid-iteration soft cap (`search.cpp:1557-1560`).

---

## 2. Branch-by-Branch Ablation Table (`go wtime 6000 btime 6000 winc 60 binc 60`, 40 UHO Pos)

| Configuration (`forge.exe` live options + override) | `r0067` Mean / Med (ms) | `R1-skip` Mean / Med (ms) | Mean Gap | Median Gap | Causal Finding |
|---|---:|---:|---:|---:|---|
| **Baseline (live `v3_uci_options`)** | `209.92` / `178.13` | `269.99` / `207.55` | **`+28.6%`** | **`+16.5%`** | Full TM + overshoot gap |
| `TmEffortBase = 100` | `196.96` / `180.80` | `242.84` / `184.47` | `+23.3%` | **`+2.0%`** | Collapses median gap (`effort` `0.8056` vs `0.8483`) |
| `TmFallingEvalPercent = 0` | `215.26` / `184.68` | `266.48` / `195.03` | `+23.8%` | **`+5.6%`** | Cuts median gap by 2/3 (`16.5% -> 5.6%`) |
| `TmUnstableFactor = 100` | `221.84` / `184.49` | `267.16` / `204.72` | `+20.4%` | `+11.0%` | Cuts mean gap by 29% (`60.1 -> 45.3 ms`) |
| `TmFallingEvalPercent=0 + TmUnstableFactor=100` | `213.03` / `181.84` | `256.86` / `193.01` | `+20.6%` | `+6.1%` | Combined instability + falling eval |
| **All three (`Falling=0, Unstable=100, EffortBase=100`)** | `190.86` / `181.24` | `222.26` / `189.02` | **`+16.5%`** | **`+4.3%`** | Residual `+31.4 ms` mean = pure late-iter spikes |
| `TmStable=100, TmSemi=100, TmUnstable=100` | `319.48` / `268.67` | `397.42` / `303.57` | `+24.4%` | `+13.0%` | Stability discounts alone don't cause gap |
| `TmNodeShare = true` | `192.79` / `151.41` | `247.48` / `183.48` | `+28.4%` | `+21.2%` | Also reveals `effort`: `0.8056` vs `0.8483` |
| `TmFinishIteration = true` | `182.51` / `148.00` | `235.56` / `175.70` | `+29.1%` | `+18.7%` | Next-iter predictor cannot foresee 1-ply PV-flip spikes |
| `TmNodeShare=true + TmFinishIteration=true` | `158.33` / `130.65` | `215.23` / `160.67` | `+35.9%` | `+23.0%` | Gap persists without mid-iter soft cap |

---

## 3. Exact Root Cause in `C:\nnue-lab\forge\r15dsg\src\search.cpp`

1. **Median Shift (`+16.5%`, `178.13 -> 207.55 ms`) — Multiplicative Soft-Deadline Inflation (`search.cpp:3163-3185`):**
   - **Root `effort_share_factor` (`search.cpp:3177`, `tm_node_share.hpp:61`):** Measured via `TmNodeShare` info strings, `R1-skip` puts less node share on its best root move (`effort = 0.8056` vs `0.8483` for `r0067`), raising `clamp(1.55 - effort, 0.6, 1.4)` from `0.7017` to `0.7444` (**`+6.1%`**). Setting `TmEffortBase=100` drops the median gap from `+16.5%` to **`+2.0%`**.
   - **Best-move stability (`search.cpp:3163-3166`):** `R1-skip` finishes with `final_stab_factor_mean = 0.680` vs `0.630` (**`+7.9%`**; `31/40` `stable_ge6` and `2/40` `unstable_d6` vs `34/40` and `0/40`).
   - **Falling eval (`search.cpp:3181-3184`):** `final_fall_factor_mean = 1.0648` vs `1.0445` (**`+1.9%`**).
   - Product: `1.061 * 1.079 * 1.019 = 1.167` (**`+16.7%`**, matching the `+16.5%` median shift).

2. **Mean Explosion (`+28.6%`, `+60.07 ms`) — Uncapped Mid-Iteration Overshoot (`search.cpp:1557-1560` vs `3211`):**
   - `search.cpp:3211` checks `elapsed_ms() >= soft_basis * factor` **only after an iteration finishes**. Inside `should_stop_with()` (`search.cpp:1557-1560`), Forge checks **only `hard_limit_ms_`** (`5 * soft_limit_ms_ = 1,585 ms` at `wtime 6000`).
   - With `R1-skip`'s `+16.7%` higher soft limit, iterations finishing around `90–145 ms` stay below deadline and start `depth + 1` with no mid-iteration soft cap. When `depth + 1` hits a PV switch or aspiration re-search, a single iteration jumps **`5x–15x`**:
     - `pre_final_ms_mean`: `124.2 ms` (`r0067`) vs `134.3 ms` (`R1-skip`) (`+10.1 ms`)
     - `final_iter_jump_mean` (`t_final - t_prev`): `85.2 ms` (`2/40 > 250 ms`, max `433 ms`) vs **`135.1 ms`** (`7/40 > 250 ms`, max `664 ms`) — **`+49.9 ms` (`83.1%` of the `+60.07 ms` mean gap)**.
     - Top 5 outlier positions (`pos 7: +601.9ms`, `pos 25: +423.2ms`, `pos 19: +418.8ms`, `pos 6: +273.4ms`, `pos 17: +263.5ms`) explain **`+1,980.8 ms` of `+2,402.8 ms` (`82.4%`)**.
     - Example `pos=25`: `R1-skip` finished `d=20` in `46 ms` (`152k` nodes), then `d=21` switched `g8h6 -> g8f6` and exploded `13.4x` to `710 ms` (`2,045k` nodes). Example `pos=7`: `R1-skip` flipped `c2c4 <-> f2f4` at `d=19, 21, 22`, reaching `747 ms` (`2,235k` nodes) vs `r0067`'s `146 ms`.

3. **Why This Hurts `6+0.06` Clock Matches:** Burning `+24–29%` more time per move early in `6+0.06` games drains the `6,000 ms` initial bank faster, leaving `R1-skip` (and similarly calibrated nets) with less remaining time for critical middlegame/endgame moves.

---

## 4. Minimal Default-Off Draft Patch (`TM_SCALE_FIX_DRAFT.patch`)

- Adds `int TmSoftCapPercent = 0;` (`0 = off`, range `0..500`) in `include/forge/search.hpp` and `src/search.cpp`.
- When `TmSoftCapPercent == 0` (default), `mid_iter_soft_cap_ms_` stays `0` (`0` node/time changes, bit-exact `forge/r15dsg`).
- When `TmSoftCapPercent > 0` (e.g., `135` or `150` in future declared clock tests), after completing `depth >= 6`, `mid_iter_soft_cap_ms_` is set to `min(hard_limit_ms_, max(soft_deadline, soft_basis * TmSoftCapPercent / 100))` and checked inside `should_stop_with()` (`search.cpp:1557`), preventing `5x–15x` late-ply overshoot spikes without shrinking `hard_limit_ms_` at shallow depths.
- Complements existing live UCI knobs (`TmEffortBase`, `TmFallingEvalPercent`, `TmUnstableFactor`) without altering default search.
