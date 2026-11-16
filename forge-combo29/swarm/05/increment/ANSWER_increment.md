# ANSWER: does raising the increment buy thinking time? — YES, as the square root of the increment

Seat 05, area 5. Branch `for-fable-and-opus/swarm-05`. All numbers Threads 1, Hash 16, OwnBook false, PC20, clock
fixed at 6000 ms, **sequential** (one engine process at a time — see `../MEASUREMENT_WARNING.txt`).
Build: PC r15, patch sha256 prefix `d6bd72c531f785f4`, honesty 8/8 (`../pcbuild/HONESTY_PC.md`).

## The measurement you asked for: 0.06 vs 0.6, ten positions, both increments

10 positions from `G.epd` (real game positions), 5 fresh processes per (position, increment) = 50 runs per column.

| increment | n | **median** | **p90** | max | **median depth** | max depth | median nodes |
|---|---|---|---|---|---|---|---|
| **60 ms (0.06 s, the owner's value)** | 50 | **202 ms** | **263 ms** | 449 ms | **22** | 29 | 414,306 |
| **600 ms (0.6 s, 10x)** | 50 | **504 ms** | **791 ms** | 799 ms | **24** | 44 | 1,115,456 |

**Answer: it does NOT plateau.** 10x the increment buys **2.50x** the thinking time and **+2 median plies**.

Per position, the increment raised the time on 9 of 10 boards (pos 2 unchanged: 447 → 448 ms); depth gains ranged
from +0 to **+17 plies** (pos 6: depth 27 → 44).

## I then tested the law with a third increment

Because two points can be fitted by anything, I added a 100x point (increment 6000 ms):

| increment | median wall | median depth | % of the 6 s clock | growth per 10x |
|---|---|---|---|---|
| 60 ms | 202 ms | 22 | 3.4 % | — |
| 600 ms | 504 ms | 24 | 8.4 % | 2.50x |
| 6,000 ms | 1,968 ms | 29 | 32.8 % | 3.90x |

Fitting a power law over two decades: **t ∝ increment^0.494** — i.e. essentially **sqrt(increment)**.
(Linear would be 10x per decade; a plateau would be 1.0x. The measured 2.5x then 3.9x brackets the sqrt prediction
of 3.16x.)

## What this means for the owner

- Raising the increment **does** buy thinking time — no plateau, and the effect is large in practice:
  - `0.06 → 0.6 s`: **2.5x** the time, **+2 median plies** (median depth 22 → 24).
  - `0.06 → 6 s`: **9.7x** the time, **+7 median plies** (median depth 22 → 29, and one board reached **depth 64**).
- The return is **diminishing but not vanishing**: to double the thinking time you need about 4x the increment.
- At the owner's `winc 60` the engine is using **3.4 %** of its 6-second clock, so there is a great deal of unspent
  time for an increment increase to unlock (32.8 % at `winc 6000`).

## Reproduce

```
python3 increment_scaling.py /tmp/build-pc/forge 5 10
```

Prints the per-position table and the aggregate. Raw output: `out/scaling.txt` (0.06 vs 0.6),
`out/third_increment.txt` (6 s), `out/scaling_law.txt` (the fit).

## Limits, stated plainly

- **10 positions, one build, one clock size (6 s).** The exponent 0.494 is fitted through three points; a fourth
  (e.g. 24 s increment) would test it further and I have not run it.
- The clock is held at 6 s throughout. I did **not** test whether the same sqrt law holds at a different clock size —
  my S-F39/S-F40 show the clock itself matters less than the increment, which is why the increment was the right
  variable, but the interaction is unmeasured.
- No cause is claimed. I did not read the time manager, so I cannot say which constant produces the sqrt.
- p90 and max are nearest-rank over the 50 runs per column; the protocol (fresh process, monotonic clock, read to
  `bestmove`) is the same one that produced S-F37–S-F49.
- **Not yet confirmed by another seat.** The protocol is one command and the script is self-contained.
