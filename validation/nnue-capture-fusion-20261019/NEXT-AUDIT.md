# Next bounded source experiments

Read-only audit of source `c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e`.
These are unimplemented hypotheses, with no measured speed or strength result.
Keep the failed strict hosted performance calibration and every earlier candidate.

1. **Finish the four-change castling specialization.** This is the smallest
   remaining exact-order accumulator change. `src/nnue.cpp:223-234` emits remove
   king, add king, remove rook, add rook. Counts two and three have fast paths,
   but this exact count-four flag pattern still reaches the copy plus four
   full-array passes at `src/nnue.cpp:145-153`. Guard count four and flags
   remove/add/remove/add, then compute each lane as
   `(((parent - removed0) + added1) - removed2) + added3`; keep every other
   pattern on the existing fallback. Do not combine feature columns first.
   The useful proof is fewer child-array stores while retaining all four
   rounding steps, both perspectives and in-place behavior. Castling is rare,
   so even a kernel improvement may have negligible whole-engine effect.

   Test hypothesis: link the same actual-API snapshot driver to frozen 6.4.11
   and the candidate. Require byte-identical complete streams, including all
   16 count-four masks, both colors' two castling sides, repeated-feature
   synthetic inputs, distinct/in-place updates and unchanged parents. Then run
   the normal correctness and exact untimed search-parity gates. A future
   separately calibrated `--group castle` diagnostic can examine code generation
   and cost; do not rerun or widen the failed hosted performance profile.

2. **Cache only the NNUE output for a still-current search-stack position.**
   `Worker::static_evaluate` reuses valid accumulator arrays at
   `src/search.cpp:543-552` but still calls the full output layer unconditionally
   at line 553. LMR/full-depth/PV re-search calls at lines 1068, 1071 and 1083,
   and a same-node razor call at line 880, can revisit the same position.
   This is an opportunity only when the existing TT raw-eval path does not
   already avoid inference; measure actual duplicate calls before implementing.
   A per-stack cached network integer must be invalidated with every new real
   move (`record_move`, lines 559-564), null move (lines 900-902), clear and new
   search (lines 1267-1281). Lazy replay may validate intermediate accumulators,
   so array validity alone must not imply an output cache is current. Keep the
   existing TT-eval priority. Recompute the handcrafted residual evaluation and
   history-dependent correction normally; cache neither corrected nor TT score.

   Test hypothesis: a bounded, non-timed actual-search counter trace should
   first demonstrate repeated output inference for an unchanged position. A
   candidate then needs identical accumulator/output snapshots and exact cold
   and warm fixed-work search transcripts, including re-search, null moves,
   sibling replacement, root changes and NNUE on/off transitions. A stale-cache
   fixture must fail when each relevant invalidation is deliberately omitted.
   This has broader possible reuse than castling fusion but substantially more
   lifecycle risk, which is why it ranks second.
