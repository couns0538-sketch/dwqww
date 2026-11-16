# seat 20 — job 36: confirmation of seat 21's 21-F11 at Threads 1 (`mate 0` on a checkmated root)

Queue entry 5. Seat 21's 21-F11: a CHECKMATED root is scored `score mate 0` on
`4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60` (python-chess: checkmate, 0 legal moves).

**Confirmed, `Threads 1`, 3 runs per cell, fresh process, on BOTH builds — and the PC build does NOT repair it.**

| build | command | runs |
|---|---|---|
| base + S14 | `go depth 1` | `0000` / **`mate 0`** / 0 nodes / 1 info line ×3 |
| base + S14 | `go depth 5` | `0000` / **`mate 0`** / 0 nodes / 5 info lines ×3 |
| PC r15 + PC20 | `go depth 1` | `0000` / **`mate 0`** / 0 nodes / 1 info line ×3 |
| PC r15 + PC20 | `go depth 5` | `0000` / **`mate 0`** / 0 nodes / 5 info lines ×3 |

## Why this line matters more than its size suggests

1. **It is a LIVE finding on the PC build.** Unlike the drawn-root doors (S-C17, S-C19, S-F33), the PC patch does
   not change this. So it belongs on the short list of things the owner's engine still does.
2. **`mate 0` is not a legal UCI claim.** A mate score of zero plies would mean the side to move is already mated —
   but the convention is that `score mate 0` is not emitted, because `bestmove 0000` plus checkmate on the board is
   the correct report. Any GUI or test that parses `score mate 0` as "mate in 0" gets an impossible number.
3. **The info-line count tracks the requested depth** (1 at depth 1, 5 at depth 5) with `nodes 0` — the same
   "report every depth without searching" loop as my S-F7/S-F16/S-C11, and the same tell: `nodes 0` plus an empty pv.

## Limits
- One checkmated position; I did not test a stalemated root here (my S-C11 and seat 05's work cover `0000` on
  stalemate separately).
- `go nodes` / `go movetime` forms not re-tested on this board; seat 25's S-F7 covers the 64-line variant.
- Threads 1 only.
