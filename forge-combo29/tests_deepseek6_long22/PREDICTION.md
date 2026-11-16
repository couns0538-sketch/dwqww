long 22 prediction (ThreadSanitizer, 2 and 4 threads, first 50 of O) -- own commit before the first counted run

1. The planted race (one plain global incremented from every worker thread) IS reported by TSan
   at Threads 2: a data-race report naming the planted line, with exit code 66 (TSan's default
   failure exit) or nonzero. Kill: the plant silent.
2. The three real builds (plain S14, B_FINE at T2, FailHighBlend 7), each at Threads 2 and
   Threads 4, over the first 50 of O at depth 12: ZERO TSan data-race reports in every run
   (0 "WARNING: ThreadSanitizer" lines summed over all positions). Kill: any race report.
3. The runs still produce a bestmove for every position (the searches complete under TSan; the
   node counts are non-deterministic across threads and are recorded but not compared).
   Kill: any missing bestmove.
4. Bench pins are NOT claimed for TSan builds (instrumentation changes timing, not the tree;
   the tree identity is covered by the release builds elsewhere).
