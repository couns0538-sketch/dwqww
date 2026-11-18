# Job 19 prediction

Fixed PC20, Threads 1, Hash 16 and the pinned standalone net768.
Each range counts mismatches on the specified comparison.

| Workload | Prediction | Mismatch range |
| --- | --- | --- |
| W1, r15d vs kF, all 1,000 depth-9 searches | Equal nodes and bestmoves | 0 rows |
| W2, r15d vs kF, all 20 ordered lifecycle sequences | Equal after removing time, nps and hashfull | 0 lines |
| W2, each literal final search vs fresh original FEN | Different | 19–20 out of 20 search blocks per build |
| W2, each literal final search vs fresh startpos | Equal | 0 out of 20 search blocks per build |
| W3, kF vs kF0, 300 depth-9 searches | Equal nodes and bestmoves | 0 rows |
| W3, kF vs kF0, all 1,000 evals | Equal | 0 eval lines |
| Supplemental kF vs kFscalar, first 300 depth-9 searches | Equal nodes and bestmoves | 0 rows |

Previous exact checks on the speed stack support W1 and W2
cross-build identity. Both sources set the board to startpos
on `ucinewgame`, so the literal final W2 search and a fresh
search of the sampled FEN are different inputs. I expect it
to match a fresh startpos instead. The prescribed ZMM switch
changes the embedded evaluator and both W3 builds still select
the active v3 AVX-512 kernel. The supplemental comparison
predicts equality for its separate scalar-vs-AVX-512 check.
