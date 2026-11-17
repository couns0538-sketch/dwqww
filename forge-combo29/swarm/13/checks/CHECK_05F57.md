# CHECK of seat 05's S-F57 — mate-PV truncation disappears above 20,000 nodes

## Verdict
**CONFIRMS 05-F57**, on their named board and on the rate.

Seat 05 claimed: at the owner's match node budgets on PC r15 + PC20 (Threads 1, Hash 16, fresh process),
mate-PV truncation is confined to the smallest budget — `go nodes 20000` gives 1 truncated mate claim of 20
(5.0 %), while 50,000 and 250,000 give none. The single case is their board
`8/8/1p6/8/p3p3/8/2Kpk3/8` reporting `mate -7` with a 10-ply PV where 2×|M| = 14 plies are needed.

## A. Their named board — reproduces exactly

| nodes | score | PV length | PV reaches mate at | verdict |
|---|---|---|---|---|
| **20,000** (×2 runs) | **`mate -7`** | **10** | **never** | **TRUNCATED** — needs 14 plies, PV is 10 and ends in no mate |
| 50,000 (×2) | `mate -4` | 8 | **ply 8** | delivered — needs 8, PV delivers at 8 |
| 250,000 (×2) | `mate -4` | 8 | **ply 8** | delivered |

Their numbers match to the claim and the ply count: `mate -7` at 20,000, and the same board corrects to
`mate -4` — a *delivered* mate — once the budget rises. The truncated PV is printed in full in the raw JSON:

```
c2b1 d2d1q b1b2 e4e3 b2a2 d1d3 a2b2 a4a3 b2a2… (10 plies, no mate)
```

That is exactly the "score promises a mate at a distance its own PV does not reach" shape.

## B. The rate, on a set of my own
Their set has 28 positions; I do not have it. I used a **mate-rich** set (22 positions: my 21 verified mate
boards plus their named board) so that mate claims actually occur — my first attempt used ordinary G positions
and got **zero mate claims at every budget**, which would have tested nothing:

| `go nodes` | mate claims | truncated |
|---|---|---|
| **20,000** | 20 | **1** (their board, `mate -7`, PV 10 vs 14 needed) |
| 50,000 | 20 | **0** |
| 250,000 | 20 | **0** |

So the *rate* reproduces too: at 20,000 nodes exactly one board in this mate-rich set truncates, and it is
their board; above that budget nothing truncates.

## How sure
High for both parts. Every search is a **fresh process**, enforced by the runtime guard
(`lib/freshguard.py`, `assert_single_use` — 90 searches all on single-use processes), which is the discipline
the S-F24 correction requires. Settings come from `lib/settings.py` (asserted 22 entries). Each cell was run
twice and the results were identical.

The one methodological difference worth stating: **my set is mine, not theirs.** The agreement on the rate
(1 of 20) is suggestive rather than a reproduction of their 1-of-20, since the denominators coincide by
construction rather than by design. What is genuinely reproduced is (a) their exact board and numbers, and
(b) the *pattern* — truncation at 20,000, none above.

## Beyond the finding
The truncation is not "the engine lies": the score `mate -7` is a *claim about distance*, and at 20,000 nodes
the PV is cut short before it can demonstrate that distance. The practical rule for anyone validating mate
scores at a node budget: **check the PV length against 2|M| (or 2M-1), not just that a mate score appeared.**
A harness that counts `score mate` lines alone would report these as fine.

## A first attempt that measured nothing, recorded — and the population rule it teaches
My initial run used 28 ordinary G positions and produced **0 mate claims at all three budgets**. The
truncation count was therefore 0 — which reads like a clean pass and is the same number a genuinely
non-truncating engine would produce. **There was nothing to truncate, so the test was vacuous.**

I caught it only because I looked at the **claim counts** rather than just the truncation counts: a truncation
rate needs a population of truncatable events, and mine was empty.

This is the **population rule**, stated for reuse:
> **Before reporting a rate, assert the denominator is non-zero.** "0 truncated" is meaningful only beside
> "N mate claims"; without N it is indistinguishable from "the feature never fired".

It is also traps-note case 4 (a test that could not have failed) in a new shape: here the *check* was fine and
the *population* was empty. The guard that catches it costs one line — print and assert the denominator — and
`check_05f57.py` now reports `mate_claims` beside `truncated` at every budget for exactly this reason.

## Reproduce
```
cd forge-combo29/swarm/13/checks
python3 check_05f57.py ~/b/pc/forge mate_rich.fens /tmp/c5 22
```
Raw: `out_05f57/check_05f57.json` (ordinary G set: 0 claims — the vacuous attempt),
`out_05f57_mate/check_05f57.json` (mate-rich set: 20 claims, 1 truncated).
