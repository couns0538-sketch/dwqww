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

## The gap I flagged, now tested: no option or depth escapes the clock-99 zero

`options_test.py`, seat 25's board at clock 99, depth 10, one setting changed at a time:

| case | score | nodes |
|---|---|---|
| S14 baseline | cp 0 | 341 |
| EvalRule50Damp **true** | cp 0 | 336 |
| EvalRule50Damp **false** | cp 0 | 341 |
| UseNNUE false | cp 0 | 706 |
| Hash 1 | cp 0 | 341 |
| Hash 1024 | cp 0 | 341 |
| Threads 4 | cp 0 | 1,292 |

And across depth 1 → 20 the score stays `cp 0` while nodes climb only 30 → 2,073 (a real depth-10 search on this
board costs ~20,000 nodes, see the control below).

**Control:** the same board at clock **0** searches normally — `cp -164`, **19,621 nodes**. So the zero is caused by
the clock value and not by the board being unsearchable.

That turns the part of 25-F4 I had listed as un-re-tested into a measured confirmation: `EvalRule50Damp`, `UseNNUE`,
Hash and Threads all leave the zero intact, and so does every depth from 1 to 20.

### One thing this does NOT show
The node counts are not zero (341 at depth 10, rising with depth). So the clock-99 zero is **not** the same shortcut as
the clock-100 one, which answers `0 nodes` and an empty pv (`../job3/`, `job1b`). Two different mechanisms, and I do
not name either.

## ASan + UBSan repeat

The whole table was re-run on the ASan+UBSan build (`raw/options_test_asan.txt`): every setting still gives
`cp 0` at clock 99, depths 1–20 still give `cp 0` (nodes 30–2,073), and the clock-0 control is identical
(`cp -164`, 19,621 nodes). The only difference is Threads 4 giving 1,342 nodes instead of 1,292, which is what real
threading does and is not a determinism problem for the single-threaded rows.

The run produced **no sanitizer output**. As in `../check_15f3/RESULT.md`, I do not call that "0 sanitizer lines
proven": this script carries neither of the two proofs the brief requires (no `nm` count in its `.meta`, no planted
fault through this script). Those proofs exist for the job3 runner (`../job3/out_planted/`). The honest phrasing is
"the ASan+UBSan build produced no sanitizer output in these 13 searches".
