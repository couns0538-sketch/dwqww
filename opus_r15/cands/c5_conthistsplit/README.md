# C5 ContHistSplit - follow-up history split by evasion / capture of the indexing move (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c5_conthistsplit\forge_ltopgo_c5chs.exe` + `setoption name ContHistSplit value 1`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c5_conthistsplit.patch` (include/forge/search.hpp +4, src/search.cpp +17 / -3), applies with `patch -p1` to
git d4f4312.

## What it changes
The continuation (follow-up) history a move indexes for the plies after it is chosen by the kind of move: a quiet move
made out of check keeps the lock's table; a capture, an evasion (a move made in check) and a capturing evasion each
get one of three new tables (`Worker::continuation_split_`, 3 x 1,384,448 bytes per worker). The choice is made where
the lock sets `ss->continuation` (quiescence, ProbCut, main move loop) by `Worker::continuation_for()`; the null move
and the root sentinel keep `[Empty][0]` of the lock's table. Readers and updaters are unchanged (they follow the
pointer). Option `ContHistSplit` (spin 0..1, default 0).

## Why it should gain
Continuation history ranks a reply by what was played just before it, but the lock pools three different situations
in one table: after a quiet move in a calm position the good replies are positional, after a capture they are mostly
recaptures and exchanges, and after an evasion the position is forcing. The frequent calm-quiet statistics then blur
the rarer capture and evasion follow-ups (and the other way round) in the same piece-to-square cells. Separate tables
give each situation its own statistics, so the ordering of the follow-up moves - and with it LMR, history pruning and
the quiet ordering that read these tables at every node - gets sharper.

## OFF identity
With `ContHistSplit 0` `continuation_for()` always returns the lock's table cell, exactly the pointer the lock set:
same tree. Kit OFF node identity ALL OK, bench d11-d22 + perft = pins. The extra tables are allocated and cleared in
every mode (clear() memsets 4 MB per worker: time, never nodes).

## Own review (structured self-review, NOT independent)
- Index `in_check * 2 + capture - 1` is only formed when `in_check || capture`, so it is 0, 1 or 2 (no wrap of the
  unsigned value); piece < 13 and to < 64 as before.
- The 4 MB clear uses `std::memset` on the heap array (no 4 MB stack temporary; the main thread stack is 1 MB on
  Windows). `std::make_unique<std::array<...>>()` value-initialises (zero) at construction.
- ProbCut runs only out of check, so it passes `in_check` = false; its moves are captures or promotions (a quiet
  promotion keeps the lock's table).
- Thread safety unchanged: every worker owns its tables. Memory +4.15 MB per worker (Threads 2 in gates: +8.3 MB).
- Risk: four tables learn from fewer samples each (slower early learning) and the cache footprint grows; ON bench
  d11 323,985 / d13 753,650 / d16 3,128,498 (not strength).
- PGO cold-path note as for every option line.
