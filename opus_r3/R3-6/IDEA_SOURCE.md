# R3-6 ideas and sources

## Job
User, R3 pack: "Lazy SMP scaling: measure Threads 1/2/3 time-to-depth and nodes on 30 positions with the
stack OFF vs ON; fix any scaling bug behind an option."

## Lazy SMP background
- Chess Programming Wiki, "Lazy SMP" and "Shared Hash Table": all threads search the same root with a
  shared transposition table; helpers are useful through the entries they store, so time-to-depth
  improves less than NPS (node overhead), and strength at equal time is the real measure.
- Stockfish (search.cpp, `Thread::search`): the iterative-deepening loop condition is
  `!(Limits.depth && mainThread && rootDepth > Limits.depth)`: only the main thread honours a `go depth`
  limit; helper threads keep deepening and are stopped by the main thread when it finishes. That is the
  model for UCI `SmpHelpersPastDepth`.
- Stockfish 7-10 "skip blocks" (`SkipSize` / `SkipPhase`: helper threads skip some depths so that half of
  them search one ply deeper than the main thread); current Stockfish no longer has them.
  Considered here as a way to reduce helpers duplicating the main thread; not implemented: it is a search
  design change that needs an SMP Elo gate, not a bug fix.
- Hyatt & Mann (2002), "A lockless transposition table implementation for parallel search" (ICGA J.):
  background of O1-LTT's `LocklessTT`, measured here as part of the stack ON.

## Forge sources read
- `src/search/searcher.inc` (helper launch, stop/join, SmpExactNodes, SmpBestThread), `src/search/iterative.inc`
  (per-worker iterative deepening: every worker, helpers included, stops at `max_depth`),
  `src/search/checks.inc` (stop flag, node publishing), `src/search/tt.inc` / `tt_lockless.inc` (striped
  mutexes vs lockless words), `include/forge/thread_data.hpp`, `src/uci.cpp`.
- `opus_round1/O1/REPORT.md` (audit, bugs 1-2, SmpExactNodes, SmpBestThread, CI scaling on a 2-core runner),
  `opus_round1/O1-LTT/REPORT.md` (LocklessTT and its scaling runs).
- MSYS2 g++ 15.2 uses the posix thread model (winpthreads 14): `std::mutex` is a pointer to a mutex object
  allocated on first lock, so the locked TT's 1024 stripe mutexes are small heap objects (not in the
  64-byte stripes); relevant when reading the OFF vs ON (LocklessTT) NPS on the PC.

## Own work
- Measurement harness (`smp_ttd.py`): fresh process per run at IDLE priority, wall time from `go` to
  `bestmove`, process CPU time (GetProcessTimes) and system load (GetSystemTimes) per run, shuffled order.
- Diagnostic build (`make_trace_src.py`, `-DFORGE_SMP_TRACE=1`, scratch copy only): per-worker iteration
  timeline, exit time, thread CPU time, TT probes/hits/cutoffs, join latency.
- The found bug: in a `go depth N` search every helper returns once it has completed iteration N and its
  core then sits idle until the main thread completes N; fix = UCI `SmpHelpersPastDepth` (default false).
