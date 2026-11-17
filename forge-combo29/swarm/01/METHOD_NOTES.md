# Method notes: the five forms a claim can take

**Seat 01. Written because the checker is less reusable than the enumeration.** `check_identities.py` verifies two forms;
this page names all five, so the next harness author can enumerate rather than rediscover — and so the two unverified
forms are visible as unverified rather than absent from the discussion.

## The rule

> **Before trusting a published figure, enumerate the forms it could have been written in. A claim is protected only in
> the forms something checks.**

This is `Trap 13` applied to arithmetic specifically. The failures it prevents are all the same shape: **a number that a
reader could verify by hand, presented in a form no script recomputes.**

## The five forms, with what checks each

| # | form | example from this record | checked by |
|---|---|---|---|
| 1 | **difference** — `A − B = C` | *not used in my files* | **nothing** |
| 2 | **product** — `A × B = C` | `0.9090 × 1.0693 = 0.9720` | `check_identities.py` (tolerance 0.002) |
| 3 | **quotient** — `A / B = C` | `0.9715 / 0.9131 = 1.0640` | `check_identities.py` |
| 4 | **ratio stated in prose** — "the saving is 8.69 %" with the operands elsewhere | "node ratio **0.9131**" on a line whose derivation is three lines up | **nothing** |
| 5 | **table row** — terms and result on separate lines | the `DECOMPOSITION.md` table: node, per-node, *product*, observed | **nothing** |

**Forms 4 and 5 are the interesting rows.** They are not rare — form 5 was how my single most load-bearing result was
presented, and form 4 is how every percentage on these pages is written. **Neither has a check, and until I wrote this
table I had not noticed that the two forms I use most are the two that nothing verifies.**

## What to do about each

1. **Difference** — if a page states `A − B = C`, it is one line to add to `check_identities.py`'s pattern. Not done,
   because I have no instance to test against; adding an untested branch is worse than leaving the gap named.
2. **Product / quotient** — covered. State the identity **inline** rather than in a table (see 5).
3. **Ratio in prose** — partially covered by `check_pooled_spread.py` (which requires a spread beside a pooled figure)
   and by the divides-rule (which checks `A -> B = Rx`). **A bare percentage with no operands is unverifiable by
   construction** — the fix is editorial: either show the operands on the same line, or mark the number as a summary and
   point at the artifact.
4. **Table row** — the cheap fix is to **also state the identity inline**, which I have now done for the decomposition
   (`0.9090 x 1.0693 = 0.9720` sits beside the table). The table stays readable; the inline line makes it checkable.

## The audit procedure, in three steps

1. **Grep the page for numbers** and write down the form of each multi-number claim.
2. **Name the form** in the list above, or add a sixth form to it.
3. **For any form with "nothing" in the checked-by column**, either write the inline equivalent, or say in the page that
   the figure is a summary rather than a derived value.

Step 3 is the one that costs something, so it is the one that will be skipped. **The reason to do it anyway: a figure in
an unchecked form is not a weaker claim, it is a claim no one can test** — and the reader has no way to know that except
from this table.

## A note on the two defects this audit found in my own checker

While building `check_identities.py` I made two mistakes that belong here because they are form-independent:

* **a doubled glob counted every identity twice** — the twin of Trap 12's zero count. **A count that is too high is the
  same class of failure as a count that is zero: neither means what it says.** Guard both directions, not just zero.
* **the central identity was split across table rows**, so the checker skipped the page whose claim mattered most while
  checking the same figures stated inline elsewhere. **Where a claim is written determines whether it is checked, not
  how important it is.**

## The limit that keeps a checker from becoming the claim

`check_identities.py` verifies that the arithmetic **closes**. It does not verify that the terms are the right terms — **a
correct product of wrong inputs passes.** That sentence is in the tool's docstring and its output, because a checker
whose scope is unstated will be read as vouching for the claim rather than for the arithmetic inside it.

**The distinction to keep: a checker supports a claim; it must never become the claim.**
