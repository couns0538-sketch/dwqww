# T05E-02: HalfKA backward fill after a refresh, so siblings and TT-eval gaps update instead of refreshing
Status: COMPLETE (research only; the counter build and the ABBA below were not run)

## Source
- Own code, read-only (git `origin/qa-r10v2-fix1` 7f79c349): `src/search.cpp:864` and `:992` (static eval taken from
  the TT entry, no evaluate() call, so no accumulator row is built there), `:661-693` halfka_evaluate() (nearest valid
  ancestor with the same king square and bucket, else full refresh), `:623-645` record_move / record_null_move.
- Stockfish e9997afb1c "Replace hint_common_parent_position() by backwards accumulator updates" (2025-02-24, PR 5870):
  https://github.com/official-stockfish/Stockfish/pull/5870 ; tests https://tests.stockfishchess.org/tests/view/67a27f26eb183d11c65945be
  (STC), https://tests.stockfishchess.org/tests/view/67a287efeb183d11c65945ee (LTC). The hint it replaced: 0838552
  "Introduce a function to compute NNUE accumulator" (2023-02-23) and 728b963 "... also at PVNodes TT hits".

## Licence
Stockfish GPL-3.0 (row in notes/T05E/licences.md): ideas only - commit messages, PR text and test pages read, never
source. Own code: own.

## Mechanism
When a node takes its static eval from the TT, or is in check, Forge builds no row there. If the move into that node was
an own-king move (or changed the material state), every child that is evaluated finds its nearest valid ancestor with the
other orientation and does a full refresh - once per child. Backward fill: right after a refresh of row e for perspective
c, walk up through the invalid entries e-1, e-2, ... and give each the row of the entry below it with that ply's recorded
piece changes reversed (adds become removes and the other way round), marked valid with the same king square and bucket.
Stop at the first valid entry, at the ply that moved c's king, at a ply that removed or promoted a queen or rook (the
state may change), or after a cap of 1-4 plies (1 = the parent only). Later siblings then update one ply from the parent.
Bit-exact for the same wrap-around reason as T05E-01: the filled rows are the exact rows of real positions on the path.

## Forge fit
Lock: no HalfKA path (`bash tools/forge_has.sh 'halfka|refresh_cache|RefreshCache|finny|AccumulatorCache'` = 0 hits).
r10fix1: no backward step; the TT-eval shortcut at `src/search.cpp:864` / `:992` is the case the Stockfish hint and its
replacement target. Change: about 30 lines after the refresh() call in halfka_evaluate(), using the per-ply `dirty`
lists already on the search stack (no new state). Works with or without T05E-01 (with it the sibling case already costs
only a cached diff, so this adds less).

## Expected gain
Stockfish (on top of its refresh table), no functional change, SPRT normalized: STC [0, 2] +2.71 +- 1.70 Elo (39,680
games, LLR 2.93, ptnml 171-4068-11042-4398-161); LTC [0.5, 2.5] +0.88 +- 0.51 (337,308 games, LLR 2.94, ptnml
276-30551-106126-31441-260); a simplified form passed non-regression STC / LTC [-1.75, 0.25]. Elo recomputed here from
the pentanomials (logistic, 95 %); no nps figure in the message. The 2023 hint it replaced: STC ~+1.4 and ~+2.3, LTC
~+1.4 (mine_commits summaries, not recomputed). PR author: filling interior rows pays only when evaluations are frequent.
Forge estimate: +1 to +4 % nps at L1 1024 alone, +0.5 to +1.5 % on top of T05E-01, node-identical, **UNPROVEN** (it
scales with the share of refreshes whose parent has no row - not measured; notes/T05E/HALFKA_COST.md).

## Effort
Crew 3 h: backward step + stop rules 1 h, counters 0.5 h, proofs 1.5 h (verify build, walk, OFF pins, ON nodes). CPU
1.5 h on one Idle core (counters + ABBA 10 pairs + 3 A/A at d16 / d20, e19 and an npt net, with and without T05E-01).
No SPRT. GPU none.

## Test plan
0. Counter build: refreshes per 1M nodes split by "parent row missing" vs "parent row has another orientation"; rows
   filled backward and how many are used later (a fill nobody uses is pure cost: pick the cap from this).
1. OFF pins; ON bench node counts equal the switch-0 counts (e19 / e9 / an npt net), Threads 1.
2. Skill forge-halfka-parity-test: walk test with random TT-style gaps, in-search verify build at Threads 1 and 3 (every
   lazily built row equals a full refresh, so a wrong filled row fails at its first use), CTest, AVX2 and znver5 builds.
3. Gate route: nps ABBA only (node-identical), alone and stacked on T05E-01; keep if the lower bound clears +1 %.

## OFF-by-default design
Build switch FORGE_HALFKA_BACKFILL (default 0 = no backward step; value = ply cap). The OFF eval (EvalFileHalfKA empty)
never reaches this code, so the lock pins hold; with a net loaded the evaluation is bit-identical, so node counts are
equal at every switch value.
