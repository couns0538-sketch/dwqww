# REPORT job20 — 21-F11 WITHDRAWN by me, and terminal-root scores on both builds

**What was asked.** (From my own job list) probe the terminal-root score defect I reported as
21-F11, and check whether it also affects stalemate and insufficient-material roots, on both
builds.

**The answer.** **21-F11 is WITHDRAWN. I was wrong.** `score mate 0` on a checkmated root is the
correct UCI score, not a fault: `score mate <y>` means "mate in y moves for the side to move", so
`y = 0` is "already mated". A mated side has no move to play, so `bestmove 0000` is right too.
Nothing to repair, and nobody should spend time on it.

**How sure.** High, and it is measured rather than asserted: the engine's own scale is
consistent across three roots whose truth python-chess establishes.

| build | case | python truth | bestmove | score | matches convention |
|---|---|---|---|---|---|
| base | side to move is checkmated | checkmate | `0000` | `mate 0` | yes |
| base | side to move can mate in 1 | can mate in 1 | `e1e8` | `mate 1` | yes |
| base | side to move is stalemated | stalemate | `0000` | `cp 0` | yes |
| pc | side to move is checkmated | checkmate | `0000` | `mate 0` | yes |
| pc | side to move can mate in 1 | can mate in 1 | `e1e8` | `mate 1` | yes |
| pc | side to move is stalemated | stalemate | `0000` | `cp 0` | yes |

If `mate 0` were a broken scale, `mate 1` would not come out right on the same build in the
same run. Both are right, so the scale is sound.

## How I got it wrong

In `job16` I saw `score mate 0` on a checkmated root, checked only that python-chess agrees the
position is checkmate, and concluded the score must be wrong because "a mated side should report
a loss". That reasoning inverted the convention: `mate N` in UCI is relative to the SIDE TO MOVE,
so being mated now is `mate 0`, not `mate -N`. I did not test a positive mate score in the same
run, which would have shown me the scale at once. That is the check I have now done.

This is the second time in this session that my own control caught me (the first was the
fullmove patch that wrongly accepted `-1`). Both are on the record rather than quietly fixed.

## Terminal-root behaviour, correctly described

| root kind | both builds | correct? |
|---|---|---|
| checkmated | `mate 0`, `bestmove 0000`, 0 nodes | yes |
| stalemated | `cp 0`, `bestmove 0000`, 0 nodes | yes |
| K v K (insufficient) | `cp 0`, a legal move, 0 nodes | yes — a draw is a draw |
| K+N v K (insufficient) | `cp 0`, a legal move, 0 nodes | yes |
| mate in 1 at halfmove 100 | base: `cp 0` 0 nodes and MISSES it; PC build: finds it | base is 21-F9, PC is repaired |

So the only terminal-root defect in my area is 21-F9 on the base tree — and the PC build does
not have it.

## Steps

| step | done | evidence |
|---|---|---|
| prediction for the terminal-score probe | done | `job20/prediction.txt` |
| terminal scores on both builds, 5 root kinds × 2 searches | done | `job20/out/summary.md` |
| the convention measurement that decides F11 | done | `job20/wd/summary.md` via `f11_withdrawal.py` |
| FINDINGS corrected in place, marked WITHDRAWN | done | `FINDINGS.md` |

## Findings

- **21-F11 WITHDRAWN** (mine, by me, with the measurement that refutes it).
- **21-F8b** and **21-F2b** unchanged: the PC build still refuses `fullmove 0` and still keeps
  the old board after a refused FEN while answering `readyok`.

## What I did NOT do

- Did not test `mate -N` (a side that is being mated in N) because I could not construct a clean
  forced case quickly; the three cases I did run already settle the scale question, and I would
  rather report the settled question than a half-built fourth case.

## What I am NOT sure about

- Whether any GUI mishandles `mate 0`. That is a GUI question, not an engine one, and I did not
  test a GUI.

## Times

see `job20/stamps.txt`.
