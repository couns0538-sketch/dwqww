# CHECK of seat 25's S-F4 — seat 05 (area 5). Also a correction of my own S-F11.

## Verdict: CONFIRMS 25-F4, and REFUTES part of my own S-F11

Seat 25's S-F4: *"The clock-99 zero is a hard-coded draw test firing one ply early, not the damped eval: the break
is exactly at clock 99 (98 scores -112, 99 scores 0 in 399 nodes) ..."* on board
`r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1`.

My own S-F11 said the boundary tracks `counter + search_depth` at ~100 and therefore that their "one ply early" and
my "nine plies early" were the same rule. **Testing on their board shows their claim right and mine over-general.**

### Their numbers, reproduced

| clock | depth 10 | nodes |
|---|---|---|
| 97 | cp -111 | 39,666 |
| 98 | cp -118 | 21,897 |
| 99 | **cp 0** | **341** |
| 100 | cp 0 | 0 |
| 101 | cp 0 | 0 |

Their -112 at clock 98 is -118 here; their 399 nodes at clock 99 is 341 here. Same break at 99, same order of
magnitude on the node count. Different exact values, which I attribute to a different build/settings, and I say so
rather than claiming a byte match.

### The boundary on their board vs mine

| depth | seat 25's board | my K+R vs K |
|---|---|---|
| 4 | 97 | — |
| 6 | 99 | 95 |
| 8 | 99 | 92 |
| 10 | 99 | 91 |
| 12 | 99 | 89 |

Their boundary is **flat at 99**, mine **falls with depth**. So the `counter + depth` law is not general, and my
S-F11 statement that the two observations were "the same rule seen on boards of different mate distance" was wrong.

### The hypothesis I then tested and had to withdraw

I proposed that the difference was "whether the search can reach clock 100" (my bare endgames have no pawns, theirs
has 12). I tested it by stripping every pawn from their board:

| board | d4 | d6 | d8 | d10 |
|---|---|---|---|---|
| seat 25's (12 pawns) | 97 | 99 | 99 | 99 |
| same board, 0 pawns | 100 | 100 | 100 | 100 |

The pawnless board is **constant at 100**, not depth-tracking. **The hypothesis is withdrawn** — removing the pawns
did not reproduce my endgames' behaviour, it pinned the boundary exactly at 100. I have no mechanism and offer none
(I did not read `search.cpp`).

## Corrections made to my own findings
- **S-F11**: scoped to the bare endgames actually tested; the "same rule" sentence is withdrawn.
- **S-F13**: the "material-independent" wording is withdrawn; three bare endgames agree, a middlegame does not.
- **S-F14** (new): the honest summary — the boundary is position-dependent, with three bare endgames at
  counter+depth ~100-101, a middlegame flat at 99, and a pawnless middlegame flat at 100.

## Reproduce
```
python3 check_25f4/check_25f4.py /tmp/build-rel/forge
python3 check_25f4/pawns_test.py /tmp/build-rel/forge
```

## What I did NOT establish
- Any cause. Three different behaviours on four position families is a description, not an explanation.
- Whether the exact break value depends on build options; I used S14 on my release build throughout.
- Whether `EvalRule50Damp`, depth range or `UseNNUE false` change their board's flat-99 result — seat 25 reports
  they do not; I did not re-test those, so that part of 25-F4 is CONFIRMED only as "the break is at 99", not as
  "no option changes it".
