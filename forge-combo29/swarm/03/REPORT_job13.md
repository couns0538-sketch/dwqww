# REPORT — seat 03, job 13: the drawn-root test, and a correction that refutes my own S-F23

> **METRIC LESSON (read this before measuring any endgame): in a bare-king ending the shortest game over is the DRAW
> and the longest is the LOSS.** Score the result — `is_insufficient_material()` / `is_checkmate()` /
> `is_game_over()` — never the ply count. Counting plies inverted the sign for exactly the population this job was
> measuring, and cost S-F23, S-F25 and S-F26.

**What was asked.** Rebuild with the drawn-root fix off, re-run the four positions at `go nodes 20000`, and report
whether the chosen move changes. If it does, the drawn-root adjudication is the cause; if not, the hypothesis is
refuted.

**The answer, on the hypothesis: REFUTED — the chosen move does not change.** With `FORGE_FIX_ROOT_DRAWN=0` the four
positions are byte-identical to the shipped build, on every move and every score. But the experiment also exposed
something much more important: **the hypothesis was the wrong question, because there was no defect in these four
positions at all.** In all four, the engine's chosen move forces an immediate draw by capturing the opponent's last
material, and the "alternative" my job-11 metric preferred is a losing move. **My S-F23 is wrong and my ply-count
metric was unsound. S-F20 is unaffected.**

## 1. The hypothesis test (what was asked)

Built `/home/ubuntu/build-nodraw/forge` = PC r15 tree with `-DFORGE_FIX_ROOT_DRAWN=0 -DFORGE_MATE_ALPHA_GUARD=1`,
`bench 11 = 312866` (unchanged, as the patch's own comment predicts: no bench root has a terminal position).

| idx | drawn-root fix OFF | shipped PC build | same? |
|---|---|---|---|
| 6 | e3f3, chosen cp 0, alt cp −944 | e3f3, chosen cp 0, alt cp −944 | **identical** |
| 22 | g5f6, chosen cp 0, alt cp −953 | g5f6, chosen cp 0, alt cp −953 | **identical** |
| 37 | f6f7, chosen cp 0, alt cp −725 | f6f7, chosen cp 0, alt cp −725 | **identical** |
| 44 | c7d6, chosen cp 0, alt cp −439 | c7d6, chosen cp 0, alt cp −439 | **identical** |

Files: `nodraw.txt`, `withdraw.txt` (the second is a control on the shipped build), `run13.py`.

**Why it could not have mattered, visible before the build:** `root_drawn` requires
`is_insufficient_material() || is_repetition() || halfmove_clock >= 100` (with the fix off) and, with the fix on, only
`is_insufficient_material()`. On all four root positions: `insufficient_material=False`, `halfmove_clock=0`,
`is_repetition(3)=False`. The root adjudication cannot fire on any of them, so the switch is inert here by
construction. I built and ran it anyway rather than argue from reading, and then checked the predicate directly.

## 2. The finding that overturns S-F23

Looking at why the chosen moves score exactly `cp 0`, I replayed them with python-chess:

```
idx 6  e3f3 -> 8/8/8/8/8/5K2/8/5k2 b - - 0 14   game_over=True  insufficient_material=True
       e3d3 -> 8/8/8/8/8/3K1p2/8/5k2 b - - 1 14  game_over=False
idx 22 g5f6 -> 5K2/8/5k2/8/8/8/8/8 w - - 0 14    game_over=True  insufficient_material=True
       g5g6 -> 5K2/8/5Pk1/8/8/8/8/8 w - - 1 14    game_over=False
idx 37 f6f7 -> 8/5K2/8/8/5k2/8/8/8 b - - 0 7     game_over=True  insufficient_material=True
       f6g7 -> 8/5pK1/8/8/5k2/8/8/8 b - - 1 7     game_over=False
idx 44 c7d6 -> 8/8/3K4/8/8/8/2k5/8 b - - 0 10    game_over=True  insufficient_material=True
       c7b8 -> 1K6/8/3r4/8/8/8/2k5/8 b - - 1 10   game_over=False
```

**In every one of the four, the engine's chosen move captures the last enemy pawn or piece and forces a draw by
insufficient material. The alternative my metric preferred keeps the enemy material on the board, i.e. it loses.**
The engine scored those moves `cp 0` because they ARE drawn, and `cp 0` was correct. The engine was right in all
four positions.

## 3. My error, stated plainly

`job11/plycost.py` measured the ply count until `is_game_over()` and treated **more plies as better**. In a bare-king
endgame the *shortest* game over is a **draw**, and the longest is a **loss**. So when the engine took the draw at one
ply, my metric scored it as the worst possible move, and when the alternative played on and lost after 22-50 plies, my
metric scored it as the best. **The sign convention was inverted for exactly the population being measured.**

That is the same class of error I had already audited in my parsers (a metric that cannot tell "measured" from
"missing"), and I did not apply it to a metric that could not tell "draw" from "loss".

## 4. What this does to each finding

| id | effect |
|---|---|
| **S-F23** (play-out ply cost: 5 of 8 die sooner; four lose at once) | **WITHDRAWN.** The metric is unsound; the four "instant losses" are forced DRAWs, i.e. the engine's best available outcome. The finding is refuted by its own data. |
| **S-F24** (self-play collapses to one position) | **Unaffected** — it is about the generator, observed directly. |
| **S-F22** (0/50 strict signature; 11/45 any-margin) | **The count stands, but its interpretation changes.** The 0/50 result is now *stronger* than I reported: the engine's choice was right in the cases I examined. The 11 any-margin cases are unexamined in the same way, and given this result they are equally likely to be correct choices my metric would have mis-scored. |
| **S-F20** (position 155: c6c7 vs c6d6) | **Unaffected, and I re-checked it under this new lens.** In 155 BOTH moves continue the game (neither forces a draw); python-chess adjudicated the play-out as "black mates" for both, so the ply comparison there compares loss-to-loss, where longer IS better. The engine's own scores also agree that c6d6 is better (cp −1142 vs mate −11). S-F20 stands. |
| **S-F25** (wrong move reproduces at `go nodes 20000`) | **WITHDRAWN AS STATED** — "wrong move" is false for these four; the moves are correct. What still stands from that job is the narrower fact that `go nodes 20000` and `go depth 16` agree on the move in 7 of 7 cases. |
| **S-F26** (cp 0 suggests a draw adjudication) | **CONFIRMED as an observation, but it was the engine being RIGHT**, not a defect. Withdrawn as a hypothesis about a bug; kept as the explanation of the cp 0s. |

## 5. Verification of S-F20 under the corrected lens

Because S-23's failure was a metric failure, I re-verified the one finding that keeps its importance:

- position 155, chosen c6c7 vs alternative c6d6;
- neither move ends the game (`is_game_over=False` after both);
- python-chess play-out: both lines end in "black mates" — so both are losses, and 22 plies versus 20 plies is a
  genuine loss-versus-loss comparison where longer is better;
- and the engine's OWN scores agree with the play-out: c6d6 cp −1142 / −1192 versus c6c7 mate −11 / −22.

So S-F20 does not rest on my flawed metric at all — it rests on the engine contradicting its own score table, backed
by a play-out where both outcomes are the same kind. It stands.

## 6. Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F27 | With `FORGE_FIX_ROOT_DRAWN=0` the four job-12 positions answer identically to the shipped PC build (same move, same scores), so the drawn-root adjudication is not the cause of anything there — and it could not be, since `is_insufficient_material`, `is_repetition(3)` and `halfmove_clock>=100` are all false at those roots. | `cd forge-combo29/swarm/03/job13 && python3 run13.py ~/build-nodraw/forge /tmp/a.txt` |
| S-F28 | **WITHDRAWAL of S-F23, and of S-F25's "wrong move" framing:** in all four positions the engine's chosen move captures the opponent's last material and forces an immediate draw by insufficient material, while the alternative my ply-count metric preferred loses — the engine was right and my metric's sign convention was inverted for bare-king endings (shortest game over = draw = best). | `python3 -c "import chess; b=chess.Board('8/8/8/8/8/4Kp2/8/5k2 w - - 0 14'); b.push_uci('e3f3'); print(b.is_insufficient_material())"` |

## 7. Suspicions, not proven

- That some of the 11 any-margin cases in S-F22 are also correct choices mis-scored by the same inverted metric. They
  are unexamined; I am not claiming they are defects, and on this evidence I would expect most to be correct.

## 8. What I did NOT do

- Did not re-audit all 45 scan positions with a proper draw-aware metric. That is the honest follow-up and it is not
  done.
- Did not re-run the 50-position scan.

## 9. Times

`job13/stamps.txt`.
