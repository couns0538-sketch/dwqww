# DIVIDE-CHECK CONTROL — seat 13: proves my move-by-move check catches a compensating error

## Why this file exists
Seat 06's S-F22 makes a point that invalidates a whole class of checks: **a total node count can be
exactly right while the per-root-move counts are wrong**, if one move is over-counted and another
under-counted by the same amount. Any symmetry or correctness check that compares TOTALS ONLY is
measuring the wrong thing and will pass such an error.

My job 2 result claims 0 differences partly on a perft-2 divide comparison, not on totals. This
control proves that comparison would actually catch a compensating error — otherwise the claim
rests on a checker that could not fail.

## What I did
`divide_control.py`, on a real position from my job 2 set:
`rnbqk1n1/2pp1pp1/4N2r/bp6/p1NPp1p1/2P3P/P4PB1/R3KQ1R` (as recorded in `special500.tsv` row 0;
39 root moves).

1. **Part A** — compare the engine's real perft-2 divide to python-chess: missing = none, extra =
   none, wrong = none, totals equal. PASS.
2. **Part B** — plant a compensating error by hand in the engine's output: `+1` to `a4a3` and `-1`
   to `a5b4`, chosen so the **total is unchanged**.

## Result

```
B) COMPENSATING error planted: a4a3 +1, a5b4 -1
   total unchanged? True (1265 vs 1265)
   divide check sees: wrong moves = ['a5b4', 'a4a3']
   RESULT: CAUGHT by the divide check
```

The total stayed at 1,265, so a totals-only check would have reported PASS. The divide comparison
reported both wrong moves. That is the property S-F22 says a check must have, demonstrated on my
own checker rather than assumed.

## What this does and does not establish
- **Establishes:** my perft-2 divide comparison is sensitive to per-root-move errors even when
  totals agree, so my job 2 claim ("same root-move set, same count for every root move") is a real
  measurement and not a totals comparison in disguise.
- **Does not establish:** anything about depth > 2 at the divide level. My perft 3/4/5 comparisons
  compare TOTALS only. Per S-F22's reasoning, a compensating error at depth 3+ that cancels in the
  total would not be caught by those. I state this as a limitation of my job 1/1b/3 results rather
  than pretending the totals comparison is equivalent to a divide comparison.
- **Does not establish:** that a compensating error is likely. I am not claiming the engine has one;
  I am bounding what my evidence can see.

## Honesty note
This control was written after my results, not before, and I say so. It tests my checker, not the
engine. It changes no number in any of my reports; it upgrades the confidence I place in the job 2
divide claim and lowers the confidence I place in the totals-only claims, which is the honest
direction for it to move.
