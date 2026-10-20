# Fixed-work NNUE output reuse counter experiment

Frozen source: c5cbf97a7291a3bd960c71dcd77a29bf7c95ad8e.
Only an isolated exported source tree is instrumented. No output is cached and
no search decision, constant, weight, TT admission or evaluation formula changes.
Build the instrumented forge target with two workers after the root build is
quiescent, using the same strict x86-64-v3/znver5 flags as the existing baseline.

Run the six recorded 6.4.11 parity cases at their original fixed depths, cold
then warm with Threads=1, Hash=32, OwnBook=false and Ponder=false. Run stdin
bench 11 separately. Execute the baseline once and the same instrumented
binary twice. Require identical complete ordered depth/seldepth/score/nodes/PV/
bestmove records after normalizing only time, NPS and hashfull. Require the
419798-node bench signature. Instrumented counter summaries must repeat exactly.
Do not compare elapsed times, derive speedups or retry a failed observation.

Count every actual public NNUE output-layer call with a thread-local counter,
and count Worker static-evaluation calls independently. The two counts must
agree for these searches. Duplicate classification is per search-stack slot
within its current position lifecycle: key, halfmove clock and side must agree,
then the full FEN must also agree. Count bit-identical accumulator inputs and
matching network integers separately. Invalidate audit markers on recorded real
moves, null moves and new searches. Emit at most 16 representative duplicate
events plus one deterministic end-search summary to stderr; retain complete
stdout/stderr and commands.

The source's existing evaluation cache is the handcrafted pawn cache:
Evaluator::PawnEntry in include/forge/eval.hpp and its uses in src/eval.cpp.
TT raw evaluations already avoid many network calls, and singular excluded-move
re-search already reuses stack static evaluation. Those paths remain intact.
No existing NNUE output memoization was found in the source scan.

The key alone is not a collision proof; full-FEN comparison checks apparent key
matches, and full accumulator bits check actual inference inputs. FEN omits
repetition history, but the pure NNUE output depends on accumulator bits and
side, not repetition history. Current-lifecycle counting deliberately excludes
positions revisited after invalidation or in another slot. This measures the
potential scope of a small stack cache, not a universal position cache. Observer
FEN construction, accumulator copies and stderr logging add substantial
overhead; only fixed-work correctness/counter conclusions are permitted.
