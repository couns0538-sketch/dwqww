Source-only next search review — 2026-10-21

Exact source21:2e151d019bc58dff2ab4e76e99ef99516af8d222. Current search.cpp,
eval.cpp,board.cpp and NNUEweights were compared byte-for-byte to that Git object;
all match. No engines, builds, timing, network or Git mutation. Only this report
directory was written. Current21 native chain and18vs17 strength run stay untouched.

Read concise NEXT_EXPERIMENTS/EXPERIMENT_LEDGER, the previous promotion-SEE next
opportunity review, double-extension repair/review, and locally available newest
Forge research ref origin/research/forge-promotion-bench-parser-regression-
20261021-0005 (352b6ff). That ref's NEXT is historical17; no result transfers to21.
The earlier quiet-evasion-history proposal is already documented and not ranked
as new. TT coherence/rule50/terminal/clock/book/SEE repairs and speed work excluded.

1. Preserve the caller's PV metadata across singular verification.

Concrete source mechanism: search.cpp:865 derives pv_node from THIS call's window;
:908 assigns ss->tt_pv = pv_node || entry.pv(). A PV call therefore establishes
true even if its hit has pv=false. Singular verification at:1080-1083 calls search
with the SAME ss and a null window, then restores only double_extensions and
excluded_move. That recursive call assigns ss->tt_pv again at:908 and can leave
false. The outer call subsequently reads the clobbered field for LMR at:1121-1123
and its final TT pv flag at:1198. This differs from ordinary child recursion and
is not fixed by the existing inherited double-extension repair. For the path with
PV outer call / non-PV TT hit / verification reaching the probe, source control
flow demonstrates a caller-local PV flag can be lost. Actual current-engine
occurrence, changed move and Elo are NOT reproduced here.

Fast falsifier: use existing Worker test access to invoke a nonroot PV depth7 node
with legal FEN `6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1`. Seed a valid non-PV lower
TT hit, depth7, nonmate score0, quiet move d1e1; ensure singular gate executes.
Observe ss->tt_pv immediately before/after same-ply verification; it must remain
true for the outer PV call. Use a wide PV window so the TT score cannot terminate
it; preserve actual stack/history/continuation setup. The seeded record tests
frame lifetime, not score accuracy. Also capture a naturally occurring current
TT/position witness before claiming an actual-search defect. Non-PV and pv=true
TT controls plus aborted verification are needed.

Isolated candidate hypothesis: saving/restoring this one flag around singular
verification retains intended PV reductions/TT classification and may improve
search allocation. Change no LMR constant, extension rule, correction history or
network. First require direct actual-core regression and bounded source-instrumented
PV invariants, then full native gates and a fresh equal-clock strength comparison.
If the guarded path cannot occur, or caller metadata is intentionally reclassified,
downgrade/reject instead of claiming a repair. Inspect high-depth null verification
separately; do not bundle a broad SearchStack rewrite.

2. Sparse-material null-move verification ablation.

Search.cpp:954-957 allows null pruning whenever side-to-move has ANY non-pawn
material; board.cpp:928-929 includes a lone bishop/knight. A null fail-high returns
without verification at depth<14 (:971-975); verification only follows at:977-985.
Pure pawn endings are protected, minor-piece pawn endings are not. Passing is
illegal in chess and can improve a zugzwang position. This is a standard selective
heuristic with a potential blind spot, NOT a demonstrated implementation bug.

Bounded falsifier: collect actual null-cutoff witnesses only from <=5-piece
minor/pawn endings, compare against authoritative tablebase WDL and no-null
reference under identical rule50/history conditions. Screening seed (legal, no
asserted WDL/zugzwang): `8/8/8/8/2k5/2p5/2K5/1N6 w - - 0 1`; its color mirror and
non-zugzwang controls belong in the set. Reject this lead if no false fail-high
is found. One candidate would add verification ONLY in that material class,
leaving general NMP margins/reductions and NNUE unchanged. Measure equal-clock
strength after correctness: extra nodes may cost more than recovered defenses.

Priority: prove the inexpensive PV-frame invariant first. Do not promote either
hypothesis from source inspection or infer Elo from qualified19/20 speed results.
