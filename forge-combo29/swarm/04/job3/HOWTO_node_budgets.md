# How to set `go nodes` budgets for the owner's matches — one page

**The short answer: compute the budget per position. There is no round number and no per-family number
that works, and both of those were measured, not assumed.**

## Why

`go nodes N` does not stop *at* N. It finishes the iteration it is in and reports the last **completed**
iteration, so the work actually done is the node count at the end of some iteration — an *iteration
boundary*. Those boundaries differ a lot between positions:

| what was measured | result |
|---|---|
| boundaries at/above 20,000, ten unrelated openings (set O) | 20,283 – 38,996 (median 22,612), **1.92x spread** |
| boundaries at/above 50,000, same ten openings | 53,570 – 173,222 (median 62,455), **3.23x spread** |
| boundaries at/above 20,000, ten positions each from THREE opening families | worst family **2.02x**, all 30 together 2.04x |
| sending B = 20,000 at target 20,000 | **0 of 10** positions get full work; each loses a whole iteration, 18%–65% of its work |
| sending B = 22,000 / 30,000 / 39,000 | 5 / 9 / 10 of 10 full, but up to 88% over-search on the fast positions |

Grouping by opening family does **not** help: a family's own spread (1.76x–2.02x) is as wide as the spread
across unrelated openings (2.04x). So the budget has to be per position.

## The exact rule, verified

Budget equal to a boundary uses 100% of itself; budget one node below it drops a whole iteration:

```
budget 19,831 -> work  9,155   (0.46x, the depth-10 iteration)
budget 19,832 -> work 19,832   (1.00x, depth 11)
budget 31,778 -> work 19,832   (0.62x)
budget 31,779 -> work 31,779   (1.00x, depth 12)
```

## Procedure (three steps)

**1. Read the boundaries for one position.** Start the engine, set it up exactly as a match does, and send
`go depth D` with D well above the depth the budget will buy (D = 20 is plenty for a 20k budget). The
`nodes` field of each `info depth k` line IS the boundary of iteration k:

```
printf 'uci\nsetoption name Hash value 16\nsetoption name Threads value 1\nisready\nucinewgame\nisready\nposition fen <FEN>\nisready\ngo depth 20\nquit\n' | ./forge
```

Read the last `info depth k ... nodes N` line for each k. Those N are the boundaries.

**2. Pick the boundary nearest your target — at or above it.** If the target is 20,000 and the boundaries
include 19,832 and 31,779, send **31,779** (the smallest boundary >= target). Sending 19,832 would give you
less work than you asked for; sending 20,000 would give you 19,832 and waste the difference.

**3. Feed that number into the match script** as the `go nodes` argument for that position.

## The script that already does this

`forge-combo29/swarm/04/job3/boundaries.py` — for one position, prints every boundary, checks two runs
agree, and prints the budget to send for each boundary:

```
python3 forge-combo29/swarm/04/job3/boundaries.py ./forge /tmp/bnd mypos \
    --settings pc20 --depth 20 --fen '<FEN>'
```

`forge-combo29/swarm/04/job3/boundary_spread.py` — the same over a list of positions, and it prints what a
single round number would cost, which is how the table above was produced:

```
python3 forge-combo29/swarm/04/job3/boundary_spread.py ./forge /tmp/bspread \
    --positions O.fens --depth 20 --target 20000 --limit 10
```

`forge-combo29/swarm/04/job3/family_spread.py` — the within-family test:

```
python3 forge-combo29/swarm/04/job3/family_spread.py ./forge /tmp/fam \
    --positions families.txt --target 20000 --depth 20
```

All three are deterministic (boundaries reproduced 2/2 runs on both positions tested) and all three abort
with a non-zero exit rather than print a number they did not measure.

## If he wants to skip step 1 anyway

Then the honest expectation is: a fixed budget either starves most positions by a whole iteration (up to
65% of their work, at B = 20,000: ten of ten positions) or over-searches the fast ones by up to 88% (at
B = 39,000). There is no middle setting that is close everywhere, because the boundaries themselves differ
by 2x at a 20k target and 3.2x at a 50k target.

## Caveat

Every number here is on the **PC build (r15) under PC20, Threads 1, Hash 16**, on this 4-core machine. If
the owner's PC has different cores or a different net file, the boundaries are different numbers — but the
procedure is the same, and the three scripts measure whatever build they are pointed at.
