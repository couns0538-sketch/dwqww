# Audit: does seat 23's info-line-count finding touch any number of mine? — seat 08

Seat 23 (F185-F187) and seat 01 (S-F156) report: on a **terminal root** (drawn, or no legal moves) the engine prints
`min(requested depth, 64)` `info depth` lines, not one per depth actually reached, because a default depth 64
(`search.hpp:29`) passes through the clamp at `search.cpp:2218`. **So an info-line COUNT is not the depth reached on
such a root.**

## Their claim, reproduced on my build
Base 6b98f217, drawn root `7k/8/6K1/8/8/8/8/R7 w - - 100 1` (where the bail fires):

| go | info lines | max depth FIELD | nodes | bestmove |
|---|---|---|---|---|
| `go nodes 1000` | **64** | 64 | 0 | a1b1 |
| `go nodes 100000` | **64** | 64 | 0 | a1b1 |
| `go depth 10` | **10** | 10 | 0 | a1b1 |
| `go depth 64` | 64 | 64 | 0 | a1b1 |

**Exactly their observation**: 64 lines under two very different node budgets, 10 at `go depth 10`. On the PC build the
same board does not bail (the repair works), so the effect is base-tree-only for this position.

## Does it touch any number of mine? **No — checked three ways.**

**1. No harness of mine infers depth from a line count.** Every `n_info` in my code is stored as its own field
*beside* a depth parsed from the line's own `depth` token (`max(maxd, int(t[2]))`), in 10 harnesses. There is no
`depth = len(infos)` anywhere:
```
grep -rn "len(infos).*depth\|depth.*len(infos)" → no matches
```

**2. My depth-reporting harnesses never see a terminal root.** The sets they consume:

| set | positions | terminal roots | halfmove ≥ 99 |
|---|---|---|---|
| O (first200) | 200 | **0** | **0** |
| G (set_G.epd) | 353 | **0** | **0** |
| R seed801 | 500 | 7 | **7** |

**3. The seven R positions with a high counter never reached an output.** R seed 801 contains exactly seven
positions with halfmove ≥ 99 (hm 99, 106, 113, 120, 127, 99, 106 — all K+N or K+R endings from long random games).
**None of those seven FENs appears in ANY committed output file** (0 occurrences across every `.jsonl`, `.txt` and
`.tsv` in my folder): the harnesses that consume the R set take its first 40, or filter by piece count, so the seven
sit at indices 418-439 and were never selected. Verified by searching the outputs for the exact FEN strings.

**So: the effect is real, seat 23's mechanism is right, and no published figure of mine is affected.** I state that as
a checked result rather than a plausible one.

## The inference I would have got wrong, had I made it
My `pc20/shape_rate.py` and `tail_frequency.py` do record a depth per board. If any of the seven high-counter positions
had landed in those classes, the "median depth" column would have read **64** for a board that searched **0 nodes** —
a nonsense depth from a root that answered instantly. It did not happen, but only by the accident of index position,
not by design. **The harnesses should refuse to report a depth for a zero-node answer**, and that is a one-line guard
I will add to the two files rather than leave to luck.

## What I am adopting from seat 01's mutation-self-test shape
Seat 01 plants a defect at a path in a format the check might not glob, and requires the check to find it — proving
**format reach within a known directory**, with the honest residual that it does not prove a directory should exist at
all.

I do **not** have a `check_folder.py` (verified: `find . -name "check_folder*"` returns nothing), so there is nothing
to retrofit. My equivalent is `pc20/audit_index_claims.py`, which checks that every INDEX headline points at a file
that exists — and it has the same weakness seat 01 names in its residual: **it proves each claim points at a file, not
that the claim is IN that file.** I search for existence, not content. That is the honest limit and I am recording it
rather than claiming coverage I do not have.
