# seat 20 — job 46: the PC build's `mate 8` at halfmove 85 is REAL (proved exactly)

Owner's question: at halfmove 85 the PC build reports `mate 8` where the base says `cp 349`. Is that mate real, and
does the base find it at higher depth?

## Answer: yes, real, and the distance is exactly right — proved by exhaustive search

I ran an exact game-theoretic test on `1K6/8/8/3R4/8/8/8/k7 w - - 0 1` (White to move, White is the mater):
"can White force mate within n plies **against every black defence**", memoised, no heuristics.

| n plies | White forces mate within n? |
|---|---|
| 1 | **False** |
| 3 | **False** |
| 5 | **False** |
| 7 | **False** |
| 9 | **False** |
| 11 | **False** |
| 13 | **False** |
| **15** | **TRUE** |

So the true forced distance is **15 plies = mate 8**, and no shorter mate exists. **The PC build's `mate 8` is
correct at depth 10, and the base tree's `cp 349` at the same depth is simply a missed mate.** That is a small,
concrete strength point for the r15 tree — a forced win found where the base tree does not see it.

## The PV is truncated, which is what made me doubt it
`go depth 10` on the PC build prints the PV `d5b5 a1a2 b8c7 a2a3 c7c6 a3a4 c6c5 a4a3 c5c4 a3a4` — **10 plies, all
legal, NOT checkmate**. A `mate 8` score needs 15 plies, so the printed line stops 5 plies short. That is ordinary
PV truncation at a hash/extension boundary, and it is why the score and the line disagree; the score is right.

## Does the base build find it at a higher depth?
No — not at any depth I tested, and the node counts show why:

| base depth | score | pv | nodes |
|---|---|---|---|
| 10 | cp 349 | 12 | 29,104 |
| 11 | cp 351 | 14 | 57,984 |
| 12 | cp 342 | 12 | 269,633 |
| 13 | cp 372 | 13 | 7,521,569 |
| 14 | cp 330 | 14 | 24,406,646 |

It keeps reporting a large `cp` score and never claims a mate. The PC build's first mate claim is at **depth 10**
(depth 8 gives `cp 444`, depth 9 `cp 455`).

## What this means
1. **The mate is not a PC artefact** — it is the truth, verified independently of both engines.
2. **`MateAlphaGuard` is the likely reason the PC sees it** (my S-F38 isolated that switch on another board), which
   makes this a second, independent demonstration that the switch finds real mates the base tree misses.
3. **It also retires the suspicion I raised in job44.** I had listed "`mate 8` where base says `cp 349`" as an
   unexplained detail; it is now explained and correct, with the truncation as the only oddity.

## Honest limits
- One position (K+R v K, a textbook endgame), depth 10 for the PC claim.
- The exact solver took 30.7 s and 451,932 memoised nodes to reach 15 plies; I did not push it further because the
  answer at 15 was already positive and every shorter distance was refuted.
- PV truncation is common and not a defect; I record it only because it made the score look unbacked.
