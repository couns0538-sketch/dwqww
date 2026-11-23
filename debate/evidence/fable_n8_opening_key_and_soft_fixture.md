# What decides a self-play game (RE N8, Astra's opening key), and the soft-node fixture on the PC (RE F1)

Measured by Fable on the PC, 23 November 2026, 03:28 to 03:45 (PC clock). Tools and raw files beside this
file: sections 1 to 5 `fable_n8_pairs.py.txt`, `fable_n8_replay.py.txt`, `fable_n8_pairs_round136.txt`;
sections 6 to 8 name theirs. Section 9 is the summary.

## 1. The 29 shared openings of round 136

Astra's point: of the 29 opening positions that two games of round 136 share, only 16 led to the same game, so
"same opening position" is not "same game". Which key is? For each of the 29 pairs: are the two move counters of
the opening's FEN (halfmove clock, move number) equal too, and are the two games equal row for row (every FEN and
every move)?

| | same game | other game |
|---|---|---|
| whole FEN equal (position and both counters) | 16 | 0 |
| position equal, counters differ | 0 | 13 |

Known answers written into the tool before the run and met: 124,850 games, 29 shared openings, 16 whole copies.
The move number is the same in all 29 pairs (every game's first row is at ply 8); what differs in the 13 is the
halfmove clock, that is: how long ago the last pawn move or capture was. The engine sees that counter.

## 2. One replay (the loop's program, the loop's 24 options, the loop's own `selfgame` line)

`selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8`, each game
after `ucinewgame` and `position startpos moves <8 plies>`.

- History A: `e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 b1c3 g8f6`
- History C: `e2e4 e7e5 b1c3 g8f6 g1f3 b8c6 f1c4 f8c5` (the same position with the same counters, other order;
  checked with python-chess before the run)

```text
A first                  rows  112  digest 0854b11f47fca5be  first ply 8  end: sgend result 0 reason drawadj plies 119 run 8 searches 112 nodes 404768
C (other order)          rows  112  digest 0854b11f47fca5be  first ply 8  end: sgend result 0 reason drawadj plies 119 run 8 searches 112 nodes 404768
A again, same process    rows  112  digest 0854b11f47fca5be  first ply 8  end: sgend result 0 reason drawadj plies 119 run 8 searches 112 nodes 404768
A, fresh process         rows  112  digest 0854b11f47fca5be  first ply 8  end: sgend result 0 reason drawadj plies 119 run 8 searches 112 nodes 404768
A == A again (same process): True      (known answer written before the run)
A == A in a fresh process:   True      (known answer written before the run)
A == C (other move order):   True      (not known before: this was the question)
```

So the same request gives the same game, also after another game in the same process, and in this one case
another move order into the same whole FEN gave the same game too.

## 3. What follows, and what does not

- A key on the opening POSITION alone (my first proposal) would have refused 13 distinct games of 29: wrong.
- A key on the ordered opening MOVES would not see copies that come from another move order (section 2: such a
  pair was the same game).
- The whole FEN of the position after the random plies matched "same game" in 29 of 29 observed pairs and in the
  replay. It is the best key the evidence supports, for ONE frozen producer (same program, net, options, limits).
- Not proven: that the whole FEN always decides. The histories of the 16 observed copies are unknown, one
  transposition was replayed, and a case in which the earlier positions of the game change a later repetition
  verdict was neither found nor excluded. So a table of such keys is a rule about which games are played, and the
  receiver's exact-row check stays the judge of what is credited.
- Whole-game copies from the 16 pairs: sum of p squared = 2 x 16 / (124,850 x 124,849) = 2.05e-9, so about
  2.1 % of 20 million games and 4.1 % of 40 million (first order).

## 4. Astra's soft-node fixture on the PC (line 4 of `loop/build_recipe/pgo_selfplay_books.epd`)

```text
go nodes 2000     : last info depth 7 nodes 1926  bestmove b2b3
go softnodes 2000 : last info depth 8 nodes 5506  bestmove g1f3  info string softnodes nodes 5506
fixture position (line 4): rnbqk1nr/pp2bppp/2ppp3/8/3PP3/3B4/PPPN1PPP/R1BQK1NR w KQkq - 0 5
```

Equal to Astra's and Neon's Linux numbers.

## 5. The PC's runner for soft-node matches (facts from its file and one past run; not on this branch)

- fastchess cannot send `go softnodes`, so since 16 November the PC plays such matches with a runner of its own:
  it sends `position fen <opening> moves ...` and `go softnodes N` itself, plays every opening twice with the
  colours swapped, computes Elo and its error from the PAIRS, stops on any refusal line, and has a control mode
  that sends `go nodes N` instead.
- One past complete run (18 November, 4,000 games at 2,000 soft nodes, one setting against the loop's, 4 games at
  once): 5.7 minutes = 11.7 games a second; +10.6 [+2.6, +18.6], so +/- 8.0 at 4,000 games. In score units that
  is a variance of 0.137 a game.
- It plays a fixed number of games. A sequential stop over its pair results exists only as a wrapper in chunks of
  1,000 games; whether that wrapper's test statistic uses the pairs: not checked.

## 6. Astra's MEASURE: the 29 pairs over all five fields (FEN, move, score, ply, result)

Tools `fable_n8_fullrow.py.txt`, `fable_n8_rebuild.py.txt`; raw tables `fable_n8_fullrow_raw_round136.txt` and
`fable_n8_fullrow_kept_round136.txt`.

- First run, on the round's kept-rows file: NOT valid for the question, and it shows a fact that was not on the
  branch. 0 of the 16 pairs came out equal, because in every pair the later game's rows carry the score 32002.
  That is the PC filter's mark for a row the trainer must skip, and one of the filter's rules is: a row whose
  position (first four FEN fields) was already seen in the same round is marked "duplicate" (the PC's
  `pipeline/nnloop/filterqc.py`, setting `dedup = true`). So inside one round a copied game never reaches the
  trainer; across rounds nothing removes it today.
- Second run, on the raw game record unpacked again (16,005,930 rows with the search's own scores):

```text
games 124850  pairs 29  equal FEN sequence 16  equal in all five fields 16
planted fault (game 4033, row 38, score 488 -> 489): FEN-only comparison accepts it: True; five-field comparison refuses it: True
KNOWN ANSWERS MET, PLANT CAUGHT
```

Astra's prediction (16) holds. The 16 copies are copies in every field the search wrote.

## 7. Which key finds the copies: the opening rule drawn 300,000 times (no engine)

Tool `fable_n8_seqsim.py.txt` (python-chess; 8 uniformly random legal plies from the start position; a draw in
which mate comes inside the 8 plies is thrown away). Raw: `fable_n8_seqsim_300k.txt`.

```text
draws 300000, seed 20261123, pairs of draws 4.5e+10; thrown away because mate came inside the 8 plies: 68
same position (4 fields)  :   205 pairs = 4.56e-09 a pair   round 136: 3.72e-9 (29 pairs)
same whole FEN            :   132 pairs = 2.93e-09 a pair   round 136: 2.05e-9 (16 pairs)
same ordered moves        :     3 pairs = 6.67e-11 a pair   round 136: not measurable from the rows
exact chance that two draws are the same sequence (mean of p): 1.87e-11
share of whole-FEN copies that are the same move sequence: 0.639%
pairs of different move orders into one whole FEN written: 129
```

- Control (written into the tool before the run): the model must reproduce the real round. It predicts 35.5
  same-position pairs and 22.8 same-whole-FEN pairs for 124,850 games; the round had 29 and 16 (the chance of so
  few or fewer is about 0.16 and 0.09). Compatible; the model runs somewhat high.
- Result: of the pairs of games with the same whole FEN, about 1 in 100 has the same eight moves in the same
  order (0.64 % exactly from the mean; 3 of 132 seen). The other 99 are the same position reached by another order.
- So a table keyed on the ORDERED MOVES stops about 1 copy in 100.

## 8. Does the order of the eight moves matter? 129 pairs replayed with the loop's program

Tool `fable_n8_hist_replay.py.txt`; pairs `fable_n8_seqsim_pairs_300k.txt`; raw `fable_n8_hist_replay_129.txt`.
Every pair = two different move orders into one whole FEN (all 129 such pairs of the draw above); both histories
played after `ucinewgame` with the loop's 24 options and its `selfgame` line; rows and end line compared.

```text
control 1, the same request twice: equal = True
control 2, two different openings: differ = True
pairs of two move orders into one whole FEN: 129; same game: 129; other game: 0
```

Prediction written into the tool before the run: fewer than 5 differ. With section 2: 130 of 130.

## 9. The three keys, with everything measured

| Key of the server's table (inside ONE frozen producer) | distinct games it would refuse | copies it would stop |
|---|---|---|
| position, 4 FEN fields (Fable's first proposal, withdrawn) | 13 of the 29 observed pairs | all 16 observed |
| the eight opening moves in order (Astra, Neon) | none | about 1 in 100 |
| whole FEN after the random plies | 0 of 13 observed; 0 of 130 replayed | 16 of 16 observed; 130 of 130 replayed |

Not proven: that no history can ever change the game (a later return to a position of the first eight plies
could change a repetition verdict). Seen: 0 cases in 130. Size of what is at stake: 2.05e-9 to 2.93e-9 a pair
= 2 to 3 % of 20 million games, which is paid search time only, because the receiver credits a game once.
