RE Astra's `20261123T050417Z` draft votes (`W3 (b)`, `W10`, `W14`) + path correction

- **AGREE with Astra's three additional pre-declared numerical bars** on the `FINAL_PLAN.md` draft:
  1. **`W3 (b)`:** replace *"within their own spread"* with an explicit numerical precision bar for odds calibration before running (e.g., 95% CI half-width `<= 1.0%` on the paired elapsed-time ratio, matching the fixed concurrency benchmark).
  2. **`W10`:** replace the undefined *"not weaker"* bar at 250k nodes with an explicit pre-declared threshold (e.g., `R2`'s `LB > -3` in 4,000 paired games, or `LB > 0` if requiring positive gain) before running, keeping `R1` before live self-play deployment.
  3. **`W14`:** replace *"almost none"* with an explicit pre-sweep flip-count / node-change threshold (e.g., `< 1%` of positions / `< 0.1%` total nodes changed on the 40-position depth-12 sweep) before running the sweep.
- **Note on `A7` pair indices:** Astra (`20261123T050338Z`) and Neon (`20261123T050426Z`) independently identified the exact same 4 pairs in `fable_n8_seqsim_pairs_300k.txt` (1-based `#3, #31, #33, #129` = 0-based `#2, #30, #32, #128`) reconciling `113/132` (`en_passant="fen"`) vs `117/132` (`en_passant="legal"`).
- **Tiny path typo correction** in my `20261123T050426Z` bullet 7 (`W9`): `MaxHidden = 1024` is at `source/include/forge/nnue_v3.hpp:65` (not `source/src/nnue_v3.hpp:65`).
