# T05B-01: pawn-king terms cached in the pawn entry (shelter, storm, open file, king-pawn distance)
Status: COMPLETE

## Source
Own: lock src/eval.cpp:198-228 (shelter loop), :250 (its mg sum feeds king danger), :269-272 (king-pawn distance),
:397-415 (pawn cache); include/forge/eval.hpp:52-65. Own profile: R7 J3, opus-r7-nps `opus_r7/j3/logs/ci_prof1_base/`.
Precedents: Stockfish https://github.com/official-stockfish/Stockfish/commit/f83b899f39a0a1b48a604dccf704b2caaeb5b068
("Cache king shelter info in pawns structure", 2009, no functional change) and .../commit/080a4995a3977a0fe7071e62151dc4d716a13302;
Arasan v22.3.0 https://github.com/jdart1/arasan-chess/blob/2dbc0649dc/src/scoring.h (per-colour king-pawn hash) and
doc/CHANGES 18.2; Ethereal https://github.com/AndyGrant/Ethereal/commit/852b97519485be90bc474fef456652190a0bbd27 and
/commit/7f6b2d39457ec0c986d55280c5de3cd1a6ceadab (Pawn-King table); Weiss https://github.com/TerjeKir/weiss/pull/374.

## Licence
Own code. Arasan 2dbc0649dc: MIT (doc/license.txt; source may be read, structure declarations read, nothing copied).
Stockfish 86f1df7134, Ethereal 7f6b2d3945, Weiss ff59b2741d: GPL-3.0, ideas only - commit messages / PR text only.

## Mechanism
The shelter / storm / open-file loop and the king-pawn distance depend only on the two pawn sets and the own king
square. Per colour, the pawn entry also stores the king square they were computed for (sentinel 0xFF = none), their
summed packed Score, and the summed middlegame part (the `shelter` integer king danger divides by shelter_divisor).
Pawn-key hit and same king square: add the stored Score, hand the stored integer to king danger. Otherwise compute
as today and store. A pawn-key refill and the default entry of clear() set both king slots to the sentinel (with
no pawns the loop still adds ShelterDistance + 0 and KingFileOpen, eval.cpp:221, :227: a zeroed slot is NOT valid).
Castling rights are not read by the shelter, so not keyed. Lifetime as today's entry (the engine never writes
params::table, eval_params.hpp:64-66; clear() at search.cpp:576). The traced path (tuner) computes everything.
Integer sums are order-free, so every eval and every node is unchanged. Optional step 2: passer king distances.

## Forge fit
Lacks it: `forge_has.sh 'shelter|king_safety_cache|KingEntry|pk_key|pawn_king'` hits only the loop (eval.cpp:207-250)
and its parameters. The entry today: 40 B, 32,768 per worker (1.25 MiB), half of all entries straddle two 64-B lines.
New entry: 64 B, alignas(64) (key, passed[2], score, Score[2], int32[2], int8 king square[2], valid): one line per
probe; 16,384 (1 MiB) or 32,768 (2 MiB) entries is a microbench knob - both node-identical (full key check).

## Expected gain
Sources: no nps number logged anywhere (Stockfish "not so fast to calculate", no number; Arasan CHANGES none; Ethereal
none). Weiss PR 374, pawn-only cache: "about 80-90% hitrate", +10.11 +- 6.10 Elo at 10+0.1, 5,776 g, SPRT [0, 5].
Forge: HCE 14.43 % of samples (R7 perf bench 16); shelter + KPD ~175-205 of ~1,650-1,900 instructions per HCE call,
2-3 data-dependent branches per file. Reuse = pawn hit x same king square: Weiss logs 80-90 % pawn hits, the
king-square share is logged nowhere (counters build, test plan step 1; lower in endgames, where kings walk). At
70-90 % reuse this removes ~1.0-1.6 % of node time before the bigger entry's cost (at 55 %: ~0.7-1.0 %).
Forge estimate: **+0.5 to +1.5 % nps UNPROVEN**.

## Effort
Crew ~4 h (eval.cpp / eval.hpp behind a build switch, microbench region, counters build, proofs); CPU ~1-2 h (two
kit builds, pins, 12k-FEN identity, microbench, probe); no SPRT; GPU 0.

## Test plan
1. Counters build (not gated): pawn hits, king-slot hits per colour on bench 13 + 200 game positions.
2. Microbench (primary go / no-go): extend S37 `forge_nnue_microbench` with old vs new `evaluate_runtime` over its
   10,000 positions + 346,182 children in one binary: 0 checksum mismatches, HCE ns per call delta.
3. ON exe with the kit (pc1 = pc2): bench d11-d22 + perft pins, 12k-FEN exe identity vs the lock; planted mutant
   (skip the king-square compare) must change bench nodes.
4. Gate route: node-identical = nps ABBA only (standard probe, protocol T12-02, fresh copies, A/A arm). Alone it may
   sit under the per-file effect (BH-8 up to 3-5 %): time it in one speed exe with T05B-02.

## OFF-by-default design
Build switch FORGE_HCE_PKCACHE (default 0 = lock source unchanged, so the lock pins by construction); not a UCI
option: a runtime branch in the hottest function costs time, and the kit's PGO workload leaves OFF-default option
paths cold (v2-path lesson), which would understate the gain. ON = 1, no range.
