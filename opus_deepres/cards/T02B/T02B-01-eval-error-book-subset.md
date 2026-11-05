# T02B-01: Eval-error book: a small self-play subset started from positions the net misjudges
Status: PARTIAL (source and Forge fit read; book-builder rate and GPU wall time PENDING)

## Source
- Stockfish commit d53071eff4 (net nn-7e66505906a6, 2021-06-03, closes PR 3521):
  https://github.com/official-stockfish/Stockfish/commit/d53071eff4 , https://github.com/official-stockfish/Stockfish/pull/3521
- Its tests (fishtest API read for TC / book / bounds / W-L-D):
  https://tests.stockfishchess.org/tests/view/60b7c79a457376eb8bcaa104 (STC) ,
  https://tests.stockfishchess.org/tests/view/60b85307457376eb8bcaa182 (LTC)
- The book-generation commit it links (a fork of the engine source) was NOT read (GPL source).

## Licence
Stockfish GPL-3.0 (LICENSE row at ff7cee4244 in notes/T02/licences.md): ideas only. Read: the commit message and the
two fishtest run pages / API records; no source file.

## Mechanism
1. Book: take quiet train positions (never 013/014 holdout rows) and keep those where a net's static eval and a
   search score of the same position disagree by more than a margin. The judging net is the npt candidate the subset
   is meant to improve (the current best w4 net), not the lock's residual net; the score it is compared with is the
   row's own 5000-node label (6.2.0 HCE). That choice is cheap (rows are quiet by construction: no check, no capture /
   promotion best move) but it also selects rows where the label is the one that is wrong, so a variant compares the
   net with a lock probe at fixed nodes on the candidate rows (relabel tool, skill forge-relabel-job) and keeps only
   rows where both scores agree against the net. Own start: margin 150 cp (range 80-300 cp), at most one book
   position per game block (T02-01 block rule), book size 200k positions (range 50k-1M).
2. Play ordinary self-play games from those positions (live rules: same nodes, adjudication, row filters), with 0-2
   extra random plies so the start row is not repeated verbatim (own start 1, range 0-3).
3. Add the new rows as a subset of the training set (own start 5 % of rows, range 2-10 %) and retrain the same recipe.
   The source's ratio (2B on 64B) is not carried over as a Forge value.
4. Overlap stays 0 (card T02-01): book positions only from the 37 train shards; new rows deduplicated against the
   013/014 holdout on board + stm and against the global dedup DB before conversion.

## Forge fit
Not a duplicate of T02-06: that card's book is an endgame / imbalance theme; this one is built from the net's own
eval errors. Both need the same driver FEN-start option, so its crew hours are counted once (here or in T02-06).
The lock has no datagen code (`bash tools/forge_has.sh 'datagen|selfplay|self_play|genfens|gensfen'` = 0 hits).
Live writer: every game starts from startpos + 8 uniformly random plies (skill forge-selfplay-datagen SKILL.md:18).
R8 driver: `--openings FILE` = one game per line as UCI moves from startpos (r8/README.md:59 at opus-r8-datagen
5dd3a57d), so starting from a FEN needs one new driver option. Net static eval per row: PENDING which scorer (the v2
holdout scorer of skill forge-o30-v2net, or an npt eval dump) and its rate.

## Expected gain
Source: 64B-position set + a 2B binpack from the eval-error book (~3 % new rows), same arch (HalfKAv2^), retrained
40 epochs. STC 10+0.1, 1 thread, book noob_3moves.epd, SPRT [-0.5,2.5] (fishtest elo_model normalized) passed,
64,592 games, W 6254 L 6028 D 52310 = ~+1.22 Elo (from W/L/D). LTC 60+0.6, same book, [0.5,3.5] passed, 45,560 games,
W 1998 L 1826 D 41736 = ~+1.31 Elo. One change (data added), but a passed SPRT is selection-biased upwards.
Forge estimate: +0 to +3 Elo **UNPROVEN** (Forge's nets misjudge more positions than the source's, so the subset may
be worth more or the book may just repeat label noise of the 5000-node HCE labels).

## Effort
Crew: ~5 h (book builder 1-2 h, driver FEN-start option + unchanged-OFF equivalence check 2 h, mix + run sheet 1 h).
CPU: book scoring PENDING (rate of the chosen scorer); datagen 5 % of 305M = ~15M rows = ~12 h at 1.24M/h beside the
live run. GPU: 2 npt runs (with / without the subset; wall time PENDING, crew). Gate: see Test plan.

## Test plan
Pre-gate: driver with the option OFF = byte-identical output (the R8 60-game equivalence test); assert 0 book keys
in the 013/014 holdout; dedup report; T02-01 overlap check on the new binpack (0 shared board + stm keys); holdout
loss of both nets on the same 013/014 holdout. Gate: net with subset vs the same-recipe net without it, UHO SPRT
[0,5] at STC, then LTC. A positive holdout-loss delta alone is not a pass.

## OFF-by-default design
Driver option `--fen-openings FILE` (default empty = off: the live random-ply openings, byte-identical); the book
builder is an offline script; the mix is a training input. No engine change, so the lock bench / perft pins are
untouched.
