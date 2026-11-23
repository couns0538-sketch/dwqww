# Evidence (fable): what the official trainer's skip rules would do to one round of this loop's data

For plan item P3c and question Q2c. Measured on the PC, one thread, 90 seconds.
Raw result: `fable_filter_shares_round136.json`. Script: `fable_filter_shares.py.txt` (reads only; run it as
`python filter_shares.py <round's positions file> <the round before's> 72 <new json>`).

**The data:** round 136 of the loop, 16,005,930 positions written by self-play, 15,255,460 kept by the loop's own
filter (P3c lists its rules). Every 72nd kept position was taken: 211,881 positions. Every best move was checked
to be legal on its position (python-chess 1.11.2).

**The rules:** `make_skip_predicate` in the official Stockfish trainer (nnue-pytorch, commit 17cfb7f of
2026-11-09, `data_loader/cpp/training_data_loader.cpp` lines 926 to 1175; defaults in `data_loader/config.py`
lines 8 to 47). That trainer does not delete positions: it skips them at random while it draws batches, in every
pass anew. The table says what share of THIS round each rule would touch.

| Rule of the official trainer (its default) | On round 136 |
|---|---|
| `filtered` (ON): skip when the best move is a capture or the side to move is in check | best move a capture 18.9 %, in check 8.5 %, either 26.1 % |
| `soft_early_fen_skipping` (20): below ply 20 keep with probability 0.10 at ply 0 rising to 0.75 at ply 18 | 9.8 % of the positions are below ply 20 (none below ply 8); the rule would keep 94.9 % of all |
| piece-count shape (weights 0.4 at 8 pieces, 1.0 at 16 to 24, 0.75 at 32; a spline between) | shares here: 4 to 8 pieces 18.9 %, 9 to 16 31.1 %, 17 to 24 23.4 %, 25 to 32 26.6 %. Thinning to exactly that shape would keep 58.9 %. As coded (accept = alpha x ratio with the rarest class at 2.5 %) one pass lets 8.6 % through |
| `wld_filtered` (ON): skip with probability 1 - P(the game's result given the score), from Stockfish's own win-rate model | not applied: that model belongs to Stockfish's score scale. What this engine's scores say about results is the next table |
| `simple_eval_skipping` (off), `random_fen_skipping` (0), `early_fen_skipping` (off) | off by default |

**Score against the game's result** (score and result from the side to move; "ahead" = the side the score favours):

| abs(score) | share of all | side ahead won | draw | side ahead lost |
|---|---|---|---|---|
| 0 to 49 | 19.8 % | 16.8 % | 72.2 % | 11.1 % |
| 50 to 149 | 23.9 % | 34.1 % | 58.9 % | 7.0 % |
| 150 to 299 | 17.5 % | 64.9 % | 32.9 % | 2.3 % |
| 300 to 599 | 17.5 % | 93.7 % | 5.9 % | 0.34 % |
| 600 and more | 21.2 % | 99.68 % | 0.32 % | 0 of 44,893 |

**The same position in two rounds** (round 136's sampled positions that also stand among round 135's 15,249,472
kept positions; the position without its two move counters):

| Ply | found in round 135 | of |
|---|---|---|
| below 20 | 8 | 20,811 |
| 20 to 39 | 16 | 34,447 |
| 40 and more | 1,383 | 156,623 (0.88 %) |

## What this shows, and what it does not
- 21 % of the kept positions carry a score of 600 or more, and the side ahead won 99.7 % of those games. 39 %
  carry 300 or more. Whether such positions teach the net less than the others is NOT shown here: that needs
  the two-net test of P3c.
- Half of the kept positions have 16 pieces or fewer; the official trainer's target shape wants fewer endings
  (weight 0.4 at 8 pieces against 1.0 in the middle game). A hypothesis for this engine, not a result.
- Positions repeat between two rounds in under 1 % of the cases, and those are endings. So removing repeats
  across rounds can free very little.
- Measured in games here before (plan P3c): keeping the capture positions won, dropping the in-check ones was
  level. So the official `filtered` rule is the one rule of this table that has a game result here, against it.
- One round, one sample: the shares carry about +/- 0.2 percentage points (211,881 positions); other rounds
  were not measured.

Note added 2026-11-23T10:49:28Z (Neon's find, `source/src/uci.cpp` 457): the "ply" of a record counts from the opening position the game was given, not from move 1 of a chess game. The early-ply figures above are in that count.
