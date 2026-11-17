# FINAL population figures: PC20 is 5.1 % slower by wall time, CI excludes 1.0 (S-C66)

**The run completed: 10,774 usable pairs of 11,192 `R_1911` positions, EXIT=0.** This replaces every intermediate figure
in the owner report.

## The final table

| quantity | value |
|---|---|
| **n** | **10,774** |
| node median | **0.9618** |
| node mean | **1.0943** |
| node Q1 / Q3 | 0.7475 / 1.2445 |
| node min / max | 0.034 / **18.37** |
| **wall median** | **1.0370** |
| **wall geometric mean** | **1.0513** |
| **95 % CI on the geometric mean** | **[1.0422, 1.0604]** — **excludes 1.0** |
| per-node median | **1.0712** |
| per-node Q1 / Q3 | 1.0471 / 1.0968 |
| per-node min / max | 0.500 / 2.02 |
| tail, node ratio > 2× | **641 of 10,774 = 5.95 %** |
| tail, > 5× | 29 = 0.27 % |
| tail, > 10× | 3 = 0.03 % |
| PC20 uses fewer nodes on | **56.2 %** of positions |
| PC20 faster on | **44.4 %** of positions |
| identity check | 0.9618 × 1.0712 = **1.0302** vs wall 1.0370 |

## The CI is robust to the sequence structure

These are **consecutive game positions**, so a naive independent-sample CI would be invalid. Checked:

* **lag-1 autocorrelation of log(wall ratio) = 0.0344** — neighbouring positions barely move together;
* **block bootstrap is flat in block size**: B=1 → [1.0423, 1.0605]; B=10 → [1.0413, 1.0613]; B=50 → [1.0421, 1.0611];
  B=200 → [1.0429, 1.0607].

**Every interval excludes 1.0**, so "PC20 is slower by wall time on this population" does not depend on treating the
positions as independent.

## What this does to the report

**The ~3.5 % slower reading survives and strengthens to 5.1 %.** The point estimate moved further from 1.0 as n grew
(from 1.035 at n=2,643 to 1.051 at n=10,774), and the interval now excludes 1.0 rather than merely sitting above it.

**But the two readings answer different questions and both should stay:**

| claim | estimate | interval | status |
|---|---|---|---|
| PC20 searches **~4 % fewer nodes** | node median 0.9618 | — | real; 56.2 % of positions |
| PC20 pays **~7 % more per node** | per-node median 1.0712 | Q1–Q3 1.047–1.097 | real and stable |
| net wall time | **1.0370 median / 1.0513 geometric mean** | **[1.0422, 1.0604]** | **slower, and now excludes 1.0** |

**The decomposition still explains it:** a ~4 % node saving consumed by a ~7 % per-node penalty nets to ~3–5 % slower,
and which of those you quote depends on median vs geometric mean — **both are given above precisely because they differ
by 1.4 points.**

## Why this took four hours of wall time

The run needed **~48 minutes of continuous CPU** (4.4 pairs/s over 10,774 pairs), spread across three turn boundaries
because my turn ended twice mid-run. **The tmux session and the per-pair checkpoint are what made that survivable**: it
resumed without losing work, and the checkpoint file is what every intermediate figure in this report was computed from.
