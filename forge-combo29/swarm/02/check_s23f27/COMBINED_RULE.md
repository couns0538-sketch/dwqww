# The combined rule, quantified — and the one place the numbers cannot be combined

The rule under test: **a position is unsafe across budgets if its top-two margin is SMALL and the answer is NOT
FORCED.**

## what the two seats' data actually supports

**Seat 23's changed side** (17 of their 60 positions, gaps measured on both candidates alone at fixed depth 18 —
their raw rows are in `job11/margins.out`, which I read):
- n = 17, gap min **3 cp**, median **14 cp**, max **66 cp**
- **16 of 17 (94 %) are within 30 cp**

**My forced/unforced split at gap ZERO** (4 budgets per board: 5,000 / 20,000 / 50,000 / 200,000):

| kind | boards | changed across budgets | rate |
|---|---|---|---|
| found mate (FORCED, gap 0) | 6 | **0** | **0 %** |
| quiet tie (UNFORCED, gap 0) | 3 | **2** | **67 %** |

**My non-zero small gaps** (S-C10, 6 boards x 2 budgets, gaps 9 / 13 / 15 cp): **3 of 12 cells changed (25 %)**.

## the rule, stated quantitatively and with the honest gap in the evidence
- **Among positions that DID change, 94 % (16 of 17) had a margin within 30 cp** — this is seat 23's figure and it
  is the strongest quantitative half.
- **At an identical zero margin, being forced or not decides the outcome completely: 0 % of forced positions
  changed (0 of 6) against 67 % of unforced ones (2 of 3).** That is my contribution and it is the mechanism.
- **What I CANNOT state:** the converse denominator — "what fraction of unchanged positions were forced or
  large-margin". Seat 23 measured 8 unchanged positions with gap min 11 / median 103 / max 331 cp, but on a
  **different instrument** (best move versus a RANDOM legal alternative, not the top-two gap), and their
  `margins_unchanged.out` holds a Python traceback rather than rows. So their two halves are not on the same
  scale and I will not divide one by the other to produce a clean 2x2. Anyone wanting that denominator needs a
  single run measuring the top-two gap for both changed and unchanged positions on the same instrument.

## so the rule stands as: small margin is necessary, being forced is what makes it safe
**Necessary:** seat 23's 94 % — changed positions are almost always small-margin, so a large margin is a reliable
"safe" signal.
**The exception that completes it:** a forced answer is safe even at zero margin, because a mate in 1 is found at
every budget (0 of 6 changed). A quiet tie at the same zero margin changes two times in three.
**Practical form for a harness:** treat a position as budget-safe only if the answer is FORCED or the margin is
LARGE; a small margin on a quiet position is where budget comparisons break.
