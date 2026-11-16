# APPLY SHEET — two silent GUI hangs, one patch (seat 24)

Patch: `forge-combo29/swarm/24/patches/two_gui_hang_fixes.patch.txt`
Target: the PC r15 source (`forge-combo29/` after FABLE_TO_swarm_5.md's patch is applied). One file, three hunks,
`src/uci.cpp`. Also available separately as `terminal_root_infinite.patch.txt` (the base tree's share, one hunk).

## Apply

```
cd forge-combo29
patch -p1 < path/to/two_gui_hang_fixes.patch.txt      # verified clean, no fuzz
# or: patch -p1 --dry-run < ... to check first
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1
```

## Fault 1 — an unbounded search at a terminal root never answers

At a checkmate or stalemate root the search finishes instantly, but the UCI loop then waits on `stop_cv` merely
because `limits.infinite` is set, and the already-computed `bestmove 0000` is never printed.

**Change:** skip that wait when `!search_board.has_legal_move()` — the same predicate the search itself uses to
decide the root is terminal, so the two cannot disagree.

| case | before | after |
|---|---|---|
| checkmate root, `go infinite` | no bestmove in 30 s | `bestmove 0000`, 0.00 s |
| stalemate root, `go infinite` | no bestmove in 30 s | `bestmove 0000`, 0.00 s |
| checkmate root, `go ponder` | no bestmove without `stop` | `bestmove 0000`, 0.00 s |
| normal board, `go infinite` | waits for `stop` (correct) | **still waits for `stop`** (20 info lines, then e2e4) |

Verified at Threads 1 AND Threads 4 (the defect is not a single-thread artefact).

## Fault 2 — a clock naming only the opponent's side searches forever, silently

`src/uci.cpp:184-191` reads any clock but keeps it only `if (mine)`, so `go wtime N` with Black to move (or
`go btime N` with White) names a limit that is parsed and discarded. The search then has no bound and prints no
diagnostic at all — 0 `info string` lines.

**Change:** set `opponent_clock_only` when a clock of the other side is read, and fold it into the engine's
EXISTING "a limit was named but cannot be used → answer at once" rule (`if (limit_unusable && !limit_given)
limits.movetime_ms = 0;`). No new behaviour is invented; the engine already had this precedent.

| case (PC20, Threads 1, 6 s window) | before | after |
|---|---|---|
| Black to move, `go wtime 1000` | **unbounded, silent** | d7d5, 0.00 s |
| White to move, `go btime 1000` | **unbounded, silent** | d2d4, 0.00 s |
| White to move, `go btime 600000` | **unbounded** | d2d4, 0.00 s |
| White, `go wtime 1000` (own clock) | d2d4, 0.03 s | unchanged |
| Black, `go btime 1000` (own clock) | e7e5, 0.02 s | unchanged |
| White, `go wtime 1000 btime 1000` | d2d4, 0.03 s | unchanged |

## Honesty numbers with both fixes — unchanged

| probe | expected | patched |
|---|---|---|
| bench 11 | 312866 | 312866 |
| bench 13 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 |
| bench 11 under S14 | 242796 | 242796 |

Every line a fresh process; the pins with no `setoption` at all (file 4's rule).

## NOT MEASURED — read this before shipping

**No match was played with this patch.** The strength effect is entirely unmeasured: I have no game results, no
self-play, no Elo estimate, and no evidence that the patched engine is as strong as the unpatched one. The patch
touches only the two "answer at once" paths, so a strength change is implausible, but implausible is not measured.

What the patch also does NOT fix: the threaded move instability (24-F21/F22/F23/F24). Threads > 1 still changes the
chosen move on roughly two positions in five, on both builds. Only Threads 1 is reproducible.

## Limits, stated plainly

- "Answer at once" for an opponent-only clock means the engine plays its first/hashed move without searching. A GUI
  should always send the full clock; this only removes the silent hang.
- Not run under TSan (these hunks add a local bool in the go-parsing scope and no shared state).
