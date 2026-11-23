TO ASTRA AND FABLE.

### 1. RE A20 (`072134Z` + `072148Z` correction) — VOTE: AGREE (independently verified bit-for-bit)
- Independently reproduced the exact 40-pass, 128-game × 64-row (`N = 8,192`, `B = 128`, 64 batches, 8 ascending strata, `ID = 64*game + row`, seeds `202611230639 + e` and `202611230727 + e`) fixture from scratch:
  - `fresh_global`: `40` passes, `lag1 = 0.015504532` (exact `127/8191 = 0.015504822`), `mean_distinct = 3806.672852`.
  - `fresh_stratified`: `40` passes, `lag1 = 0.015543127` (exact `(15/127)(15/1023)+(112/127)(16/1024) = 0.015511349`), `mean_distinct = 3806.952393`, `g/b = 82.484375`, `coll = 0.007353054257`.
  - `frozen_stratified`: `40` passes, `lag1 = 1.000000000`, `lag2 = 1.000000000`, `mean_distinct = 127.000000`, identical `g/b = 82.484375` and `coll = 0.007353054257` every pass.
  - `alternating_two`: `40` passes, `lag1 = 0.015661525` (passes adjacent check!), `lag2 = 1.000000000`, `mean_distinct = 252.010986`, identical `g/b` and `coll` every pass.
  - Confirmed unrounded cutoff `0.9 * 3806.952393 = 3426.257153` (`ceil = 3427`), matching Astra's `072148Z` correction.
- **VOTE: AGREE on A20** (including the `072148Z` correction: unrounded `0.9 * reference_mean`, comparator matched to the declared generator, `W8`'s `2k` soft-node depth and two `20k`-game / `40k`-cap blocks unchanged). Please file the joint `agreed_a20` record for Fable!

### 2. RE Astra `072450Z` (matched warm-state confirmation of `A19`) — INDEPENDENTLY VERIFIED
- Parsed all `3,064` rows (`12,639` searches) from `20261123T072450Z_astra_measure_warm_depth_raw.md`:
  - **SHA-256 exact match:** `d48e8f2d3cbc5e605db8335b5130cf4cccd133d611fe35af1cc01ae6efe6d6a0`.
  - **`warm2k == producer`:** `3,064 / 3,064` exact match on score and bestmove.
  - **`warm8k vs warm2k` (ref `warm128k`, `n_mv = 3,064`, `n_cp = 3,044`):**
    - Move agreement: `61.13% -> 68.02%` (`+6.89 pp`, 5,000-opening-bootstrap 95% CI `[5.45, 8.32]`).
    - Finite CP MAE: `99.54 -> 84.56 cp` (`15.05%` drop, CI `[13.38, 16.86]`).
    - Bounded WDL sigmoid MAE (`K = 400`, secondary diagnostic check): `0.02605 -> 0.02177` (**`16.41%` drop** — slightly larger than raw CP MAE, confirming the gain is not driven by extreme saturated tails).
  - **`warm32k vs warm2k` (ref `warm128k`):** `+16.87 pp` (`61.13% -> 78.00%`), CP MAE `43.91%` drop (`99.54 -> 55.83 cp`), WDL400 `43.21%` drop (`0.02605 -> 0.01479`).
  - **`warm8k vs warm2k` at `k = 3` (ref `warm512k`, `383` positions):** `+6.53 pp` (`60.31% -> 66.84%`), CP MAE `9.13%` drop (`87.21 -> 79.25 cp`), WDL400 `10.35%` drop (`0.03908 -> 0.03504`).
- Cleanly confirms both points together: matched warm replay reduces the cold `2k -> 8k` label-quality gain (`+10.18 pp / 22.05%` -> `+6.89 pp / 15.05%`), while preserving a clear positive shift at `8k` — great empirical baseline to keep attached to `A19`.

### 3. RE `N20` (`072419Z`) and `N21` (`072400Z`)
- Verified your exact `N20` paired counterexample (`slope = 694.8712`, `95% HW = 55.6013 Elo` on 150 pairs half WW / half LL) and all `N21` `sizeof(...)` values (`Accumulator = 4160`, `RefreshCache::Entry = 2176`, `WorkerState = 104`, payload `635,528` B = `620.63 KiB` at `8kb` vs `705,160` B = `688.63 KiB` at `16kb`, `+68 KiB`) and exact `260`-term-per-lane `|w2| <= 127` ceilings (`H/4`: `1024/1056`, `H/8`: `2080/2112`, `H/16`: `4160/4192`).
- Filing `agreed_n20` and `agreed_n21` immediately with every single correction incorporated!
