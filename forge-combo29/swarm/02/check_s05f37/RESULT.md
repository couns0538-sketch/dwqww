# S02 check of seat 05's S-F37 — CONFIRMS, every number to the digit

Their finding: "`go wtime 6000 btime 6000 winc 60 binc 60` uses 0.36 s and reaches depth 19, identical to
`go depth 19` on the same board (same 650,246 nodes, same 0.35-0.36 s). But `go movetime 6000` on the same
board/settings uses 5.99 s and reaches depth 27."

## my measurement (own harness, `check_s05f37.py`, written from their sentence)
PC r15 + PC20, Threads 1, Hash 16, OwnBook false, startpos, 2 fresh runs per command, interactive driver.

| go command | wall ms | depth | nodes |
|---|---|---|---|
| `go wtime 6000 btime 6000 winc 60 binc 60` | 362, 359 | 19, 19 | 650246, 650246 |
| `go movetime 6000` | 5990, 5991 | 27, 27 | 7061631, 7061631 |
| `go depth 19` | 360, 360 | 19, 19 | 650246, 650246 |

**Every number matches theirs**: 0.36 s, depth 19, 650,246 nodes for the clock path; 5.99 s, depth 27 for
movetime; and the clock path IS identical to `go depth 19` in nodes and time. Raw `rows.json`.

## verdict: CONFIRMS
A 6-second clock is expressed as `wtime/btime/winc` and the engine declines to use it, reaching the same depth
and node count it would reach if it had been told `go depth 19`. The same 6 seconds given as `go movetime` IS
used, to depth 27. So the budget is real and the engine can use it; the clock path simply does not.

This is the same phenomenon my S-F13/S-F12 measured from the other direction — 3.3-5.8 % clock utilisation — and
their finding supplies the missing comparison: the clock path stops where a fixed-depth search would stop, not
where the clock would allow. Two independent harnesses, two different framings, the same conclusion.

## one thing to be careful of, and it is not a contradiction
The two facts look inconsistent with a naive reading and are not: my utilisation number says the engine uses a few
per cent of the clock MEDIAN across boards, and theirs says on startpos the clock path is exactly `go depth 19`.
Both describe the same behaviour — the soft plan for this clock is 317 ms, so the search stops after whatever
iteration crosses ~317 ms x factor, which on startpos is depth 19 at 360 ms. Whether that is conservative by
design or leaves strength unused is O-3 in my OPEN_ITEMS.md, and it needs a strength match to settle, not more
measurement.
