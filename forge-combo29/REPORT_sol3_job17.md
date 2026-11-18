# sol3 Job 17 — Short-mate census on F7k

## (1) Step 0 — reader build passed

Linux cloud, Case A. The Job 16 reader executable matched SHA-256
`40ace81ab55777c1e46787b079c35d02279b7eab59dcf70068a33a167894f910`.
A separate process for each pin reproduced all five counts below with the
built-in evaluation. The fresh PC20 processes used Threads 1 and Hash 16.
[Raw pins and commands](sol3/job17/stage0)

| Profile | bench 11 nodes | bench 13 nodes | startpos perft 5 nodes |
| --- | ---: | ---: | ---: |
| Default | 312,866 | 862,329 | 4,865,609 |
| PC20 | 278,024 | 587,276 | — |

## (2) K1 — seven fresh-search ladders on P

All six reference ladders matched on requested and reported depth,
bestmove, score type and value, and last-info nodes, 120 of 120 rows.
G was a new ladder. Each search used built-in evaluation, one thread,
Hash 16, NullMateGuard 0, and fresh game state at each depth from 1 to 20.

| Setting | Reference | First `g3g6 mate 2` depth and nodes | D20 move, score, nodes |
| --- | --- | --- | --- |
| [A](sol3/job17/K1/A) | Astra5 `follow_off`, 20/20 | D16, 240,516 | g3g6, mate 2, 241,262 |
| [B](sol3/job17/K1/B) | Job 16 quiet-only, 20/20 | None through 20 | f6h5, cp 814, 957,869 |
| [C](sol3/job17/K1/C) | Job 16 S14 L1, 20/20 | D18, 709,856 | g3g6, mate 2, 710,342 |
| [D](sol3/job17/K1/D) | Job 16 S14 L3, 20/20 | D15, 153,147 | g3g6, mate 2, 154,711 |
| [E](sol3/job17/K1/E) | Job 16 PC20 all-zero, 20/20 | None through 20 | f6h5, cp 916, 1,052,250 |
| [F](sol3/job17/K1/F) | Job 16 PC20 L3, 20/20 | D18, 550,507 | g3g6, mate 2, 551,879 |
| [G](sol3/job17/K1/G) | New | D17, 287,961 | g3g6, mate 2, 288,602 |

K1 uses independent fresh searches for each requested depth. The census
uses one iterative search per root, whose hash and histories carry over
between depths. First-depth results are comparable within each protocol.

## (3) K2 — fixture matched

I verified the F7k source PGN hash
`9c89d7bbb8ea2b66c24625881775c48a6f4a17e23fd64c5f98b158e6934f41b1`.
Python-chess module 1.11.2 replayed all 2,000 games and found 1,438
terminal checkmates of at least eight plies. I took the first 30 in
file order and extracted 3, 5 and 7 plies before each final position.
All 90 roots had the recorded winner to move. The replayed suffix
reached the game's final checkmate.

Both the extracted list and Opus's expected list have SHA-256
`ce9c50e11ae4a0a7f27b3561bb8677a4551ba2b546e7be11a35a991c547f33b5`.
Game 1 at 3 plies and game 43 at 7 plies matched the specified endpoints.
[F7k provenance](sol3/job17/F7k.provenance.txt) · [Extractor receipt](sol3/job17/K2.txt) · [Ordered 90 positions](sol3/job17/positions.txt)

## (4) Prediction graded

The [prediction](sol3/job17/prediction.md) was published alone in
`21f42e509b8bee9bf8ad536db950331eb181cda1` before the census. It hit
one of six point estimates after rounding and five of six ranges.
The only range miss was how often full PC20 found mate later than A.

| Predicted outcome | Point and range | Observed | Point / range |
| --- | --- | --- | --- |
| B misses on M | 1%, 0–5% | 0/89, 0% | miss / hit |
| B later on M | 5%, 0–15% | 1/89, 1.12% | miss / hit |
| E misses on M | 1%, 0–8% | 0/89, 0% | miss / hit |
| E later on M | 8%, 0–20% | 19/89, 21.35% | miss / miss |
| C recovers B misses on M | 0, 0–3 positions | 0 | hit / hit |
| D recovers B misses on M | 1, 0–4 positions | 0 | miss / hit |

[Forecast and search order](sol3/job17/stamps.txt)

## (5) Census — one iterative depth-16 search per position

M has 89 positions where A's last score was positive mate. Earlier,
same, and later compare the first positive exact mate depth against A.
I excluded `lowerbound` and `upperbound` lines from first-mate
detection. Each setting completed all 90 searches, with the same
reader build, built-in evaluation, Threads 1, Hash 16, MultiPV 1,
and NullMateGuard 0. The table is in the requested run order.

| Setting | Positions with mate | Earlier / same / later / none on M | Mates outside M |
| --- | ---: | --- | ---: |
| [A](sol3/job17/census/A) — S14 defaults | 89 (M) | 0 / 89 / 0 / 0 | 0 |
| [B](sol3/job17/census/B) — A with quiet 2, correction 0 | 89 | 2 / 86 / 1 / 0 | 0 |
| [D](sol3/job17/census/D) — B with R3 plain | 88 | 2 / 86 / 0 / 1 | 0 |
| [C](sol3/job17/census/C) — B with R1 plain | 89 | 0 / 89 / 0 / 0 | 0 |
| [E](sol3/job17/census/E) — PC20, both halves follow legacy 2 | 89 | 18 / 52 / 19 / 0 | 0 |
| [G](sol3/job17/census/G) — E with quiet 0 | 89 | 18 / 53 / 18 / 0 | 0 |
| [F](sol3/job17/census/F) — E with R3 plain | 89 | 18 / 52 / 19 / 0 | 0 |

No setting found a mate outside M. The sole outside position was row
68, game 29 at 5 plies. All seven settings reported cp 0 at depth 16.
The independent audit matched 630 census searches and 140 K1 searches
against the exact commands and raw output. First-mate presence and
positive last-score presence agreed on all 630 census searches.
[Independent census readback](sol3/job17/audit/census.json) · [K1 readback](sol3/job17/audit/K1.aggregate.json)

## (6) Every miss on M

| Setting | FEN | Game | Plies before end | A first mate depth | Setting's last move and score |
| --- | --- | ---: | ---: | ---: | --- |
| D, row 24 | `8/8/kp3QK1/p2R4/2p5/3n4/PP6/8 w - - 6 49` | 8 | 7 | 13 | D16 f6d4, cp 2108, 146,941 nodes |

B, C, E, G, and F had zero misses. On row 24 the first positive exact
depths for A/B/C/D/E/G/F were 13/14/13/none/16/12/15. A's D13 first-mate
line used 81,457 nodes, B's D14 line used 240,694, and C's D13 line used
121,813. [Raw rows on the same ordered F7k fixture](sol3/job17/census)

## (7) What the readers changed

On S14, the quiet twin alone hid none of A's 89 mates by depth 16.
It delayed one by one depth and brought two forward by one depth.
Making R1 plain in C put all 89 first-mate depths back at A's depths,
including the one delay. B had no misses for either reader to recover.
Making R3 plain in D turned that one delay into the census's only miss.
Relative to B, D kept all other 88 first-mate depths.

Full PC20 found all 89. It found 19 later and 18 earlier than S14 A.
Within PC20, disabling the quiet half in G changed only four first
depths relative to E (two earlier, two later). Making R3 plain in F
changed only row 24, bringing it forward from depth 16 to 15.
Both PC20 interventions kept all 89 mates. The E versus A result
compares the entire profiles, including their correction and pruning
settings. The E versus G and E versus F comparisons isolate quiet-half
and R3 changes within PC20. [Paired comparisons](sol3/job17/audit/census.json)

### Facts

- The census used `ucinewgame`, `isready` and its reply, the exact
  K2 FEN, and `go depth 16` once per position. Each run retained the
  first exact mate depth and nodes, last depth, score and nodes,
  bestmove, and five NC0 values. The counted executable was the Job 16
  speed-1 build with GCC 14.2.0 and embedded evaluation.
  [Census driver](sol3/job17/search17.py) · [Build](sol3/job16/readers_build.txt)
- Sol's F7k games used a separate Forge binary and UHO openings, with
  FailHighBlend 7 vs 0, one thread, seed 7203, and a 2,000-node budget
  per side. Three census positions are clustered within each selected
  game. The saved game suffixes give the sampling windows, and play
  against best defense can take longer. For example, row 24's game
  ended after seven plies and A's first positive exact report was
  `mate 11`. [F7k game metadata](sol3/job18/F7k.provenance.txt) · [A rows](sol3/job17/census/A/rows.tsv)

### Suspicions

Move ordering is the most direct explanation of the three S14 timing
shifts that disappear with R1 plain. The D miss and the one PC20 R3
timing shift show that the reduction input can also change a search
near the depth limit. I did not trace the first divergent internal
node. The observations identify the toggled reader in each paired
run and leave its subsequent search path open.

### What I did not do

I ran the requested seven settings. The `F7k.pgn` contents were used
only in scratch. The pushed evidence contains the position list, hashes,
scripts, and search logs.

### What I am not sure about

I cannot tell whether the D line at row 24 would find a mate promptly
above depth 16, or which internal reduction first changed its result.
This fixture does not estimate how often the result recurs on new games.

### Limits of this check

The PC's own net and exe; mates longer than 4 moves; positions that are not near a mate; games. Short mates at the end of games played at 2,000 nodes are mostly endgames: a low count here says little about middlegame mates like P.
