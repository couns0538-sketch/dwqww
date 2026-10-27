# O1 IDEA_SOURCE

O1 audits and hardens the Lazy SMP that AL1 s198 already has. The two fixes are plain engineering. Ideas
behind the options and tools are listed below, concepts only. No third-party code was copied; all code is
our own.

| Item | Source (concept only) |
|---|---|
| Lazy SMP itself: shared TT, independent helper searches, the main thread's result (already in AL1) | Chess Programming Wiki, "Lazy SMP" (https://www.chessprogramming.org/Lazy_SMP); the original description by Dan Homan (TalkChess, 2013), cited there |
| `SmpExactNodes`: reset the published per-thread node counters before a search and sum them only after the helpers stop, so a node budget never sees counts from the previous search | Own analysis of AL1's `Worker::nodes_` / `total_nodes()` (bug 1); general practice of per-search counter reset in multi-threaded engines |
| `SmpBestThread`: report the result of the helper with the deepest completed iteration (ties: higher score) instead of always thread 0's | Best-thread selection in Lazy SMP engines, as discussed on CPW "Lazy SMP" and in Stockfish's public thread-voting design (concept only; our rule is simpler: deepest completed iteration, then score) |
| ThreadSanitizer acceptance runs, UCI stress (stop / ponderhit / isready / setoption Threads races), self-play legality checks | Clang/GCC ThreadSanitizer documentation; UCI protocol specification (Stefan Meyer-Kahlen, "Description of the universal chess interface", 2004); fastchess (QA's pinned build) for self-play; python-chess for move legality |
| Scaling table (time-to-depth, NPS, node overhead per thread count) | Standard SMP evaluation practice (CPW "Parallel Search", speedup and search overhead) |
