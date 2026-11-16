# REPORT — seat 07, job 44: settling the budget ordering over all 353 positions

## What was asked / the answer / how sure

**Asked:** (cycle work) my 07-C42 checked seat 10's 10-F53 on a disjoint 100-position sample and found
the budget ordering reversed. Two samples then disagreed about which budget is safest, so the useful
next step was to settle it rather than leave two orderings in conflict.

**Answer:** **there is no ordering.** Over all 353 positions the two budgets disagree with the match
budget on essentially the same positions — 70 versus 69, of which **59 are the same positions** —
so neither is safer. Both 100-position orderings were noise.

**How sure:** very high, and this is the one case tonight where I can say settled rather than
"at this sample". The paired analysis (McNemar) is the decisive instrument, because the counts come
from the *same* positions rather than two independent samples.

## The measurement

PC r15 under PC20, Threads 1, Hash 16, fresh process per cell, the owner's three budgets
(`go softnodes 20000`, `go nodes 50000`, `go nodes 250000`), all **353** G positions.

| measure | value |
|---|---|
| all three budgets agree | **273/353 = 77 %** |
| any disagreement | **80/353 = 22.7 %** |
| `softnodes 20000` vs `nodes 250000` differ | **70** |
| `nodes 50000` vs `nodes 250000` differ | **69** |
| disagreements shared by BOTH small budgets | **59** |
| unique to 20000 / unique to 50000 | **11 / 10** |
| McNemar χ² (1 df) | **≈ 0.00, p ≈ 1.00** |

Raw: job44/raw/check_10f53.json, job44/all353.log.

## Why the paired analysis is the right test here

These are not two independent samples — every position contributes to both counts. So the question is
not "are 70 and 69 different rates" but "**do the two budgets fail on the same positions?**" The answer
is yes: 59 of the ~70 are the same positions, and the discordant counts are 11 against 10.

That is what makes the result strong. A rate difference of one position in 353 could be argued about;
the fact that the two budgets fail on **the same trees** cannot.

## What this does to the 10-F54 recommendation

| sample | `20000` vs `250000` | `50000` vs `250000` | implied conclusion |
|---|---|---|---|
| seat 10, first 100 | 17 | **8** | 50000 is 2.1× safer → recommend it |
| this seat, last 100 | 18 | **22** | 50000 is worse |
| **all 353** | **70** | **69** (59 shared) | **no difference** |

Both 100-position orderings were noise, and they were noise **in opposite directions** — which is
precisely why 07-C42 refused to call seat 10 wrong. The full set shows both were sampling artefacts.

**The defensible statement for the owner:** both small budgets differ from the match budget on about
one position in five (22.7 %), and **choosing between 20000 and 50000 on node-count evidence is not
supported** — they fail on the same positions. If a single budget must be chosen, the argument has to
come from something else (time cost, or a strength match), not from these rates.

## Findings

**07-C43** in FINDINGS.md; it supersedes 07-C42's ordering claim (which was itself a correction of
10-F54) while keeping 07-C42's confirmation that budgets do change moves.

## Suspicions, not proven

- That the 59 shared failures are the positions where the search is simply unfinished at both small
  budgets, i.e. the budgets are both "too small" rather than differently wrong. Consistent with the
  data; not tested.

## What I did NOT do

- Did not test a budget between 50000 and 250000 (e.g. 100000) to find where failures stop being
  shared. That would be the natural next question.
- Did not examine the 21 discordant positions individually.

## Why I am not reporting a damage figure at all

This deserves its own heading rather than a footnote, because a "damage" number is the single most
quotable output of a budget study and the easiest to get wrong.

Seat 10 reported that on 2 of their 100 positions the small budget's move is **≥200 cp worse by the
engine's own evaluation at the large budget** — a real, disciplined figure. **I am not reporting the
equivalent, and the reason is not caution for its own sake:**

1. My run re-scored the disagreeing positions **generically** (each distinct budget-chosen move
   searched at `nodes 250000`), not with seat 10's per-move discipline of scoring *the specific move the
   small budget chose* against *the large budget's own choice* under identical conditions.
2. The largest score gap I saw was **95,212 cp**, which is not a centipawn quantity at all — it is a
   mate score collapsed into my `cp` conversion, i.e. a distance artefact. Ranking by that number would
   put artefacts at the top of a damage table.
3. A damage figure derived that way would look authoritative and be wrong, which is worse than no figure.

So the report gives the **disagreement rate** (22.7 %, with 59 of 70 shared between budgets) and stops
there. Anyone wanting damage must re-score per move the way seat 10 did; their 2-of-100 figure stands as
the only disciplined measurement of it I have seen, and nothing in my run contradicts it.

## What I am NOT sure about

- Whether the 80 disagreements include large-damage cases. My generic re-scoring cannot tell a blunder
  from a mate-distance artefact, which is exactly why no damage figure is claimed above.

## Times

See job44/stamps.txt.
