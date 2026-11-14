# Focused KRK repeat result

Ten of ten focused searches completed without reproducing the original miss. Every search returned **mate 7, b5g5**, score 31987, at depth 14. The unchanged KRK oracle reports 13 plies for the position and chosen move; all ten satisfy the original miss predicate. Counts are 0/10 misses, 0 no-mate-score results and 0 non-mating moves. The helper exited 0 with empty stderr and no sanitizer diagnostic text.

FEN: `8/4K3/8/1R6/8/8/7k/8 w - - 0 1`. The reused Searcher uses Threads 2 and Hash 16; every repetition constructs a new Board and calls Searcher::clear(). SearchLimits use depth 14 with all other fields at their original defaults, shared TT access, NNUE enabled, and MateAlphaGuard/HindsightDepth/SoundMatePruning false. The helper includes the byte-identical original test/oracle source and links the frozen candidate core objects; all source/object/binary hashes were rechecked.

This focused process omits the original full-suite position selection, 100-search T1 preflight and preceding-position process history. Thread scheduling also varies. These ten successful searches therefore establish non-recurrence in this focused run; they do not invalidate the retained original 1/400 miss, prove a cause or measure a reliable failure rate. The original full-suite fault remains byte-identical.

Root executed the already-prepared command at 2026-11-14T22:51:36.353Z through 2026-11-14T22:51:38.833Z: `/usr/bin/timeout -k 2 400 /workspace/work/r4-krk-repeat/repeat-one --run-ten`. Full CONFIG, BEGIN, ROW, PV, node and SUMMARY records are in repeat-run.stdout.txt; stderr and exact exit/hash metadata are adjacent. Nodes and elapsed times are retained observations, not performance claims. These ten searches are separate from the original 118 suite entries and the later alternating full-suite trials.

Independent post-run verification: all ten sequential markers/rows, configuration, summary, original fault and full stream/source/object hashes checked by verify-followups.mjs.txt in the final suite audit directory. No additional search was executed for this review.
