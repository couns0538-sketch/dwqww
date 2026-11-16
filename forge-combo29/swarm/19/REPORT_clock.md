# The 6 s + 0.06 clock, third measurement — the class medians do not order, but ρ = 0.999 says the mechanism is settled

seat 19 · area 9 · build **PC r15** · **PC20** · **Threads 1** · Hash 16 · cold, one fresh process per search.

## 1. The three lines

**What was asked.** Settle the direction disagreement between seat 08 (08-F28/F29: sparse boards are the heavy
tail, median 853 ms) and seat 02 (S-F14: sparse is *lighter*, 207 ms vs 303 ms full), with (1) the class
definitions in code plus per-class counts so they can see whether their classes match mine, and (2) a
per-position table with material, legal-move count, last-iteration cost and wall time, because the correlation
across positions settles the mechanism even if the class medians disagree.

**The answer.** **The correlation settles it: Spearman ρ between the last completed iteration's cost and the
measured wall time is 0.999 over 42 positions.** Wall time *is* the last iteration's cost — the clock stops on
an iteration boundary, exactly as seats 02 (ρ 0.998) and 08 described. **The class medians do not order
reliably** — sparse_few 272 ms, sparse_many 256 ms, mid 326 ms, full_many 231 ms — with ranges that overlap
heavily and one mid class position at 1586 ms. So the direction disagreement is **a boards problem, not a
mechanism disagreement**: both seats were right about the mechanism, and the class ordering depends on which
boards land in the class.

**How sure.** Very high on ρ = 0.999 (42 positions, deterministic at Threads 1). Explicitly low on the class
ordering — I do not claim sparse is heavier or lighter, and my own numbers point in different directions by
class.

## 2. Class definitions, in code, and counts

```
heavy = knights + bishops + rooks + queens, both colours
nm    = legal moves in the position
sparse = heavy <= 4 ;  full = heavy >= 10 ;  otherwise mid
within sparse/full:  few = nm <= 20 ;  many = nm > 20
```

| class | positions in set G | tested |
|---|---|---|
| sparse_few | **124** | 10 |
| sparse_many | **59** | 10 |
| mid | **92** | 10 |
| full_many | **76** | 10 |
| full_few | **2** | 2 |

**`full_few` has only 2 positions in all 353 of set G** — that class cannot be measured from this file, and any
seat quoting a `full_few` median is quoting a two-board sample. That alone may explain part of the disagreement
between 08 and 02: if "full material, few moves" is nearly absent from game positions, a class defined that way
will be dominated by whichever two boards someone happened to include.

## 3. Per-position records (42 positions, all rows in `clock/out2/RESULT.txt`)

| class | heavy | nm | last iteration ms | wall ms | depth |
|---|---|---|---|---|---|
| sparse_few | 0 | 6 | 857 | **857.7** | 18 |
| sparse_few | 2 | 13 | 856 | **856.3** | 17 |
| sparse_few | 2 | 10 | 434 | 435.1 | 17 |
| sparse_few | 4 | 12 | 237 | 237.3 | 17 |
| sparse_many | 1 | 22 | 718 | **718.6** | 19 |
| mid | 6 | 36 | 749 | **1585.8** | 20 |
| full_many | 12 | 43 | 669 | 670.2 | 18 |
| full_many | 12 | 45 | 369 | 370.0 | 18 |
| full_many | 14 | 38 | 159 | 159.6 | 15 |
| mid | 5 | 2 | 162 | 162.5 | — |
| full_few | 10 | 2 | 210 | 210.8 | 17 |
| full_few | 11 | 4 | 277 | 278.2 | 18 |

(the full 42 rows, with every per-position number, are in the file; this is the informative subset)

### Class medians — and why I do not draw a direction from them

| class | n | median wall ms | max ms |
|---|---|---|---|
| sparse_few | 10 | 272.1 | **857.7** |
| sparse_many | 10 | 255.6 | 718.6 |
| mid | 10 | **325.6** | **1585.8** |
| full_many | 10 | 230.7 | 670.2 |
| full_few | 2 | 244.5 | 278.2 |

The medians span 231–326 ms — a factor of 1.4, well inside the position-to-position spread of any single class
(sparse_few alone runs 237 ms to 858 ms). **The maxima are where the tail lives and they do not respect class
boundaries**: the largest is a **mid** position (1586 ms), not a sparse one. My numbers therefore support
neither seat's ordering, and I say so rather than picking the side my sample happens to favour.

## 4. The mechanism, settled by the correlation

**ρ = 0.999 over 42 positions** between the last completed iteration's own `time` field and the wall time I
measured. That is the answer to the mechanism question, and it agrees with seat 02's S-F13 (ρ 0.998). So:

- The clock's tail is **the cost of one iteration**, not the clock arithmetic and not a fixed overhead.
- A position's wall time is determined by **how expensive its final iteration happened to be**, which depends on
  the position's branching and on which depth the budget ran out at — which is why a class defined by material
  count does not predict it well.

**The one exception, and it is worth flagging:** the `mid` position at **1586 ms wall vs 749 ms last iteration**.
Every other position has wall ≈ last-iteration cost to within a few ms; this one is **2.1×**. That is the
signature of a search that paid for an iteration it then *discarded* — most plausibly a fail-high re-search, or
an iteration aborted by the hard limit. **I did not investigate it**, and it is the single most interesting row
in the table: seats 28 and 08 both describe tail cases, and this may be that mechanism rather than a big
iteration.

## 5. Findings

**19-F50 — on the owner's 6 s + 0.06 clock, wall time equals the last completed iteration's cost with Spearman
ρ = 0.999 over 42 positions (PC r15, PC20, Threads 1, Hash 16, cold).** This confirms seats 02 (ρ 0.998) and 08
on the mechanism and makes it a third independent measurement.

**19-F51 — the sparse-vs-full class ordering does NOT reproduce, and the disagreement between seats 08 and 02 is
a boards problem, not a mechanism disagreement.** My medians: sparse_few 272.1, sparse_many 255.6, mid 325.6,
full_many 230.7 ms — a 1.4× span against 3.6× within-class spread, and **the worst position is a `mid` one
(1585.8 ms), not a sparse one**. Also: **`full_few` contains only 2 of set G's 353 positions**, so that class is
not measurable from game positions at all — a likely source of the original disagreement.

**19-F52 — one position in 42 shows wall time 2.1× its last-iteration cost** (`mid`, heavy 6, nm 36: 1585.8 ms
wall vs 749 ms last iteration, depth 20). Every other position is within a few ms. This is the signature of an
iteration that was paid for and discarded — the tail mechanism the other seats describe — but I did not trace it.

### Suspicions, not proven

- That the 1585.8 ms position paid for a discarded iteration (fail-high re-search or hard-limit abort). It is
  the obvious reading of a 2× gap but I did not instrument the search to confirm.
- That a class defined by **last-iteration cost** rather than material count would order positions usefully.
  Since ρ = 0.999, any class that predicts iteration cost predicts wall time — that is the reframing this data
  suggests, and I did not test it.

## 6. What I did NOT do

- I did not investigate the 1585.8 ms anomaly (see above). It is the best lead in this report and I am handing it
  over rather than half-chasing it.
- I did not test the clock at other time controls, so this is the 6 s + 0.06 regime only.
- I did not reconcile my class thresholds with seats 08/02 numerically — I published mine in code so they can do
  it, which is what was asked.

## 7. Files

`clock/clock_records.py` (class definitions in code), `clock/out2/RESULT.txt` (all 42 per-position rows plus the
class table and ρ), `clock/out/RESULT.txt` (the earlier class-only pass).
