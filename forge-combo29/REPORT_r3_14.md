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

## Follow-up

`set_draw_jitter` writes the number and, when the number actually changes, clears that searcher's hash the way UseNNUE does. Setting the same number again does not clear. Scores stored under the old width are not reused.

One `Searcher` (16 MB, one thread), owner build, Clang 18.1.3, `-O3 -march=x86-64-v4`, portable off, no extra `FORGE_*` flag:

- DrawJitter 0, bench 13 = 862329, hashfull 44
- DrawJitter 8, bench 13 = 857947, hashfull 44
- DrawJitter 0 again, hashfull 0, bench 13 = 862329

The CPU has AVX-512F and BMI2, so this is the owner build. Default pins on that binary: bench 11 = 312866, bench 13 = 862329, perft 5 = 4865609.

Five alternating bench 13 runs, nodes fixed, nps from the same process:

| value | nodes | nps |
| --- | --- | --- |
| 0 | 862329 | 1781671 |
| 8 | 857947 | 1806204 |
| 0 | 862329 | 1882814 |
| 8 | 857947 | 1893922 |
| 0 | 862329 | 1878712 |

Binary sha256: `1e3ca575f62687793050f72e23a05fd30c800a7234ea5b5b1442704511583896`

`id name Chess Engine Forge 6.4.24 candidate`

The check is `forge-combo29/tests_r3fu_14/same_searcher_bench.cpp`. This is a node-count check, not a strength claim.

UHO screen, same owner binary, nodes 50000, book `UHO_4060_v4.epd`.

Chunk 1 finished 500 games (openings 1-250, both colors) in 22 minutes 58 seconds. PGN: `forge-combo29/tests_r3fu_14/screen/chunk001.pgn`. Value 8 first: W-L-D 132-138-230, Elo -4.17 ± 22.41 (95%), LOS 35.75%, pentanomial 9, 46, 141, 50, 4. Summary: `forge-combo29/tests_r3fu_14/screen/chunk001-summary.md`.

Chunk 2 finished 500 games (openings 251-500, both colors) in 22 minutes 35 seconds. PGN: `forge-combo29/tests_r3fu_14/screen/chunk002.pgn`. Value 8 first: W-L-D 125-129-246, Elo -2.78 ± 21.73 (95%), LOS 40.09%, pentanomial 8, 62, 112, 62, 6. Summary: `forge-combo29/tests_r3fu_14/screen/chunk002-summary.md`.

Chunk 3 finished 500 games (openings 501-750, both colors) in 20 minutes 53 seconds. PGN: `forge-combo29/tests_r3fu_14/screen/chunk003.pgn`. Value 8 first: W-L-D 137-134-229, Elo 2.08 ± 22.45 (95%), LOS 57.23%, pentanomial 7, 53, 124, 62, 4. Summary: `forge-combo29/tests_r3fu_14/screen/chunk003-summary.md`.

Chunk 4 finished 500 games (openings 751-1000, both colors) in 19 minutes 25 seconds. PGN: `forge-combo29/tests_r3fu_14/screen/chunk004.pgn`. Value 8 first: W-L-D 127-134-239, Elo -4.86 ± 22.03 (95%), LOS 33.24%, pentanomial 11, 56, 121, 53, 9. Summary: `forge-combo29/tests_r3fu_14/screen/chunk004-summary.md`.

Chunk 5 finished 500 games (openings 1001-1250, both colors) in 20 minutes 20 seconds. PGN: `forge-combo29/tests_r3fu_14/screen/chunk005.pgn`. Value 8 first: W-L-D 121-127-252, Elo -4.17 ± 21.47 (95%), LOS 35.16%, pentanomial 5, 58, 132, 48, 7. Summary: `forge-combo29/tests_r3fu_14/screen/chunk005-summary.md`.

Chunks 1-5 together, value 8 first: 2500 games, W-L-D 642-662-1196, Elo -2.78, 95% -10.63 to 5.07, LOS 24.38%, pentanomial 40, 275, 630, 275, 30. That combined interval is the paired normal approximation on the summed pentanomial, not a fastchess print.
