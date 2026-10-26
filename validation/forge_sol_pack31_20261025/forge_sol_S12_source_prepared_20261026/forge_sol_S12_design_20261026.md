# S12 bounded refinement: zero-dirty accumulator copy elision

Scope: source preparation only, 2026-10-26. All compiler, engine, sanitizer,
benchmark, parity, and speed results for this candidate are UNVERIFIED.

The supplied L/Lprime/B already compute NNUE accumulators lazily from the nearest
computed ancestor. This patch does not claim to invent that existing mechanism.
Its single hypothesis is narrower: a zero-dirty/null edge can use the same const
physical accumulator and white-piece PSQT state as its computed ancestor. The
baseline instead copies 512 float lanes (H256, both perspectives) across that
edge. NNUE chooses the output perspective using the current board, so changing
side to move does not require changing those features.

One CMake switch FORGE_NNUE_LAZY_ACC and one UCI option NnueLazyAcc are OFF by
default. The option is atomic pending configuration; Searcher snapshots it before
spawning workers. Only that immutable per-search value is read in the worker.
All added fields and code are compiled out when the build switch is OFF.

An alias points only to a physical, valid ancestor accumulator in that Worker's
fixed stack. Aliases never set the local accumulator.valid flag. Every normal or
null child invalidation clears its alias, and root initialization clears every
alias. Nonempty dirty edges still call the original nnue::update in precisely
the original order and materialize their own physical accumulator. Zero-dirty
edges skip the accumulator and PSQT copy. PSQT fallback refresh uses the current
board; aliased positions have identical pieces, score, and phase.

Production accumulator/PSQT consumers were enumerated in search.cpp: only
static_evaluate, record_move, record_null_move, and root initialization. Tests
that inspect private physical caches retain their default OFF behavior; the new
test must resolve the owner explicitly in ON mode. No changes to nnue.cpp,
evaluation values, SIMD, search decisions, TT, move ordering, or make/unmake.

Counters distinguish refreshes, physical updates, zero-dirty edges, avoided
copies, alias reuse, and evaluations. Worker-owned counters are aggregated only
after helper threads join. ON statistics and a process-once active message are
printed before the bench summary, never after it. OFF UCI output is unchanged
apart from the advertised OFF option in an opt-in build. Counts are not CPU time.

Source-first validation: pure finite-state/float-word model, deliberate missing
invalidation negative control, exact zero-fuzz patch application to independent
copies of all three source variants, and original full source inventories before
and after. These checks are not substitutes for the later native gates.

Native gate, after S10/S11 order permits: baseline/candidate default/ON all five
fixed node totals, perft5 and kiwipete5, FMA0, complete original CTest, dedicated
actual-Worker null/move/sibling regression, exact float-word/integer API parity,
and ASan/UBSan including ON and Threads2. No NPS or strength claim is allowed
from preparation. Later advisory timings require an exclusive window and the
existing preregistered paired protocol. A failed candidate is kept with evidence.

Idea sources: own supplied Forge implementation and this task's zero-dirty
copy-elision hypothesis; no other engine code or tuned constants.
