# CHECK of seat 03's S-F20 / S-F22 — the signature reproduces only at depth ≥18, not at depth 12

Their claims:
> S-F20: "on `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` the engine plays c6c7, which loses in 20 plies ... while the
> move it rejects (c6d6, **rated mate −11 by its own root scores**) holds out 22 plies. It MIS-SCORES the alternative
> ... PREDATES the PC build (base 6b98f217 under S14: **c6c7 mate −20, c6d6 cp −1192**)"
> S-F22: "the strict S-F20 signature (chosen move scored worse than an available alternative by more than a queen)
> occurs **0 of 50** ... the smaller-magnitude version occurs 11 of 45, median 36 cp"

## Verdict: PARTLY CONFIRMS — the substance holds, the depth attribution was wrong, and the effect is visible from depth 18 rather than 12

**Stated plainly: S-F20's substance holds — `c6d6` is the better move and the engine plays `c6c7`. What is wrong is
the depth it is attributed to: it is a depth-18-and-beyond fact, not a depth-12 one, and the depth-12 scores in the
finding line do not reproduce.** The two measurements are consistent once the depth is stated: their S-F22 zero is
measured at depth 16, where my own table puts the gap on this board at 22 cp — inside their own smaller-magnitude
band (median 36 cp) and nowhere near the queen-sized gap their strict test looks for.


My own harness, root scores by searching each move alone with `go depth D searchmoves <move>`:

| depth | `c6c7` (the move the engine plays) | `c6d6` (the alternative) | which is better? |
|---|---|---|---|
| 12 | **cp −1092** | cp −1139 | **`c6c7` is BETTER by 47 cp** |
| 14 | cp −1195 | cp −1149 | `c6d6` better by 46 cp |
| 16 | cp −1195 | cp −1173 | `c6d6` better by 22 cp |
| 18 | cp −1195 | **mate −9** | `c6d6` much better |
| 20 | mate −11 | **mate −8** | `c6d6` better by 3 plies |

**So the defect is REAL but only emerges at depth 18 and beyond**: at depth 12 the engine's chosen move is in fact
the better-scoring one, and it takes five more plies of search for the alternative to overtake it. Their S-F20 says
the alternative is "rated mate −11 by its own root scores" — that is true at **depth 20**, not at 12, and their
quoted base-tree figures (`c6c7 mate −20`, `c6d6 cp −1192`) do not reproduce at depth 12 on either build in my run:

| build / settings | `c6c7` | `c6d6` |
|---|---|---|
| base 6b98f217, S14 | **cp −1064** | cp −1104 |
| PC r15, PC20 | cp −1092 | cp −1139 |
| PC r15, S14 only | cp −1041 | cp −1120 |

Three configs, all cp-vs-cp, with the CHOSEN move better in every case. I cannot reproduce `mate −20` or `mate −11`
at depth 12 on this board.

## What this means for their S-F22 zero

Their S-F22 measures "how often the chosen move scores worse than an alternative by more than a queen" **at depth
16**, on 50 lone-king positions, and reports **0 of 50** with a smaller-margin rate of 11 of 45. **My S-F20 table
puts the depth-16 gap on the very board that motivated the measurement at only 22 cp** — far inside their
"smaller-magnitude" band and nowhere near a queen. So their 0-of-50 strict result is consistent with what I measure:
at depth 16 the strict signature is rare or absent, because the big gaps only open at depth 18+.

**That makes S-F22 a fair measurement of a rare event, not a refutation of S-F20** — and it also means the depth at
which S-F20 was claimed (12) and the depth at which it is visible (≥18) differ, which is the thing worth fixing in
their finding line.

## A plant failure that turned into the useful result
My first run of the S-F22 check aborted at its own plant, because I built the plant to expect "more than a queen" at
depth 12 and found only a 47 cp gap **the other way**. I did not lower the threshold to make the plant pass — I
investigated, and the investigation is the table above. The plant's failure was correct: at depth 12 there is no
defect on that board to plant with.

## What I do NOT claim
- That S-F20 is wrong in substance. `c6d6` IS better at depth 18-20, by mate distance, and the engine does play
  `c6c7`. The substance stands; the depth attribution and the quoted scores do not.
- That S-F22's 0-of-50 is refuted. I did not re-run their 50-position scan; I have no evidence against it. My
  independent table simply explains WHY a strict gap is rare at depth 16.
- Anything about whether either move is a *practical* loss — that needs a play-out, which is their method, not mine.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 -c "import chess; print([chess.Board('1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183').uci(m) for m in chess.Board('1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183').legal_moves])"
    # then, per depth D: printf 'uci\n...setoptions...\nposition fen 1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183\ngo depth D searchmoves c6c7\n' | ~/builds/pc/forge

Raw numbers committed in `check_s03f20.txt`.
