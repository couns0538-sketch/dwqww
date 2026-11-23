# Neon Phase 4 Memory (2026-11-23)

## Current State (09:02Z)
- Shared branch `debate/forge-plan-20261123` synced; Fable entered Batch 2 (`A20`, `N18`–`N21`, `A21`, `A19` warm recount).
- Waiting for Fable's next event-driven look (~45 min after first new `_agreed_` / `_to_fable`; closing look `12:40Z` UTC, deadline `12:35Z`):
  - `AGREED A22` (`083324Z`, Astra): 40-pass max pairwise co-batch retention `<= 0.10`.
  - `AGREED N22` (`083557Z`, Neon; confirmed on stock binary by Astra `085538Z`): post-stronger-net & high-depth two-stage search re-calibration ("For later").
  - `084106Z_neon_to_fable_kill_tree.md`: answered Fable `153513Z` on Windows `psutil 7.2.2` kill-tree / `TerminateProcess` / `EnumProcesses` / Job Objects.
- Independently verified Astra measurements:
  - `081746Z` (`A19` SF17.1 referee) + `082109Z` (offline TB bound) -> posted `084238Z`.
  - `085039Z` (castling-rights sensitivity), `085323Z` (phase-`K` calibration negative), `085538Z` (`N22` stock panel) -> posted `090214Z`.

## Completed Local Diagnostics (Scratch in `/tmp/`, `source/` untouched)
1. **`r67_h768` weight & activation audit (`n=5,881` selfgame rows, `max_err=0`):**
   - King-bucket residual RMS `3.86/88.58`, yet shifts eval `mean|diff|=25.39 cp` (`max=256 cp`); output buckets `mean|8ob-1ob|=47.78 cp` (`132.5 cp` in `ob=0`); SCReLU median active `7.89%`, `8/768` dead, `14/12,288` `w2` at `|w2|==127` (`11` in `ob=0`).
2. **Correction-history saturation & LOO residual audit (`search.cpp`, cold `2k..1M` + warm persistent `20k/250k` games):**
   - Clean negative: all 6 tables (`pawn`, `mat`, `np_w`/`np_b`, `joint`, `cont0`, `cont1`) reduce MAE (`LOO - corr > 0` in all regimes; warm `250k` MAE `63.68 -> 45.44 cp`), saturation `<= 4.25%`, cancellation `1.378x`. Do NOT propose changing.
3. **Full `source/` audit (`search.cpp`, `uci.cpp`, `board.cpp`, `nnue_v3.cpp`, `clock_plan.hpp`, `tm_*.hpp`) + ASan/UBSan sweep:**
   - Compiled unmodified `source/` with `-fsanitize=address,undefined -DFORGE_PAWN_HISTORY=1 -DFORGE_SDK_BADCAP_PREFIX=1`; ran ALL 26+ currently-OFF search options ON together across `1T`, `4T` (`HistRework=0..3`), `MultiPV=4`, clock searches, `selfgame`, option toggles, malformed UCI: **0 ASan/UBSan errors**.
   - Noted minor latent details to test/check next:
     - `nnue_v3.cpp` AVX2 path lacks fused `apply_pair_and_evaluate` (also double-calls `collect_changes`), lacks 2x unroll in `output_sum_avx2`, and lacks 4-column batching in `refresh_from_pieces` (relevant if rented Linux CPU or Fable's PC uses AVX2, especially for `W13` `H=1024`).
     - `search.cpp:1224` `Worker::clear()` skips clearing `pawn_history_` when `PawnHistory==0` (stale state if toggled off before `ucinewgame` and back on).
     - Still to check: TSan on 4T Lazy SMP, `W14` individual option activity & interactions (A18-style), `nnue_v3` `w2` `|w2|<=127` quantization/clipping & AVX2 speed impact at `H=768`/`H=1024`, `eval.cpp` / `nnue.cpp` / `book.cpp`, and Astra's pending results (`082001Z`, `082621Z`, `083029Z`, `085142Z`, `085343Z`).
