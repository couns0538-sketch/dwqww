# REPORT job23F90 — 23-F90's "the mate DISTANCE can be wrong" is REFUTED: the engine converges to the true DTM

Build: PC r15 sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`, **PC20, Threads 1,
Hash 16, OwnBook false** (22 options asserted).

Seat 23's 23-F90 reads this sequence on board W2 `8/5K2/7Q/4k3/8/8/8/8 w - - 0 1`:

```
depth 14-15:  mate 13
depth 16-18:  mate 10
```

as **"A SHORT MATE PV CONTAINS TWO INDEPENDENT DEFECTS ... the DISTANCE can be wrong"**, i.e. that the engine
is reporting mate distances that are not real. That reading requires `mate 13` to name a mate that does not
exist. **It does. It is just not the fastest one.**

## The true distance, established independently of the engine

I computed the exact DTM for W2 by exhaustive forced-mate search in python-chess (minimax over the full legal
move list, alternating min/max, memoised), escalating the ply bound:

```
plies  1  (mate  1): False
plies  3  (mate  2): False
plies  5  (mate  3): False
plies  7  (mate  4): False
plies  9  (mate  5): False
plies 11  (mate  6): True     <-- TRUE DTM = 11 plies = MATE IN 6
```

**The true distance is mate in 6.** So on this board:

| score the engine printed | is it a real mate? | verdict |
|---|---|---|
| `mate 13` (depth 14-15) | yes — a mate in 13 exists | a real but SLOWER mate |
| `mate 10` (depth 16-18) | yes — a mate in 10 exists | still slower than optimal |
| the true DTM | mate 6 | neither statement is false |

**`mate 13` is not a lie and `mate 10` is not a lie.** In a K+Q v K position there are many mates of many
lengths, and a search that reports a 13-move mate at depth 14 and a 10-move mate at depth 16 has not
contradicted itself — it has looked further and found a faster win. Seat 23 read a *decreasing* distance as
evidence of a *false* distance. Those are different things, and the direction of the decrease (toward the
true value) is what distinguishes them.

## The engine converges to the true DTM — the decisive test

If the distances were "wrong", deeper search would not systematically approach the true value. It does:

```
depth 10: cp 1068     nodes    80,154   pv 12 plies
depth 12: cp 1086     nodes   150,412   pv 14 plies
depth 14: cp 1324     nodes   358,225   pv 15 plies
depth 16: mate 8      nodes 1,466,041   pv 15 plies
depth 18: mate 6      nodes 2,982,632   pv 11 plies   <-- TRUE DTM REACHED
depth 20: mate 6      nodes 4,180,263   pv 11 plies
depth 22: mate 6      nodes 5,229,647   pv 11 plies
depth 24: mate 6      nodes 6,197,389   pv 11 plies
```

**From depth 18 onward the engine reports exactly the true DTM, mate 6, with an 11-ply PV (2N−1 = 11, the
correct length), and it never moves again through depth 24.** A score that converges to the ground truth and
stays there is not a defective score; it is a search that was not yet deep enough at depth 14.

**And every PV in that table is exactly the right length** — verified cell by cell against 2N−1:

```
depth 16: mate 8   pv 15 plies   needs 2*8-1  = 15   OK
depth 18: mate 6   pv 11 plies   needs 2*6-1  = 11   OK
depth 20: mate 6   pv 11 plies   needs 2*6-1  = 11   OK
depth 24: mate 6   pv 11 plies   needs 2*6-1  = 11   OK
```

So on this board **neither** of 23-F90's two alleged defects is present once the search is deep enough: the
distance is right and the PV is full-length. Even the depth-16 `mate 8` — a slower mate, found before the
optimal one — carries a complete 15-ply proof. The truncated-PV hazard they found elsewhere is real, but it is
not what is happening on W2.

So the correct description of seat 23's sequence is **iterative improvement**, and it belongs with the
ordinary behaviour of a depth-limited search, not with the truncated-PV hazard:

- depth 14-15: a 13-move mate is genuinely available and found first (13 moves is within the depth reached).
- depth 16-18: a 10-move mate is found, the shorter win preferred. Correct.
- depth 18+: the 6-move mate is found, which is optimal. Correct, and stable.

## What seat 23 got right, and it should keep

The **truncated PV** half of 23-F86/23-F88 is a separate and genuine finding, and my DTM work here does not
touch it. A `mate N` score whose PV is shorter than 2N−1 plies, on a cell where the replay does not end in
checkmate, is a real front-end hazard: a display or a trainer that trusts the PV will show an incomplete line.
Their operational rule — *"a mate score is unverified unless its PV is at least 2N−1 plies AND the replay ends
in checkmate"* — is right, and my own S-C15/05-F58 confirmations are the same defect.

**The distinction that matters, and that 23-F90 collapses:** a PV can be TOO SHORT (a real defect, because the
proof is not in the line), while a mate DISTANCE can DECREASE with depth (completely normal, because a faster
mate was found). 23-F90 treated the second as an instance of the first. The test that separates them is the
one above: compute the true DTM and see which direction the engine is moving.

## A cheap pre-screen any seat can use

Before reporting a decreasing `mate N` as a defect, ask whether the FINAL value equals the true DTM:

- **if it converges to the true DTM, the earlier values were real-but-slower mates** — improvement, not error;
- **if it converges to a distance that is NOT the true DTM, or oscillates and never settles**, that is a
  genuine distance defect and worth a finding.

For 3-piece endings the true DTM is cheap to get by exhaustive search, as here. For richer positions the
same logic works with a very deep reference search (depth 30+ with a large hash) as the stand-in.

## Limit of this report

- **One board.** W2 is a single K+Q v K position. It establishes that 23-F90's reading of *this* sequence is
  wrong, and it establishes the mechanism (decreasing distance = improvement toward DTM). It does **not**
  establish that every decreasing-distance sequence in their sweep is improvement; their W1 board showed a
  stable `mate 8`, which is consistent, but I did not compute W1's true DTM and should not claim it.
- The DTM search is exponential in the ply bound and my attempt to also extract the explicit mating line
  timed out at 260 s on the 9-ply refutation step. **The convergence table above is the stronger evidence
  anyway** — it needs no trust in my mover, only in the engine's own output.
- I did not test the base build on this board; the PC build is the one the owner plays.

## Files

- `pc/dtm_kxk.py` — exact DTM by exhaustive forced-mate search, with controls including a **non-vacuity**
  check (an earlier version of this file reported DRAW for both boards because its tables came back empty and
  every control passed vacuously — the control that would have caught it is control 6).
- This report's numbers are reproducible from the depth table alone; the convergence run is inline in the
  report and needs only the standard PC20 option list.
