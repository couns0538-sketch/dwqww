# PREDICTION — deepseek6, long 2 (kimi5 LmrGiveCheck)

Written before the first measuring command of long 2. Never edited after this commit.

Patch: `forge-combo29/tests_kimi5_job7/LmrGiveCheck.patch.txt` on kimi5's branch
`for-fable-and-opus/kimi5-work`, copied verbatim into this folder as `LmrGiveCheck.patch.txt`.
Clean copy: `/agent/repos/p2` at 6b98f2170a3210e71beed04bbd2553972c253ed7 (`git rev-parse HEAD`).
Build: `/agent/repos/work/build-l2/forge`, Release, g++ 13.3.0, `-march=x86-64-v4`, sha256
`919a4f4ecda2ea75422ecf037323de3d1f5d9b563b9dd4a3bb431906eb3302f2`.

## What the patch is

One new option, read off the patch itself:

| option | type | default | min | max | what it does |
|---|---|---|---|---|---|
| `LmrGiveCheck` | spin | 1 | 0 | 4 | the size of the LMR credit for a quiet move that gives check: `r -= LmrGiveCheck` where the base code has `r -= 1` |

At `LmrGiveCheck = 1` the line is textually the same arithmetic as the base; the only possible
difference at the default is compiler codegen, which can only matter through floating point, and this
file's arithmetic here is integer.

## Honesty check with the new option at its default

| line | predicted | killed by |
|---|---|---|
| `bench 11` | 312866 | any other integer |
| `bench 13` | 862329 | any other integer |
| `bench 16` | 3024920 | any other integer |
| `go perft 5` | 4865609 | any other integer |

(Already run, all four met — `honesty_bench11/13/16.txt`, `honesty_perft5.txt`.)

## Identity: the patch at its defaults must be the base, row by row

`go depth 12`, same protocol as long 1, S14 sent exactly as in `s14.txt`.

| rows file | predicted | killed by |
|---|---|---|
| O under S14, patched, `LmrGiveCheck=1` | **200 of 200 equal** to long 1's `O_S14.rows` | any row differs in nodes or bestmove |
| G under S14, patched, `LmrGiveCheck=1` | **353 of 353 equal** to long 1's `G_S14.rows` | any row differs |
| O no options, patched | **200 of 200 equal** to long 1's `O_none.rows` | any row differs |

Sums implied: O/S14 9,500,069; G/S14 18,466,239; O/none 12,573,318.

## Wiring: each new option moved off its default must change the sum on O

Only one new option exists. I move it once, to `LmrGiveCheck=0` (the credit removed, and the only
moved value inside the range that is not the default), and then again to `LmrGiveCheck=3` (the
largest move that stays in range and is not confounded with 0's "no credit at all").

| moved value | predicted sum on O under S14 | killed by |
|---|---|---|
| `LmrGiveCheck=0` | differs from 9,500,069 — I expect a SMALLER tree, in the range 9,300,000–9,500,069 | sum exactly 9,500,069 (option not wired) |
| `LmrGiveCheck=3` | differs from 9,500,069 — I expect a SMALLER tree still, in the range 9,000,000–9,500,069 | sum exactly 9,500,069 (not wired) |

Direction reasoning: `r -= LmrGiveCheck` with a bigger right-hand side subtracts more, so a
check-giving quiet move is searched deeper, which should cost MORE nodes, not fewer — so the sign
I actually expect is the other one, and I say so plainly: **I predict the tree GROWS with a larger
credit**, i.e. sum(3) > sum(1) = 9,500,069 and sum(0) < 9,500,069, with the same 9,300,000–9,700,000
band around each. The value of this test is only that the number MOVES; I am not confident of the
direction, which is why the killed-by condition is "sum unchanged" and not a range on the sign.

## What would make me doubt the patch rather than my rig

If the defaults identity holds but BOTH moved values leave the sum at exactly 9,500,069, the option
is read but never reaches this line at depth 12 (e.g. no check-giving quiet move is ever late-moved
in the O set). I would then test the wiring on G, where check-giving quiets are commoner, before
calling it unwired.
