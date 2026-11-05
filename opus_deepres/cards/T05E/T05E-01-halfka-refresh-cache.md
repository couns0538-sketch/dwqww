# T05E-01: HalfKA refresh cache ("Finny table") keyed by perspective, own-king square and material state
Status: PARTIAL (every unfinished field says PENDING)

## Source
- Own code (read-only, git D:/grok-pc-data/dwqww origin/qa-r10v2-fix1 7f79c349 = the r10fix1 exe of the npt gates):
  src/nnue_halfka.cpp:436-445 refresh() (bias copy + one row_add per piece), src/search.cpp:661-693
  halfka_evaluate() (nearest valid ancestor with the same king square and bucket, else full refresh), and
  docs/OPUS_R10_HALFKA.md stage table (L1 1024: refresh 626.5 ns / perspective, update 124.5 ns, forward 279.2 ns;
  2,259 of 24,000 perspective-moves = 9.4 % refresh) and its "next speedups" item 3.
- Stockfish commit 49ef4c935a "Implement accumulator refresh table" (2024-04-24, PR 5183):
  https://github.com/official-stockfish/Stockfish/commit/49ef4c935a5cb0e4d94096e6354caa06b36b3e3c ,
  https://github.com/official-stockfish/Stockfish/pull/5183 ; tests
  https://tests.stockfishchess.org/tests/view/6627fa063fe04ce4cefc6560 (final),
  https://tests.stockfishchess.org/tests/view/662301573fe04ce4cefc1386 (first),
  https://tests.stockfishchess.org/tests/view/662808133fe04ce4cefc667c (SMP).
- MIT engine with the same mechanism: PENDING.

## Licence
Stockfish GPL-3.0 at 49ef4c935a (Copying.txt): ideas only - commit message, PR text and test pages read, never
source. Own code: own. MIT engine: PENDING.

## Mechanism
PENDING (written below once the sources are complete).

## Forge fit
PENDING

## Expected gain
Stockfish (big net L1 2560 HalfKAv2_hm at the time, no functional change), UHO_Lichess_4852_v1, SPRT [0, 2]
normalized: final STC 10+0.1 1 thread +9.75 +- 3.48 Elo (9,696 games, LLR 2.94, ptnml 30-964-2604-1204-46); first
version STC +17.36 +- 4.74 (5,408 games, LLR 2.93); SMP 5+0.05 8 threads +3.13 +- 1.83 (32,672 games, LLR 2.95).
Elo computed here from the pentanomial counts (logistic, 95 %); SPRT stopping inflates them. No nps figure in the PR.
Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
