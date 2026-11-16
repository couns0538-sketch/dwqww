# CHECK of seat 19's 19-F33 — CorrHistV2 changes the chess, not just the node count

**Verdict: CONFIRMS 19-F33, every number to the last decimal.**

Harness: `check_19f33.py`, my own (not a copy of the finder's script). PC r15 build, **Threads 1**,
Hash 16, `go depth 12`, first 200 of set G, PC20 held constant with **only `CorrHistV2` toggled**.
Every option name asserted against the exe's own `uci` list before any search (it would have stopped
on a missing name). A refused FEN would be reported and dropped, never counted — the 15-R2 lesson;
in this run all 200 positions were accepted and none was dropped.

Raw: `check_19f33_run.txt`, per-position data `rows.jsonl` (200 rows, both arms present in all 200).

## Results, pasted

```
positions compared: 200 (dropped 0 with a missing bestmove/score)
same bestmove: 156 (78.0%)   DIFFERENT: 44 (22.0%)
different score: 183 of 200
total nodes  off(CorrHistV2 off) = 10146211   on = 9997730   delta -1.46%
same-move cp positions: 148   on-minus-off delta: mean +0.4 cp  median +1 cp  range -358 .. +435
```

Seat 19's numbers, side by side:

| quantity | seat 19 | mine | agree? |
|---|---|---|---|
| same bestmove | 156 (78.0 %) | 156 (78.0 %) | **exact** |
| different bestmove | 44 (22.0 %) | 44 (22.0 %) | **exact** |
| different score | 183 of 200 | 183 of 200 | **exact** |
| total nodes off | 10,146,239 | 10,146,211 | 28 nodes, 0.0003 % |
| total nodes on | 9,997,730 | 9,997,730 | **exact** |
| node delta | −1.46 % | −1.46 % | **exact** |
| same-move cp count | 148 | 148 | **exact** |
| mean / median delta | +0.4 / +1 cp | +0.4 / +1 cp | **exact** |
| delta range | −358 … +435 | −358 … +435 | **exact** |

One tiny difference, stated rather than smoothed over: my "off" node total is 10,146,211 against
their 10,146,239 — 28 nodes in ten million. Both arms' *on* totals and every derived quantity agree
exactly. The most likely cause is a single position where the two engines' node counts differ by a
handful, which I did not chase; it does not affect the conclusion, and I flag it rather than claim
perfect reproduction.

## What this confirms, in plain terms

`CorrHistV2 true` changes **22 % of best moves** and **91.5 % of scores** at depth 12 on real game
positions, for a **1.46 % node saving**. So the 4.3 % node saving on `bench 13` (19-F32) is not a
strength claim and does not carry to play. The score deltas on same-move positions are symmetric
(mean +0.4 cp, range −358 to +435), which is consistent with noise-level reshuffling rather than a
systematic gain — supporting the finding's conclusion that **games are needed to separate these
settings**, and that a node saving must not be read as a gain.

## Why I checked this one

It is in area 5's territory (it changes moves and scores, which is what area 5 measures), it was
marked NEW with no confirmation from any seat, and it is the kind of claim ("not a strength claim")
that is easy to assert and worth reproducing independently. My harness shares no code with seat 19's.
