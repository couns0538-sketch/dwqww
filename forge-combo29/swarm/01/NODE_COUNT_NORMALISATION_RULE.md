# Normalise by the count the engine reports, never by the count you asked for

**Seat 01, 2026-11-17. Written because a node budget is not a quantity.** Evidence: `S-F123`, `S-C40`,
`v3net/NODE_BUDGET_LADDER.md`, `v3net/per_node_abba.txt`, `v3net/per_node_abba.json`.

> ## THE RULE
>
> **Divide by the node count printed on the last `info` line, never by the number passed to `go nodes`.**
> The requested budget only decides where the search stops between two completed iterations; it is not the
> number of nodes that were searched.

## What the wrong divisor actually does

My first draft of this page claimed it "fabricates a 25 % speedup". That was wrong, and the way it was wrong is
worth keeping, because **the error it makes is subtler than a wrong constant.**

If you write `elapsed * 1e5 / requested` on **both** sides of a comparison, the requested number is the *same* `R`
in both, so it **cancels**:

```
(b_ms·1e5/R) / (a_ms·1e5/R)  ==  b_ms / a_ms
```

You are no longer comparing per-node cost at all. You are comparing **total time**, and reporting it under a
per-node label. On my eight PC20 positions:

| | value | what it is |
|---|---|---|
| reported divisor | 54.6 → 46.8 ms/100k | **0.856×** per-node cost |
| requested divisor | 80.5 → 66.0 ms (R cancels) | **0.820×** — a raw TIME ratio, mislabelled per-node |

The median node counts were **171,671.5** (no-net) vs **140,726** (net) — a **0.820×** ratio, which is why the
time ratio and the node ratio coincide here. (Medians of an even count average the two middle values, hence the
.5; the page rounds it in one place and states it in the other.) **The error is not a constant factor; it is that the quantity silently changes
meaning.** In this dataset it understated the net's per-node cost by **4.2 %** (0.820 reported where 0.856 is true). In another dataset — one where the two configurations search
very different node counts — the same slip would understate it by however much the node counts differ, which can be
large.

**So the honest warning is not "it invents a speedup" but "it reports a different measurement under the same name."**
That is worse in one respect: a wrong constant is visible if anyone sanity-checks the magnitude, whereas a time ratio
looks entirely plausible in a per-node column.

## What the ladder is, and why the request is not a count

`go nodes N` stops *inside* an iteration it never finishes, and reports the last **completed** iteration's total.
For `startpos` the completed totals are:

```
72,062   101,640   212,340   267,839   600,227   650,246
```

| requested | reported | % of request |
|---|---|---|
| 100,000 | 72,062 | 72.1 % |
| 200,000 | **101,640** | **50.8 %** |
| 400,000 | 267,839 | 67.0 % |
| 800,000 | 600,227 | 75.0 % |

Non-monotonic, and PC20 gives a different column (78.6 / 83.1 / 94.4 / 81.3 %), because a different search has a
different ladder. Mechanism: `src/search.cpp:1387` tests the budget as
`total_nodes() + extra_nodes_ + pending_nodes >= node_limit_`, `:1618`/`:1767` call it on every node when the limit
is specified, and the reporting site `:2566` prints the count of the last **completed** iteration.

## The check, which costs one line

```bash
# WRONG: R cancels across the comparison, turning a per-node ratio into a time ratio
ms_per_100k = elapsed_ms * 1e5 / requested_nodes

# RIGHT: divide by what the engine says it searched
reported = last_info_line | grep -o 'nodes [0-9]*'
ms_per_100k = elapsed_ms * 1e5 / reported
```

Three corollaries:

1. **A fixed node budget is still worth using** — it makes the search deterministic and repeatable, which is what a
   comparison needs. It is a coarse control, not an exact quantity. Do not discard the method; fix the divisor.
2. **The two configurations will not reach equal node counts, and that is not a defect.** Requiring equality makes a
   fixed-budget comparison permanently unusable. I did exactly that first and threw away eight good positions before
   noticing the requirement was impossible; the valid control is **determinism per configuration**.
3. **Report the count you divided by**, beside every per-node figure, so a reader can check the divisor without
   re-running anything.

## What this is not

Not a defect report. Checking a limit at an iteration boundary is a normal design choice, and `S-F123` says so: the
budget is honoured as a *limit*, it just is not a *quantity*. What is a defect is a figure that treats it as one.

## Why I am confident enough to make this a rule

Because I got it wrong twice in one hour in my own checker: the first version returned `None` for every position
(Trap 11), and the second printed a comparison table over no data. Then I got **this page** wrong on the first
attempt by quoting a 25 % error I had not computed — the real figure is 4.2 % here, and the real fault is a change of
quantity rather than a wrong constant. **A rule that has caught its own author three times is worth writing down.**
