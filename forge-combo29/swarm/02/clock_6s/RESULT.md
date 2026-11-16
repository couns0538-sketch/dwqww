# The owner's 6 s + 0.06 clock: the engine uses a small fraction of it

File 6 names the strength-match clock as 6 s + 0.06 per move. Measured on the PC build under PC20, Threads 1,
Hash 16, OwnBook false, 5 runs per position, wall time from sending `go` to reading `bestmove`. Raw `clk.json`.

| position | median ms | min | max | share of 6060 ms available |
|---|---|---|---|---|
| game_mid1 (middlegame) | 380.8 | 376.4 | 433.5 | 6.3 % |
| game_mid2 (middlegame, Black) | 160.6 | 159.0 | 161.0 | 2.7 % |
| game_end (endgame) | 199.9 | 198.7 | 201.2 | 3.3 % |
| startpos | 358.0 | 357.0 | 448.9 | 5.9 % |

## what this shows
On a 6 s + 0.06 clock the engine answers in **160-380 ms**, i.e. it spends **2.7-6.3 %** of the 6,060 ms it has.
It is nowhere near its time limit, so on this clock the search length is set by the engine's own conservative plan
(seat 08's S-F9 area measured the same shape: the achieved time is 55-79 % of the planned soft limit, and the soft
limit itself is far below the clock).

## the position-dependence the coordinator asked about
The spread across positions is real but modest: **160 ms (game_mid2) to 381 ms (game_mid1)**, a 2.4x range, with
startpos at 358 ms and the sparse endgame at 200 ms. So on THIS set the middlegame is the SLOWEST class and the
sparse endgame is in the middle — which is consistent with the two seats' view that sparse endgames are a heavy
class relative to their node counts, but it does not make them the slowest in absolute terms on these four boards.

Honest limit: four positions is not a class survey. This is a third independent measurement of the sparse
endgame's absolute behaviour, not a statistical statement about the endgame class; a class claim needs a sample
per class, which I did not build here. What I can say is that the sparse endgame I used is NOT slow in absolute
terms (200 ms median, 200 ms spread of under 3 ms across 5 runs — the tightest of the four).
