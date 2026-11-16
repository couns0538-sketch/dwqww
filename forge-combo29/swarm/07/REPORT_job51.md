# REPORT — seat 07, job 51: check of 05-S-F57 (mate-PV truncation confined to the smallest budget)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 05's **S-F57** claims the mate-PV truncation disappears above 20,000 nodes:
the same 28 positions give **1 truncated of 20 mate scores at `go nodes 20000`**, and **0 at 50,000 and
250,000**. Their own **S-W6** then *withdrew* their retest as void — only 2 of 120 positions qualified for
a long-mate filter — so the claim still rested on one board.

**Answer:** **confirmed on a pool I built from their sentence, and the reason their retest was void is now
explained: mate scores are rare at 20k nodes** — 8 of 361 positions.

**How sure:** high for the truncation itself (the same board reproduces, with the same 10-ply PV needing
14). The *rate* is honest but small-sample: 1 of 8.

## Why the pool had to be built differently

A rate over mate scores needs positions that **produce mate scores at the budget under test.** I scanned
**353 set-G positions plus 8 constructed mates** at `go nodes 20000` and kept only the ones reporting a mate:

    scanned 361, kept 8  (2.2 %)

That single number explains seat 05's void retest: filtering for long mates at 20k nodes will almost
always return nothing, and a sample with no mate scores measures nothing.

## Result on those 8 positions

| budget | mate scores | truncated | rate |
|---|---|---|---|
| `go nodes 20000` | 8 | **1** | **12.5 %** |
| `go nodes 50000` | 8 | **0** | 0 % |
| `go nodes 250000` | 8 | **0** | 0 % |

The one truncated case is **the same board seat 05 named**:

    fen  8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1
    score mate -7, PV 10 plies, needs 14, all moves legal

So the defect is real, and it is confined to the smallest of the owner's three budgets on this pool — the
same shape they reported.

## My checker was wrong first, and the controls caught it

My initial version required `2|N|` plies for **every** mate. For a positive mate the correct distance is
**`2N−1`**; 07-C40 had measured the `2|N|` form only for mates **against** the side to move.

**The tell:** the single kept position in my first pool reported `mate 5` with a **9-ply** PV, and my
checker called it truncated at **all three budgets** — including 250,000 nodes, where a truncation
disappearing is exactly the thing under test. A defect that fails to vanish at the largest budget is a
checker bug, not an engine bug. Corrected to `2N−1` for positive mates, the same position reads 9/9 at
50k and 250k and only the genuinely short line at 20k.

## Findings

**07-C51** in FINDINGS.md.

## Suspicions, not proven

- That the truncation is the partial-iteration publish (`FORGE_FIX_ABORT_PUBLISH`), which seat 11 measured
  as inert on its sample. On this one board at one budget the symptom matches, but I did not test the
  switch against it.

## What I did NOT do

- Did not build a larger mate-enriched pool; 8 mate-reporting positions is enough to reproduce the case
  and not enough to quote a tight rate.
- Did not test budgets between 20,000 and 50,000 to find where the truncation stops.

## What I am NOT sure about

- Whether "12.5 %" means anything given n=8. It is one board. The reliable statements are: the defect
  exists at 20k on that board, it does not appear at 50k or 250k on the same eight, and mate scores at 20k
  are rare (2.2 % of positions).

## Times

See job51/stamps.txt.
