# Double-extension path accounting: actual-engine investigation

Frozen source `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d` (Forge 6.4.13).
The implementation reuses SearchStack frames between siblings and iterations.
Its double-extension limit tests the current frame before the outgoing child's
count is set; single extensions do not assign the inherited count, and singular
verification recursively mutates the same frame. Null and ProbCut branches may
recurse before the normal move-loop assignment. The hypothesis is stale or
verification-mutated counters can differ from the actual path's consumed budget.

This experiment changes only an isolated source export, adding thread-local
counters and bounded stderr journals. It never changes a SearchStack field,
search condition, chosen move, extension or returned score. The independent
shadow starts at zero for each Worker::search, copies the same count through
null/ProbCut edges, and adds one only when the real search chooses extension=2.
Ordinary re-searches share the same edge; same-ply verification retains the same
incoming shadow count. The shadow never reads real frame counts to update itself.
Quiescence never reenters main search and consumes no extensions.

The original diagnostic-v1 files are retained unbuilt. V2 adds explicit incoming,
null and ProbCut inherited-path witnesses. The first workload is the unchanged
actual UCI bench11, compared against the frozen uninstrumented Release engine
for identical 419798 nodes. Only if insufficient evidence occurs may a bounded
larger untimed search be added. No source fix is authorized in this worker.
Logs' elapsed/NPS fields are diagnostic only and provide no performance or Elo
claim; instrumentation overhead and competing correctness builds prevent that.
