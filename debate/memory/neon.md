# Neon Phase 4 Memory (2026-11-23)

## Current State (09:30Z)
- Shared branch `debate/forge-plan-20261123` synced through Fable `3489272237` (`161335Z` third addendum: `A22` & `N22` entered in `FINAL_PLAN.md`, `A18` pulse sentinel recounted 600/600 & pos-1-only, `A19` referee table cited, W5 Linux handoffs adopted with exact loop `selfgame` args).
- Closing look: `12:40Z` UTC (`_agreed_` cutoff `12:35Z`).
- Posted `092930Z` (confirming third addendum, agreeing to Astra `A23` with exact 5-plant & 512-game bootstrap reproduction, verifying Astra `090010Z`, `090705Z`, `092620Z`, reporting `r67` weight sanity and `W14` 5-candidate firing rates) and **`092931Z` `PROPOSAL N23`** (`W1` final-value liveness audit plateau/threshold disambiguation).

## Active Proposals / Open Threads
1. **`PROPOSAL A23` (Astra `092436Z`):** Bind each W5 game ID's independently reserved opening to the serialized `position ...` command written to that worker's engine stream and its receipt, including retries and local fallback. Neon reproduced all 5 plants to exact SHAs and 512-game timing bootstrap (`CPU +0.27086% [-0.91929, +1.51088]`, `wall +0.24229% [-0.94888, +1.48182]`), confirmed `W5(c, e, f)` misses concurrent payload/receipt swaps, and voted **AGREE** (`092930Z`) — awaiting Astra's `_agreed_a23.md`.
2. **`PROPOSAL N23` (Neon `092931Z`):** `W1`'s final-value liveness audit (`FINAL_PLAN.md:47-61`, `N1`) — and later `A18` parameter-liveness tables (`N22` Stage A) — must not classify a setting dead or revert `final -> start` on local `final +/- step == 0/600` alone. `source/src/board.cpp:25` (`SeeValue` `gcd = 100`) creates exact flat plateaus in `QsSeeMargin` (width 100 — explaining the 17 Nov `0/600` surprise), `SeeNoisyMultiplier` (`145 +/- 4 = 0/60`, `106 +/- 6 = 0/60` while differing from start `150` on `59/60` and `60/60`), and `SeeQuietMultiplier` (`21 +/- 1 = 0/60`, `26 +/- 1 = 0/60` vs start `24` `60/60`), plus depth-12 threshold censoring (`SingularDepth = 14`: `14 +/- 1 = 0/60` vs start `6` `60/60`). Three-case rule using `final vs start` + `final vs [min, max]` protects moved plateau settings while cleanly reverting genuinely gated-off partners (`0/60` at both `[min, max]`) and within-start-plateau drift. Awaiting Astra verification & feedback.
3. **Astra's pending measurements to verify when posted:**
   - `085142Z` natural-castling A7 opening draw check
   - `090046Z` output-bucket head ablations (`r67`)
   - `090939Z` quiet-move prior offline study
   - `091351Z` equal-CPU 2k vs 8k frozen-L1 readout proxy
   - `092620Z` post-training `768 -> 640` width compression (arithmetic verified `092930Z`)

## Completed Local Diagnostics (Scratch in `/tmp/`, `source/` untouched)
1. **`r67_h768` weight & activation audit:** completely healthy (`max|w1|=559`, `max|b1|=432`, accumulator headroom `18,320/32,767`, `|w2|==127` clips `14/12,288 = 0.114%`, king-bucket `MAE=22.57 cp`, output-bucket `MAE=38.18 cp`, active `88.4/768`, saturated `1.1/768`).
2. **Correction-history saturation & LOO audit:** clean negative across `2k..1M` cold and `20k/250k` warm; all 6 tables reduce MAE, saturation `<= 4.25%`.
3. **ASan/UBSan sweep across all 26+ OFF options + `1T/4T` + `MultiPV=4` + `selfgame`:** 0 errors.
4. **`W14` 5-candidate firing-rate audit (`/tmp/w14_audit`, `bench 11 = 312866` exact):** `C1`, `C3`, `C4`, `C5` (`LmrDeeperShallower value true`) all `120/120` live at depth 12 (`C5` `+0.325` mean depth at `250k`); `C2` (no root IIR, `search.cpp:2184`) is `0/120` at d12 / 20k and `0/40` at 250k (`W14`'s existing `6/600` rule drops it automatically).
5. **Next deep code audits to explore (zero bloat — only propose if genuinely load-bearing):**
   - **TSan race audit on 4T/8T Lazy SMP** (`source/src/search.cpp`, `tt.hpp`, `nnue_v3.cpp`, `uci.cpp`) — relevant for `N18` multi-thread / `W13` / `N20`!
   - **Time management & clock edge cases** (`source/include/forge/clock_plan.hpp`, `tm_*.hpp`, `search.cpp` `check_time()` / `go wtime ...` / `movestogo` / `ponder` / `stop` / `Move Overhead`) — relevant for `N19` / `N20` `60+0.6` clock matches!
   - **NNUE v3 AVX2 speed gap at `H=768` / `H=1024`** (`source/src/nnue_v3.cpp` missing fused `apply_pair_and_evaluate` & 4-col refresh on AVX2) — check exact measured speedup on Linux AVX2 vs AVX-512!
   - **`eval.cpp` / `book.cpp` / `board.cpp` / `movegen` / `selfgame`** edge-case audit (`halfmove_clock`, threefold at ply 0/1, `evallimit` vs mate scores, `drawply`/`drawscore`/`drawcount`, `PawnHistory` clear bug at `search.cpp:1224`).
