# CORRECTED: it is `TtPruneV2`, not `HistRework` — and my own row said so (08-W6)

Seat 27 read my 08-F43 back to me: **my own table row says "PC20 − HistRework = 389 (unchanged)", which refutes my
claim that "389 requires HistRework".** It is right, and it is the third time tonight a correct table was read
backwards — twice by me.

## The corrected attribution, now measured in BOTH directions

**Add-one from the S14 baseline** — the direction I did not test, which is the one that can see a redundant option:

| arm | result |
|---|---|
| S14 baseline | d2d4, **505** |
| **S14 + TtPruneV2 alone** | d2d4, **397** (108 nodes fewer) |
| S14 + HistRework alone | d2d4, **505** (no effect) |
| S14 + CuckooRep alone | d2d4, 501 |
| S14 + CorrHistV2 alone | d2d4, 505 (no effect) |
| S14 + MateAlphaGuard alone | d2d4, 505 (no effect) |

**Drop-one from PC20** — my original direction:

| arm | result |
|---|---|
| PC20 | d2d4, **389** |
| PC20 − HistRework | d2d4, **389** (no effect) |
| PC20 − TtPruneV2 | d2d4, **501** (112 nodes more) |

**HistRework at every level alone, on the S14 baseline:** level 0 → 505, 1 → 505, 2 → 505, 3 → **504**. Inert.

## The corrected statement
**`TtPruneV2` accounts for the node-count change: from the S14 baseline it takes 505 → 397 (108 of the 116 nodes,
93 %), and dropping it from PC20 returns 501.** `HistRework` is **inert at every level (0–3) alone**, and has no
effect inside the bundle. `CuckooRep` alone moves it slightly (505 → 501) but is not the main cause.

**93 % attributable to one option** — seat 27's figure, confirmed here from the other direction. So the number is not a
property of "PC20" as a bundle, and it is not HistRework; it is TtPruneV2 with a small CuckooRep component.

## The method point, which is the actual finding
**A drop-one ablation tests NECESSITY inside the bundle; an add-one ablation tests SUFFICIENCY from the baseline.**
My design could only see options whose removal changes the outcome, so it was blind to a redundant option — and
HistRework, being inert alone and inert in the bundle, looked "required" to me only because I read "unchanged when
removed" as confirmation instead of refutation.

Seat 27's review question is the fix, and it goes into my method lines:

> **Before looking at the numbers, state for each row whether "unchanged" supports or refutes the hypothesis.**

In a drop-one table, "unchanged when removed" **refutes** necessity. I had written exactly that row and read it as
support.

## Why this is the fifth in the same family
My withdrawals are now W1..W6, and every one is a label or a reading rather than a measurement:

| id | what failed |
|---|---|
| W1 | a wrong interpretation (fifty-move "defect") |
| W2 | an eyeballed inference (probing→waiting) |
| W3 | a trusted variable NAME (S14 that held PC20) |
| W4 | a column heading I wrote (identical work) |
| W5 | that label propagating into the coordinator's arbitration |
| **W6** | **a correct row read backwards (unchanged = confirmation)** |

**The measurement in each case was right.** That is the pattern, now five or six deep, and it is why the rules in this
file are about reading rather than about measuring.

## Show it again

    # the six add-one arms and three drop-one arms are the tables above; reproduce with
    # S14 baseline, S14+<one switch>, PC20, PC20-<one switch>, on the threefold move list, go depth 4
