long 78 prediction (the fresh-process pair replay) -- own commit before the runs

1. Pair counts from the seed-56 sequences: 7,538 (position, go) pairs in total, of which 4,803
   have a real search command (go depth / go nodes / go movetime) -- exactly seat 10's count.
   The remaining 2,735 = go infinite 1,064 + go ponder 1,039 + the garbage `go banana` 632.
   Kill: my extraction gives a different split.
2. The real run (the release build, every pair, fresh process, the position line sent, all
   engine lines read): 0 illegal bestmoves judged on the position the engine kept (a refused
   FEN keeps the start position in a fresh process; a refused move keeps the position up to
   the last legal move -- file 19's rule). Kill: any illegal bestmove on a python-chess-valid
   kept position with legal moves.
3. The plant (fake_engine.py answers bestmove a1a8 to every go, first 200 pairs): illegal =
   200 minus the pairs where a1a8 is legal or no legal move exists; I expect 0-2 such pairs.
   Kill: the plant reports fewer illegals than that arithmetic.
4. The infinite/ponder/banana pairs: the runner stops the search after a grace period and
   records what answered; their rows are recorded with the same judgment.
