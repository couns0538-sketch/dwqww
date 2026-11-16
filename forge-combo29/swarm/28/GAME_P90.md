# Per-move search time at 6 s + 0.06 on REAL GAMES: p90 = 359 ms, median 132 ms, zero flags in 4 games

Independent second measurement of the number the owner needs, on real game positions rather than a FEN set.

## The number asked for

| metric | value |
|---|---|
| moves measured | **281** (4 complete games) |
| median | **132 ms** |
| 75th | 202 ms |
| **90th** | **359 ms** |
| 95th | 428 ms |
| 99th | 550 ms |
| **max** | **608 ms** |
| moves whose search exceeded the 60 ms increment | 275/281 = **98 %** |

## The clock trajectory — the part that decides whether it runs out

| game | plies | result | min clock reached | final white | final black |
|---|---|---|---|---|---|
| 1 | 101 | draw (repetition) | 1457 ms | 1457 | 1672 |
| 2 | 61 | draw | 1907 ms | 1907 | 2061 |
| 3 | 61 | draw | 1899 ms | 1899 | 2039 |
| 4 | 58 | draw | 1848 ms | 1848 | 2470 |

**games flagged: 0 of 4.** Net clock change per game: −4543, −4093, −4101, −3530 ms. The clock never rose on
either side in any game (0 same-side increases), which is what a 98 % over-increment rate implies.

## What this settles, and what it does not

**It settles the tail:** at the owner's real control the per-move search time has a **p90 of 359 ms and a
max of 608 ms on real game positions.** That is well under my constant-clock figures (which reached 1585 ms)
and consistent with the countdown runs — confirming again that a constant-6000 ms harness inflates the tail
and must not be used for this question (S-F30 vs S-F32).

**It does not settle "does the clock run out in a long game", because these games were short.** At 132 ms
median and 359 ms p90 per move, a side spends roughly 132 ms and gains 60 ms per move, i.e. it loses about
**72 ms per move at the median and 299 ms per move at the p90**. With 6000 ms to start:

- at the median rate, the clock lasts ~83 of that side's moves (166 plies);
- at the p90 rate, ~20 of that side's moves (40 plies).

So the answer depends entirely on how long the game lasts and how many p90 moves it contains. These four
games ended as draws by repetition at 58-101 plies, well before either bound. **A longer or more
decisive game would flag, and the mechanism is visible: a game that needs 85+ moves per side while spending
the median rate runs out.**

That extrapolation is arithmetic on the measured rates, not a measurement — I did not play long games.

## Prediction score
G1 (median 100, range 50-200): 132 SURVIVES. G2 (p90 300, range 120-600): 359 SURVIVES. G3 (p90/median
3.0, range 1.5-6.0): 2.72 SURVIVES. G4 (max 1200, range 500-1700): 608 **SURVIVES** — I over-predicted the
max by 2x, which is the countdown doing its job. G5 (over increment 85 %, range 60-100): 98 % SURVIVES.
G6 (0 flags of 4): 0 SURVIVES. G7 (clock declines): yes, net −3530..−4543 with zero same-side rises,
SURVIVES.

## Method, stated because it decides the answer
- **Real countdown**: each side starts at 6000 ms; after each move its clock loses the search wall time and
  gains 60 ms; the engine is sent the ACTUAL remaining clocks. This is what a GUI does.
- **Real game positions**: positions arise from the games themselves, not a FEN list.
- PC r15 build, PC20 settings, Threads 1, Hash 16 (`ucinewgame` + `isready` before every search).
- Referee is python-chess: legal moves only, `claim_draw=True` game-over detection, 250-ply cap. Zero illegal
  moves in 281.
- Games ended as draws by repetition; that is a property of engine self-play at this control, not a defect.

## Limits
- 4 games, 281 moves, one engine playing itself. A match against another engine would take different paths.
- Self-play draws end early, so these games do not probe the long-game regime where the clock actually dies.
  To measure that, the run needs longer games (or an opening book to avoid repetition draws) — I did not do
  that.
- The p90 is over MOVES, not over games; a game with many p90 moves and few median ones would spend more.

## Reproduce
```
cd forge-combo29/swarm/28/pc20
python3 game_p90.py ~/build/r15-pc/forge PC20 /tmp/g 4
```
Raw: `out_game/gamep90_PC20.tsv` (every move with clock before/after, wall, depth, nodes) and `.games.txt`.
