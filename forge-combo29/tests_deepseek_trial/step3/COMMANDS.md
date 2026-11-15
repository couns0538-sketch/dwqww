# Step 3 - 500 legal positions

Script: `make_positions.py` (committed next to this file). It was run with
`python -I` from `/tmp/ds`, outside the repository:

```
cd /tmp/ds
python3 -I /agent/repos/dwqww/forge-combo29/tests_deepseek_trial/make_positions.py /tmp/ds/positions.txt
```

Output (`step3/generator-output.txt`):

```
wrote 500 positions to /tmp/ds/positions.txt (playouts started: 502, seed 20261115)
invalid-or-over: 0
ply range in FENs: 8..60 (limit 8..60)
unique positions: 500
```

`positions.txt` has 500 lines, one FEN per line, sha256
`09a3bc2cab6acce92f134880b53dd4cff5525bd75648bf40242471d411c74644`.

## How the rules of the job are met

- Random legal moves from the start position: `rng.choice` over
  `board.legal_moves` from `chess.Board()`, i.e. the standard start position with
  its normal castling and en-passant rights.
- 8 to 60 plies: `plies = rng.randint(8, 60)` per playout; the ply count is
  visible in the FEN halfmove/fullmove fields and was re-checked with
  `chess.Board(fen).ply()`.
- Fixed seed 20261115: `random.Random(20261115)`, one stream for the whole run.
- No finished game: `board.is_game_over()` is checked after every move and once
  more on the final position; a playout that ends early is discarded and the next
  draw from the same stream is used, so the file is a pure function of the seed.
  Two of 502 playouts were discarded this way (`playouts started: 502`).
- `python-chess`'s `is_game_over()` covers checkmate, stalemate, insufficient
  material, the seventy-five-move rule and fivefold repetition.

The positions are legal in the stronger sense too: `chess.Board(fen).is_valid()`
is true for all 500 (the generator's `invalid-or-over` counter is 0).

## A decision I made and why

The job says "no position where the game is over". I read that as the position
must be playable, and used `is_game_over()`. I did **not** additionally exclude
positions that are in check: a position where the side to move is in check is a
perfectly legal position to search, and the engine's own search tests evasions
there, which is a useful part of a race test. I checked afterwards: 18 of the 500
positions have the side to move in check (`step3/checkcount.txt`); the other 482
do not.
