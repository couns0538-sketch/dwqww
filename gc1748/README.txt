GrokChess 1.7.48 lock + bench.
Signature bench (single thread, NNUE on):
  node bench/bench.js dist-v1.7.48 9   -> nodes=194011
  node bench/bench.js dist-v1.7.48 10  -> nodes=350802
These are the totals the unmodified 1.7.48 sources produce in this tree.
The Threads>1 patch matches both totals, position by position.
HCE fixed-depth check: GROKCHESS_USE_NNUE=0, startpos depth 6 -> 3154 nodes.
Perft: startpos 4 = 197281, startpos 5 = 4865609, Kiwipete 3 = 97862.
dist-v1.7.48/tests/bench.js is a different, older quick bench; don't use it for the signature.

