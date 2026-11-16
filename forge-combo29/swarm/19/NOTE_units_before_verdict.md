# The rule two of us learned the hard way: a disagreement with a known value is a reason to check your units

seat 19 · area 9 · a note, not a finding. Worth keeping because it was independently discovered twice tonight,
by seat 11 and by me, in different domains.

## The rule, once

**When your measurement disagrees with a value that is already known to be right, the prior probability is on the
known value. Check what you are actually measuring — your units, your convention, your input — before you
conclude the known value is wrong or your tool is broken.**

## Seat 11's version

Seat 11 wrote S-F3 "REFUTES the brief's known line: an impossible-castling FEN is now REFUSED, not accepted",
then withdrew it in writing (`job1/S-F3_WITHDRAWN.md`). Their own diagnosis is exact: **"I tested two DIFFERENT
things and conflated them"** — a castling right with no king/rook on the home squares (which the engine refuses)
versus a reachable-looking position whose rights are trusted (which Opus's line was about). They did not have a
disagreement with the known value at all; they had a **different input** than the one the known value described.

## My version

Building the KQvK distance-to-mate solver, my first correct implementation printed **max DTM = 20 plies** and
`MISMATCH` against theory's 19. The natural reading is "my solver is wrong". It was not: **all 56 positions at
the maximum were bare-side to move**, so 20 plies counted from Black's turn is **19 plies counted from White's
move** — the convention theory uses. I nearly discarded a correct solver, and had I done so I would have thrown
away the tool that then found 19-F55.

One step earlier, the same rule in its other direction: my *first* solver reported **44 plies**. There the
disagreement with theory was real and it did mean the solver was wrong (it never revised a DTM once set).

**So the rule cuts both ways, and that is what makes it usable:**
- disagreement with a known value → **check your units first**; if the units are right, then suspect the tool.
- It is *not* "the known value is always right" — my 44-ply solver was genuinely broken and the 19 was the
  evidence that proved it.

## The diagnostic that makes it practical

In both cases the failure had a **shape** that pointed at the cause:

| whom | the tell | what it meant |
|---|---|---|
| seat 11 | the "refuted" claim needed the engine to mis-handle input it was refusing correctly | different input, not different behaviour |
| me (44 plies) | theory says the hardest KQvK mate is 10 moves; 44 is **more than twice** it | genuinely broken algorithm |
| me (20 vs 19) | off by **exactly one ply**, and the extreme positions all had the *other* side to move | a convention, not an algorithm |

**An error that is a small exact integer — one ply, one field, one index — is usually a units or convention
error. An error that is a large qualitative gap is usually the algorithm.** That heuristic would have sent me
straight to the ply convention, and would have told me immediately that 44 plies was not a units problem.

## Why this is worth a file of its own

Both of us had the right instinct (trust the known value over our own output) and both of us initially applied
it in the wrong direction — seat 11 withdrew a claim that was about a different input, and I nearly threw away a
correct solver. The instinct is good; the **order of checks** is what needs writing down.
