# T05E-01: HalfKA refresh cache ("Finny table") keyed by perspective, own-king square and material state
Status: COMPLETE (research only; the counter build and the ABBA below were not run)

## Source
- Own code, read-only (git D:/grok-pc-data/dwqww `origin/qa-r10v2-fix1` 7f79c349 = source of the r10fix1 exe of the npt
  gates): `src/nnue_halfka.cpp:436-445` refresh(), `src/search.cpp:661-693` halfka_evaluate(); `docs/OPUS_R10_HALFKA.md`
  stage table and its "next speedups" item 3.
- Stockfish https://github.com/official-stockfish/Stockfish/commit/49ef4c935a5cb0e4d94096e6354caa06b36b3e3c (PR 5183,
  2024-04-24); tests https://tests.stockfishchess.org/tests/view/6627fa063fe04ce4cefc6560 (final), .../662301573fe04ce4cefc1386
  (first), .../662808133fe04ce4cefc667c (SMP). Eleanor https://github.com/rektdie/Eleanor/pull/193 (merge 134af1abde,
  test https://bench.rektdie.com/test/5251/). Titles only: chessgo 3eedea13d6, onechess 928d53d2eb.

## Licence
Stockfish GPL-3.0 at 49ef4c935a, chessgo and onechess GPL-3.0: ideas only (messages, PR text, test pages, titles; never
source). Eleanor MIT at 2c81f2fc4e (copy with notice allowed; only PR text and titles read). Own code: own.

## Mechanism
K32H3^ has one king bucket per own-king square of the mirrored half board, times 3 material states, so every own king
move, d/e-file crossing (mirror flip) and queen / rook state change forces a full refresh of that perspective: bias copy
plus one 1-KB int8 row per piece (about 30 rows at L1 1024, each with a load and store of the 2-KB row). A refresh cache
keeps, per worker, one entry per (perspective, own-king square, material state) = 2 x 64 x 3: an int16 row plus the 12
piece bitboards it represents (empty board + bias at first). A refresh XORs the entry's bitboards with the board's,
applies only the removed / added pieces' rows to the entry in one register pass (as apply() does for one ply), writes
the result to the accumulator row and stores the board's bitboards in the entry. Bit-exact: int16 adds wrap, so order
does not matter, and the loader's bound (|bias| + 32 x max|w| <= 32767 per output) keeps every final row inside int16.

## Forge fit
Lock: `bash tools/forge_has.sh 'halfka|refresh_cache|RefreshCache|finny|AccumulatorCache'` = 0 hits (no HalfKA path; the
lock's 768-input net has no king buckets). r10fix1 rebuilds from scratch on every orientation change
(`src/search.cpp:668-675`), no cache (the 30-Oct report, section 10, dropped the idea only because FB1's FORGENN3 path
has one). Change: a per-worker table beside `AccumulatorStack` (`include/forge/nnue_halfka.hpp:66-81`), sized in
ensure(): 384 x (2 KB + 96 B) = about 0.8 MB at L1 1024 (0.2 MB at L1 256); cleared at net load, ucinewgame, ensure().

## Expected gain
Stockfish (HalfKAv2_hm big net, no functional change), UHO_Lichess_4852_v1, SPRT [0, 2] normalized: final STC 10+0.1
1 thread +9.75 +- 3.48 Elo (9,696 games, LLR 2.94, ptnml 30-964-2604-1204-46); first version +17.36 +- 4.74 (5,408
games); SMP 5+0.05 8 threads +3.13 +- 1.83 (32,672 games); Elo recomputed here from the pentanomials (logistic, 95 %),
SPRT stopping inflates them, no nps figure in the PR. Eleanor (MIT, 8 king buckets): lazy updates + refresh cache
together +39.43 +- 11.28 Elo, 4.0+0.04s Threads 1 Hash 8 MB, SPRT [0, 5], LLR 2.95, 1,000 games (ptnml 1-73-251-162-13).
Titles: chessgo "+2.3% NPS, bit-exact", onechess "+4 % NPS" (no conditions). Forge side (R10 tool, L1 1024): refresh
626.5 ns per perspective vs update 124.5 ns, 9.4 % of perspective-moves refresh -> about 0.094 x (626.5 - 150..250) x 2
= 70-90 ns per evaluation, x about 0.55 evaluations per node (lock counter) of 826-980 ns per ON node (bench).
Forge estimate: +3 to +8 % nps at L1 1024 (less at L1 256), node-identical, **UNPROVEN**; the in-search refresh share is
not measured and moves the number (notes/T05E/HALFKA_COST.md).

## Effort
Crew 5 h (table 1 h, diff + one-pass multi-row apply 1.5 h, counters 0.5 h, proofs 2 h); CPU 1.5 h on one Idle core
(counters + ABBA 10 pairs + 3 A/A, d16 / d20, e19 + one npt net); no SPRT; GPU none.

## Test plan
0. Counter build: refreshes per 1M nodes by cause (king move, mirror flip, state change, no valid ancestor), cache hit
   rate, rows per cached refresh. 1. OFF pins (bench d11-d22, perft); ON bench nodes at switch 1 = switch 0 for e19 / e9
   (373062 / 831975 / 4115992 / 17885060 / 37006232) and an npt net. 2. Skill forge-halfka-parity-test: 12k-FEN parity,
   walk incremental == refresh, verify build (`-DFORGE_HALFKA_VERIFY`) at Threads 1 and 3, CTest, AVX2 + znver5, scalar.
3. Gate route: node-identical speed change = nps ABBA only (palindromic, fresh exe copies, A/A first), d16 and d20, e19
   and an npt L1 1024 net; keep only if the lower bound clears +1 %.

## OFF-by-default design
Build switch FORGE_HALFKA_FINNY (default 0 = today's refresh()). EvalFileHalfKA empty: table never allocated, lock eval
runs, lock pins hold at 0 and 1; with a net loaded the eval is bit-identical, so node counts are equal (step 1).
