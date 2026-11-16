# REPORT — the owner's clock path (seat 05, area 5)

**Question:** file 6 says the owner's strength matches use `PC build, PC20, Threads 1, Hash 16, clock 6 s + 0.06`.
What does the engine actually do with that clock?

**Answer in one line.** It spends 0.35 s of the 6, reaches depth 19, and that result is *bit-identical* to
`go depth 19` — the clock is not a time limit on this path in any practical sense; it is an implicit depth limit
chosen by a formula dominated by the **increment**, not the clock.

All numbers: PC r15 build (patch sha256 prefix `d6bd72c531f785f4`), PC20 settings, **Threads 1**, Hash 16,
`OwnBook false`. Honesty of that build: 8/8 (`../HONESTY_PC.md`).

## 1. The gap, on the same board and settings

| go command | wall | depth | nodes | % of 6 s |
|---|---|---|---|---|
| `go wtime 6000 btime 6000 winc 60 binc 60` | 0.35-0.36 s | **19** | 650,246 | **5.9 %** |
| `go movetime 6000` | 5.99 s | **27** | 7,061,631 | ~100 % |

5 runs each, identical every time. The **base build + S14** shows the same gap (startpos 0.23 s / d19 / 466,541 vs
5.99 s / d27 / 11,003,901), so this is not a PC-specific change (`out/clock_repro.txt`).

## 2. It is a formula, not a depth cap

Varying only the clock: the depth keeps growing, so nothing is pinned — the *fraction* falls.

| clock | engine time | depth | used / clock |
|---|---|---|---|
| 1,000 ms | 95 ms | 15 | 9.5 % |
| 2,000 ms | 141 ms | 17 | 7.1 % |
| 6,000 ms | 234 ms | 19 | 3.9 % |
| 12,000 ms | 397 ms | 20 | 3.3 % |
| 30,000 ms | 911 ms | 21 | 3.0 % |
| 60,000 ms | 1,883 ms | 24 | 3.1 % |
| 120,000 ms | 2,583 ms | 25 | 2.2 % |

`out/clock_cap.txt`.

## 3. The increment, not the clock, sets the budget

This is the sharpest result, because the owner's control is `6 s + 0.06` — a tiny increment.

| winc (clock fixed 6 s) | wall | depth | % of 6 s |
|---|---|---|---|
| 0 | 0.35 s | 19 | 5.9 % |
| **60 (the owner's value)** | **0.35 s** | **19** | **5.8 %** |
| 200 | 0.51 s | 20 | 8.6 % |
| 500 | 1.28 s | 21 | 21.3 % |
| 1,000 | 1.29 s | 21 | 21.5 % |
| 2,000 | 1.29 s | 21 | 21.5 % |
| 4,000 | 1.93 s | 23 | 32.1 % |

Raising the increment 66× (60 → 4,000) buys **4 plies**. Raising the clock 30× (2 s → 60 s) buys 6 plies at a
*shrinking* fraction of the budget (4.4 % → 3.3 %). At the owner's `winc 60` the engine sits in the flat
low-allocation region, so the 6-second clock contributes very little. `out/winc_scaling.txt`.

## 4. What does NOT explain it

- **Hash size:** depth 19 with Hash 1, Hash 16 and Hash 256 alike (0.42 / 0.35 / 0.25 s). Not a TT effect.
- **btime:** `go wtime 6000 winc 60` (no btime at all) behaves identically to the full clock. `out/ratio_controls.txt`.
- **Position:** holds on five diverse positions — 5.9 % startpos, 3.0 % G0, 11.9 % middlegame, 6.3 % deep
  middlegame, 4.7 % K+Q endgame. Never near the budget. `out/ratio_by_position.txt`.
  (The endgame row is the worst for strength: depth 15 with the clock against **depth 64** with an explicit 6 s
  `movetime`.)

## 5. The clock is an implicit depth limit — proven bit-for-bit

For each of 12 G-set positions I took the depth the `wtime` search reached, then re-asked with `go depth <that>`:

**the move matched in 12 of 12 cases.** So the wtime result is exactly "search to depth D", where D is chosen by the
allocation formula. `out/move_quality.txt`.

## 6. Does it cost moves? Partly — and I corrected my own first answer

Comparing the `wtime` move against a full `go movetime 6000` on the same board, **10 of 12 agree and 2 differ**
(G idx 0 `g7g6`/d18 vs `e5e4`/d28; G idx 7 `g5h5`/d18 vs `g5h6`/d21).

My first draft called that a strength loss. **Checking the scores shows it is not demonstrable:** both positions are
losing for the side to move and the deeper search is the *more pessimistic* one (cp −294 → −341; cp −1915 → −2121),
so the shallow choice was over-optimistic about a lost position rather than worse. I withdrew the strength
interpretation (S-F42 CORRECTED, and S-F43 records the scores that forced it). What remains established: moves *can*
differ, and at these two they did.

## 6b. What two full games say (the practical answer)

I played two complete self-play games at the owner's clock (`match/match_clock_game.py`):

| game | start | plies | result | illegal | lost on time | per-move wall (min/median/max) | depths |
|---|---|---|---|---|---|---|---|
| 1 | startpos | 151 | draw rule | **0** | **none** | 0.03 / 0.10 / 0.71 s | 16 / 19 / 24 |
| 2 | real middlegame | 120 | move limit | **0** | **none** | 0.03 / 0.11 / 0.69 s | 16 / 22 / **36** |

**Across 271 plies of match-clock play the engine never spent more than 0.71 s of a 6-second clock**, kept legal moves
throughout, and never came close to a forfeit (final clocks 673/564 ms and 406/884 ms). In endgames it reaches depth
32-36 because the trees are small.

So the honest summary is: **the clock is almost entirely unused, and that is not currently harmful.** The engine plays
these games at roughly depth 16-24 (deeper in endgames) and the games complete cleanly. Whether spending the remaining
5.5 s would make it *stronger* is a separate question that my move-level evidence (§6) does not settle — the two move
differences I found were both positions already lost, where the shallow search was merely over-optimistic.

## 7. Confidence and limits

- **High** on §1–§5: deterministic, 5 runs per cell where it matters, and §5 is a 12/12 bit-match.
- **Not established:** any cause in source. I did **not** read the time manager, so I cannot say which constant
  produces the 0.02–0.2 fraction, nor whether the increment dependence is deliberate. That is a question for
  whoever reads `search.cpp`'s time code.
- **Not established:** whether this is *wrong* for the owner. If the engine is strong at depth 19 in 0.35 s, spending
  6 s may buy little. My evidence says the search is 10–18 plies shallower than it could be, not that the moves are
  worse — §6 is where that question has to be settled and my data does not settle it.
- **Needs a confirming seat.** This is the one finding of mine on file 6's "worth most" path, and it is
  unconfirmed. `REPRO_for_seats.md` in this folder is a self-contained script (tested as published) for another seat
  to run.

## 8. Files

`clock_path.py`, `clock_depth_cap.py`, `clock_move_quality.py`, `REPRO_for_seats.md`,
`out/{clock_repro,clock_cap,ratio_by_position,ratio_controls,winc_scaling,move_quality,move_diff_detail}.txt`.
Times: see `../stamps.txt` and the git log.
