# Applying file 6's rule: my 15-C6 is WITHDRAWN, and one case survives on a new argument

File 6 (FABLE_TO_swarm_6) makes a drawn-root `cp 0` **not** a defect unless a forced mate ends no later
than the 100th half-move, tested as: same board at counter 0, `go depth >= 20`, read `mate N`, and it
is a defect only if **2N-1 <= 100 - counter** and the real counter still scores `cp 0`. I applied that
test to the boards I had. **Threads 1, PC20, PC build**, truth from two python-chess solvers.

## 1. My 15-C6 confirmation is WITHDRAWN — the K+R board is CORRECT, not defective

`file6_kr_h91.txt`:

```
STEP 1: counter 0, go depth 24 -> mate 8 (reached depth 24)
  => mate +8 means 15 plies; half-moves left at counter 91: 9
  INEQUALITY 2N-1 <= 100-counter : 15 <= 9 : FALSE
STEP 2: counter 91 at go depth 10 -> cp 0   d5a5
VERDICT: NOT A DEFECT
```

The mate needs **15 plies** and only **9** remain at counter 91, so the half-move rule fires first: a
`cp 0` there is the **correct** verdict. 15-C6 confirmed seat 08's *measurement* (the band at H=91..99
and the 82.9x node spike — those numbers reproduce exactly) and then treated the band as a defect,
which under file 6's rule it is not. **The measurement stands; my "defect" framing is withdrawn.**
The 7.25 M-node spike at H=91 remains a real cost worth knowing about, but it is the cost of correctly
discovering "this is now a draw", not a wrong answer.

## 2. A case file 6 does not cover: a PAWN move resets the counter, so the mate IS reachable

`6k1/5ppp/8/8/8/8/8/R5K1 w - - 100 1` — mate in 1 with `a1a8#`, a **rook** move:
2N-1 = 1 ply, 100 - 100 = **0** left, `1 <= 0` is **FALSE** → **not a defect** by the rule. And
indeed the PC build finds it anyway (`mate 1`, 144 nodes), so there is nothing to report.

`8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1` — the only mate is **`a7a8=Q#`, a PAWN move**. A pawn move
**resets the halfmove clock to 0**, so the mate lands at half-move 0, which is before half-move 100.
The mate is therefore *reachable*, and 2N-1 = 1 ply against a counter that never reaches 100.

`pawn100_check.txt`:

```
base/S14   score=cp 0       nodes=0        bestmove=a7a8q
PC/PC20    score=mate 1     nodes=265      bestmove=a7a8q
```

**Under file 6's own rule this is a REAL defect on the base tree** — and the PC build has fixed it. Two
things worth flagging:

- it is a defect the rule as written does not catch, because the rule compares 2N-1 against
  `100 - counter` without asking whether the mating move is a **capture or pawn move**, which resets
  the counter and makes the mate reachable regardless of the current count. The general form is:
  a mate is reachable if `2N-1 <= 100 - counter`, **or** if the mating line contains a capture or pawn
  move within the remaining plies;
- the base tree plays the *right move* here (`a7a8q`) for the *wrong reason* — 0 nodes means "first
  legal move", and the first legal move happens to be the mate. That is exactly the trap I noted in
  15-F12: the base-tree defect is not reliably a lost half-point, it is always an unsearched answer.

## 3. What this changes in my finding list

- **15-C6** (confirming seat 08's band as a defect): withdrawn as a defect claim; its *measurements*
  are unaffected and still reproduce seat 08 exactly. Recorded as 15-R3.
- **15-F12 / 15-F24 / 15-F25** (the drawn-root split): unaffected. Under file 6, searching a
  thrice-repeated root is **not a defect either** — so the split becomes a *policy option* rather than
  a bug fix, which is what my apply sheet already says ("the drawn-root policy is the owner's choice").
  The apply sheet's framing was right; only the urgency changes.
- **The pawn-move case** is the one live defect in this thread, on the base tree only, and it is
  already repaired on the PC build.

## 4. Honesty note

I confirmed seat 08's finding, and it took a new handoff file to show that the *label* I put on it was
wrong. The numbers were right; the verdict was not. That is the fifth self-correction of this run and
the one with the most consequence, because a "defect" that is actually correct behaviour would have
sent someone to fix a working guard.
