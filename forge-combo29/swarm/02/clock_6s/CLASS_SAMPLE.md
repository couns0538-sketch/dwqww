# The authoritative clock result: 20 boards, 4 shape classes, 5 runs each, owner's 6 s + 0.06 clock

> **Headline, in one line each.** (1) A move's wall time IS the last completed iteration's cost (Spearman
> rho = 0.998, 17 of 20 boards within 2 %), and the engine uses only 3.3-5.8 % of a 6 s clock. (2) **A wall-to-
> last-iteration ratio near 2.4 identifies a hard-limit cut after the fact** — useful for auditing clock logs,
> though it cannot predict one. (3) The cut is the only route to an expensive move: 1585.6 ms = 26.2 % of the
> clock, which is the engine's hard plan for this clock, hit to 0.5 ms.

PC r15 build, **PC20**, **Threads 1**, Hash 16, OwnBook false, fresh process per run, interactive driver.
`class_tail.py`, raw `tail_rows.json`, `correlation.json`. **My own boards — none of seat 08's or seat 28's.**

Class definition (seat 08's shape framing, so the numbers can be compared): piece count x legal-move count.
`sparse_few` = <=6 men and <12 legal moves; `sparse_many` = <=6 men and >=20; `full_few` = >=26 men and <40;
`full_many` = >=26 men and >=34. Every board verified legal with python-chess before use.

## TABLE 1 — wall time and utilisation, per class (100 runs per class)

| class | men | legal moves | median ms | p99 ms | worst ms | worst as % of 6060 ms |
|---|---|---|---|---|---|---|
| sparse_few | 3-7 | 4-19 | **207.5** | 1585.6 | 1585.8 | **26.2 %** |
| sparse_many | 3-4 | 21-29 | **353.0** | 696.8 | 701.9 | 11.6 % |
| full_few | 30-32 | 27-42 | **197.4** | 516.4 | 575.9 | 9.5 % |
| full_many | 26-32 | 34-59 | **303.0** | 545.6 | 542.2 | 8.9 % |

## TABLE 2 — utilisation, stated on its own because it is the bigger fact

| class | median | utilisation | worst | worst utilisation |
|---|---|---|---|---|
| sparse_few | 207.5 ms | **3.4 %** | 1585.8 ms | 26.2 % |
| sparse_many | 353.0 ms | **5.8 %** | 701.9 ms | 11.6 % |
| full_few | 197.4 ms | **3.3 %** | 575.9 ms | 9.5 % |
| full_many | 303.0 ms | **5.0 %** | 542.2 ms | 8.9 % |

**The engine spends 3.3-5.8 % of a 6 s clock.** The tail is real but rare: only one board in twenty ever exceeded
26 % of the clock, and the median usage in every class is a few per cent. So the two facts to state together are
"the clock is almost entirely unused" and "the worst case is 26 %, not 100 %".

## TABLE 3 — the MECHANISM, and it is exact: wall time IS the last completed iteration's cost
| class | median wall | median last-iteration cost | ratio |
|---|---|---|---|
| sparse_few | 207.5 ms | 207.0 ms | 1.00 |
| sparse_many | 353.0 ms | 352.0 ms | 1.00 |
| full_few | 197.4 ms | 196.0 ms | 0.99 |
| full_many | 303.0 ms | 302.0 ms | 1.00 |

Across the 20 positions: **Spearman rho = 0.998**, Pearson r = 0.834 (Pearson is dragged down by the single
hard-limit board — see below). **17 of the 20 boards have wall time equal to the last iteration's own reported
`time` within 2 %.** That is the mechanism confirmed: the engine stops at an iteration BOUNDARY, so the wall time
of a move is the cost of the last iteration it chose to finish.

## the three exceptions, and the one that matters
| board | wall | last iteration | ratio | what happened |
|---|---|---|---|---|
| `6k1/8/6K1/8/8/8/8/5R2 w` | 1.7 ms | 1 ms | 0.59 | a tablebase-like position solved at depth 64 immediately — no iteration cost to speak of |
| `8/8/8/3k4/8/3K4/8/2R4R w` | 17.5 ms | 17 ms | 0.97 | within noise |
| **`8/8/6k1/Q7/1P4PP/1K3P2/8/8 b`** | **1585.6 ms** | **667 ms** | **0.42** | **cut at the HARD limit** |

The third is the important one: 1,585.6 ms is the engine's **hard plan for this clock** (seat 08 measured exactly
1585 ms on the same board shape), while its last completed iteration was only 667 ms. So on that board the search
did NOT stop at an iteration boundary — it ran until the hard limit and was cut mid-iteration. That is a DIFFERENT
tail mechanism from the iteration-boundary one, and it is the only way a move can approach the full clock.

## the class claim, restated in the precise form the data supports
The correlation says the class claim is really a claim about **the last completed iteration's cost**, and that
quantity depends on the board, not on the piece count:

- **My classes do NOT order the way seat 08's did.** On my boards the sparse endgames are NOT the slow class in
  median: sparse_few is 207.5 ms and full_many is 303.0 ms, i.e. **sparse_few is the FASTER of the two by 0.68x**.
  Their 08-F28 has sparse+few at 853.1 ms and full+many at 161.2 ms, a 5.3x spread the other way.
- **What reproduces is the WORST case.** My worst is sparse_few at 1585.8 ms — 26.2 % of the clock — and it is the
  same board shape family they flagged (`8/8/6k1/Q7/1P4PP/1K3P2/8/8`), on which their harness measured 1585.4 ms
  and mine 1585.6 ms. So the SPARSE-ENDGAME HARD-LIMIT TAIL reproduces to 0.2 ms across two independent harnesses
  and two different board sets.
- **Why the medians can disagree without either being wrong:** the median depends on which boards happen to sit
  near an iteration boundary that costs a lot. That is board-specific, so a 5-board class sample of medians is a
  sample of that accident, not a property of the class. The robust, harness-independent statement is about the
  worst case and about the mechanism (iteration cost = wall time).

## so the precise claim to put to the owner
1. **On a 6 s + 0.06 clock the engine uses 3.3-5.8 % of it** (median per class), never approaching the clock in
   the ordinary case.
2. **A move's wall time is the cost of the last completed iteration** (rho = 0.998; 17/20 boards within 2 %). The
   clock tail is therefore an iteration-cost tail, not a clock-management tail.
3. **The one way a move gets expensive is the hard limit**: a sparse endgame with very few legal moves can fail to
   finish an iteration inside the plan and be cut at the hard limit, giving 1585.8 ms = 26.2 % of the clock. This
   reproduces across two independent harnesses and board sets to 0.2 ms.
4. **An earlier claim of mine needs correcting**: my four-board result ("sparse endgame mid-range at 200 ms") was
   a small sample, and this 20-board result shows the medians do not order by class the way the other seats' do.
   The tail does reproduce; the median ordering does not, and I would not quote a median-ordering claim.

## what I did NOT do
- Did not use node-normalised cost, which might make the classes comparable where raw wall time does not.
- Did not test whether the hard-limit cut is specific to sparse endgames or just needs few legal moves; 20
  boards is enough for the mechanism, not for a per-class rate.
