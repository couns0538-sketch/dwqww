# REPORT — seat 07, job 45: do both small budgets fail because both are simply too small?

## What was asked / the answer / how sure

**Asked:** (cycle work, following 07-C43) 59 of ~70 budget disagreements were shared between
`softnodes 20000` and `nodes 50000`, which suggested both are simply "too small". The test is an
intermediate budget: if its failures are a subset of theirs, the "too small" account holds.

**Answer:** **it holds.** Disagreements with `nodes 250000` fall **22 → 20 → 8** as the budget rises
(20000 → 50000 → 100000), and **5 of the 8 remaining are shared** with the small budgets. My script's
automated verdict said the opposite, and **that verdict was wrong** — it compared moves instead of
scores. Scoring the disputed positions withdrew the alternative account entirely.

**How sure:** high after the score check; the automated verdict alone would have been wrong.

## The measurement

PC r15 under PC20, Threads 1, Hash 16, fresh process per cell, 120 G positions, four budgets.

| budget compared with `nodes 250000` | positions disagreeing |
|---|---|
| `softnodes 20000` | 22 |
| `nodes 50000` | 20 |
| `nodes 100000` | **8** |

    n100 failures that are also n20 failures: 5
    n100 failures that are also n50 failures: 5
    n100 failures on positions NEITHER small budget fails: 3
    n20 failures that n100 fixes: 17

The count falling monotonically with budget, plus 17 of the 20-budget's failures disappearing at
100000, is what "too small" looks like.

## The mistake I made and corrected

My script printed:

    RESULT: the intermediate budget fails on positions the small budgets do not ->
            the budgets fail for different reasons, not just depth.

That was derived from **move inequality** alone. Checking the three disputed positions by scoring both
candidate moves at `nodes 250000`:

| # | n100 move | n250 move | scored at 250000 | reading |
|---|---|---|---|---|
| 15 | `c6b5` | `h6h5` | **mate −12** vs **cp −2196** | two different losses, not a blunder |
| 94 | `g6f4` | `f5f4` | **cp 348** vs **cp 315** | the **100k** move is better |
| 118 | `b7b5` | `g7f6` | cp 26 vs **cp 91** | 250k better by 65 cp |

**None is a regression.** #94 actually favours the 100000 budget; #15 compares a mate score with a
centipawn score in a lost position, which is not a comparison at all; #118 is a 65 cp preference.

So the "different mechanisms" reading is withdrawn. The data support 07-C43's simpler account: **the
budgets fail on shared trees, and a bigger budget fails on fewer of them.**

This is the same class of error as my earlier ones — a verdict derived from a proxy (move inequality)
that the real quantity (score) does not support — and it was caught only because I scored the disputed
positions instead of trusting the script's summary line.

## Findings

**07-C44** in FINDINGS.md.

## Suspicions, not proven

- That failures keep falling past 100000 until they reach 0 at some large budget. My data stops at
  250000 (by definition the reference), so I cannot say whether 250000 itself is "enough".

## What I did NOT do

- Did not run all 353 positions at four budgets (cost); this is 120.
- Did not test budgets above 250000, since 250000 is the owner's largest and serves as the reference.

## What I am NOT sure about

- Whether the 8 remaining n100 failures are the same kind of tree as the shared ones or a different
  species that happens to be small in number. 8 is too few to characterise.

## Times

See job45/stamps.txt.
