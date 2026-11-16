# Patch: an unbounded search at a terminal root must not wait for `stop`

File: `terminal_root_infinite.patch.txt` — unified diff against base 6b98f217, one hunk in `src/uci.cpp`.
Applies with `patch -p1` from the repository root **without fuzz** (verified: `patch -p1 --dry-run` then apply, both clean).

## The defect
`src/uci.cpp:556` waits on `stop_cv` whenever `limits.infinite || limits.ponder`, even when the search has already
finished. At a root with no legal move the search returns immediately (`src/search.cpp:2250-2265`, `max_depth` is
clamped to at least 1 at `src/search.cpp:2219`), so its `bestmove 0000` is computed and then held back forever.

Behaviour before the patch (base tree AND the PC r15 build under PC20, Threads 1):
- `go infinite` at a checkmate root or a stalemate root: no bestmove in 30 s.
- `go ponder` at a terminal root: no bestmove without a `stop`.
- Every BOUNDED command at the same roots answers `bestmove 0000` in 0.00 s: `go depth 5`, `go nodes 1000`,
  `go movetime 200`, `go wtime 1000 btime 1000`, `go mate 3`, `go searchmoves e2e4 depth 3`
  (matrix in `../pc_build/pc_terminal_matrix.txt`).
- An explicit `stop` does produce `bestmove 0000` in 0.20 s, so the search is not stuck — only the wait is.

## The change
Skip the wait when the root has no legal move. `search_board.has_legal_move()` is the same predicate the search
uses to decide it is a terminal root, so the two cannot disagree.

## Proof the patch works (build: separate copy ~/work/fixwork, Release, gcc 13.3.0)

```
PATCHED mate       go infinite  -> bestmove 0000                    0.00s found=True
PATCHED mate       go ponder    -> bestmove 0000                    0.00s found=True
PATCHED stalemate  go infinite  -> bestmove 0000                    0.00s found=True
PATCHED stalemate  go ponder    -> bestmove 0000                    0.00s found=True
```

## Regression check: a normal board still waits (the patch must not answer early)

```
REGRESSION CHECK (normal board, go infinite):
  bestmove BEFORE stop? no (correct: it must wait)
  info lines seen while running: 20
  bestmove after stop: bestmove e2e4
```

## Honesty numbers with the patch applied — unchanged

| probe | expected | patched build says | unchanged |
|---|---|---|---|
| bench 11 | 312866 | 312866 | yes |
| bench 13 | 862329 | 862329 | yes |
| bench 16 | 3024920 | 3024920 | yes |
| go perft 5 | 4865609 | 4865609 | yes |

Each line above is a fresh process, no `setoption` (the pins are default-option numbers, per FABLE_TO_swarm_4).
