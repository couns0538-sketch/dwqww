# S12 source reconnaissance, 2026-10-26

No engine implementation, compiler, benchmark, test, match or native runtime was
started. Existing inputs remain unchanged. The companion JSON pins40 exact input
files by absolute path, SHA256 and size, including all20 original per-bench
refresh logs. All seven Job A delivery manifest rows match actual supplied bytes.

Job A's final advisory controller record contains80 recorded processes,10 ABBA
blocks and20 ratios per depth. Recomputing the declared adjacent ratios gives
**0.9759681528985205 at d13** and **0.9298144110530071 at d16**, respectively
−2.4031847% and−7.0185589%. These are historical advisory results on a shared Xeon,
not new timings, PC evidence or playing-strength gains. The supplied timing
subdirectory has the final and partial controller JSONs but lacks the80 individual
process stdout/stderr files; independent authentication of those omitted streams
is not claimed. Their recorded hashes/exits remain in the original JSON.

The raw supplied bench stdout files verify these identical OFF/ON counts on BOTH
lock and buffix:

| Depth | Refreshes | Incremental updates | NNUE evaluations | Refresh/(refresh+update) |
|---:|---:|---:|---:|---:|
| 11 | 8 | 238992 | 194803 | 0.003347280% |
| 13 | 8 | 571275 | 468251 | 0.001400357% |
| 16 | 8 | 1862090 | 1529986 | 0.000429623% |
| 20 | 8 | 9547266 | 8129843 | 0.000083794% |
| 22 | 8 | 23231031 | 19748055 | 0.000034437% |

These are **construction-call fractions**, not elapsed-time fractions. Refresh
CPU share remains UNVERIFIED. Only eight full refreshes per bench provide very
little opportunity for a refresh-only cache on this piece-square architecture;
updates/evaluations number in the millions. No refresh cache was implemented in
the shelved Job A patch.

The source shows an additional conversion and scale of512 integer lanes into
2KiB float temporaries on every ON evaluation, per-update integer widening,
representation branches and unconditional TLS counters. The compiled-feature
accumulator footprint was reported as2080→4128 bytes, even with its runtime
option OFF. These are plausible overheads relative to the rare refresh opportunity.
Their individual causal contributions were **not** measured. In particular, the
source does not demonstrate that every hot update copies both float and int32
sidecars: update_exact writes the int32 representation, so a blanket assertion
that all update copies doubled would overstate the evidence. The size/cache,
conversion, branch and evaluate_values outlining explanations remain hypotheses.

Historical independent QA arrays also recompute exactly: C1 ON/lock medians
0.9533786160/0.9579743328 at d13/d16; same-binary C2 ON/OFF
0.9570076534/0.9539282617; buffix C4 0.9557727162/0.9611985817. Default-build C3's
separate20-block rerun was0.9943458032/1.0048596484. Those arrays and the separate
rerun are retained; they are not pooled with Sol's different static recipe.
CR explicitly spot-checked rather than rerunning QA's large tests. Both CR and
QA kept the bit-exact int32 feature shelved/DROP, with no strength claim. CR also
identified unconditional default-build counters/UCI/stats and the old outlined-
evaluation FMA-checker false failure, so that shelf must not be silently revived.

The present baseline **already performs nearest-valid-ancestor lazy NNUE replay**
in Worker::static_evaluate, search.cpp599–620, and replays residual runtime PSQT
from the same dirty changes. Reintroducing that mechanism would duplicate existing
work. SearchStack already stores an accumulator, runtime PSQT and DirtyPieces.
Worker::record_move at623–629 still builds the full descriptor eagerly, before
make_move; the calls at844,1013 and1123 cover qsearch, ProbCut and main search.
Both qsearch and main search have TT return paths before static_evaluate, and
TT-stored evaluation can also avoid it. Thus some eager descriptor work may never
be consumed, but its actual frequency and cost have not been measured here.

The bounded proposed refinement is to defer **only dirty-descriptor materialization**.
Capture the historical move, moved piece, captured piece and side before making
the move, then reconstruct the original ordered descriptor only when the existing
nearest-ancestor replay consumes it. Do not inspect the current descendant board
to infer historical captures. Preserve exact remove-mover/remove-capture/add-mover
or promotion/castle-rook ordering, EP's displaced capture square, null zero-change
handling, and both NNUE and runtime-PSQT replay. All three call paths already set
parent current_move/moved_piece before record_move, but private child context is
safer than assuming those mutable fields survive all same-frame/sibling reuse.
No heap allocation, floating arithmetic change, extra refresh, TT change or S11
material-key mechanism is needed. Both patches touch search.cpp, so combined
application still requires an actual check despite separate functional scope.

No existing deferred-descriptor implementation was found in the searched local
repository/pack patches, C++/headers/S12 notes, or local Git commit-message query.
The related lazy-runtime-psqt patch explicitly retains eager dirty_pieces and is
already reflected in the baseline. This is scoped local reconnaissance, not proof
about unfetched remote branches. One broad /tmp filename search encountered the
restricted codex-daemon directory and was not treated as complete filesystem
coverage. The JSON records those limitations.

The next implementation decision belongs to the coordinating root after this
report: one isolated OFF-default descriptor-deferral experiment, with source-
identical float/update ordering, actual descriptor parity on special moves and
lazy ancestor chains, active/counter proof, exact five-depth nodes, full Std,
sanitisers and controlled advisory timing. First measure eager records versus
materialized/never-used contexts; do not infer savings by subtracting NNUE updates
from search-node totals. No source patch or speed result is delivered by this
reconnaissance.
