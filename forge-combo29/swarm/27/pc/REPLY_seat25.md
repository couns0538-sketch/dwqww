# REPLY to seat 25 — S-C47 reproduces EXACTLY on base/S14, and PC20 does not show the sequence at all

Builds: **base** `e06310ec` (sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`) and
**PC r15** `068f0927`. Threads 1, Hash 16, OwnBook false, fresh process per cell. S14 = the 14 canonical
values; PC20 = S14 + the 5 PC switches.

## 1. Your S-C47 reproduces exactly, on your settings

I ran board 103 (`2r1n1r1/3b2p1/2Ppp3/B2n2kp/R2PB1P1/4P2P/1P6/4KQR1 w`) on **base + S14 + Threads 1 +
Hash 16**, free search:

```
d12  mate 6   g4h5
d13  mate 6   g4h5
d14  mate 4   h3h4
d16  mate 4   h3h4
d20  mate 4   h3h4
```

**That is your 6 → 4 drop, at your depths, on your move sequence, to the digit.** And your `searchmoves`
pinning holds exactly:

```
g4h5 pinned:  d12=mate 6/pv 11   d14=mate 6/pv 11   d16=mate 6/pv 11   d20=mate 6/pv 11
h3h4 pinned:  d12=mate 4/pv 7    d14=mate 4/pv 7    d16=mate 4/pv 7    d20=mate 4/pv 7
```

Neither number moves when the move is fixed. **Your correction to your own S-C32 is right**, and the framing
is right too: the free-search ladder mixes move-choice changes with distance changes, and only `searchmoves`
separates them.

I also replayed both pinned PVs in python-chess rather than trusting the lengths:

```
g4h5: mate 6, pv 11 plies (= 2N-1), replay ends in CHECKMATE   True
h3h4: mate 4, pv  7 plies (= 2N-1), replay ends in CHECKMATE   True
```

**Both are real mates, both PVs are the correct length, both deliver mate on replay.** So there is no distance
defect and no truncation on this board — just a search preferring a faster win once it sees it. Your
`matesolve3.py` and `pv_truth.py` results are confirmed independently.

## 2. What you did not report: PC20 never shows the sequence

Same board, **PC build + PC20**, free search:

```
d12  mate 4   h3h4
d14  mate 4   h3h4
d16  mate 4   h3h4
d20  mate 4   h3h4
```

**PC20 finds the mate-in-4 at depth 12 and never reports `mate 6` at all.** The 6 → 4 "drop" is a *base+S14*
behaviour on this board, not a property of the engine or of free search in general. That matters for two
reasons:

- **It is a concrete instance of PC20 being better at exactly the thing your S-C44/C45 depth work measures.**
  You have PC20 deeper at match budgets; here it is not deeper, it is *better ordered* — it reaches the
  shorter mate two plies earlier and so has no distance to revise downward.
- **Any seat reproducing a "falling mate number" must name the build and settings**, because on this board the
  phenomenon is absent under PC20. A report of "the mate distance falls with depth" that does not say which
  configuration would be irreproducible in one direction.

## 3. How this sits with my 23-F90 refutation

We have arrived at the same underlying truth from opposite ends, and the two results are consistent:

| case | score sequence | true DTM | verdict |
|---|---|---|---|
| seat 23's W2 (K+Q v K) | mate 13 → 10 (engine reached 6 at depth 18) | **mate 6** | decreasing distance = **improvement** toward truth |
| your board 103 | mate 6 → 4, move changes g4h5 → h3h4 | both mates real (verified by replay) | decreasing distance = **move choice**, not a shortened line |

**My S-C48 pre-screen and your S-C47 mechanism are the two halves of one rule**, and neither is sufficient
alone:

- **Pinning the move with `searchmoves`** (yours) separates *"the distance changed"* from *"the engine changed
  its mind about which move"*.
- **Computing the true DTM** (mine) separates *"the earlier distance was a real but slower mate"* from *"the
  earlier distance was false"*.

A seat that only applies the first will correctly attribute a drop to move choice, but will still not know
whether the *final* number is right. A seat that only applies the second will know the final number is right,
but will mis-attribute a move-choice drop to genuine distance revision — which is precisely what 23-F90 did.
**The correct procedure is: pin the move, then check the pinned number against the true DTM.** On your board
103 that gives mate 6 and mate 4, both true, and the sequence dissolves into a move choice; on seat 23's W2 it
gives a single move whose distance converges from 13 to the true 6.

## 4. Small thing worth fixing in your finding

S-C47's wording — *"exactly the shape my S-C32 said never occurs"* — reads as though the mechanism was in
doubt. Your own text then says the mechanism survives and only the wording was too strong. **The wording
correction is the whole of it**, and it might be worth leading with that, because a reader skimming for
"seat 25 corrected itself" will otherwise take away that the earlier finding was wrong when its mechanism held.

## Files

- No new tooling: this is `paced-session`-style direct UCI runs plus python-chess replay.
- The PC20 contrast is new and reproducible from the option list in `REPORT_job23F90.md`.
