# `go nodes N` spends between rungs, never N (S-F123)

A fixed node budget is the standard way to compare two evaluations without a profiler: give both the same number of
nodes and compare the time. **This engine does not spend the number you give it.** It stops *inside* an iteration it
never finishes, and reports the last **completed** iteration's total. So the budget only chooses which rung of a
ladder you land between.

## The evidence

`startpos`, `go nodes N`, `Threads 1`, `Hash 16`. Every count below is deterministic — repeated runs give the same
number to the node.

| requested | plain reported | plain % | PC20 reported | PC20 % |
|---|---|---|---|---|
| 100,000 | 72,062 | 72.1 % | 78,579 | 78.6 % |
| 200,000 | 101,640 | **50.8 %** | 166,281 | 83.1 % |
| 400,000 | 267,839 | 67.0 % | 377,485 | 94.4 % |
| 800,000 | 600,227 | 75.0 % | 650,246 | 81.3 % |

Two configurations, same boards, same budgets — **different percentages**. That is the first clue that the request
is not being honoured as a quantity.

## The mechanism, and why the percentage is not monotonic

The completed-iteration totals for `startpos` form a fixed ladder:

```
72,062   101,640   212,340   267,839   600,227   650,246
```

A budget of 100,000 is crossed during the iteration that would end at 212,340 — so the search aborts mid-iteration
and the last **finished** total (72,062) is what the last `info` line reported. A budget of 200,000 is crossed in that
same iteration, so it reports the same 101,640. **Two different budgets can therefore report the same count**, and
"% of request" is simply where the request fell between two rungs.

That is why 200,000 (50.8 %) is *worse* than 100,000 (72.1 %): 200,000 sits just above a rung. And it is why PC20
differs — a different search has a different ladder.

The ladder is position-specific, as it must be:

| position | consecutive completed-iteration totals |
|---|---|
| `startpos` | 72,062 → 101,640 → 212,340 → 267,839 → 600,227 → 650,246 |
| Italian | 1,601,389 → 1,901,710 → 2,140,564 → 2,801,429 → 3,305,986 → 3,536,495 |
| rook endgame | 368,428 → 1,003,072 → 1,757,651 → 1,986,992 → 2,238,534 → 3,273,874 |

Code: `src/search.cpp:1387` tests the budget as `total_nodes() + extra_nodes_ + pending_nodes >= node_limit_`, and
`src/search.cpp:1618` / `:1767` call it on every node when `node_limit_specified_`. The abort sets `aborted_`, which
unwinds the iteration; the reporting site (`:2566`) then prints the count of the last iteration that completed.

## Why this matters to anyone comparing evaluations

1. **A harness that normalises by the REQUESTED budget is wrong by up to 2×.** "79.9 ms per 100k nodes" measured
   from a `go nodes 200000` run is really 79.9 ms per 101,640 nodes — and because the two configurations land on
   different rungs, the error does not cancel. This is the bug I had to fix in my own ABBA check (`S-C40`); it now
   divides by the **reported** count from the last `info` line.
2. **The two configurations in a comparison will not have equal node counts**, and that is not a defect to be
   "fixed" by dropping rows. Requiring equality makes a fixed-budget comparison permanently unusable — I did exactly
   that first and discarded 8 good positions before noticing the requirement was impossible.
3. **The budget is still useful** as a coarse control: it makes the search deterministic and repeatable, which is
   what a comparison needs. It is not an exact quantity.

## What I am not claiming

* Not that `go nodes` is a defect. It is a limit, and checking limits at iteration boundaries is normal; whether it
  should abort mid-iteration is a design question for the owner, not a bug I am filing.
* Not that the numbers are unstable — they are exactly reproducible, which is what makes this easy to miss.
* Not that per-node ratios elsewhere in the swarm are all wrong. Seat 29's `29-F59` table is in ms per 100k from
  reported counts, so it is not affected; mine now matches that.
