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
| 2 | **product** — `A × B = C` | `0.8761 × 1.0693 = 0.9368` | `check_identities.py` (tolerance 0.002) |
| 3 | **quotient** — `A / B = C` | `0.9715 / 0.9131 = 1.0640` | `check_identities.py` |
| 4 | **ratio in prose** — split into two sub-forms | `0.8761 (12.39 % fewer nodes)` vs "the saving is 8.69 %" with operands elsewhere | **same-parenthetical form: `check_ratio_percent.py`**; operands-elsewhere form: **nothing** |
| 5 | **table row** — terms and result on separate lines | the `DECOMPOSITION.md` table: node, per-node, *product*, observed | **`check_table_identities.py`, product rows only** |

**Form 4 is the remaining gap; form 5 is now half-closed.** They are not rare — form 5 was how my single most load-bearing result was
presented, and form 4 is how every percentage on these pages is written. **When I first wrote this table, neither had a check** — and I had not noticed that the two forms I use most were
the two nothing verified.

## What to do about each

1. **Difference** — if a page states `A − B = C`, it is one line to add to `check_identities.py`'s pattern. Not done,
   because I have no instance to test against; adding an untested branch is worse than leaving the gap named.
2. **Product / quotient** — covered. State the identity **inline** rather than in a table (see 5).
3. **Ratio in prose** — partially covered by `check_pooled_spread.py` (which requires a spread beside a pooled figure)
   and by the divides-rule (which checks `A -> B = Rx`). **A bare percentage with no operands is unverifiable by
   construction** — the fix is editorial: either show the operands on the same line, or mark the number as a summary and
   point at the artifact.
4. **Table row** — the cheap fix is to **also state the identity inline**, which I have now done for the decomposition
   (`0.8761 x 1.0693 = 0.9368` sits beside the table). The table stays readable; the inline line makes it checkable.

## Form 4 was attempted, abandoned, and then rebuilt — the abandonment was wrong

I first wrote that prose-ratio checking could not be fixed cheaply and deleted the tool. **That was too strong, and the
correction matters because the broad version caught a real error in my own headline** (`0.9090` with `12.4 % fewer`,
where 1 − 0.9090 = 9.10 %). Abandoning the class would have discarded the one instrument that worked.

**What separates the true positive from the false ones is grammatical form, not tolerance.** A ratio and its percentage
inside **one parenthetical** is an identity claim; the three false-positive mechanisms are all excluded by requiring that
adjacency:

| the broad checker read this as an identity | why it is not one |
|---|---|
| `92.7 %` beside a node count of `92.7` | the count is not a ratio |
| `1.079–1.092× — 7.9–9.2 % dearer` | a range has no single percentage |
| `0.530 us -> 0.578 us = 1.09x (9 % dearer)` | the first decimal is not the ratio |

**`check_ratio_percent.py` matches only `ratio (percent direction)`**, strips quoted regions first, and examines 6 claims
across the pages. Proven by restoring the fabricated pair into `DECOMPOSITION.md`: it reports
`ratio 0.9090 with 'fewer' implies 9.10 %, but the line says 12.40 %` and exits 1; corrected, exit 0.

**So the honest split of form 4 is:**

* **same-parenthetical** — checked, and this is where my real error lived;
* **operands elsewhere on the page** — still unchecked, because deciding which number is the ratio is how a checker
  invents an identity (`S-F159`).

**The lesson is not "prose cannot be checked". It is "prose can be checked where the grammar states the relation".** My
first attempt inferred the relation from proximity; the second read it from the punctuation.

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
