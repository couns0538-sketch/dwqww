# CHECK of seat 07's 07-F1 — a root with no legal move prints a fabricated `score cp 0 nodes 0`

**Verdict: CONFIRMS 07-F1**, and adds two things the finding does not state:
(1) a terminal root gives the identical answer **with or without** `searchmoves`, so the
fabricated line is not specific to restricted roots; (2) a **live** board restricted to no legal
move prints the *same* `score cp 0 nodes 0` as a genuinely terminal board, so a GUI cannot tell
"this position is over" from "your searchmoves was illegal" — except that the live case also emits
`info string searchmoves restriction has no legal root moves` and the terminal case does not.

Harness: `check_s07f1.py`, written from the finding's command alone, reader thread with a
deadline, ABSENT reported distinctly from 0, and controls that must be able to fail.
Raw output: `check_s07f1_release.txt`. Engine: release `e06310ec…16a83`.

## Results (all pasted from the raw file)

```
--- terminal stalemate, go depth 3 searchmoves a1a2
    bestmove: bestmove 0000
    last: info depth 3 seldepth 3 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
--- terminal stalemate, go depth 3 (no restriction)
    bestmove: bestmove 0000
    last: info depth 3 seldepth 3 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
--- checkmated root, go depth 3 searchmoves a1a2
    bestmove: bestmove 0000
    last: info depth 3 seldepth 3 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv

--- startpos, go depth 4 searchmoves (empty list)
    bestmove: bestmove 0000
    last: info depth 4 seldepth 4 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
    string: info string searchmoves restriction has no legal root moves
--- startpos, go depth 4 searchmoves e2e5 (illegal name only)
    bestmove: bestmove 0000
    last: info depth 4 seldepth 4 score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv
    string: info string searchmoves restriction has no legal root moves

--- CONTROLS
--- startpos, go depth 4 (plain)
    bestmove: bestmove c2c3
    last: info depth 4 seldepth 6 score cp 12 nodes 701 ... pv c2c3 c7c5 g1f3 g8f6
--- startpos, go depth 4 searchmoves e2e4 (one legal name)
    bestmove: bestmove e2e4
    last: info depth 4 seldepth 4 score cp -2 nodes 52 ... pv e2e4 c7c5 c2c3
```

## Why the controls matter

`bestmove 0000` with `nodes 0` is exactly what a broken harness also reports. The two controls
show the same harness on the same engine reading a real search: 701 nodes and a 4-move PV for a
plain `go depth 4`, and 52 nodes with `e2e4` as bestmove when a legal `searchmoves` name is given.
So the 0-node answers above are the engine's, not the harness's.

## Beyond the finding

- The terminal stalemate board prints `score cp 0`; the checkmated board prints `score mate 0`.
  Both with `nodes 0` and an empty PV. This is my 15-F5 seen from the other side (seat 07's
  framing is the restricted-root case; the terminal case needs no restriction at all).
- The distinction a GUI *could* use is the `info string searchmoves restriction has no legal root
  moves` line, which appears for the live-restricted case and not for the terminal case. A GUI that
  ignores `info string` (most do) therefore sees two different situations as identical.
