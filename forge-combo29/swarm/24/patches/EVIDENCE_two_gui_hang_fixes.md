# Patch: two silent GUI hangs, both fixed (`two_gui_hang_fixes.patch.txt`)

Unified diff against **the PC r15 source** (FABLE_TO_swarm_5.md's tree), one file, three hunks, `src/uci.cpp`.
Applies with `patch -p1` from `forge-combo29/` (verified). It also applies to the base tree for the terminal-root
hunk alone (`terminal_root_infinite.patch.txt`); this file is the combined version for the engine the owner plays.

## Bug 1 — an unbounded search at a terminal root waits forever (24-F7/24-F14/24-F15)

Before: `go infinite` (or `go ponder`) at a checkmate or stalemate root produced **no bestmove** (30 s window,
0 answers). Every bounded form answers `bestmove 0000` in 0.00 s, so the search path is correct and only the
UCI-layer wait is wrong: `stop_cv.wait` blocks whenever `limits.infinite`, even though the search has finished.

Fix: skip the wait when the root has no legal move.

## Bug 2 — a clock naming only the OPPONENT'S side searches forever, silently (seat 02's S-F4, my 24-C8)

Before: `go wtime 1000` with Black to move, or `go btime 1000` with White to move, stayed unbounded past 30 s and
printed **zero** `info string` diagnostics. Source reason: `src/uci.cpp:184-191` reads any clock but keeps it only
`if (mine)`, so the opponent's clock is parsed and discarded and can never bound anything.

Fix: remember that only the opponent's clock was named (`opponent_clock_only`) and fold it into the EXISTING
"a limit was named but cannot be used -> answer at once" rule (`if (limit_unusable && !limit_given) movetime = 0`).
This reuses the engine's own precedent for an unusable limit rather than inventing a new behaviour, and it turns a
silent hang into an immediate `bestmove`.

## Measured effect (PC r15 source + this patch, built with -DFORGE_MATE_ALPHA_GUARD=1)

Partial-clock matrix, PC20, Threads 1, Hash 16, 6 s window (`checks/c_02f4_patched2.txt`):

| side to move | command | before | after |
|---|---|---|---|
| white | `go wtime 1000` | d2d4, 0.03 s | d2d4, 0.03 s |
| black | `go wtime 1000` | **unbounded, silent** | d7d5, **0.00 s** |
| white | `go btime 1000` | **unbounded, silent** | d2d4, **0.00 s** |
| black | `go btime 1000` | e7e5, 0.02 s | e7e5, 0.02 s |
| white | `go btime 600000` | **unbounded** | d2d4, **0.00 s** |
| white | `go wtime 1000 btime 1000` | d2d4, 0.03 s | d2d4, 0.03 s |

Terminal-root matrix (`patches/pc_terminal_matrix_PATCHED.txt`): **no MISSING entry**; `go infinite` and `go ponder`
at both terminal kinds answer `0000` in 0.00 s, where before they never answered.

Regression: a normal board's `go infinite` still waits for `stop` (20 info lines, then `bestmove e2e4`).

## Honesty numbers with both fixes applied — unchanged

| probe | expected | patched | |
|---|---|---|---|
| bench 11 | 312866 | 312866 | ok |
| bench 13 | 862329 | 862329 | ok |
| bench 16 | 3024920 | 3024920 | ok |
| go perft 5 | 4865609 | 4865609 | ok |
| bench 11 under S14 | 242796 | 242796 | ok |

## Limits of this patch (stated, not hidden)

- It does NOT make the multi-threaded node explosion deterministic (24-C6/F12, seat 04's 04-F1); that is a search
  problem, not a UCI one, and no fix is offered here.
- "Answer at once" for an opponent-only clock means the engine plays its first/hashed move without searching. That is
  the same treatment the engine already gives an unreadable limit; a GUI should always send the full clock.
- Not tested under TSan (these two hunks add no shared state; the flag is a local in the go-parsing scope).
