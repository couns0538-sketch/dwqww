# The two switch claims, tested independently on the S-F19 board

**Both CONFIRMED.** PC r15 build, **Threads 1**, Hash 16, `-DFORGE_MATE_ALPHA_GUARD=1`, one option at a
time **on top of S14**, fresh process per cell. Harness `switches.py`, my own.

**Truth, re-established on this machine before the test** (`truth.txt`) — not taken from anyone's
report: two python-chess solvers that share no code path, both returning the same answer:

```
matedbf:     MATED_IN_PLIES 8
solvemate2:  MATED_IN_PLIES 8 (depth 8)
```

So the correct output is **`mate -4` with an 8-ply PV ending in checkmate**.

Board: `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1` (seat 05's S-F19 board, white to move, white lost).

## Results — `switches_SF19.txt`

```
arm                          d    score      nodes     pv    mate?  consistency
S14 baseline                 12   mate -9    37664     14    False  plies 14 != want 18
S14 baseline                 16   mate -4    83450     8     True   plies==want
+ CuckooRep true ALONE       12   mate -13   26914     17    False  plies 17 != want 26
+ CuckooRep true ALONE       16   mate -4    113064    8     True   plies==want
+ MateAlphaGuard true ALONE  12   mate -4    31996     8     True   plies==want
+ MateAlphaGuard true ALONE  16   mate -4    48022     8     True   plies==want
```

## Claim 1 — `CuckooRep true` alone makes the mate score WORSE: **CONFIRMED**

| | depth 12 score | vs baseline | vs truth (`-4`) | PV self-consistent? |
|---|---|---|---|---|
| baseline | `mate -9` | — | wrong by 5 moves | no (14 plies, no mate, claims 18) |
| **`CuckooRep true`** | **`mate -13`** | **worse by 4 moves** | **wrong by 9 moves** | no (17 plies, no mate, claims 26) |

`CuckooRep` on its own takes a score that was already wrong and makes it substantially more
pessimistic. It also **reduces** nodes at depth 12 (26,914 against 37,664) — so it looks "cheaper"
while returning a worse answer. That is the most dangerous combination in the whole set: the switch
would appear to be a speed win to anyone measuring nodes.

At depth 16 all three arms converge on the truth, which is consistent with the fault being a
horizon effect (as 15-F11 established) rather than a permanent misevaluation — but a depth-12 answer
is what a game sees most of the time.

## Claim 2 — `MateAlphaGuard` alone FIXES it: **CONFIRMED**

| | depth 12 | depth 16 |
|---|---|---|
| score | **`mate -4` — the truth** | `mate -4` |
| PV | **8 plies, ends in checkmate** | 8 plies, ends in checkmate |
| self-consistent | **yes (plies==want)** | yes |
| nodes | 31,996 | 48,022 |

`MateAlphaGuard true` alone reaches the correct answer at **both** depths, with a PV that is
internally consistent and genuinely ends in mate. It also costs **fewer** nodes at depth 12 than the
baseline (31,996 against 37,664) — the fix is not a speed trade.

## The actionable pair, for the owner

- **KEEP `MateAlphaGuard true`.** It is the switch that makes the mate distance correct, on its own,
  at both depths tested, and it does not cost nodes here.
- **DO NOT enable `CuckooRep true` as a speed measure.** It reduces nodes and worsens the mate
  distance from `-9` to `-13` on this board. Seat 08's 08-F23 found the same worsening independently.

This is a **two-seat confirmation** of both directions: seat 08 (08-C9, 08-F23) and I reached the same
conclusion with separate harnesses, and my numbers here additionally verify against a solver-derived
truth rather than against each other.

## What I did not test, stated plainly

- One board. Both seats used this same S-F19 board, so "MateAlphaGuard is right for every mate" is
  not shown — 15-F18/15-F22 show 28 mate scores with 0 PV violations on G at depths 12 and 14 under
  full PC20, which is consistent but has all five switches on.
- Whether `MateAlphaGuard` costs strength in play. No match was run.
- Whether `CuckooRep` is bad *in general* or only interacts badly with mate scoring. Its node
  reduction is real (19-F32 measured it); what this test shows is that the node reduction must not be
  read as a gain.
