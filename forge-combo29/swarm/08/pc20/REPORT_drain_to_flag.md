# Draining the owner's clock all the way — does the engine ever flag? — seat 08

My earlier countdown sweep (08-F24) stopped at ~3000 ms after 40 moves per position, so it never reached the
interesting part: a long game whose clock has drained. This closes that gap.

**Method.** Owner's control, `go wtime X btime X winc 60 binc 60`, PC r15 under PC20, Threads 1, Hash 16. After each
move the clock is decremented by the measured wall time and incremented by 60 ms, exactly as a GUI does, and the same
position is searched again with the new clock — 200 moves per position, three positions.

**The answer: 0 flags in 600 moves, and the clock stabilises rather than draining.**

| starting position | moves played | lowest clock reached | moves where wall > remaining clock |
|---|---|---|---|
| G middlegame 1 | 200 | **1744 ms** | **0** |
| G middlegame 2 | 200 | **1577 ms** | **0** |
| startpos | 200 | **1438 ms** | **0** |

**The clock never came close to zero.** From 6000 ms it settled to a floor of 1438–1744 ms and stayed there for 200
moves. That is the increment doing its job: once the engine's per-move spend falls below the 60 ms increment, the
clock is a random walk with positive drift, and the engine's time manager shortens its thinking as the clock
approaches its floor. In 600 moves it never once spent more than the clock it had.

**So the answer to "does the owner's engine flag?" is: not on this test, and the mechanism that prevents it is visible.**
The clock has a stable equilibrium rather than a slow decline, because the increment is larger than the spend once the
engine has shortened down.

## What this does NOT show, stated plainly
- **It is not a game.** The same position is re-searched with a falling clock rather than a real game progressing, so
  the positions do not change and no game is ever won or lost. What is measured is the time manager under a draining
  clock, not a match result.
- **A 6 s + 0.06 control is generous relative to the engine's spend.** With a median move of ~185–340 ms (08-F33) the
  engine uses far less than the increment, so of course the clock rises. A control whose increment were, say, 20 ms
  would be a very different test and I did not run it.
- **The flag risk I measured earlier is unchanged**: a single move in a ≤8-piece endgame can take 1585 ms
  (08-F33). If such a position arrived with only 1400 ms on the clock, a flag becomes possible. This test's positions
  did not contain such an endgame at the low-clock moment, so the two results do not contradict each other — they
  bound different things.

## The honest summary for the owner
On 6 s + 0.06 the clock is **not** on a path to the flag: it stabilises around 1.4–1.7 s after 200 moves and the
engine never exceeded its remaining time in 600 moves. The residual risk is the **single expensive move** in a bare
endgame (up to the 1585 ms hard plan) arriving when the clock is already low — which this test did not stage.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 drain_to_flag.py /tmp/drain.txt
    # per-position summary: /tmp/drain.txt.jsonl
