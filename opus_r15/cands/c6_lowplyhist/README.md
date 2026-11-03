# C6 LowPlyHist - low-ply quiet history for move ordering near the root (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c6_lowplyhist\forge_ltopgo_c6lph.exe` + `setoption name LowPlyHist value 1`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c6_lowplyhist.patch` (include/forge/search.hpp +4, src/search.cpp +19), applies with `patch -p1` to git d4f4312.

## What it changes
Each worker gets a 32 KB table `low_ply_history_[ply][from][to]` for plies 0-3 from the root. At a quiet beta cutoff
at those plies (`update_quiet_stats`) the cutting move gets the usual history bonus and the other quiet moves tried
get the malus, exactly as in the main butterfly history. The quiet move ordering at plies 0-3 adds the table value with
weight 4 / (ply + 2) (2 at the root, 4/3, 1, 4/5). The table is cleared at the start of every search (a new root) and
by `clear()`. It is NOT read by LMR or history pruning (only by the move picker's quiet scores). Option `LowPlyHist`
(spin 0..1, default 0).

## Why it should gain
The main histories average a move's merit over the whole tree and over many previous searches, so near the root -
where every node is searched deeply, mistakes in ordering cost the most and each node is visited by many iterations -
the ordering is driven by statistics that mostly come from far deeper, unrelated positions. A small table that only
learns from the cutoffs of the current search at the first four plies gives those few, expensive nodes ordering
information about exactly these positions, while the clear at every new search keeps stale knowledge from an earlier
root out. Better ordering near the root lets more early cutoffs happen at the most expensive nodes of each iteration.

## OFF identity
With `LowPlyHist 0` the table is never read or written by the search (only cleared), so the ordering is the lock's:
kit OFF node identity ALL OK, bench d11-d22 + perft = the lock pins.

## Own review (structured self-review, NOT independent)
- Index safety: plies are checked `0 <= ply < 4` at both read and write; from / to < 64; values are int16 updated by
  the same saturating `apply_history` (|v| <= 16384); the weighted read (<= 2 x 16384) fits easily in int.
- `clear()` uses `std::memset` on the 32 KB array; the per-search clear runs only while the option is on.
- Threads: every worker owns its table; helpers clear their own at their search start.
- The PV-improvement bonus (main history only) and evasion ordering are left as in the lock.
- Risk: four plies of extra statistics can over-fit the ordering at the root to a few early iterations; the weight
  shrinks with ply and the table restarts each search. ON bench d11 320,362 / d13 897,394 / d16 2,563,336 (not strength).
- PGO cold-path note as for every option line.
