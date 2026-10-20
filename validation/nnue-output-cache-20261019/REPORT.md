# NNUE output reuse counter result

The proposed per-stack output cache has a small observed reuse ceiling and is
**not recommended as the next production candidate**. No cache was implemented.
This is an actual fixed-work engine counter experiment, not a timing comparison.

The frozen 6.4.11 source is
c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e. Its isolated source export and build
remain under /workspace/.cloud-setup/nnue-output-reuse-instrumented.
instrumentation.patch is the exact four-file audit-only change. Search decisions,
NNUE formulas, weights, TT behavior and production repository files are unchanged.

One fixed suite produced the following counts; a second independent invocation
of the same instrumented binary reproduced every end-search summary exactly.
The six named cases each include their prescribed cold and warm searches.

| Case | Actual NNUE output calls | Exact-input duplicates | Duplicate fraction |
| --- | ---: | ---: | ---: |
| Start | 2545 | 0 | 0% |
| Kiwipete | 1315 | 2 | 0.1521% |
| Middlegame | 1089 | 6 | 0.5510% |
| Endgame | 1137 | 3 | 0.2639% |
| White promotion | 7 | 0 | 0% |
| Black promotion | 7 | 0 | 0% |
| Six-case subtotal | 6100 | 11 | 0.1803% |
| Bench 11, eight positions | 269643 | 1406 | 0.5214% |
| Combined fixed suite | 275743 | 1417 | 0.5139% |

Every repeated identity had identical accumulator float bits and the same
network integer. There were zero changed-input repeats, output mismatches,
key/full-FEN mismatches or unmarked position changes. Independent counters at
Worker::static_evaluate and inside the actual public nnue::evaluate agree for
every search. Existing TT raw evaluations served another 77,798 reads in the
combined suite. Those TT and excluded-move static-evaluation reuse paths were
preserved; the header's existing “evaluation cache” denotes the handcrafted
pawn cache, not an NNUE output cache.

All twelve cold/warm search records per binary match the uninstrumented baseline
in ordered depth, seldepth, score, bounds, nodes, PV and best move after the
preregistered normalization of time, NPS and hashfull. All three bench processes
report 419798 nodes. Instrumented bench summaries account for that entire sum.
All 21 engine processes exited normally. Final hashes of the baseline,
instrumented executable, instrumentation, driver and complete instrumented source
tree match the initial freeze. The instrumented forge target built successfully
with two workers and the frozen strict floating-point flags.

The 0.5139% figure is a fraction of NNUE output calls, not engine CPU time or
potential measured speedup. A stateful cache would also add checks and lifecycle
maintenance on non-reused positions. These finite, shallow/depth-11 workloads do
not exclude greater reuse elsewhere, but the observed benefit is too small to
prioritize that extra state now. A narrowly scoped same-call optimization would
need separate evidence about its exact call site; this experiment does not
attribute duplicates to individual pruning or re-search paths.

The audit checks key, halfmove clock and side plus full FEN, then compares exact
accumulator input bits. A key match alone is not trusted. Current-slot lifecycle
markers reset on real moves, null moves and new searches; revisits after reset
or in another slot are intentionally outside the proposed small-cache scope.
FEN does not encode all repetition history, but NNUE output itself depends on
the accumulator bits and side. FEN construction, full-array copies and diagnostic
logging add substantial observer overhead. No timing, NPS or Elo inference is
permitted from these runs.

Full commands, raw stdout/stderr, representative duplicate events, deterministic
per-search summaries, source and artifact hashes are retained in this directory.
No failed observation was retried or replaced. No Git mutation or production
engine edit was performed.
