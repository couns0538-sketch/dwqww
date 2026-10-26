# S12 source checkpoint, 2026-10-26

Decision: PREPARED, not accepted. All S12 native gates are UNVERIFIED. Parent is
still completing S10 and S11 in order. No compiler, engine, sanitizer, bench,
timing process, or Git mutation was launched for S12.

## What is actually new

The supplied lock, lockderived, and buffix trees already implement lazy NNUE and
runtime PSQT updates from the nearest valid ancestor. Reimplementing that would
duplicate accepted code. This candidate instead borrows the same physical valid
ancestor across zero-dirty/null edges, avoiding the otherwise redundant H256
512-float copy and PSQT copy. Nonempty dirty edges use the original update API,
order, and arithmetic. Current-board STM/EP/clocks still enter both evaluations.
No NNUE format, weights, SIMD, search decision, TT, or move-ordering change.

One build switch FORGE_NNUE_LAZY_ACC and one UCI option NnueLazyAcc both default
OFF. All new state/code is behind the build guard. The UCI setter joins before
updating pending atomic configuration; Searcher snapshots before helpers start.
Each worker owns aliases and counters; aggregation and output occur after join.
Aliases reference only physical valid strict ancestors, remain locally invalid,
and are cleared on normal/null child reuse and root reset/Worker clear.

Final patch: forge_sol_S12_lazyacc_h256e12_reviewv2_20261026.patch. The original
88a789a6... source attempt is preserved, superseded by the explicit Release-mode
owner validity check and fallback alias reset. Apply only v2, never both.

## Why the old Job A refresh idea was not a speed win

The original timing controller JSON records 80 processes and 20 ON/lock ratios
per depth. Recomputed medians are 0.9759681528985205 at d13 and
0.9298144110530071 at d16. Individual stdout/stderr of all 80 timing processes
are absent from the supplied bundle; this recomputation authenticates the
supplied controller rows, not missing process transcripts. Independent QA-box
arrays are separate measurements and were not pooled.

The supplied original per-depth counter stdout is present. Both bases and both
old modes have the same counts:

| Depth | Full refreshes | Incremental updates | NNUE evaluations |
|---:|---:|---:|---:|
|11|8|238992|194803|
|13|8|571275|468251|
|16|8|1862090|1529986|
|20|8|9547266|8129843|
|22|8|23231031|19748055|

There are only eight root refreshes per eight-position bench. Refresh share of
construction calls falls from 0.003347280% at d11 to 0.000034437% at d22; this is
not elapsed CPU share. Old ON evaluates by converting/scaling 512 int32 lanes
to a 2KiB float temporary on every evaluation; its Accumulator grows2080 to4128
bytes, including compiled-feature OFF layout. The old feature copies the
selected representation, not both sidecars on every update. Conversion,
layout/cache, dispatch, and unconditional instrumentation overhead are plausible
costs; this evidence does not isolate their causal elapsed-time contributions.
The old int32 path stays shelved and is not applied here. No int16 accumulator.

## Completed source-only checks

| Check | Status | Evidence |
|---|---|---|
| Exact Job A source/evidence binding | PASS | 40 input hashes, seven original delivery hashes,20 raw counter logs |
| Pure alias model | PASS | Six tests including2400 deterministic DFS reuse operations |
| Baseline-copy model negative | PASS as negative control | Deliberate return1: zero avoided copies instead of seven |
| Missing alias-invalidation negative | PASS as negative control | Deliberate stale-owner model gives different float words |
| GNU patch dry/apply, fuzz0 L/LP/B | PASS | Six original stdout/stderr captures |
| Original complete input trees | PASS | L75/LP77/B78 hashes unchanged before/after |
| Independent final-v2 source review | PASS within source scope | No must-fix issue found; actual native behavior remains UNVERIFIED |
| Build-OFF guard erasure of runtime source | PASS | Original search.cpp/uci.cpp nonblank text restored; not a compiler proof |
| Dedicated actual-Worker test source | PREPARED | Null chains, real/null replay, siblings, invalid PSQT, special moves |
| Native baseline-RED/candidate-GREEN test | UNVERIFIED | Prepared test must fail real copy-elision assertions on base |
| Compiler/Release/full CTest | UNVERIFIED | Native held in ordered queue |
| OFF/ON bench11/13/16/20/22 | UNVERIFIED | Required308972/745494/2460422/11901452/31111774 |
| OFF/ON perft5/kiwipete5/FMA | UNVERIFIED | Required4865609/193690690/0 |
| ON actual refresh/update/skip statistics | UNVERIFIED | Counters implemented, not run |
| Actual float-word/API parity | UNVERIFIED | Reuse frozen S09 corpus plus deliberate null transitions |
| ASan/UBSan/LeakSanitizer/Threads2 | UNVERIFIED | Separate full builds required |
| Advisory NPS, own-box, Windows | UNVERIFIED | No timings launched |
| Equal-time matches/Elo | UNVERIFIED | No games, no claim |

Native command recipes and limits are in the dated native preregistration.
The immediate next bounded action is one private LP candidate build-switch OFF
Release build via the existing qualified owned build protocol after root grants
the ordered native lease. First main execution must be bare bench11/quit once,
then full standard gates before ON comparisons. A compile/runtime failure stops
that path and is preserved; it is not hidden by changing a fixture or timeout.

Resource estimate, not a measured S12 build: source-only preparation is under a
few MiB; use /tmp's separate filesystem for full private trees/build artifacts.
Conservatively reserve1GiB for initial full Release tree and logs,3GiB for both
Release arms plus later sanitizer artifacts, and owned RSS<=4GiB. No bulk raw
parity output belongs in the nearly full primary filesystem. Reuse S11 chunked
stream transport; do not regenerate the million-FEN corpus or create a new
publisher. Parent handles durable GitHub publication.

Idea sources are appended, never replacing the lock's existing provenance text.
This source checkpoint is useful for independent review even before native work.

Compact delivery excludes private sourceview_L/sourceview_L_v2/applycheck_* trees;
the originals remain local with complete inventories in the source receipts.
Only final-v2 is delivered as an applicable `.patch`. The superseded v1 patch's
exact original bytes are retained as a clearly named history `.txt` record and
locally under its original filename. Apply final-v2 alone. All source-preparation
tools must be copied into a NEW work folder before a recovery/reproduction run;
never mutate the sealed compact delivery itself.
