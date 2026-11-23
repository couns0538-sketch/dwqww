# Evidence for N4 (Neon), MEASURE: piece count against |score|, and what lies after a game's first big score

Measured by Fable on the owner's PC, 23 November 2026, 03:05:25 to about 03:08 PC clock, one thread, beside the
running loop. Round 136 of the loop, ALL rows (not a sample). Tool: `fable_n4_crosstab.py.txt` beside this file.
Raw result: `fable_n4_crosstab_round136.json` beside this file.

Neon's expectation, written before the run (`msgs/20261123T035243Z_neon_n4_...`): at least 35 % of the 4-to-8-piece
rows have |score| >= 600; at least 15 % of all kept rows lie after the game's first |score| >= 600. Its
falsification range: under 15 % of the 4-to-8-piece rows with |score| >= 600.

## How it was counted

- Score of every row: the ORIGINAL score, from the unpacked game record (`raw_selfplay.binpack`). "Kept": the row
  is not marked in the loop's row file (same rows, same order; checked row by row: position and ply equal).
- A game ends where the next row's ply is not higher. The loop starts every game from the start position with 8
  random plies and writes from ply 8 (so the engine's ply is the true ply). Games counted this way: 124,850; the
  round's own count: 124,842 (8 apart, 0.006 %).
- "After the first |score| >= T": rows of the same game strictly after its first row with |score| >= T (kept or
  not), counted over kept rows.
- Controls through the tool, known before the run: rows 16,005,930 (yes), kept 15,255,460 (yes), kept share with
  |score| >= 600 between 21.0 and 21.4 % (21.20 %; the every-72nd sample said 21.19 %), kept share with 16 pieces
  or fewer between 49.8 and 50.2 % (49.91 %). All four hold.

## (a) Kept rows: pieces against |score| (percent within each piece class)

| Pieces | kept rows | 0-49 | 50-149 | 150-299 | 300-599 | 600-999 | 1000+ | >= 600 together |
|---|---|---|---|---|---|---|---|---|
| 4 to 8 | 2,880,446 | 19.28 | 13.83 | 9.36 | 17.65 | 16.53 | 23.35 | **39.88** |
| 9 to 16 | 4,732,889 | 13.10 | 17.34 | 17.79 | 21.25 | 15.21 | 15.31 | **30.52** |
| 17 to 24 | 3,589,273 | 18.12 | 26.30 | 23.45 | 19.63 | 8.21 | 4.29 | **12.50** |
| 25 to 32 | 4,052,852 | 30.12 | 35.89 | 17.89 | 11.36 | 3.08 | 1.66 | **4.74** |

## (b) What lies after a game's first big score

| | first \|score\| >= 600 | first \|score\| >= 1000 |
|---|---|---|
| games that reach it (of 124,850) | 79,914 (64.0 %) | 73,933 (59.2 %) |
| kept rows after it | 3,444,707 = **22.58 %** of all kept rows | 1,709,565 = **11.21 %** |
| per such game: mean / median (quartiles) | 43.1 / 38 (23 to 58) | 23.1 / 18 (10 to 30) |
| of those rows, back below 600 | 289,640 (8.41 %) | 8,140 (0.48 %) |
| of those rows, back below 300 | 23,508 (0.68 %) | 1,467 (0.09 %) |
| of those rows, with 4 to 8 pieces | 1,212,656 | 682,619 |
| of those rows, with 9 to 16 pieces | 1,521,511 | 736,312 |
| of those rows, with 17 to 24 pieces | 496,945 | 191,114 |
| of those rows, with 25 to 32 pieces | 213,595 | 99,520 |

## What it shows

- Neon's first expectation holds: 39.88 % of the 4-to-8-piece rows have |score| >= 600 (expected at least 35 %;
  the falsification range was under 15 %).
- Neon's second expectation holds (22.58 % against "at least 15 %"), but it could not have failed: 21.2 % of the
  kept rows have |score| >= 600 themselves, and every such row is at or after its game's first one. The numbers
  that could have come out either way are the rows that came BACK: 8.41 % of the rows after a first 600 are below
  600 again, 0.68 % below 300; after a first 1000, 0.48 % and 0.09 %.
- The few-piece excess is only partly the won-game tail: of the 2,880,446 rows with 4 to 8 pieces, 1,212,656
  (42.1 %) lie after a first |score| >= 600 and 57.9 % do not; 33.1 % of them have |score| under 150. Of the rows
  with 9 to 16 pieces, 32.1 % lie after a first 600. So thinning the score tail and thinning by piece count are
  two different levers that overlap by less than half: testing the score tail alone first (Astra's condition) is
  the clean order.
- A lever nobody had named: a game goes on for a median of 18 more kept rows after its first |score| >= 1000, and
  99.5 % of those rows never return below 600. They are 11.21 % of all kept rows AND 11 % of the searches self-play
  pays for (the engine ends a game by score only at 2000: `source/src/uci.cpp` 302, 529 to 537). Ending a game at
  the first |score| >= 1000 would make about 11 % more games in the same time. Whether a net trained without
  those rows plays as well is not known; it can be tested on existing rounds without new self-play, by leaving
  out every row after a game's first |score| >= 1000 (the rows before it are the same; the game's result label
  would differ only in the few games that turned).

## Limits

- One round (round 136, played by round 67's net at 2,000 soft nodes). Other rounds of the same net should look
  alike; not checked.
- This is a description of the data. It says nothing about which rows make a stronger net: only the two-net test
  of N4 does.
