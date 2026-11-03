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

## Check results (generated)

- exe `D:\o15\cands\c5_conthistsplit\forge_ltopgo_c5chs.exe` sha256 `3b9f56da360852656514e7cd591c04fdb0ee4159e2070f26dd9060b32580f9f7` md5 `25f4015a2173f2c7b4ded606bea41b2a`; kit pc1 = pc2 `3b9f56da360852656514e7cd591c04fdb0ee4159e2070f26dd9060b32580f9f7`
- ON bench d11 / d13 / d16 / d20 / d22: 323985 / 753650 / 3128498 / 11261436 / 29194446; OFF = the lock pins; perft 4865609 / 193690690 both ways
- cand_pack checks: patch_applies PASS, cleanroom_lint PASS, kit_build PASS, pc1_equals_pc2 PASS, kit_identity PASS, kit_vfmadd0 PASS, kit_missing_profile0 PASS, kit_on_live PASS, exe_copy_sha256 PASS, pin_off PASS, pin_on_live PASS, smoke PASS
- smoke with the fixed clock (12:37 fix): PASS - 21 games, 2514 plies, illegal 0, crashes 0, hangs 0, time losses 0
- R13 cand_checks (T1 / T4 movetime smoke with perft-1 legality, mate probe 22 positions at 3M nodes): FAIL; mates OFF 19 / ON 20; strict-rule flips: mate lost: ContHistSplit=1 3k4/8/8/8/7r/8/8/6K1 b - - 0 1 OFF mate 15 ON cp 512
  - 30M re-probe (lost) `3k4/8/8/8/7r/8/8/6K1 b - - 0 1`: 3M OFF mate 15 / ON cp 512; 30M OFF mate 11 / ON mate 11 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/1r6/8/8/8/4K2k/8/8 b - - 0 1`: 3M OFF cp 474 / ON mate 17; 30M OFF mate 14 / ON mate 14 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/3k4/5R2/8/8/8/8/2K5 w - - 0 1`: 3M OFF cp 544 / ON mate 15; 30M OFF mate 14 / ON mate 13 -> horizon flip (both find it at N)
- CI ASan+UBSan self-play: run 41628366851 success on 9fc59ea3c497 (patch sha256 = the built one)
