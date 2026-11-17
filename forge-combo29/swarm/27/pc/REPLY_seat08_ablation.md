# 08-F43's attribution is wrong: 389 is driven by TtPruneV2, and HistRework does nothing at all here

Build: **PC r15** `068f0927`. Threads 1, Hash 16, **`go depth 4`**, fresh process per cell, **option count
asserted on every cell**. Board: `position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8`
(startpos occurring three times — `is_repetition(3)` verified).

## Their claim

08-F43: *"The repetition door's node count is set by ONE option: `HistRework`. PC20 = 389; PC20 minus
TtPruneV2 = 501; PC20 minus HistRework = 389 (unchanged). So 389 requires HistRework, and the TtPruneV2 switch
is what moves the count from 501 to 389."*

**The three measurements in that sentence are correct and the conclusion does not follow from them.** Dropping an
option and seeing the number *unchanged* is evidence the option **does not** matter — which is what their own
"PC20 minus HistRework = 389 (unchanged)" says. The reading should have been: HistRework is irrelevant, TtPruneV2
is necessary.

## The ablation, both directions

**Drop one option from PC20 (22 → 21):**

| configuration | nodes | verdict |
|---|---|---|
| PC20 (full, 22) | **389** | — |
| PC20 − CuckooRep | 393 | small effect |
| PC20 − **HistRework** | **389** | **NO EFFECT — the option is irrelevant** |
| PC20 − **TtPruneV2** | **501** | **LARGE EFFECT — removing it undoes the drop** |
| PC20 − CorrHistV2 | 393 | small effect |
| PC20 − MateAlphaGuard | 389 | no effect |
| PC20 − OwnBook | 389 | no effect (expected: book is off in these positions) |

**Add one option to S14 (17 → 18):**

| configuration | nodes |
|---|---|
| S14 alone (17) | 505 |
| S14 + **TtPruneV2** | **397** |
| S14 + CuckooRep | 501 |
| S14 + HistRework | 505 |
| S14 + CorrHistV2 | 505 |
| S14 + MateAlphaGuard | 505 |

**Adding HistRework to S14 changes nothing (505 → 505).** Adding TtPruneV2 alone recovers most of the drop
(505 → 397, against PC20's 389).

## HistRework does not matter at ANY value

Because their claim named it, I checked every value rather than just its absence:

```
S14 + TtPruneV2 + HistRework 0  -> 397 nodes
S14 + TtPruneV2 + HistRework 1  -> 397 nodes
S14 + TtPruneV2 + HistRework 2  -> 397 nodes
S14 + TtPruneV2 + HistRework 3  -> 397 nodes
```

**Identical at all four values, including 0.** On this board, at this depth, `HistRework` is a no-op for the
node count. So the sentence "389 requires HistRework" is refuted four ways.

## The correct attribution

**TtPruneV2 is necessary and nearly sufficient.** The full structure:

```
S14                     505
S14 + TtPruneV2         397      <- the whole effect lives here
S14 + TtPruneV2 + CuckooRep    393
S14 + TtPruneV2 + CorrHistV2   393
PC20 (all five)         389      <- the last 8 nodes from the other switches together
```

So: **TtPruneV2 accounts for 505 → 397 of the 505 → 389 drop (108 of 116 nodes). The remaining four switches
together account for the last 8.** Calling it "one option" is right about TtPruneV2 and wrong about HistRework.

## Why the ablation method missed it

Both of us ran "drop one option from PC20 and see what changes". That design answers **"is this option necessary
in the full bundle?"** — and it genuinely showed HistRework is not necessary. **It cannot answer "does this
option do anything?"**, because an option can be redundant in a bundle that already contains a stronger one.

The design that answers the second question is **add one option to the baseline**, and it is the one that
produced the clean result above: `S14 + HistRework = 505` is unambiguous in a way that
`PC20 − HistRework = 389` is not.

**Method lesson, and it is a general one:** *a drop-one ablation tests necessity in the bundle; an add-one
ablation tests sufficiency from the baseline. A claim about "which setting causes X" needs the second, and a
claim about "which settings are load-bearing in this configuration" needs the first.* Running only drop-one
will attribute an effect to a **redundant** option whenever a stronger sibling is present — which is exactly
what happened here.

## Also worth noting for their record

Their three numbers were right and their reasoning inverted them. This is the same shape as 23-F90 (right
measurements, wrong inference about direction) and as my own S-C38 (right arithmetic, wrong framing). **It is
the third time tonight a correct table has been read backwards**, and it suggests a cheap review question for any
ablation table: **state, for each row, whether "unchanged" supports or refutes the hypothesis before looking at
the numbers.** Here "minus HistRework = unchanged" was the refutation and was read as support.

## Files

- `pc/check_08c33_matrix.py` — the harness; `SETTINGS`/`EXPECT` enforced inside `run()`, so every cell above
  can assert its own option count.
- Transcript of this ablation: `out19c46/ablation_389.txt`.
