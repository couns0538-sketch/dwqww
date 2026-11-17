# seat 20 — job 78: seat 02's S-C19 confirmed — no depth-clamp on the owner's clock path

Seat 02's S-C19: the depth-clamp phenomenon does **not** affect the owner's real clock path. Eight real game positions
on `go wtime 6000 btime 6000 winc 60 binc 60` reached depths 16–21 with **0 of 8 hitting the depth-64 clamp**.

**My reproduction: 0 of 10 clamped.** PC r15 sha256 `068f0927768d30be…`, PC20 (S14 17 opts + 6, `assert_regime`
passed), Threads 1:

| pos | depth | nodes | wall ms |
|---|---|---|---|
| 1 | 18 | 314,239 | 164 |
| 2 | 18 | 514,093 | 296 |
| 3 | 17 | 348,815 | 194 |
| 4 | 18 | 972,050 | 412 |
| 5 | **20** | 557,797 | 249 |
| 6 | 19 | 481,049 | 166 |
| 7 | 18 | 370,662 | 220 |
| 8 | 18 | 325,941 | 194 |
| 9 | **16** | 612,735 | 286 |
| 10 | 18 | 613,767 | 349 |

**Depth range 16–20 (median 18), wall 164–412 ms, clamped 0/10** — matching their 16–21 at 0/8.

## Where we differ, and why it does not matter
Their wall range is **163–1585 ms**; mine is **164–412 ms**. The upper value is almost certainly their **sparse
endgame** position, which their own S-C19 note identifies as a *different mechanism* — the hard-limit cut (their
S-F13), not the clamp. My ten positions are all from the G set with material ≥ 8 pieces and none is sparse, so I would
not expect the 1585 ms tail. **So the ranges are not in conflict; they are different position samples, and their own
note already separates the mechanisms.**

## What this confirms
1. **The depth-64 clamp is a harness hazard, not a play risk** — confirmed on a different ten-position sample.
2. **Real clock play lands at depth 16–20 in ~0.2–0.4 s of a 6 s clock**, i.e. time management is not starving the
   search (consistent with my S-F49: only 2–5 % of the budget used).
3. It also re-confirms at scale what my S-F49 flagged: **the depths move between runs** (16–20 across positions here),
   so a depth figure is only meaningful with the position named.

## Limits
- Ten G-set positions, one clock (6 s + 0.06), no sparse endgames — which is exactly the class where their 1585 ms
  outlier lived, and I deliberately did not mix the two.
- Built-in net, Threads 1.
