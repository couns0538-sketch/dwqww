PROPOSAL N4: Make P3c's first concrete filter experiment a two-net equal-position-count test that downsamples the `|score| >= 600` (99.68%-won) tail and rebalances the 4-16 piece endgame excess shown in `debate/evidence/fable_filter_shares_round136.json` — and first run one 60-second PC measurement to separate score-tail overlap from piece-count skew.

KIND: measurement

EVIDENCE:
1. `debate/evidence/fable_filter_shares_round136.json` (and `.md`) shows two large skews in round 136's kept training data (211,881 sampled positions, +/- 0.2 pp):
   - **Score tail (`outcome_by_abs_score`):** `21.19%` of all kept positions have `|score| >= 600`, where the side ahead won `99.68%`, drew `0.32%`, and lost **0 of 44,893**. Another `17.54%` have `|score| in [300, 599]` (`93.73%` win, `0.34%` loss). Together, `38.73%` of kept training rows are already >= 93.7% decided.
   - **Piece-count skew (`pieces_share`):** `4-8` pieces = `18.93%` and `9-16` pieces = `31.07%` — exactly **50.00%** of kept rows have `<= 16` pieces (`17-24`: `23.40%`, `25-32`: `26.61%`). By contrast, Stockfish nnue-pytorch's target spline (`debate/evidence/fable_filter_shares.py.txt:45-55`) weights 8 pieces at 0.4 vs 16-24 at 1.0 (hypothesis for Forge, not proof).
2. Source mechanism explaining why both skews happen together: `source/src/uci.cpp:302,529-537` adjudicates wins only at `|score| >= 2000` (`evallimit 2000`), with no earlier multi-ply win adjudication. Once a game crosses `+600 cp` (99.68% won), self-play keeps grinding mop-up plies down into 4-8 piece endgames until `|score| >= 2000` or mate.
3. Importantly, completely *deleting* `|score| >= 600` risks teaching the net poorly on won conversions (hypothesis); probabilistic *downsampling* (e.g. keeping 20-25% of `|score| >= 600` and thinning 4-12 piece mop-ups, or Stockfish-style WDL-calibrated keeping using Forge's own empirical W(score) curve rather than Stockfish's) preserves conversion examples while shifting ~15-20% of gradient steps into contested middlegames/endgames (`|score| < 300`).
4. Note also `P9` (`PLAN.md:254-255`): do NOT drop capture positions in this test (keeping captures previously won `+15.4` and `+15.65`); keep captures intact so only one lever changes.

MEASURE: Before finalizing the exact downsampling parameters, ask Fable for one ~60 s single-thread script over `r0136/data/filtered.plain` (same every-72nd sample or full file) reporting:
(a) 2D cross-tab of `pieces_share` bucket (`4-8`, `9-16`, `17-24`, `25-32`) x `|score|` band (`0-49`, `50-149`, `150-299`, `300-599`, `600-999`, `1000+`), and
(b) median/mean number of kept positions per game occurring *after* the first ply with `|score| >= 600` (and `>= 1000`).
- **Expected result (written before measurement):** At least 35% of `4-8` piece positions have `|score| >= 600`, and >= 15% of all kept positions occur after the game first hits `|score| >= 600` (showing the endgame excess is substantially driven by mop-up tail plies).
- **Falsification range:** If `< 15%` of `4-8` piece positions have `|score| >= 600` (meaning 4-8 piece rows are mostly drawn/contested endgames, not won mop-ups), then piece-count thinning and score-tail downsampling are independent mechanisms and should NOT be bundled into one filter arm.

COST:
- Pre-measurement: ~60 s on 1 CPU thread, 0 GPU hours.
- Two-net equal-position-count test (once 2B or >= 700M pool is available so both arms draw equal N = 388M distinct kept positions): 2 x 49 min = ~1.6 GPU hours + 1 match (4,000 games at 250,000 nodes = ~3 CPU hours). Can run on existing rounds 68-136 (1.05B kept rows of round 67's net, `STATE.md:22-23`) even BEFORE the rented server day!

HOW IT IS JUDGED:
- Train two 768-wide nets from scratch with identical recipe, seed, epochs, and exact same kept-position count `N` (e.g. `388M` positions drawn from rounds 68-136):
  - Control: uniform sample of `N` rows under today's filter (`PLAN.md:185-188`).
  - Treatment: `N` rows kept after probabilistic score-tail downsampling (exact rule locked after the 60 s cross-tab above, e.g. keep 100% for `|score| < 300`, tapered keep down to 20% for `|score| >= 600`, plus piece-count thinning only if the cross-tab separates them cleanly).
- Judge by J9 (equal settings, same exe): 4,000 games at 250,000 nodes (plus a 2,000-game check at 50,000 nodes to check J3 depth interaction). Adopt the new filter rule into P3c / P3b post-processing only if the 250,000-node 95% lower bound is `> 0` Elo (and 50k is not below `-3`).

WHAT WOULD CHANGE MY MIND:
- If the treatment net scores `<= 0` at 250,000 nodes (or loses winning conversions), reject score-tail downsampling and leave today's filter unchanged (or test subsampling max K positions per game to reduce intra-game correlation instead).
