# REPORT — seat 15's class claim, run on my own positions (seat 05)

**Assignment:** measure whether, at the owner's clock then a completed deeper search on the same board, sparse endgames
gain mates that the clocked search reported only as a score, while middlegames do not. Seat 15 reported 2 of 5 sparse
(median 312 cp movement) and 0 of 5 middlegame (median 12 cp); seat 17 reproduced the counts.

**My configuration.** PC r15 build (patch sha256 prefix `d6bd72c531f785f4`, honesty 8/8), PC20, **Threads 1**, Hash 16,
`OwnBook false`, **fresh process for every search** (COLD). Clocked search `go wtime 6000 btime 6000 winc 60 binc 60`,
then `go depth D+4` where D is the depth the clocked search reached. Machine checked clean with seat 20's script
immediately before the run. My own positions: 8 sparse endgames constructed by hand, 8 middlegames generated from
random play with 20+ pieces (seeded, reproducible).

## The answer

| class | positions | gained a mate | median cp movement on the rest |
|---|---|---|---|
| **sparse endgames** | 8 | **4 (50%)** | **5.5 cp** (movements 5, 5, 6, 90) |
| **middlegames (20+ pieces)** | 8 | **0 (0%)** | **52.5 cp** (9, 21, 29, 36, 69, 78, 82, 244) |

**The direction reproduces robustly: sparse endgames gain mates, middlegames do not.** My sparse rate is higher than
seat 15's (4 of 8 vs 2 of 5) and my middlegame score movement is much larger (52.5 vs 12 cp), so the effect is
**class-level but its magnitude is position-set dependent** — as I would expect for a claim about "sparse endgames" as a
category.

## The per-position table

### Sparse endgames

| position | clocked | D | deeper (D+4) | gained mate? | movement | replay |
|---|---|---|---|---|---|---|
| KQ v K, king active `8/8/8/8/4k3/8/8/KQ6 w` | cp +7 | 19 | cp +12 d23 | no | 5 cp | — |
| KQ v K, king boxed `8/8/8/8/8/5k2/8/K1Q5 w` | mate +14 | 18 | mate +8 d22 | no | 6 cp | **mates at ply 15** |
| KR v K, king cut `8/8/8/8/4k3/8/8/K1R5 w` | cp +617 | 23 | mate +16 d27 | **YES** | — | **DOES NOT MATE** |
| KR v K, rook active `8/8/8/3k4/8/8/8/KR6 w` | cp +585 | 21 | mate +20 d25 | **YES** | — | **DOES NOT MATE** |
| KBB v K, bare `8/8/8/8/4k3/8/8/KBB5 w` | cp +7 | 19 | cp +12 d23 | no | 5 cp | — |
| KQ v KR, queen up `8/8/8/8/3rk3/8/8/K1Q5 w` | cp +327 | 19 | cp +417 d23 | no | 90 cp | — |
| KRP v KP `8/8/8/8/4k3/5p2/4P3/K1R5 w` | cp +1829 | 26 | mate +14 d30 | **YES** | — | **mates at ply 27** |
| KQ v K, far corner `7k/8/8/8/8/8/8/KQ6 w` | cp +1028 | 15 | mate +8 d19 | **YES** | — | **mates at ply 15** |

### Middlegames

| position | clocked | D | deeper (D+4) | gained mate? | movement |
|---|---|---|---|---|---|
| midgame 1 (25 pieces) | cp −582 | 19 | cp −651 d23 | no | 69 cp |
| midgame 2 (31 pieces) | cp +170 | 16 | cp +134 d20 | no | 36 cp |
| midgame 3 (29 pieces) | cp +86 | 15 | cp +77 d19 | no | 9 cp |
| midgame 4 (32 pieces) | cp +1313 | 15 | cp +1395 d19 | no | 82 cp |
| midgame 5 (31 pieces) | cp +280 | 16 | cp +309 d20 | no | 29 cp |
| midgame 6 (31 pieces) | cp +1275 | 15 | cp +1519 d19 | no | 244 cp |
| midgame 7 (28 pieces) | cp −355 | 16 | cp −433 d20 | no | 78 cp |
| midgame 8 (31 pieces) | cp +129 | 18 | cp +108 d22 | no | 21 cp |

## What the replay rule added — and it changed the result

Of the 4 sparse positions that "gained a mate", **2 do not actually mate**:

| position | claimed | promises | PV | replay verdict |
|---|---|---|---|---|
| KR v K, king cut | `mate +16` | 31 plies | 28 plies, all legal | **final position NOT checkmate** (33.9 M nodes) |
| KR v K, rook active | `mate +20` | 39 plies | 25 plies, all legal | **final position NOT checkmate** (2.88 M nodes) |

So the honest count is: **the score gains a mate label in 4 of 8 sparse endgames, but only 2 of those 4 have a PV that
delivers the mate.** The other 2 are the same truncation defect as S-F63/S-F64, now at |N| = 16 and 20 — long endgame
mates, which extends the defect's range beyond the middlegame boards I had before.

**Stated plainly: had I used the ply-length comparison instead of the replay, I would have logged these two as short
PVs, not as lines that do not mate.** The length test does catch them here — the counts are short (28 vs 31 plies, 25 vs
39) — but it reports a *quantity* defect ("the PV is shorter than the score needs") where the replay reports a *fact*
("the line printed does not end in checkmate"). Those are different statements about the same board:

- a short PV could, in principle, still end in mate early — which would be a different (and benign) situation;
- a line that replays legally and does not mate **cannot** be a mate, whatever its length.

So the length comparison infers the defect from a proxy and the replay proves it. For a training label the difference
matters: "this mate score has a short PV" invites the reading "the score is a bound the PV did not finish printing", while
"this mate score's line does not mate" says the label itself is not delivered by the engine's own output. The second is
what a label consumer needs to know, and it is what I recorded in S-F66.

## A correction I made while checking

My first medians were **6 cp** and **69 cp**. Both were wrong: my median helper took `sorted[n//2]` on an even-length
list, which returns one of the two middle values rather than their mean. Re-deriving from the raw table gives **5.5** and
**52.5**. The helper is fixed in the script; the corrected values are what appear above. The direction of the result is
unchanged, and the corrected middlegame figure (52.5) is further from seat 15's 12 cp than my wrong one was.

## Limits

- **My positions, not theirs.** Different sets, so different rates are expected; the class-level direction is what
  replicates, not the numbers.
- **8 + 8 positions.** Small. A 4-of-8 vs 0-of-8 split is suggestive, not a rate.
- **D+4 is my choice.** A larger jump might find mates in middlegames too; a smaller one might find fewer in endgames.
  I did not sweep it.
- **No cause claimed.** I did not read the search; the "gain a mate when the search completes" behaviour is consistent
  with depth being what finds mates, but I have not demonstrated that.
- Everything Threads 1, COLD, one engine process at a time.

## Evidence
`out/run1.txt` (full run with both tables), `out/suspect_mates.txt` (the two non-mating mates re-run with full PVs).
Script: `deepgain_test.py`. Findings: S-F65, S-F66.
