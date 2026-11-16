# S-C4 — CONFIRMS seat 04's 04-F14 / 04-F16, and CORRECTS my own S-F25's mechanism

Seat 04's claim: `go nodes N` finishes the iteration it is in and stops at an **iteration boundary**,
so the work done is quantised to the `nodes` values the `info depth k` lines report; N equal to a
boundary uses the whole budget, N = boundary − 1 falls back a whole iteration.

**Verdict: CONFIRMS, exactly as stated — and it corrects my own S-F25.**

**Threads 1** throughout (no `Threads` option sent), Hash 16, MultiPV 1, `OwnBook false`, startpos,
PC r15 build. My own harness (`checks/check_04f14.py`), which reads the position's own boundary list
first rather than assuming it.

## The position's boundaries (measured, not taken from seat 04's list)

`go depth 24` on startpos reports one `nodes` value per depth. Those numbers **are** the boundaries:

```
d1:26  d2:54  d3:215  d4:404  d5:1,001  d6:1,703  d7:2,574  d8:4,099  d9:9,653
d10:13,102  d11:23,975  d12:56,720  d13:72,062  d14:101,640  d15:212,340
d16:267,839  d17:600,227  d18:846,653  d19:920,173  d20:1,089,334 ...
```

## The quantisation, tested at three boundaries

`go nodes <boundary>` vs `go nodes <boundary - 1>`, fresh process each:

| budget | work done | ratio | stopped at | verdict |
|---|---|---|---|---|
| 1,001 (= d5) | **1,001** | **1.00** | depth 5 | full budget used |
| 1,000 (= d5 − 1) | 404 | 0.40 | depth 4 | fell back a whole iteration |
| 9,653 (= d9) | **9,653** | **1.00** | depth 9 | full budget used |
| 9,652 (= d9 − 1) | 4,099 | 0.42 | depth 8 | fell back a whole iteration |
| 72,062 (= d13) | **72,062** | **1.00** | depth 13 | full budget used |
| 72,061 (= d13 − 1) | 56,720 | 0.79 | depth 12 | fell back a whole iteration |

**3 for 3 at the boundary: exactly 1.00x. 3 for 3 at boundary − 1: a whole depth lost, down to 0.40x.**
That is seat 04's mechanism reproduced with my own boundary list.

## It is NOT a cap at the last boundary

Budgets far above the deepest boundary still work — the search simply continues:

| budget | work done | ratio | stopped at |
|---|---|---|---|
| 17,939,026 | 13,616,554 | 0.76 | depth 25 |
| 35,878,052 | 30,606,312 | 0.85 | depth 27 |
| 71,756,104 | 48,242,071 | 0.67 | depth 28 |

So the rule is "stop at the last boundary you can reach", not "stop early and give up".

## This corrects my own S-F25, and I am stating that plainly

My S-F25 said `go nodes N` "stops SHORT of N" and gave requested → reported of
100,000 → 72,062 (72 %), 300,000 → 267,839 (89 %), 1,000,000 → 920,173 (92 %).

**Every one of those three numbers is exactly an iteration boundary** — d13, d16 and d19 above. So:

- The **numbers in S-F25 are right** and still useful: nps must be computed from the reported count.
- The **mechanism in S-F25 was wrong**. It is not a shortfall or a cap; it is quantisation to
  iteration boundaries, which seat 04 explains and I have now reproduced.
- **The practical consequence I missed**: because the work is quantised, an A/B comparison at a fixed
  `go nodes` budget is not comparing equal work unless the budget is a boundary. Two positions can
  differ by 50-60 % in real work for the same nominal budget. That matters for seat 04's threaded
  comparison work and for anybody benchmarking with `go nodes`.

S-F25 is marked CORRECTED in my FINDINGS, cross-referencing S-C4 and seat 04's 04-F14/04-F16.

## The practical advice that follows (seat 04's, and my numbers agree)

**Send the boundary value itself as the budget.** It is the `nodes` field of the deepest
`info depth k` line you are willing to pay for. Sending one less wastes a whole iteration; sending a
value between boundaries wastes the difference.

## Files

- `checks/check_04f14.py` — the harness.
- `checks/check_04f14.json` — raw, every budget tested with its reported work and depth.
- `checks/check_04f14.meta` — exe hash, Threads 1, settings, date.

## What I am not claiming

- Not that these boundaries are the same on another machine or under other settings — they are
  position- and settings-specific, which is exactly why the harness reads them rather than hard-coding.
- Not that I reproduced seat 04's exact middlegame numbers; I used startpos, which is a cleaner
  reference and is reproducible by anyone.
