# REPORT — seat 07, job 49: check of 01-S-F72 (MultiPV dilutes a fixed node budget)

## What was asked / the answer / how sure

**Asked:** (cycle work) seat 01's **S-F72** claims a parameter that looks cosmetic changes the budget:
with MultiPV > 1 a fixed node budget buys far fewer plies (d10→d7 at 20,000 nodes; d8→d2 on
`softnodes 2000`), because the M lines come from the same N nodes. It is in this seat's competence — I
ran MultiPV cases in job1 — so it needed an independent check.

**Answer:** **confirmed in kind, and the effect is smaller than their quoted figures.** Every cell was
also **exactly reproducible across two runs**, which is worth recording because node *stops* are
deterministic even though node counts under a *clock* are not (07-C47).

**How sure:** high. 16 cells (2 positions × 2 budgets × MultiPV 1–4), two fresh runs each, all identical.

## Results (PC r15 under PC20, Threads 1, Hash 16, fresh process per cell)

| position | budget | MPV 1 | MPV 2 | MPV 3 | MPV 4 | plies lost (1→4) |
|---|---|---|---|---|---|---|
| startpos | `go nodes 20000` | **d11** | d10 | d8 | **d8** | **3** |
| startpos | `go softnodes 2000` | **d7** | d6 | d5 | **d5** | **2** |
| middlegame | `go nodes 20000` | **d10** | d9 | d8 | **d8** | **2** |
| middlegame | `go softnodes 2000` | **d7** | d6 | d5 | **d5** | **2** |

**All 16 cells stable**: identical depth *and* node total on both runs. So this is a reproducible
measurement, unlike anything taken under a clock.

The drop is **monotone** in MultiPV at every cell (e.g. d11 / d10 / d8 / d8 on startpos at 20,000 nodes),
which is the signature of lines competing for one node budget rather than a threshold effect.

## Where I differ from seat 01, and why it does not matter

They report **d10→d7** at 20,000 nodes and **d8→d2** on `softnodes 2000`. I measure **d11→d8** and
**d7→d5** — same direction, smaller size. The likely reason is positions: they did not name theirs in the
row, and dilution depends on how much of the budget the first line consumes. So:

- the **finding stands**;
- the **magnitude should be quoted per position**, not as a single figure, and my numbers are the ones for
  startpos and for `r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R`.

## The operational advice, which I would keep verbatim

> **A harness should assert `MultiPV 1` explicitly and record it, exactly as it should assert Threads 1.**

That is the actionable part and my data supports it: a leftover MultiPV from an analysis session silently
buys three fewer plies on startpos at 20,000 nodes and two on a middlegame — with no error, no warning, and
a perfectly plausible-looking node count.

## Findings

**07-C49** in FINDINGS.md.

## Suspicions, not proven

- That the dilution is proportional to how much of the node budget the first line consumes. Consistent
  with the monotone ordering, not tested directly.

## What I did NOT do

- Did not test MultiPV above 4 (the engine advertises 1–8).
- Did not test with a clock rather than a node budget, deliberately: 07-C47 shows node counts under a clock
  are irreproducible here, so a clock-based version would measure noise.

## What I am NOT sure about

- Whether the depth difference corresponds to a strength difference. Plies are not strength; a match or a
  fixed-depth-vs-fixed-node comparison would be needed, and neither is my job here.

## Times

See job49/stamps.txt.
