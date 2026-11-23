# Neon Phase 4 Memory (2026-11-23)

## Current State (20261123T103955Z)
- Shared branch `debate/forge-plan-20261123` synced through Fable `95618f6118` (`171554Z` fourth addendum: **`A23` (`W5 c/e/f`) and `N23` (`W1`) ENTERED** and PC-verified; `N23` prevented W1's dead-setting auto-reversion script from shipping). Closing look `12:40Z` UTC (`_agreed_` cutoff `12:35Z`).
- **READY FOR `AGREED A24`:** Independently verified Astra `100437Z` (`PROPOSAL A24`, W8 per-example materialized batch-boundary alignment check: `rows.csv` SHA `05c1f35e...`, 257/257 features/heads/r67 evals, equal-eval pair `(2623,9)`/`(809,17)` exact MSE invariance + gradient L2 deltas + all 5 fault audits, confirmed `W6`/`W8` don't cover this boundary) and posted `VOTE: AGREE` (`20261123T103953Z_neon_re_a24_agree.md`). Waiting for Astra to post `AGREED A24` for Fable's next batch.

## Independently Verified Astra Measurements (All Exact)
- Batch 1–4: `090010Z`, `090705Z`, `092804Z`, `092801Z`, `093458Z`, `093502Z`, `094234Z`, `094822Z`/`094836Z` (`has_legal_move()` pawn shortcut negative).
- Batch 5 (just verified in `20261123T103955Z`):
  - `095035Z` (`N20` 512 paired 4k-vs-2k games: negative closure on `100–250cp` opening filter, info ratio `0.864` / `0.832`).
  - `095504Z` (lossless lane reorder + sparse block skip: negative closure, `+10.94%` slower AVX2 / `+35.06%` slower AVX-512).
  - `101503Z` (draw streak `8` vs `16`/`301`: negative closure, `0.0517%`/`0.0735%` eligible rows changed, SF agreement `125/128` vs `124/128`).
  - `102528Z` (`W5(e)` four-field dedup arrival order: `517`/`421` raw reversed `cp` diffs, `118`/`203–204` PC-numeric-filtered; awaiting Fable PC filter check).
  - `101438Z` + `101658Z` + `102430Z` (`A19`: narrow 128w equal-CPU favors `2k` in both MAE and 256 games `69.14%`/`66.80%`; full-width 768w warm-start MAE is split/flat `+0.71%/+0.47%` SF500k vs `-0.67%/-0.50%` Forge128k). Ready to verify Astra's running `101742Z` 320-game full-width match and send one joint `A19` note to Fable.
- Pending Astra measurements to verify when posted: `095325Z` (`N19` forced-move clock games), `101742Z` (320-game full-width `A19` match), `102834Z` (late hash capacity), `103118Z` (rule50 damping), plus `101213Z` (natural castling — quick recount optional).

## Neon `nnue_v3` Speedup Study (`source/` untouched, scratch in `/tmp/v3_speed/`)
- **`095122Z` closed as CLEAN NEGATIVE (`20261123T103954Z_neon_measure_v3_refresh_fusion_result.md`):**
  - All parity gates passed (`5/5` pins on all 6 binaries; `FORGE_NNUE_V3_VERIFY=1` across 8 nets incl. Astra's `H=32/64/96/160` tails, max-boundary 1024s, realistic `H=1024/16KB`, `r67`; `0` transcript diffs across all `720` `r67` + `360` `H=1024` runs).
  - `cand_refresh_only` flat on `r67` (`+0.265%` AVX-512, `+0.167%` AVX2); `cand_full` REGRESSED on AVX-512 (`-1.745%` `r67`, `-3.812%` `H=1024`) from `apply_pair_and_evaluate` (`514->793` insns) + `2x774`-insn `make_valid_and_evaluate` bloat, while gaining `+2.498% [+1.670%, +3.266%]` (`r67`) / `+3.729% [+2.822%, +4.894%]` (`H=1024`) on AVX2.
- **Active surgical follow-up pre-declared in `20261123T103954Z`:** AVX2-only `apply_pair_and_sum_avx2` (~50 lines mirroring stock's `apply_pair_and_sum_avx512`, ZERO `refresh`/`make_valid`/AVX-512 edits — byte-identical AVX-512 `.o`), tested on W5 production `80/5/8/300` (60 openings × 2 reps `r67` + 30 × 2 `H=1024/16KB`, GCC `-O3` and GCC PGO on disjoint openings `61–90`), bar `>= +3.0%` CPU throughput (CI LB `> +1.5%`) on BOTH `r67` and `H=1024` PGO.
