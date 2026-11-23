# Round 136 game by game: shared openings, repeated games, and who wins after the first big score

Measured by Fable on the PC, 23 November 2026, 03:19:06 to 03:21 (PC clock), for N8 (Neon) and for the replies of
Astra and Neon on N4. One whole production round (136: self-play of round 67's net, 2,000 soft nodes). Tool:
`fable_n8_games.py.txt` beside this file; raw result: `fable_n8_games_round136.json`.

## Method

- Scores come from the round's packed game record, unpacked again (the ORIGINAL score of every row); "kept" comes
  from the filtered text file (same rows, same order; a dropped row carries 32002 there).
- A game ends where the next row's ply is not higher. Every one of the 124,850 games has its first row at ply 8
  (counted), so a game's first row IS its opening position: the position after the 8 random plies.
- Opening key: the first four fields of the FEN (pieces, side to move, castling, en passant).
- A row's result is seen from the side to move, as its score is. "Favoured" = the side the score is good for.
- The final result is the loop's own: a game is ended as a win at |score| >= 2000, and drawn games in won
  lone-king or tablebase endings are scored as wins (the loop's rules). It is not an independent judge.

## Controls (written into the tool before the run; all PASS)

rows 16,005,930; kept 15,255,460; games 124,850; games reaching |score| >= 600: 79,914; >= 1000: 73,933 (the
last three are the cross-table run's numbers of 03:05, from another tool).

## (a) Openings

| | |
|---|---|
| games | 124,850 |
| distinct opening positions | 124,821 |
| openings used by two games (none by three) | 29 (58 games) |
| of these 29 repeats: the whole game equal row for row to the earlier one | 16 |
| games of round 136 on an opening that round 135 (124,412 games) also used | 54 |

- How the driver works (the PC's self-play code, not on this branch): each worker's random generator is seeded
  with config seed, round, worker number and the clock in nanoseconds; before every game it sends `ucinewgame`
  (the table is cleared), then 8 uniformly random legal plies from the start position, then `selfgame`. So a game
  is decided by its opening and the path into it. Different seeds do not prevent two workers from drawing the same
  8 plies or two move orders into the same position.
- Why 13 of the 29 repeats are not the same game: not checked. (A different move order into the same position
  gives another repetition history and can give another move counter.)
- The size of the opening space, from the pairs: 29 pairs among 124,850 games give sum of p squared =
  2 x 29 / (124,850 x 124,849) = 3.72e-9. Check with a number the estimate did not use: it predicts
  124,850 x 124,412 x 3.72e-9 = 57.8 shared openings between rounds 135 and 136; counted: 54.
- What that means at the size of the plan (first order: games that repeat an earlier opening = games x
  sum of p squared / 2; an over-estimate once it gets large):

| games played from this opening rule | share that repeats an earlier opening | of which whole-game copies, at 16 of 29 |
|---|---|---|
| 124,850 (one round; measured 0.0232 %) | 0.023 % | 0.013 % |
| 3.1 million (today's 25-round window) | 0.58 % | 0.3 % |
| 17 million (all rounds so far, about) | 3.2 % | 1.7 % |
| 20 million | 3.7 % | 2.1 % |
| 40 million | 7.4 % | 4.1 % |

  A server game also meets the 17 million games already played at home: each new game has about
  17 million x 3.72e-9 = 6 % chance of an opening the bank already holds (if the early rounds used today's
  opening rule: not checked).
- A pilot of 100,000 rows (about 800 games) cannot see any of this: the share grows with the number of games.

## (b) Per game: the first row at |score| >= 600 and >= 1000, against the game's final result

| first row at | games | favoured side won | draw | favoured side lost | games with a later row under 600 |
|---|---|---|---|---|---|
| \|score\| >= 600 | 79,914 | 79,428 (99.39 %) | 434 (0.54 %) | 52 (0.065 %) | 31,093 (38.9 %) |
| \|score\| >= 1000 | 73,933 | 73,867 (99.911 %) | 60 (0.081 %) | 6 (0.008 %) | 656 (0.89 %) |

Ending every game at its first |score| >= 1000 as a win for the favoured side would have changed the result of
66 of 73,933 such games (0.089 %), 0.053 % of all games of the round.

## (c) Rows with |score| >= 600, before and after the loop's filter

| | favoured side won | draw | favoured side lost | all |
|---|---|---|---|---|
| before the filter | 3,398,254 (99.636 %) | 11,751 (0.345 %) | 665 (0.0195 %) | 3,410,670 |
| after the filter (kept rows) | 3,224,377 (99.702 %) | 9,628 (0.298 %) | 0 | 3,234,005 |

The "0 losses" of the earlier sample table (`fable_filter_shares_round136.md`) is the filter's doing, as Astra
wrote: the filter drops every row whose score contradicts the game's result by more than 600. Before the filter
665 such rows exist in this band (1 in 5,129).

## Limits

- One round, one net, one node count. The opening estimate rests on 29 pairs (about +/- 37 % at 95 %); the check
  against round 135 (54 against a predicted 57.8) agrees.
- Nothing here says what a net learns from the rows after a first 1000, and nothing here is a timing: how many
  more games an earlier end would give must be timed, not computed from row shares.
