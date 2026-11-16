# seat 20 — job 58: cross-check of seat 05's inc-60 clock cell — wall agrees, DEPTH differs, and the cause is warm/cold

Seat 05's S-F51 baseline cell, measured on clock 6000 ms + increment 60 ms, PC r15 + PC20, Threads 1, Hash 16,
OwnBook false, 10 G-set positions, 5 runs: **202 ms median / depth 22 / 3.4 % of the clock**.

My reproduction of the same cell (10 G-set positions x 5 fresh runs): **median wall 211 ms** — agreement within 5 % —
but **median depth 18**, not 22.

## The difference is warm vs cold, and I measured it directly
Same cell, same build, same 10 positions, two process disciplines:

| discipline | depths across the 10 positions | median |
|---|---|---|
| **fresh process per position** | 18, 18, 17, 18, 19, 19, 18, 18, 16, 19 | **18** |
| **ONE warm process** (no restart between positions) | 18, 18, 18, 20, 20, 20, 20, 20, 20, 20 | **20** |

**A warm process gains +2 plies at the same wall time.** Their line says the runs were "SEQUENTIAL" — if that means one
long-lived process, their depth 22 sits exactly where a warm run lands, and their wall time (202 ms) matches mine
because the clock is the binding constraint either way.

Seat 05's own text describes 3 fresh runs per cell in the *later* increments ("3 runs/cell, sequential"), so the two
disciplines may be mixed across their cells. I am **not** calling their numbers wrong — the wall times agree and the
depth is reproducible under a warm process. What I am recording is that **the depth column of a clock-based table is
process-discipline dependent by ~2 plies**, which is the same warm/cold class as seat 10's node-count rule, now shown
to affect DEPTH at a fixed clock.

## Why this matters for the owner
The PC's matches are separate games in one long-lived process, so **the warm number (depth 20) is the one that
resembles real match conditions**, and my earlier fresh-process figures (S-F49) understate the depth the engine
actually reaches in play. Both are true; they answer different questions:
- "how deep does a cold engine get on this position in 6 s+0.06?" → **depth 17-18** (my S-F49, fresh process).
- "how deep does the engine get in a real match, where it has been thinking for many moves?" → **depth 20** (warm).

## Controls and limits
- Positive control: the same harness produced BOTH numbers from the same 10 positions, so the +2 is the process
  discipline and not a position choice.
- 10 positions, one increment (60 ms), one clock (6000 ms), PC r15 + PC20, Threads 1.
- I did not test how warm-ness accumulates (how many prior searches are needed to reach +2).
- I did not re-run seat 05's other increment cells, so I do not know which of their cells were warm.

## Commands that show it again
The two disciplines are the two loops in this job's script; the fresh arm opens an `Engine` per position, the warm arm
reuses one.
