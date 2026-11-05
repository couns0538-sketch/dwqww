# T05B sources (one line per source read: url or repo@sha | licence tier | what it gave | card id or "no card")

Sub-track T05B: node-identical speed of the hand-crafted eval (own code) - pawn / material caches, attack-map reuse.
Worker start 23:57 PC clock (2026-11-04); research stop at 01:17 (80 min) at the latest.

## Local (own code and records, read-only; not counted as web sources)

## Web sources
- L1. Lock source (read-only) C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean:
  src/eval.cpp (530 lines, read in full), include/forge/eval.hpp (PawnEntry 40 B, PawnCacheSize 1<<15, RuntimePsqt),
  include/forge/eval_params.hpp (flat table + KingSafetyWeights), include/forge/bitboard.hpp + src/bitboard.cpp (magics,
  masks, nearest_square_distance), include/forge/board.hpp + src/board.cpp:180-200, 719-790, 1048-1056 (incremental:
  squares, bitboards, occupied, king squares, key, pawn_key, checkers; no material key, no PSQT in Board),
  src/search.cpp:560-656 (material_key Horner chain, static_evaluate, record_move, corrected_eval, update_correction),
  :771-870 (qsearch eval site), :875-949 (search eval site) | own | T05B-01, T05B-02, HCE_COST
- L2. S37 NNUE microbench report (Sol leftover S37, branch opus-sol-S37 4822281e; copy read at
  C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/bin/ltopgo_v23x/astra3_5eabdb7_v23x_pc1/src_copy/opus_round1/sol_S37/REPORT.md):
  lock-net search-case static eval 403.1 ns (AVX2, PC Zen 5 at Idle under load, advisory), HCE ~232 ns (57 %, with
  pawn cache and runtime PSQT), NNUE update+output ~97 ns (24 %), rest ~74 ns; HCE evaluate_uncached 396.1 ns | own | HCE_COST, T05B-01
- L3. R7 J3 profile (branch opus-r7-nps, D:/grok-pc-data/dwqww/<cfg>/worktrees/opus-r7-nps/opus_r7/j3/REPORT.md and
  logs/ci_prof1_base/perf_self_off.txt, profile_self_off.txt): engine with the lock's bench pins (312866 / 862329 /
  3024920 / 12389307 / 34048354), Linux runner -O3 (not LTO+PGO): perf self time bench 16: evaluate_position<false>
  14.43 %, corrected_eval 2.76 %, update_runtime_psqt 1.03 %, static_evaluate 0.49 %, scale_factor 0.42 %, nnue::update
  8.28 %, nnue::evaluate 4.91 %; callgrind bench 13: evaluate_position 10.93 % (eval.cpp) + 4.11 % (bitboard.hpp
  inlined) + ~1.8 % other headers = ~15.0 % of instructions | own | HCE_COST, T05B-01, T05B-02
- L4. Same R7 report, NPS table: R7EvalPrefetch (prefetch the child's pawn-cache entry after make_move) -0.60 %
  [-2.36, +1.18] d16 wall, 5 runs, callgrind +0.08 % instructions -> "no measurable gain", kept OFF | own | dead end (pawn-entry prefetch)
- L5. Lock bench pins from skill forge-engine-verify (bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354,
  perft5 4865609, kiwipete 193690690) and its note "S37 ... search-case static eval ~403 ns AVX2, HCE 57 %" | own | test plans
