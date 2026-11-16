# Can the clock path lose a game? — 36 self-play games at 6 s + 0.06, and a narrow margin

**The answer: no forfeit in 36 games (4,648 searches), but the margin is NARROW and the clock does
drain.** So "the clock path does not lose games" is true for games of the length the engine actually
plays, and would stop being true for a game a few moves longer.

PC build r15, **PC20**, **Threads 1**, Hash 16, engine vs **itself**, a real clock decremented by the
measured wall time of every search, `go wtime X btime X winc 60 binc 60`, 6,000 ms start. Openings: the
first 30 (and 6 more at a 400-ply cap) positions of set O. Prediction committed and pushed before the
first game. Raw: `games30.txt`, `games_long.txt`, `games.jsonl`.

## Headline numbers

| | result |
|---|---|
| games played | **36** (30 at ply cap 160, 6 at ply cap 400) |
| searches | **4,648** |
| **forfeits** | **0** |
| illegal moves | **0** |
| clock ever ≤ 0 | **never** |
| minimum clock reached by either side | **174 ms** (game 17, at ply 160) |
| clock used per move | median **105 ms**, 99th pct **599 ms**, max **1,350 ms** |
| results | 14 draw by rule, 8 ply cap, 5 checkmate, 3 insufficient material (30-game set) |

## The margin, which is the part that matters

The clock **drains**. Median use is **105 ms** per move against a **60 ms** increment, so each move
costs the clock about **45 ms net**. Measured end to end: the heaviest games lost **~5,826 ms of 6,000
over 160 plies — about 73 ms net per move of the draining side.**

That puts the arithmetic right at the boundary:

- 6,000 ms ÷ 73 ms ≈ **82 moves** of one side before the clock is empty;
- 160 plies = **80 moves** of one side;
- observed minimum clock at 160 plies: **174 ms**.

**The 30-game set hit the ply cap at 160 with 174 ms left.** A game reaching ~165 plies would have
forfeited. That is not a comfortable margin — it is about **four more moves**.

Note this drain is *not* the engine mis-managing time; it is the setting. 6 s + 0.06 with a search that
typically takes 105 ms is a **negative-sum clock** by construction: it cannot be sustained indefinitely,
and it is sustained only because games end before it runs out.

## What the ply-cap-400 run showed

Six games with four times the ply budget all ended naturally well before it: **149, 199, 104, 121, 115,
155 plies** — by draw, insufficient material or checkmate. So in practice **games terminate before the
clock does**, which is why 36 games produced no forfeit. The drain is real; the games are shorter.

## Does the per-move cost accelerate? No — it falls

Comparing the first 40 plies against the last 40 of each game, the cost **drops sharply**:

| game | first 40 plies | last 40 plies |
|---|---|---|
| 1 | 217 ms | **83 ms** |
| 2 | 210 ms | **100 ms** |
| 3 | 222 ms | **67 ms** |
| 5 | 222 ms | **81 ms** |
| 6 | 194 ms | **55 ms** |

Searches get *cheaper* as the position simplifies, so the drain decelerates rather than accelerating.
That is what saved the 160-ply games: the average is dragged up by the expensive middlegame opening
phase, and the endgame is cheap.

## My prediction

| # | prediction | verdict |
|---|---|---|
| P1 | zero forfeits | **HELD** (36 of 36 games) |
| P2 | clock never negative | **HELD** |
| P3 | every move legal | **HELD** (4,648 moves) |
| P4 | median clock used under 400 ms | **HELD** (105 ms) |
| P5 | all games reach a result | **HELD** (36 of 36) |

All five held. But **P1 holding is not the same as "the clock path is safe"** — it held because games
ended, not because the clock was comfortable. The honest summary is that P1 would fail for the first
game that lasted ~165 plies at this increment.

## Scope, stated plainly

- **Self-play, not against another engine.** A stronger opponent would produce longer, more complex
  games; a weaker one shorter. Self-play is the setting most favourable to *short* games at equal
  strength, and these games still came within ~4 moves of forfeiting.
- 36 games is a sample, not a distribution. I can say **no forfeit in 36** and **the minimum clock was
  174 ms**; I cannot give a forfeit *rate*, and I would not extrapolate a tail from 36 games.
- One time control (6 s + 0.06), one opening set (positions from O), one build.
- Resignation was not implemented; games ended by rule, mate or the ply cap.
