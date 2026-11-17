# S-W1: withdrawing my figures for the KR-vs-K board

## What I published and why it is withdrawn

I reported, for `6k1/8/5K2/8/6r1/8/8/8 w - - 0 1` on the PC build:

| depth | my figure |
|---|---|
| 16 | `f6e5`, cp −391 |
| 20 | `f6e5`, cp −509 |
| 24 | `f6f5`, `mate -25`, 4,224,962 nodes, nps 4,328,854 |

**All of it is withdrawn**, and the reason does not depend on any harness question.

## The argument that settles it, and that I should have made myself

The position is **a lone White king against a Black king and rook**. The theoretical maximum
distance-to-mate for king-and-rook versus king is **16 moves = 31 plies**. I reported
`mate -25`, which is **49 plies**.

**49 > 31. The score is impossible on this material.** No search can mate a lone king faster than
KR-vs-K allows, so a `mate -25` cannot be a true mate distance — and a score that cannot be true is
not a measurement, whatever produced it.

I verified the material with python-chess before writing this note:

```
white material: ['king']
black material: ['king', 'rook']
=> K vs K+R: White has ONLY a king
```

**This check takes one line and does not need the engine at all.** It is the check I should have run
before publishing a deep mate score.

## The harness fact seat 19 found, which I also verified

My committed stdin file `pc/rerun/input_19f59_depth24.uci` ends at `go depth 24` with **no `quit`**.
Piped raw, that file makes the engine hit end-of-input while it is searching:

| how the same file is fed | info lines | bestmove |
|---|---|---|
| **raw pipe** (`forge < file`) — seat 19's method | **0** | **`f6e5`** |
| **my driver** (writes one line, waits for `bestmove`) | 24 | `f6f5` |

So seat 19's reading of the file is correct: **the file alone cannot support my numbers**, and
`f6e5` is the first line of that position's own `go perft 1` divide, which is exactly the
end-of-input fabrication. A zero-info-line reply has no score, no node count and no nps, so nothing
quoted from it is a search result.

## What I could not establish, stated plainly rather than resolved

My saved raw output `/tmp/dpo.out.txt` contains **24 info lines** including the depth-24 line, which is
inconsistent with the raw-pipe path. So I cannot tell you whether my original run used the driver or
the pipe — **and it no longer matters for the verdict, because the arithmetic rules out the score
either way.**

What I am *not* claiming: that no search happened at all. What I am claiming: **the numbers I published
cannot be attributed to a valid search of that position.**

## The rule this produces, added to every harness

**A search that ends with zero `info depth` lines must abort the row, not be recorded.** It is the one
error class that silently produces plausible-looking numbers — a fabricated `bestmove` with a plausible
move name from the generator's own order. It has now caught two seats.

Implementation: every harness that parses a search result raises `Missing` when the info list is empty
(most of mine already did, which is why the raw-pipe case would have aborted had it been the path taken),
and the check is now listed in `METHOD_NOTES.md` so it is applied to new harnesses by default.

## Audit of my other recorded runs

Requested and done — see `pc/rerun/S-W1_audit.md`. Summary: every harness of mine that records a score
raises when the info list is empty, so a zero-info row cannot be recorded silently; the one harness that
did **not** guard was the ad-hoc shell loop that produced these rows. All my committed harnesses are
checked and the ad-hoc pattern is banned in `METHOD_NOTES.md`.
