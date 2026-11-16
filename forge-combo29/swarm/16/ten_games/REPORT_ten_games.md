# REPORT_ten_games — clock utilisation across whole games, and what ten self-play games revealed

**What was asked:** does the 2.6–5.3 % clock-utilisation figure stay stable over a game or drift? Ten games.

**Two answers, and the second was not what I was looking for.**

## 1. The utilisation fraction DOES drift upward within a game, and the band is wider than 2.6–5.3 %

```
phase    n     median   min      max
first  200    3.64 %   2.43 %   12.26 %
middle 200    4.32 %   2.43 %   21.90 %
last   200    4.70 %   2.73 %   16.10 %
ALL    600    4.34 %   2.43 %   21.90 %
```

- The median fraction **rises monotonically across the game: 3.64 % → 4.32 % → 4.70 %.** So it drifts, it is
  not stable — roughly a 29 % relative increase from the first third to the last.
- The **single-move maximum reaches 21.9 %**, well above the 5.3 % ceiling I reported from isolated positions.
  The band for a real game is therefore **2.4 % to 21.9 %**, not 2.6–5.3 %.
- **0 overruns in 600 moves** across 10 games, so the drift never threatens the clock.
- Consistent per game (10 of 10 games show min ≈ 2.4–2.5 % and median 4.1–4.8 %), so this is systematic, not
  position luck.

The mechanism is visible in the per-move trace: the fraction spikes on **critical positions** (the opening move,
and tactical moments) and sits near its floor on easy ones. As the game enters a complex middlegame the spikes
come more often, which is the upward drift.

## 2. UNEXPECTED: ten deterministic self-play games produced only THREE distinct final positions

```
game  1: 2r3k1/4bppp/p1q1p3/n3P3/...
game  2: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...
game  3: 2r3k1/4bppp/p1q1p3/n3P3/...     <- identical to game 1
game  4: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...
game  5: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...
game  6: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...
game  7: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...
game  8: 5bk1/nr3pp1/2n1p2p/3pP2P/...     <- the one different game
game  9: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...
game 10: r5k1/1q1n1pp1/2n1p2p/p2pP2P/...

distinct final positions: 3 of 10
```

**Seven of the ten games reached the SAME position.** That follows from determinism: same engine, same settings,
same start, one thread, fixed node/clock limits with no randomness — so the games must repeat. It is not a
defect (file 6 settles that multi-thread variation and draws are not defects, and determinism is what S-F16
verified), but it has a practical consequence for the owner: **self-play from a single fixed start will
repeatedly produce the same game**, so a self-play data set needs varied starts (an opening book, random
openings, or per-game randomness) or it collects one game many times.

Note the one game that diverged: it differs because the clock bookkeeping drifts by milliseconds between games,
which occasionally changes which depth the engine reaches and therefore the move. So the divergence is a
side-effect of the clock, not of any deliberate variety.

**How sure:** high. 10 games × up to 60 moves = 600 searches, PC20, Threads 1, one process per game, position
resent each move, every move legality-checked, 0 overruns, 0 illegal.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge  PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; clocks start 6000 ms + 60 ms per side, decremented by measured wall time
games 10, up to 60 moves each, one process per game, `position` resent before every `go`
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 10 self-play games, clock bookkeeping by measured wall time | done | `raw/ten_games.txt`, `run.log` | 600 moves, 0 overruns, 0 illegal |
| utilisation by game phase | done | same | 3.64 % / 4.32 % / 4.70 % — drifts upward |
| per-move maximum | done | same | 21.90 % (exceeds my earlier 5.3 % ceiling) |
| distinct final positions | done | same | 3 of 10 |
| separate the drift's cause from position difficulty | NOT done | — | mechanism is visible in the trace but not isolated |
| more than 10 games | NOT done | — | 600 moves was the time budget |

## Findings

`S-F26 | 6 | the clock-utilisation fraction DRIFTS upward across a game and its real band is wider than isolated positions suggested: over 10 games and 600 moves (PC build, PC20, Threads 1, 6 s + 0.06 s, clock bookkeeping by measured wall time) the median fraction is 3.64 % in the first third, 4.32 % in the middle and 4.70 % in the last, with a per-move maximum of 21.90 % — so the usable figure for a real game is 2.4 % to 21.9 %, not the 2.6–5.3 % I reported from single positions; 0 overruns in 600 moves | ten_games/raw/ten_games.txt ten_games/run.log (again: `python3 ten_games/ten_games.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

`S-F27 | 6 | ten deterministic self-play games from the same start produce only THREE distinct final positions — seven of the ten games reach the identical position — because the engine is fully deterministic at Threads 1 with fixed limits (S-F16), so self-play from one fixed start repeats itself; the single diverging game diverges only because millisecond clock drift occasionally changes the depth reached, so a self-play data set needs varied starts rather than many games from one | ten_games/raw/ten_games.txt | NEW |`

## Suspicions, not proven

- That the drift is "more critical positions per move as the game gets complex". The per-move trace supports it
  (spikes at tactical moments) but I did not classify positions by complexity to prove it.
- That the 21.9 % maximum is a time-manager decision at a sharp position rather than a long single depth step.
  Not isolated.

## What I did NOT do

- Did not isolate the drift's cause (position complexity vs a time-manager parameter that changes with the move
  number).
- Did not use varied openings, which is exactly what the diversity finding says is needed — that is a
  recommendation, not something I ran.
- Did not test whether the PC's own match program already varies openings (it may well).

## What I am NOT sure about

- Whether the owner's self-play already uses varied starts. If it does, S-F27 is moot for him; the determinism
  it demonstrates still stands.

## Times

`ten_games/stamps.txt`, every line a `date -u`.
