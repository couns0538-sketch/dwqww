# The "why" casualties — counted, with what each got wrong — seat 08

The coordinator asked for the list rather than the word "five or six". Here it is. **Six claims about WHY something
happened, every one of which I formed by reasoning or looking rather than measuring, and every one of which failed or
needed correction.** Each is recorded in `FINDINGS.md`; the id is given so it can be checked.

| # | the claim I made | what it got wrong | how it was caught | id |
|---|---|---|---|---|
| 1 | "one iteration at depth 19 costs ~350-460 ms at the owner's clock" | that was the **whole search ladder**, not one iteration. The iteration itself costs **157 ms** (393.2 − 235.8 measured per depth) | I measured the per-depth timing curve instead of inferring it | 08-F24 correction |
| 2 | "`movetime 50` stops at 50 minus overhead because the deadline is checked inside the search" — as an explanation of a *median* | the **median** is the plan; the **kept iteration** is 1–69 ms early. Two different quantities, and seat 16's REFUTES was about the one I had not named | ran both measures on the same search | 08-F2 restatement, 08-F10 |
| 3 | "the tail is driven by few pieces AND few moves" | on 15 sourced boards per class the spread is **1.8x not 5.3x**, and "few pieces + few moves" is the **fastest** median. Piece count drives it; move count does not | repeated the classification on sourced boards | 08-F33 |
| 4 | "the 37 % mate-appearing rate is because my first sparse set was nearer to mate" | **refuted in the opposite direction**: 17 % on near-mate boards, 26 % on not-near-mate. The composition difference is real, the causal story is not | classified every board by nearness-to-mate with an independent deep search | 08-F32 |
| 5 | "several of the 11 divergences turn a probing move into a waiting move" | only **2 of 11**; **8 of 11 have both moves waiting** and 1 reverses | classified all 11 with a python-chess PROBING/WAITING test | 08-W2 |
| 6 | "a move-ordering effect of the bare-king switches explains the both-waiting pattern" | ordering is **eliminated**: the pattern is 8/9/8 of 11 across V0/V1/V2, and the actual cause is `BARE_KING_LMR_CAP` alone (11 of 11) | built and ran the two switch variants | 08-F37 |

## The count, precisely
**Six claims, all about mechanism, all wrong or incomplete, all caught by measurement.** Plus, separately, the
arithmetic/scale slips where the number itself was wrong rather than the story: the 72/360 vs 117/585 regime
confusion, the mate-to-30000 mapping, and two false positives from my own static analyser (08-N4). Those are a
different failure — the claim's *form* was right and its *value* was wrong — and they are counted where they belong.

## What the list shows that the rule alone does not
- Every single one was **plausible when I said it.** That is the defining property: a wrong "what" looks wrong (a
  number is visibly off), but a wrong "why" is *constructed* to fit the evidence I already had, so it survives
  every check except a test designed to break it.
- Five of the six were **my own correction of an earlier claim of mine** — the pattern is not "I was wrong once", it
  is "each time I explained a correction, the explanation was the next thing to be wrong". Items 3, 4, 5 and 6 are
  all second-order: I fixed a measurement, then mis-explained the fix.
- The two that produced something useful (items 4 and 6) did so **because the test killed them**: 08-F32's
  refutation left the composition finding standing as a separate fact, and 08-F37's ordering kill produced the
  switch-level attribution.

## So the rule, with its evidence
**A claim about WHY needs a test designed to kill it; a claim about WHAT needs only a measurement.** The six-item
list is why I believe that rather than merely assert it — and the fact that four of the six were explanations of my
own earlier corrections is what makes the rule worth carrying beyond this seat.
