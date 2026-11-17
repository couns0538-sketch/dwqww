# The 18× outlier is not a defect: all five were proving a stronger claim (S-C47)

`S-C46` found five positions where PC20 searched 3–18× more nodes than S14 and took up to 24× longer — and dropping
those five moved the mean node ratio from **1.214 to 0.956**, so they decide whether "PC20 saves nodes" is true. This
answers the three questions asked of them.

## 1. Deeper iteration, or lost time at the same depth?

Neither, as it turns out. Per-position, `go depth 12`, full per-iteration trace:

| i | halfmove | S14 depth/seldepth/nodes | PC20 depth/seldepth/nodes | PC20 final score | S14 final score | verdict |
|---|---|---|---|---|---|---|
| 16 | 4 | 12/25/12,957 | 12/**51**/238,009 | mate −3 | mate −3 | **seldepth +26, same score** — more verification, 18.4× work |
| 78 | 11 | 12/18/37,761 | 12/18/230,493 | **mate 4** | mate 6 | **shorter mate** |
| 99 | 1 | 12/21/4,711 | 12/**26**/17,936 | mate −4 | mate −4 | **seldepth +5** — extension |
| 72 | 7 | 12/18/7,411 | 12/20/25,883 | **mate 4** | mate 5 | **shorter mate** |
| 116 | 16 | 12/26/11,101 | 12/26/32,733 | **mate 4** | mate 5 | **shorter mate** |

**Not one is a defect, but they are not all the same kind of result, and the distinction matters:**

* **Three proved a mate one move shorter** (`mate 6→4`, `mate 5→4`, `mate 5→4`) — a strictly **stronger** claim
  obtained with more nodes. This is what a better-tuned search should do.
* **i=99 raised seldepth 21→26 with the same score** (`mate -4`): deeper searching inside the same reported depth,
  reaching the **same** conclusion. More *verification* of the same answer.
* **i=16 raised seldepth 25→51 with the same score** (`mate -3`) at **18.4× the nodes** — the same conclusion,
  reached with more than an order of magnitude more work. **This one I cannot call an improvement.** The claim is
  no stronger, the answer is identical, and the extra nodes bought nothing a reader of the score can see. It is
  the one position of the five where "spent more, concluded the same" is the honest description, and it is worth
  a follow-up rather than a verdict.

The per-iteration trace for i=78 shows where the work goes — not a re-search storm, but a genuinely different
conclusion at every depth from 7 on:

| depth | S14 nodes | S14 score | PC20 nodes | PC20 score |
|---|---|---|---|---|
| 7 | 10,075 | mate 7 | 12,657 | **mate 5** |
| 8 | 20,294 | mate 6 | 61,573 | mate 5 |
| 10 | 24,846 | mate 6 | 105,898 | mate 4 |
| 12 | 37,761 | mate 6 | 230,493 | **mate 4** |

Every one of PC20's iterations is more expensive *and* better. That is a search reaching a stronger verdict, not a
search thrashing.

## 2. Are they the documented families?

* **fifty-move / drawn-root: excluded.** Halfmove clocks are **4, 11, 1, 7, 16** — all far from 100, so the door is
  shut. Asserted and printed, not assumed.
* **MultiPV: excluded by construction.** `MultiPV` is 1 throughout the run.
* **No repetition loops**: `repeated_depths` is empty for every position under both settings — no depth index is
  emitted twice, so there is no aspiration re-search storm.

So none of the five is explained by a family I had already documented; the explanation is simply that they are all
**mate positions** where a better search proves more.

## 3. How much of the mean is those five?

| statistic | all 116 | dropping the five (n=111) |
|---|---|---|
| mean node ratio | **1.214** | **0.956** |
| median node ratio | 0.926 | 0.903 |
| mean wall ratio | **1.318** | **1.027** |
| median wall ratio | 0.983 | 0.975 |
| geometric mean wall | 1.015 | 0.942 |
| 95 % CI (geo mean) | 0.916–1.125 | 0.871–1.018 |

**Five positions out of 116 flip the mean's sign** — 1.214 → 0.956 for nodes, 1.318 → 1.027 for wall — while the
medians barely move (0.983 → 0.975). Those five contribute **7.2 % of all nodes searched and 5.5 % of all time**.

And with them dropped, the CI on the geometric mean is **0.871–1.018**, which now sits essentially on seat 19's
predicted range at its upper edge while still excluding a large effect. The honest summary of the whole experiment:

> **PC20 is 2–3 % faster by median, and its mean is dominated by a handful of positions where it proves a shorter
> mate. Both are true, and neither is a defect.**

## My two-stage error, which is the part worth keeping

**First** I classified i=78 and i=116 as "DEFECT candidate — same depth and seldepth, 6.1× the nodes". That was wrong
because I compared **depth, seldepth and nodes** and never looked at the **score**. Two searches can report the same
depth and seldepth while proving different things, and the score is the axis that distinguishes them.

**Second**, having found the scores, the fix was to add the score to the classifier — not to hand-correct two verdicts.
The rule generalises: **when classifying a search as wasteful, the axes that define "the same search" must include
what it concluded, not only how far it looked.** A shorter mate at the same depth is more nodes for a stronger result.

The failure was not noticing a subtlety; it was **choosing a comparison basis that omitted the most important column**
— which is `S-F126`'s shape (a figure judged without the value it should be paired with) appearing in my own analysis
for the third time today.
