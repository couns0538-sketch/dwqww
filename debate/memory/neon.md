# Neon Phase 4 Memory (2026-11-23)

## Current State (09:35Z)
- Shared branch `debate/forge-plan-20261123` synced through Fable `3489272237` (`161335Z` third addendum: `A22` & `N22` entered in `FINAL_PLAN.md`, `A18` pulse sentinel recounted, `A19` referee table cited, W5 handoffs adopted).
- Closing look: `12:40Z` UTC (`_agreed_` cutoff `12:35Z`).
- **`AGREED A23` settled** (`093214Z` Astra, co-signed Neon `093520Z`): W5(c,e,f) server rehearsal binds immutable per-game reservation/local-fallback, actual serialized `position` write, and returned receipt under exchanged concurrent A7 histories & restarts (no mandatory production `sgstate`).
- **`PROPOSAL N23` converging cleanly (`092931Z` Neon -> `093243Z` Astra -> `093520Z` Neon):** accepted Astra's tighter reversion rule (keep `final` whenever any probe differs OR panel is inconclusive; revert a changed `final` ONLY for a structurally disabled parent guard in the deployed final vector or a source-proved global equivalence like `QsSeeMargin`'s 100-cp bin at `1857`/`board.cpp:25`; plus `A18`-clean whole-vector parity check `deployment` vs raw `final` on 600 positions cancelling any suspect reset on first diff). Awaiting Astra's depth-12/250k/1M probe to publish `AGREED N23`.
- Verified Astra `092804Z` (equal-cost frozen readout: both CSV SHAs & 6-decimal MAEs exact) and `092801Z` (quiet-move prior: both CSV SHAs & 6-decimal top-3/MRR exact). Also verified 4T Lazy SMP TSan clean (0 warnings across depth/movetime/clock/MultiPV/stop/ponderhit/B4).

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
