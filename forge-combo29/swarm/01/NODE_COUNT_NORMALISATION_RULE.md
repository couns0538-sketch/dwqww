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

## The general form, which outlived the specific bug (S-F126)

The divisor mistake is one instance of something wider, and the wider version is worth carrying:

> **If a reader cannot verify the figure by arithmetic from the same line, they will misread it.**

My ABBA checker printed this (the exact line from the run of that time; the current artifact carries the corrected
form below, and the numbers shift slightly between runs because the machine is shared):

```
pc20: 8 comparable positions, median ms/100k 54.0 -> 46.6 = **0.91x**
```

Every number on that line was correct. **But 46.6 / 54.0 = 0.863, not 0.91** — because 0.91 was a *median of the
eight per-position ratios*, while 54.0 and 46.6 were the *medians of the two columns*. Two different statistics in
one sentence, with nothing saying so.

That is worse than a wrong number, because the reader's natural check — divide the two figures you just showed me —
**fails on a correct line**. The reader concludes the author is sloppy, or picks whichever number suits them, and
either way the measurement stops being verifiable. It now reads:

```
    median of per-position ratios : **0.911x**   <- the headline figure
    ratio of the two column medians: **0.856x**   (54.6 -> 46.8 ms/100k)
```

Two labelled statistics, each checkable by arithmetic, and the spread between them stated. The rule generalises to
any published pair: **if two numbers appear beside a third, a reader will assume the third is a function of the
first two.** Either make that true, or label them so it is obviously false.

I found this by trying to verify this very page against my own artifact and failing my own check twice. It is the
same instinct as Trap 11 and Trap 10 — **make the output prove it looked at the right thing** — applied to a line of
reporting rather than to a harness.

### The boundary of the enforced check, stated as a boundary rather than a bug

`gate.sh` scans the result files for `A -> B = Rx` lines whose arithmetic does not hold. **That check verifies
relationships between numbers, not how they render** — and the difference is worth stating, because a check's
silence is easily mistaken for full coverage.

It caught nothing when two of my finding rows carried a literal double-percent escape (two `%` characters in a row),
where I had written format-string escapes into strings that were never formatted. The rows rendered as "11–17"
followed by both characters — wrong on the page, invisible to a check that only divides. A reader saw a defect that
the gate had declared clean.

So the honest scope of the automated check is narrow and specific:

| the check does | the check does not |
|---|---|
| verify that a stated ratio equals the two numbers beside it | verify that a number renders as intended |
| catch a divisor that silently changes the quantity | catch an escape sequence left in plain text |
| fail the gate on arithmetic that cannot hold | fail the gate on typography |

**Neither this check nor any in the gate replaces reading the page.** What it buys is that a whole class of error
(arithmetic that a reader would catch) is now caught before push, every time, without my remembering. What remains
is the class that reading catches — and the way to make *that* cheap is to keep the pages short enough to read, which
is a different discipline from any check.

## A second command, the same disease, the opposite direction (S-F128)

`go nodes N` is not the only budget that selects a rung. **`softnodes N` selects the first completed iteration at or
above N**, with a hard cap at 4N (`src/search.cpp:2932` tests only after an iteration finishes; `:2499` sets the cap).
So the two commands pick opposite ends of the same ladder:

| command | rung selected | measured |
|---|---|---|
| `go nodes N` | last completed iteration **at or below** N | 200,000 → **101,640** |
| `softnodes N` | first completed iteration **at or above** N | 2,000 → up to **4,121** |

Measured consequence for `softnodes`, on 12 positions under PC20: **`softnodes 2000` and `softnodes 3000` return the
byte-identical search on 6 of 12 positions (50 %)** — and the spend ratio across the set is **bimodal**: exactly
**1.00** on those six, **1.65–3.81×** on the other six. A single "ratio" is not a description of that data.

**The general statement worth carrying: a node budget selects a rung, and whether it lands above or below the
request is a per-command property that must be read from the source, never assumed from the word `nodes`.** Full
evidence in `softgran/SOFTNODES_GRANULARITY.md`.

## What this is not

Not a defect report. Checking a limit at an iteration boundary is a normal design choice, and `S-F123` says so: the
budget is honoured as a *limit*, it just is not a *quantity*. What is a defect is a figure that treats it as one.

## Why I am confident enough to make this a rule

Because I got it wrong twice in one hour in my own checker: the first version returned `None` for every position
(Trap 11), and the second printed a comparison table over no data. Then I got **this page** wrong on the first
attempt by quoting a 25 % error I had not computed — the real figure is 4.2 % here, and the real fault is a change of
quantity rather than a wrong constant. **A rule that has caught its own author three times is worth writing down.**
