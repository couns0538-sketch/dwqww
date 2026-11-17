# CORRECTION to S-F24 (job 20): the original numbers were contaminated by process reuse

## What went wrong
My first version of `job20/clockgain.py` created **one** engine process and ran every search of all 16
positions through it: 32 clock searches plus up to 8 depth-16 scoring searches, all sharing one transposition
table. The warm table changes what the search finds, so **scores and even moves drifted with position order**
rather than with the clock.

I found it while auditing process reuse after establishing (in S-C7) that `ucinewgame` is a cold reset and
that a warm table changes node counts dramatically (52,591 → 27,239 → 21,407 on repeated searches). That
prompted a direct test of the same position scored fresh versus warm:

| | fresh process | after ~30 earlier searches in the same process |
|---|---|---|
| position 15, `h6h5` at depth 16 | **cp 2231** | cp 2311 |

An 80 cp shift on an identical request. So the first run measured a mixture of position order and clock, not
the clock.

## The corrected measurement
Same 16 G positions, same 2,000 vs 60,000 ms, PC20 / Threads 1 / Hash 16 — but now **a fresh process for
every single search**.

| | original (one shared process) | **corrected (fresh per search)** |
|---|---|---|
| positions changing move | 5 of 16 | **1 of 16** |
| longer-clock move better | 4 | **1** |
| longer-clock move worse | 1 | **0** |
| median gap | +58 cp | **+17 cp** |
| median depth 2 s → 60 s | 15 → 24 | 15 → 23 |

The one remaining changed position is position 0 (`g7g6` at 2 s → `e5e4` at 60 s), better by **+17 cp**.

## Direct demonstration that process reuse manufactured "changes"
Six positions, short and long clock, run both ways:

| position | fresh: 2 s / 60 s | shared: 2 s / 60 s |
|---|---|---|
| `1r6/2k2pp1/2p2n2/2Pppb1p/...` | `g7g6` / `e5e4` | `g7g6` / `e5e4` (agrees) |
| `r3r1k1/p1bb1ppp/1p1q4/...` | `b6b5` / `b6b5` | `b6b5` / `b6b5` |
| `6k1/p4r1p/1p2Q3/...` | `g1g6` / `g1g6` | `g1g6` / `g1g6` |
| `5R2/5npp/5k2/...` | `f6e7` / `f6e7` | `f6e7` / `f6e7` |
| `8/1p1k1KN1/4pB2/...` | `f6g5` / `f6g5` | `f6g5` / `f6g5` |
| **`8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w`** | **`f4f5` / `f4f5`** | **`e4f5` / `f4f5`** ← a "change" that is not one |

In the shared run the 2 s search answered `e4f5` while the 60 s search answered `f4f5`, so that position
counted as "the clock changed the move". In a fresh process **both clocks answer `f4f5`** — the position does
not change with the clock at all. The apparent change was the warm table.

## What survives and what does not
**Survives:** the *direction*. In the one genuinely changing position, the longer clock's move is better
(+17 cp). And the mechanism is still visible in the data — median depth reaches 23 at 60 s versus 15 at 2 s.

**Does not survive:** the *magnitudes*. "5 of 16 positions change", "4 of 5 better", "median +58 cp" were all
inflated by the shared process. The corrected statement is much weaker: **1 of 16 positions changed, and it
changed for the better by 17 cp.** A single case supports a direction, not a rate.

**Also withdrawn:** the +984 cp extreme in the original table. That margin came from scores measured under
accumulated state; in fresh processes the position-15 moves were not even both chosen at those clocks, so the
comparison that produced it no longer exists in the corrected data.

## The lesson (and it is the same one as S-C7, from the other side)
**A harness that reuses one process across many searches measures a moving target.** I had written that rule
into my traps note the same evening — and then violated it in a finding about search behaviour. Warm state
changes node counts, scores and sometimes moves; any comparison of *search results* across positions or
settings needs a fresh process per search, or an explicit cold reset, and must say which.

Two safeguards now in place: `clockgain.py` creates a fresh `Eng` per search (the reason is written into the
`score_move` docstring), and `lib/settings.py` already asserts the option list so the settings side is sound.

## Corrected finding
**S-F24 (corrected):** over 16 G positions at 2,000 vs 60,000 ms with a fresh process per search, only
**1 position changes its move** with the clock, and there the longer clock's move is **better by 17 cp** at
equal depth 16. Median depth reached rises 15 → 23. The earlier figures (5 changed, 4-of-5 better, median
+58 cp, one case at +984 cp) came from a shared engine process and are **withdrawn**. This remains a
self-consistency measure, not ground truth, and no match was run, so there is no Elo claim.

## Files
`out_fresh/clockgain.json` (corrected, fresh per search), `out/clockgain.json` (the withdrawn shared-process
run, kept so the difference can be inspected), `stamps2.txt`.
