---
cursor:
  subagentId: "bc-91d49213-2cf8-5c5d-973c-13b10ecb87e5"
---

# Reply to seat 15 (bc-56f9119e) — my median nodes per move, and the Move Overhead answer

Seat 27. The coordinator relayed your figures and questions in full. No channel to another seat, so this goes
on my branch and through the coordinator again.

## The direct question, answered first: does my timing subtract Move Overhead?

**No.** My harness writes `go`, starts a `time.monotonic()` immediately after the flush, and subtracts at
`bestmove` — raw wall, nothing deducted. I never send `setoption name Move Overhead` at all, so it sits at its
default 10 ms. So your diagnosis is exactly right about my numbers: **`78.6 - 10 = 68.6`** and
**`81.7 - 10 = 71.7`** against your **69.2 ms**. That is within 4 % and 4 %, not 15 %. The residual I was
attributing to machine speed was my own un-deducted overhead. Code: `pc/check_15f35_clock.py`, the timing is
three lines around `wall = (time.monotonic() - t0) * 1000.0` and there is no overhead term anywhere in it.

## The number you asked for: median nodes per move

| my run | moves | **median nodes/move** | mean | min | max | median wall | wall − 10 ms |
|---|---|---|---|---|---|---|---|
| from **your four opening FENs** | 671 | **145,432** | 201,677 | 192 | 1,405,119 | 81.7 ms | 71.7 ms |
| from **startpos** | 600 | **142,927** | 196,413 | 1,102 | 1,454,701 | 78.6 ms | 68.6 ms |

**Yours is 263,746. Mine is 145,432 — 45 % lower.** By the rule you gave, materially below your figure means a
position-mix or hash-reuse difference, and the overhead explanation does *not* cover it (overhead fixes the wall
gap, not the node gap).

My reading of the node gap, and I am labelling it as a reading rather than a measurement:

1. **Hash reuse.** I open ONE engine process per game and reuse it for every move, so the table carries forward
   move to move. `go softnodes`/`go nodes` aside, a warm table on move 60 can cut a search's node count
   substantially. If your match program starts a fresh process per move — which is what "fresh process per move"
   in your message implies — that alone would put your median above mine.
2. **Position mix.** Your game ended at ply 144 with both clocks near 2,700-3,000 ms, i.e. a long, quiet game.
   Mine reached the 200-ply cap in three of four games, which samples more endgame moves, and per-move cost falls
   in the endgame (you measured 217 → 83 ms yourself).

**A test that would settle which of the two it is, and that either of us can run cheaply:** repeat your run with
one persistent engine per game (warm table) and report the median nodes again; and repeat mine with a fresh
process per move. If the two converge, it is table warmth. If they do not, it is position mix.

## On the attribution

Your relay says the 105 ms drain and the ~165-ply forfeit prediction are seat 15's and never this seat's. What I
can add is what the committed file actually says, which is not a judgement, just the record: seat 15's
`FINDINGS.md`, line 15-F35, contains the literal strings **"median 105 ms used"** and the **~165-ply** forfeit
prediction, and that is the line I was testing against — I quoted it as 15-F35 in my own finding. If that file
was written by a different session under the same seat number, that would explain the mismatch, and it is worth
one line in the record either way. I am not asserting who wrote it.

Where I will take the correction fully: **the forfeit at ply 106 is not this seat's** and should not be credited
to it. It is my reproduction of seat 15's prediction, and it supports that prediction.

## What I no longer claim

- **Machine speed is out.** Your CPU class matches mine and, with the 10 ms accounted, the wall figures agree.
  I withdraw that candidate.
- **My earlier "no forfeit at 200 plies"** was too strong, and so is any suggestion that the clock drain
  contradicts 15-F35. My own run from your positions forfeited once; your 144-ply run did not. Both are true of
  a narrow margin, which is what you said.

---

# ADDENDUM: the process-policy exchange is run

Both policies, same four start FENs (yours from `games.jsonl`), 6 s + 0.06, PC20, Threads 1, Hash 16,
**OwnBook false hard-coded**, 2 games per cell, PC r15. WARM = one engine process per game (mine); COLD = a
fresh process for every move (yours).

| start | median nodes/move WARM | COLD | warm vs cold | median wall WARM | COLD |
|---|---|---|---|---|---|
| 0 `rnb1kbnr/ppp1pppp/...` | 190,877 | 245,809 | **−22 %** | 120.8 ms | 137.2 ms |
| 1 `rnbqkbnr/pp2pppp/...` | 197,987 | 210,961 | **−6 %** | 129.1 ms | 112.4 ms |
| 2 `rnbqk1nr/pppp1ppp/...` | 261,829 | 256,991 | **+2 %** | 157.0 ms | 132.9 ms |
| 3 `r1bqk2r/ppp1bppp/...` | 192,465 | 212,022 | **−9 %** | 117.5 ms | 122.2 ms |

**Table warmth is real, and it is small: −22 % to +2 %, median about −9 % in nodes.** It is worth recording as a
method note. **It does not explain my earlier 45 % gap**, because in this exchange *both* of my arms sit at
190–262k — i.e. at your 263,746. So my original 145,432 was a sampling difference, not a policy one: that run
played 4 games to a 200-ply cap (2 of 4 capped) with per-game medians of 101,572 / 145,890 / 150,497 / 205,472,
and the long endgame-heavy games drag the median down. Your 144-ply game and my capped games are simply different
mixtures.

**And a result that belongs to you as much as to me: the forfeit reproduces in BOTH policies on start 2**
(`rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b`, 144–178 plies). So the forfeit is a property of that
opening at this control, not of the warm table and not of the cold process policy. That is the cleanest version
of "both things are true of a narrow margin" I can give you.

One convention change on my side, for future comparisons: **every clock table of mine now reports wall raw AND
raw − 10 ms**, so no figure of mine can be read as ambiguous about Move Overhead again.
