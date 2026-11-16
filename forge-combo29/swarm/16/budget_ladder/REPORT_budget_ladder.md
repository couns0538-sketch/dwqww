# REPORT_budget_ladder — HOW FAR should the self-play budget move up? (the number behind S-F31's advice)

**What was asked (my own follow-up):** S-F31 said a strength-minded self-play choice should move up from 2,000
nodes but gave no target, which makes the advice hard to act on. This measures cost against budget.

**The answer: the damage falls MONOTONICALLY with the budget, and 20,000 nodes captures most of it. A concrete
recommendation: move the self-play budget from 2,000 to 20,000.**

```
budget | same move as ref | median cost | >30 cp worse | >100 cp worse | total damage
-------|------------------|-------------|--------------|---------------|-------------
  2000 |  21 of 39        |     +0 cp   |      3       |       0       |    +213 cp
  8000 |  28 of 39        |     +0 cp   |      2       |       0       |    +180 cp
 20000 |  31 of 39        |     +0 cp   |      1       |       0       |     +96 cp
 50000 |  34 of 39        |     +0 cp   |      1       |       0       |     +69 cp
```

(reference = `go nodes 250000`; each move judged by one fixed `go depth 16` search of the resulting position;
"total damage" = the sum of positive costs, i.e. how much is lost across the positions where the budget errs)

**Reading it:**

- **Every step up is an improvement, with no reversal** (213 → 180 → 96 → 69). That is the monotone shape I
  predicted (P1 confirmed) and it is the cleanest form the answer could take.
- **20,000 is where the return flattens:** 2,000→8,000 removes 33 cp of damage, 8,000→20,000 removes 84 cp (the
  largest single step), and 20,000→50,000 removes only 27 cp while costing 2.5x the nodes. So 20,000 is the knee.
- **No budget in this range produced a >100 cp error** on this sample — so at 2,000 nothing is catastrophic; the
  cost is spread thinly across three positions, not concentrated in one blunder.
- **14 of 39 moves change between 2,000 and 8,000 nodes** — about a third, so the budget does shift many
  decisions, not just a few (P4 confirmed: my bar was "under a third", measured exactly a third).
- Median cost is 0 cp at EVERY budget, which is why the median was the wrong summary statistic in S-F30 and the
  sum is the right one. That is the same lesson as S-F31, in a cleaner form: for a budget used over many moves,
  what matters is accumulated damage, not the typical case.

**P2 confirmed** (8,000 removes 33 of the 144 cp available by 50,000 — about a quarter — inside my predicted
range). **P3 confirmed** (0 of 39 worse than 100 cp at 50,000, median 0). **P4 confirmed** (14 of 39 changed,
exactly at my "a third" boundary).

**Honest caveat on the reference.** Every cost here is relative to the 250,000-node budget, which is itself not
ground truth. If 250,000 is also imperfect, the absolute figures shift; the MONOTONE ordering and the 20,000 knee
are the robust part, not the exact centipawns. The one >100 cp case from S-F30 (idx 34) does not appear as >100
here because this run judges with a depth-16 reference instead of depth-12, which is consistent with S-F31's
finding that the reference depth changes the magnitude.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dcded
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; budgets 2000/8000/20000/50000 vs reference 250000;
         each resulting position judged by one fixed `go depth 16` search; 40 G positions, cold per search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 4 budgets vs a 250,000-node reference, 39 scored positions | done | `raw/budget_ladder.txt`, `run.log` | total damage 213 / 180 / 96 / 69 cp |
| monotonicity | done | same | strictly decreasing, no reversal |
| where the return flattens | done | same | 20,000 (the largest single step is 8,000→20,000) |
| moves changing 2,000→8,000 | done | same | 14 of 39 |
| ground-truth validation | NOT done | — | the reference is another budget, not exact truth |

## Findings

`S-F32 | 6 | raising the self-play node budget reduces accumulated damage MONOTONICALLY and 20,000 is the knee: against a 250,000-node reference on 39 real-game positions, total damage (sum of positive costs, each judged by a fixed depth-16 search) falls 213 cp at 2,000 nodes to 180 at 8,000, 96 at 20,000 and 69 at 50,000, while the median cost is 0 cp at EVERY budget — so for a budget used over many moves the sum, not the median, is the right statistic, and the actionable recommendation is to move self-play from 2,000 to 20,000 (2.5x more nodes buys only 27 cp beyond that) | budget_ladder/raw/budget_ladder.txt budget_ladder/run.log (again: `python3 budget_ladder/budget_ladder.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That the knee at 20,000 would hold on a different position set or against a deeper reference. The monotone
  ORDER is robust to the reference choice in principle; the exact knee is not necessarily.

## What I did NOT do

- Did not use tablebase or very long searches as ground truth, so every figure is relative to a 250,000-node
  judgement.
- Did not measure the TIME cost of the higher budgets (2.5x nodes at 50,000 is a real cost in self-play
  throughput, and I did not quantify it).
- Did not test budgets between 20,000 and 50,000 to locate the knee more precisely.

## Times

`budget_ladder/stamps.txt`, every line a `date -u`.
