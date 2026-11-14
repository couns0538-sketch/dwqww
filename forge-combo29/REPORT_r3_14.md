# DrawJitter

Repetition leaves and fifty-move leaves can return a draw score a few centipawns off zero. The offset follows the node count. Mate scores are not adjusted.

`DrawJitter` is a UCI spin option, listed in the `uci` answer. Default 0, minimum 0, maximum 8. Zero keeps today's scores: those leaves return exactly 0.

## Where the idea comes from

A search that scores every draw as 0 cannot tell two drawing lines apart. Engines have avoided that with contempt, a constant added to draw scores. Stockfish exposed the constant as Contempt and later removed it. This is not that option. No contempt value, margin, or table was copied.

Only two kinds of leaf move. A repetition, and a position whose half-move clock has reached 100 and is not checkmate, score

    (nodes % (2 * DrawJitter + 1)) - DrawJitter

That stays inside [-DrawJitter, +DrawJitter] and changes as nodes are counted. The step was written for this search. Plain stalemate and insufficient material stay at 0. A stalemate whose clock is already 100 is a fifty-move leaf, so it uses the same step. Checkmate, including checkmate on the hundredth half-move, still returns a mate score.

If the root itself is already one of those draws, no nodes have been counted, so the score is -DrawJitter.

## Default pins

Threads 1, Hash 16, OwnBook false, and every other option at default, including DrawJitter 0. Printed before any edit and again on the final binary:

- bench 11: 312866
- bench 13: 862329
- `go perft 5` from the start position: 4865609

Build: `cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3`, then `cmake --build build`. The system `c++` is Clang 18.1.3. It found libstdc++ headers only with `--gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13`.

## Showing the option is live

On this depth-13 bench, DrawJitter 4 still returns 862329 nodes. The leaves are no longer exactly 0, but the tree does not change. DrawJitter 5 is the smallest value that changes the count: 880111 nodes. DrawJitter 8 changes it too, and a second run matched.

## Tests

`forge-combo29/tests_r3_14/draw_jitter_test.cpp` checks the node-count step, a fifty-move root, an in-tree fifty-move score, a capture on half-move 99, a constructed threefold, the ply just before that threefold, and mate scores with the option at 0 and at 8. Setting the option back to 0 restores an exact zero on the fifty-move root.

It then runs 200 searches to depth 10 with DrawJitter 8, one thread, and a 16 MB hash. The best move and every move in the PV were legal, and the score stayed inside the mate bounds (0 illegal). The same 200 positions at DrawJitter 5 also returned legal lines. A two-thread depth-10 search from the start position returned a legal line.

That binary was g++ 13.3 with `-O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined` and the portable feature macros. Exit status 0. No sanitizer diagnostic.

With DrawJitter left at 0, the existing rules suite, the repetition/mate driver, and the fifty-move transposition cases also passed, including the same drivers rebuilt with address and undefined sanitizers. Those runs were checks only. They are not part of this change.

The diff in `forge-combo29/src` and `forge-combo29/include` is 28 insertions and 3 deletions.

## Re-check

One release process, Threads 1, Hash 16, OwnBook false:

- DrawJitter 0: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609
- DrawJitter 8: bench 13 = 857947, and the repeat was 857947
- DrawJitter 0 again: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609
- DrawJitter 5: bench 13 = 880111
- Values 1, 2, 3, and 4 leave bench 13 at 862329
- Value 9 is out of range, clamped to 8, bench 13 = 857947
- Value -3 is out of range, clamped to 0, bench 13 = 862329
- A non-numeric value is refused and does not change the option

The same release commands were run again at 14:19 UTC. Bench 11, bench 13, and perft 5 matched the numbers above, including DrawJitter 8 at 857947 twice and the return to 0. The sanitizer binary was run again: both 200-search samples and the two-thread search passed, exit 0, no sanitizer diagnostic.

A later pass at 14:39 UTC matched again: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609, DrawJitter 8 bench 13 = 857947, then DrawJitter 0 bench 13 = 862329.

No strength claim.

setoption name DrawJitter value 8

bench 13 nodes 857947
