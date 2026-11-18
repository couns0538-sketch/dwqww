# sol3 Job 18 — Short-mate census with more pieces

## (1) Step 0 — reader build passed

Linux cloud, Case A. The Job 16 reader executable matched SHA-256
`40ace81ab55777c1e46787b079c35d02279b7eab59dcf70068a33a167894f910`.
Independent processes reproduced all five counts with built-in
evaluation. The PC20 processes used Threads 1 and Hash 16.
[Raw pins and commands](sol3/job18/stage0)

| Profile | bench 11 nodes | bench 13 nodes | startpos perft 5 nodes |
| --- | ---: | ---: | ---: |
| Default | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

## (2) K1 — P ladders matched

Both fresh-search ladders matched Job 17 on requested and reported
depth, bestmove, score type and value, and last-info nodes in all
20 rows each. Same reader build, built-in evaluation, one thread,
Hash 16, NullMateGuard 0, fresh game for each requested depth 1–20.

| Setting | Matching rows | First `g3g6 mate 2` depth and nodes | D20 move, score, nodes |
| --- | ---: | --- | --- |
| [A](sol3/job18/K1/A) — S14 | 20/20 | D16, 240,516 | g3g6, mate 2, 241,262 |
| [B](sol3/job18/K1/B) — S14 q2/c0 | 20/20 | None through 20 | f6h5, cp 814, 957,869 |

## (3) K2 — 120-position extraction matched

Python-chess module 1.11.2 verified the pinned F7k PGN hash
`9c89d7bbb8ea2b66c24625881775c48a6f4a17e23fd64c5f98b158e6934f41b1`,
replayed 2,000 games, and identified 1,438 terminal checkmates.
132 had at least 14 pieces seven plies before the final mate and at
least eight plies in the game. I selected the first 40 and took each
position 3, 5, and 7 plies before the end, recording its own piece
count. Every continuation replayed legally to the same checkmate.
The selected games range from file game 45 to 512.

The extracted file and Opus's expected file both have SHA-256
`b2131c5af5307ac14174fe30d66780d8007dab68c7fbc6a8b9126f52637389ab`.
Both endpoint lines matched. There are 48 roots with 12–15 pieces,
52 with 16–19, and 20 with at least 20.
[F7k provenance](sol3/job18/F7k.provenance.txt) · [Extraction receipt](sol3/job18/K2.txt) · [Positions](sol3/job18/positions.txt)

## (4) Prediction graded

The [forecast](sol3/job18/prediction.md) was pushed alone as
`88d92fe8c6eccfcb4985d98cd4ccb3fc2fedec8b` before the first census
search. All six observations fell in range and none matched the
point estimate. I overestimated quiet-only misses, both profiles'
delays, and recoveries from B.

| Outcome | Point and range | Observed |
| --- | --- | --- |
| B misses on M | 3%, 0–12% | 0/113, 0% |
| B later on M | 10%, 0–25% | 5/113, 4.42% |
| E misses on M | 4%, 0–15% | 2/113, 1.77% |
| E later on M | 17%, 3–35% | 5/113, 4.42% |
| C recovers B misses | 1, 0–8 positions | 0 |
| D recovers B misses | 2, 0–8 positions | 0 |

[UTC checkpoint order](sol3/job18/stamps.txt)

## (5) Census — 120 positions, one iterative search each

M consists of the 113 roots whose S14 A final score was positive mate.
The first positive exact mate line determines earlier, same, later,
or missing through depth 16. All seven settings used the same reader
binary, built-in evaluation, Threads 1, Hash 16, MultiPV 1, and
NullMateGuard 0. The table follows run order.

| Setting | Positions with mate | Earlier / same / later / none on M | Mates outside M |
| --- | ---: | --- | ---: |
| [A](sol3/job18/census/A) — S14 defaults | 113 (M) | 0 / 113 / 0 / 0 | 0 |
| [B](sol3/job18/census/B) — A with quiet 2, correction 0 | 113 | 2 / 106 / 5 / 0 | 0 |
| [D](sol3/job18/census/D) — B with R3 plain | 112 | 1 / 107 / 4 / 1 | 0 |
| [C](sol3/job18/census/C) — B with R1 plain | 112 | 2 / 109 / 1 / 1 | 0 |
| [E](sol3/job18/census/E) — PC20, halves follow legacy 2 | 112 | 11 / 95 / 5 / 2 | 1 |
| [G](sol3/job18/census/G) — E with quiet 0 | 113 | 13 / 94 / 5 / 1 | 1 |
| [F](sol3/job18/census/F) — E with R3 plain | 112 | 12 / 94 / 5 / 2 | 1 |

The only outside-M find was row 99, game 390, seven plies before
the end, 15 pieces. E/G/F first found mate at D12/D11/D12 and finished
D16 with `a8a2 mate 5`. A finished D16 with `a8a3 cp 2080`.

```text
r4k2/2N2p1p/6p1/2p1B3/1pP1n2P/6P1/7r/2K5 b - - 7 43
```

The independent parser matched all 840 census searches and 40 K1
searches to the raw transcripts and commanded settings. First exact
mate presence and last positive mate presence agreed on every census
row. [Census readback](sol3/job18/audit/census.json) · [K1 readback](sol3/job18/audit/K1.aggregate.json)

## (6) Every miss and the piece-count splits

| FEN | Game | Plies | Pieces | A first mate depth | Setting's last result at D16 |
| --- | ---: | ---: | ---: | ---: | --- |
| `1k6/p1p2p2/1p5B/3r1b1P/1PK2P2/8/P3rP1R/8 b - - 2 44` | 91 | 7 | 16 | 13 | C `d5d3 cp 2196`, 216,292 nodes<br>E `d5d3 cp 2268`, 238,023 nodes<br>G `f5e6 cp 1847`, 254,209 nodes<br>F `d5d3 cp 2317`, 291,274 nodes |
| `5rk1/n5b1/1R5p/p1p5/8/P4N1P/5PP1/1Q4K1 w - - 1 36` | 428 | 7 | 15 | 16 | D `b6b7 cp 2930`, 693,424 nodes<br>E `b6b7 cp 2390`, 475,049 nodes<br>F `b6b7 cp 3042`, 732,121 nodes |

These are all seven missed setting-position combinations, on rows 12
and 105. B missed none. Every bin below shows the total positions
with mate, then earlier/same/later/none on its part of M, then
outside-M finds.

| Setting | 12–15 pieces (M 47 of 48) | 16–19 pieces (M 49 of 52) | 20+ pieces (M 17 of 20) |
| --- | --- | --- | --- |
| A | 47 · 0/47/0/0 · 0 | 49 · 0/49/0/0 · 0 | 17 · 0/17/0/0 · 0 |
| B | 47 · 1/44/2/0 · 0 | 49 · 1/45/3/0 · 0 | 17 · 0/17/0/0 · 0 |
| D | 46 · 0/44/2/1 · 0 | 49 · 1/46/2/0 · 0 | 17 · 0/17/0/0 · 0 |
| C | 47 · 1/45/1/0 · 0 | 48 · 1/47/0/1 · 0 | 17 · 0/17/0/0 · 0 |
| E | 47 · 6/36/4/1 · 1 | 48 · 4/43/1/1 · 0 | 17 · 1/16/0/0 · 0 |
| G | 48 · 7/36/4/0 · 1 | 48 · 5/42/1/1 · 0 | 17 · 1/16/0/0 · 0 |
| F | 47 · 6/36/4/1 · 1 | 48 · 5/42/1/1 · 0 | 17 · 1/16/0/0 · 0 |

## (7) Part 2 — Job 17 row 24 at depth 22

I reran the ten-piece game 8 root once each under D and A after
the census. The first 16 info lines for each setting reproduced
Job 17 on stable fields and PV. D still reported `f6d4 cp 2108` at
depth 16 with 146,941 nodes. Continuing that search found an exact
mate at depth 19. A found its first at depth 13. Both returned
`d5d6 mate 6` at the final depth.

| Setting | First exact positive mate depth and nodes | Final D22 bestmove, score, nodes |
| --- | --- | --- |
| [D](sol3/job18/part2/D) | D19, 1,159,755, mate 6 | d5d6, mate 6, 1,722,340 |
| [A](sol3/job18/part2/A) | D13, 81,457, mate 11 | d5d6, mate 6, 930,647 |

D final output

```text
info depth 22 seldepth 53 score mate 6 nodes 1722340 nps 1320812 hashfull 529 time 1304 pv d5d6 d3b4 d6b6 a6a7 f6d6 b4a6 b6a6 a7b7 d6c6 b7b8 a6a8
bestmove d5d6
```

A final output

```text
info depth 22 seldepth 32 score mate 6 nodes 930647 nps 1548497 hashfull 306 time 601 pv d5d6 d3b4 d6b6 a6a7 b6b5 b4d5 f6f7 d5e7 f7e7 a7a6 e7b7
bestmove d5d6
```

[Depth-16 prefix check](sol3/job18/part2/prefix_readback.txt)

## (8) What the readers changed on this fixture

The quiet twin alone missed none of A's 113 mates. B delayed five
(4.42%) and brought two forward. In the sparser Job 17 fixture the
same contrast missed none of 89 and delayed one (1.12%).

Plain R1 in C removed all five B delays relative to A, introduced
one later find elsewhere, and missed row 12, which B had found at
D10. Plain R3 in D removed one B delay and missed row 105, which B had
found at D15. Neither reader had a B miss to recover. Both changed
timing and could harm a position in this sample.

Full PC20 missed two of A's mates and gained row 99. Disabling the
quiet half in G recovered game 428's row 105 at D15. Plain R3 in F
recovered neither of the PC20 misses. At row 12, B and D found mate at
D10, while C and all three PC20 arms missed it by D16. PC20 and S14
differ in other search settings. The E–G and E–F pairs measure the
effect of disabling the quiet half and making R3 plain within PC20.
[Paired readback](sol3/job18/audit/census.json) · [Job 17 report](REPORT_sol3_job17.md)

### Facts

- The census used `ucinewgame`, an `isready` barrier, the saved
  FEN, and one `go depth 16` per root. First exact positive mate
  lines omit aspiration bounds. The optional repeat used one
  `go depth 22` under each setting, with the same build and other
  options. [Runner](sol3/job18/search18.py) · [Reader build](sol3/job16/readers_build.txt)
- The F7k games were produced with a different binary at 2,000 nodes
  per side, seed 7203. Three roots are drawn from each selected
  game's actual continuation. Piece count is the sampling condition,
  and the observed mate in the game need not be the forced distance
  against best defense. [Game provenance](sol3/job18/F7k.provenance.txt)

### Suspicions

Plain R1 can move a quiet branch earlier, and plain R3 can change
the depth at which a late quiet is tested. Either intervention can
help one root and hurt another because it changes which paths
produce the history and TT state for later depths. The paired
changes identify which inputs matter in each arm, while their
first divergent internal search steps remain untraced.

### What I did not do

I kept the F7k PGN in scratch and published the position list and
text evidence. I used the depth-22 extension only on Job 17's row 24.

### What I am not sure about

Whether the two Job 18 misses would persist above depth 16, which
internal move or cutoff causes each switch to change the outcome,
and how the pattern carries over to a different set of games.

### Limits of this check

The PC's own net and exe; mates longer than about 4 moves; positions not near a mate; mates the losing side could have avoided earlier; games.
