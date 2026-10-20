# Forfeit diagnostic design review

Review scope: the proposed preparation described by parent `/root/tt_failed_run_audit`, plus the original failed-run report/exchange. This is a design review, not a review of a completed instrumentation patch or runner. No engine, build, Git mutation or network request was performed for this review. Timing execution remains blocked until root confirms competing builds have stopped.

The two-case design is suitable for gathering new local causal evidence: one cold final position, then one replay of the original Baseline command history, using a newly compiled instrumented export of trusted frozen source. Keep the original failure, clocks, tolerance and selection intact. These are diagnostics, not repeated match attempts, newly played games, Elo evidence or a reconstruction of the missing game85 PGN.

Required measurement boundaries:

- Controller: immediately before and after writing/flushing each `go`; actual stdout kernel-read/line-receive observation; and consumer dequeue/interpretation if a reader queue is used. Without separate receive and consumer events, Python queue delay can look like engine delay.
- Engine: UCI receipt after complete `getline`, facade entry, Worker entry and actual request/start origin, timer polls including elapsed/hard limit/node count/stop result, each completed iteration's time sample and pre-write/post-flush, search result, and bestmove pre-write/post-flush. A bestmove-only bracket cannot explain an earlier delayed `info` line.
- Use explicit common-host CLOCK_MONOTONIC values for engine events and `time.monotonic_ns()` for controller events. Record clock identifiers and sample order; clock reads in one event are sequential, not simultaneous.
- Include pid/tid/search sequence. Subtract thread CPU timestamps only for the same pid/tid. UCI receipt and Worker entry are different threads: their raw thread-CPU values are not comparable. Process CPU can cross threads within the same engine process; controller CPU is a separate process.
- Preserve telemetry write failures, truncation and dropped-event counts. Use a separate bounded telemetry sink, not protocol stdout; telemetry or pipe stalls are part of the observer effect. Do not silently treat missing events as proof of a short phase.

Warm-history contract:

- Preserve all260 original Baseline commands and order, including duplicated `isready`, original `position` commands and historical clock values. Wait for `uciok`, each `readyok`, and one `bestmove` for each `go`; eager replay followed by original `stop`/`quit` must not truncate an active search.
- Validate every requested position and emitted bestmove. Preserve raw stdout/stderr, exact sent bytes, parsed records, errors and source/binary/input hashes before and after.
- Subsequent original positions are forced even if the new engine's chosen move differs. Record such divergence. Identical requested boards do not imply identical TT/history state: timed searches on a different host and under instrumentation can visit different nodes.
- Original `wtime`/`btime` values are fixed diagnostic inputs. They are not newly maintained tournament clocks and do not create valid new results.
- One fixed cold-then-warm execution, no repeats or outcome-based selection, fits the proposed global60-second guard. Preserve an incomplete or failed diagnostic as such. Cleanup must stop only its owned process group and join/drain captures; process-leader exit alone does not prove descendants exited.

Permitted interpretation remains narrow. Outgoing-go to engine receipt includes transport and receiver scheduling, not pure transport latency. A high wall-minus-CPU interval means non-CPU elapsed time, which may be blocking, preemption, I/O or another cause; it is not uniquely proof of host descheduling. Phase events can locate a newly observed local stall. Failure to reproduce one does not explain or invalidate the original hosted forfeit. The original last completed `info time24` alone cannot distinguish later unreported work, formatting/flush, manager-read delay or scheduling.

Follow-up design clarifications supplied before implementation: the original260commands contain50`go` requests. Poll telemetry is restricted to warm sequence50 and cold sequence1; other phase/info events remain recorded. Per-worker sequence TLS is captured by the UCI worker lambda, avoiding a later control-thread `go` relabeling prior-worker events. Telemetry records the prior write's wall/CPU cost per thread, uses no fsync, and keeps the raw observer cost visible. These choices address the corresponding design risks above; their implementation still requires source review and execution evidence. The cold FEN deliberately omits the original repetition history and must remain labelled separately.
