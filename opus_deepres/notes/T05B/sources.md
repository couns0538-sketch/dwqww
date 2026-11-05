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
- L6. objdump -d (static disassembly, no run) of the lock exe C:/Users/Administrator/grok-pc/forge_push/locks/
  lock_AL1_s198_ltopgo_x_20261030/forge_ltopgo_x_al1s198_v23.exe (sha256 fd3a51903e73dc1f..., = lock FD3A5190; output
  in F:/odr/work/T05B/lock_dis.txt): material_key survives LTO+PGO as 10 popcnt + **9 dependent imul by
  0x100000001b3 + lea** + imul $0x3c15 + and $0x3fff at three inlined sites (Worker::search corrected_eval at
  0x1400ee33e, Worker::search update_correction at 0x1400ef925, Worker::qsearch at 0x1400fae4d); the material-correction
  load issues only after the chain. evaluate_position<false>.constprop.0 = 2,968 static instructions (79 imul, 69
  popcnt, 331 branches, 63 cmov) | own | T05B-02, HCE_COST

## Web sources
1. https://github.com/AndyGrant/Ethereal commits via tools/mine_commits.py --grep (652 commits since 2017 cached) +
   gh api commits 9e7cc597, 852b9751, 7f6b2d39 (messages only; recorded 00:14) | GPL-3.0, ideas only (commit messages)
   | Ethereal keeps a "Pawn-King evaluation table": 9e7cc59 (2018-01-12) "Evalute Pawn/King Shelter" (Elo change,
   SPRT 5+0.05 [0,5] LLR 2.96, 13,175 g W 3508 L 3307 D 6360; 20+0.2 LLR 3.15, 3,550 g), 852b975 (2018-07-11) "Cleanup
   some logic around the Pawn-King evaluation tables" (no functional change, no speed number), 7f6b2d3 (2018-07-22)
   "Remove seperate Zobrist for Pawn-King table" (non-regression 10+0.1 [-3,1] +1.72 +- 2.89, 23,620 g; [-2,2] +1.88
   +- 2.56, 30,080 g). Design evidence for T05B-01 (pawn + king terms cached together); **no nps number logged** | evidence for T05B-01
2. https://github.com/jdart1/arasan-chess/tree/6e432a21ef (HEAD 2026-11-04): src/ listing + src/scoring.h (89 lines,
   recorded 00:17) | MIT (LICENSE at root) | Arasan's current eval is NNUE-only (Scoring wraps nnue::Evaluator; no
   pawn or king-pawn tables left) | no card (context: HCE caches removed with the HCE)
3. https://github.com/jdart1/arasan-chess/blob/2dbc0649dc/src/scoring.h (v22.3.0, 2021-05-31, last HCE era; lines
   60-160 read, recorded 00:19) | MIT (doc/license.txt at that commit; licence_at.py reports "absent" because the file
   is not at the root - checked by hand) | design: a pawn hash entry (16,384) holding per-colour pawn-only data beside
   the scores (passers, opponent pawn attacks, weak pawns, pawn-file and passer-file masks, pawns on light / dark
   squares counts, outside-passer info), and a SEPARATE king-pawn hash per colour (2 x 8,132 entries, own hash code)
   holding king cover, storm, pawn attacks near the king and the king's endgame-position score | evidence for T05B-01;
   pawn-only masks row in TABLE
4. https://github.com/jdart1/arasan-chess/blob/2dbc0649dc/doc/CHANGES (doc; grep for cache / speed lines, recorded
   00:21) | MIT doc | 18.2 (Dec 2015): "Combine endgame score cache with king cover cache (since they can use the same
   hash signature)"; 11.6 (2009): partial evals cached, eval cache, "better alignment/sizing of structures"; 11.0
   (2008): magic bitboards "About 20-25% speedup"; **no speed number for the king-cover / pawn caches** | evidence for T05B-01
5. https://github.com/official-stockfish/Stockfish/commit/f83b899f39a0a1b48a604dccf704b2caaeb5b068 (2009-05-16,
   "Cache king shelter info in pawns structure": "It does not change often and is not so fast to calculate. No
   functional change.") + .../commit/080a4995a3977a0fe7071e62151dc4d716a13302 (2009-07-24, "Simplify king shelter
   cache handling", no functional change); found by gh search commits "shelter" (recorded 00:23) | GPL-3.0, ideas
   only (commit messages) | direct precedent for T05B-01: a node-identical shelter cache in the pawn entry; **no nps
   number logged** | evidence for T05B-01
6. https://github.com/official-stockfish/Stockfish/commit/ddc9f48bc3e0b1d22b2d1259d5d45d4640e0374d ("Introduce
   Material Correction History", 2024-08-24: "The material key is the zobrist hash representing the number of pieces
   left in a position"; STC <0,2> LLR 2.94, 189,472 g; LTC <0.5,2.5> LLR 2.94, 224,190 g) + e9aa20ad (2009, "Fixed
   incorrect material key update when making promotion moves" -> the key is updated incrementally in do_move) +
   86f1df71 / PR 6894 (2026-06-10, "Fix material key computation error", introduced by PR 6891, "Also enables more
   checking in debug builds", no functional change) + PR 6891 text ("Reorder operations in do_move" so the TT entry is
   prefetched earlier: STC <0,2> LLR 2.93, 57,248 g; nps +2.78 % on a large machine, local bench +1.58 % over 200 runs);
   gh search commits "material key" + gh api (recorded 00:27) | GPL-3.0, ideas only (commit messages, PR text) |
   design precedent for T05B-02 (incremental material key feeding the material correction) and its pitfall (an
   incremental key bug slipped in with a do_move reorder -> debug-build check incremental == recomputed); PR 6891 is a
   new number for the earlier-TT-prefetch idea (T05 SPEED_LIST row 7, R7PrefetchEarly) | evidence for T05B-02; evidence for T05 SPEED_LIST #7
7. https://github.com/TerjeKir/weiss/pull/374 = commit ff59b2741deca8c99b9d21ec5ebf9ba4373dc308 ("Pawn cache",
   2020-10-26; found by tools/mine_commits.py --grep, 782 commits since 2019 cached; PR text read 00:29) | GPL-3.0,
   ideas only (PR text) | a pawn-structure cache as a pure speed change: "Gets about 80-90% hitrate depending on
   position"; ELO 10.11 +- 6.10, SPRT 10+0.1 Threads=1 Hash=32MB [0, 5] LLR 3.06, 5,776 g (W 1427 L 1259 D 3090);
   **no nps number** | evidence for T05B-01 (logged hit rate of a pawn-only cache; the lock already has that cache)
