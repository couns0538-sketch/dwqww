# CHECK of seat 03's S-F5 — perft agreement with python-chess at depth

**Verdict: CONFIRMS S-F5's claim** (move generation agrees with python-chess and the sums match
exactly), on my own harness, my own perft implementation, and my own position subset.

## What I could and could not check

Seat 03's claim has two parts, and only one of them is reproducible without their files:

- **checkable and checked:** "perft agrees exactly with python-chess … 0 refused FENs, 0 crashes,
  0 error lines, and the perft-1 move sets identical" — I reproduce this on my own positions.
- **NOT checkable from their finding alone:** the exact figure **3,925,995,728** and "1,150 of 1,150
  (position, depth) values". Those depend on *their* exact 230 positions, which I did not obtain; my
  sum is therefore different by construction and I do not claim to have matched that number.

## What I ran

`check_03f5.py` — my own harness. **PC build r15**, Threads 1, Hash 16, `positions fen` + `go perft 4`,
30 positions (the first 30 of set G), compared against a **perft I implemented myself with python-chess**
(recursive walk, not `board.perft`), comparing **both** the total **and** the full per-move divide.

```
positions: 30   AGREE (total AND full divide): 30   disagreements: 0
engine perft-4 sum: 26624970
python perft-4 sum: 26624970
sums equal: True
```

**30 of 30 agree, including the complete per-move divide on every position** — which is the stronger
form of the check, since matching totals while differing per-root-move would hide a compensating pair
of errors (a missing move in one subtree and an extra in another). Zero mismatches, zero refused FENs,
zero engine error lines.

My sum for these 30 positions is **26,624,970**; seat 03's 3,925,995,728 is for 230 different
positions at depth 5, so the two numbers are not comparable and I do not present them as such.

## Why this is worth confirming

Move generation is the foundation every other area rests on: if perft diverged, every score, PV and
mate-distance finding in the swarm would be suspect. Seat 03 (S-F1, S-F2, S-F4, S-F6) and seat 27 have
established this extensively; this check adds one more independent harness and one independently
written perft, on the PC build, at the divide level rather than the total level.

## Scope

- 30 positions, depth 4, one build (PC r15). Not a re-run of their 230 positions at depth 5.
- I did not test the en-passant-pin or castling-transit families they cover in S-F2/S-F4; this check is
  on ordinary game positions from G.
- My perft is a plain recursive walk, so it validates the engine against python-chess's legality rules
  as a library, not against a second engine's generator.
