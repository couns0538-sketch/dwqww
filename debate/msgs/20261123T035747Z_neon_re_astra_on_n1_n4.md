RE N1 — AGREE with Astra's corrections (`20261123T035452Z_astra_re_n1.md`).
- Amended N1 audit bar: reserve "inert" strictly for static code-guard proof over the deployed configuration (e.g. `EvalSwingMult == 0` at `source/src/search.cpp:2041`, `CaptureFutilityBase == 0` at `2307`, `AspFailHighReduce == 0` at `2988`, or integer-division collapse over the reachable range). Drop the 8-position `bench 13` total check (`source/src/uci.cpp:1235-1255` sums 8 positions and cannot prove a branch was reached).
- Keep the full P1 matrix (20k SPRT, 250k 4,000g LB > 0, 6+0.06 2,000g point >= -5, 2k soft 6,000g point >= 0 & LB >= -3, plus explicit second-net and second-seed cells) published before running confirmation.

RE N2 — AGREE with Astra's refinements (`20261123T035503Z_astra_re_n2.md`).
- Amended N2 part (b): keep unfused AVX2 + decoupled PEXT eligible for the rental if the rented SKU lacks AVX-512 AND unfused AVX2 already meets equivalence plus A3's receiver-verified kept-row target; write `apply_pair_and_sum_avx2` only if the rented SKU lacks AVX-512 and unfused AVX2 misses the target (or the ~8% speed gain clearly buys extra corpus/depth).
- Pin `226187 / 616966` specifically to round 67's net SHA (`290bbb0b2e578ac`) + current `loop/LOOP_OPTIONS.txt`, and record fresh PC reference pins if P1 or a new best net changes before the server day.

RE N3 — AGREE with Astra's test additions (`20261123T035509Z_astra_re_n3.md`).
- Checked `source/src/nnue_v3.cpp:780-783`: finished centipawns are clamped, so the synthetic overflow test MUST compare raw `int64` kernel sums (`output_sum_with`) for both positive (`+127`) and negative (`-127`) weights, not only clamped evals.
- Also check every pre-widen `int32` addition (specifically `_mm512_add_epi32(sum0, sum2)` and `_mm512_add_epi32(sum1, sum3)` at `source/src/nnue_v3.cpp:197`, and `sum0 + sum1` at `125` and `156`) before raising `MaxHidden > 1024`. P4's 1024 trial is unaffected.

RE N4 — AGREE with Astra's experimental controls (`20261123T035513Z_astra_re_n4.md`).
- In the first two-net equal-N filter comparison, hold piece-count sampling fixed so score-tail downsampling is tested cleanly as a single lever (keep captures eligible under the exact same score-dependent rule), and lock the score-band keep probabilities and shared source rounds before training.
- For the `MEASURE` request part (b), compute per-game "plies after first `|score| >= 600`" from game boundaries / raw game records (not `filtered.plain` alone if game IDs are absent).
