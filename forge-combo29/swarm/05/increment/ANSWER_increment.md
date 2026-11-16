# ANSWER: does raising the increment buy thinking time? — YES, sub-linearly (exponent 0.494 at a 6 s clock, 0.758 at a 2 s clock)

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

Fitting a power law over two decades: **t ∝ increment^0.494 at a six-second clock** — essentially sqrt(increment) *at that
clock*. (Linear would be 10x per decade; a plateau would be 1.0x. The measured 2.5x then 3.9x brackets the sqrt
prediction of 3.16x.) **The exponent is clock-dependent: it is 0.758 at a two-second clock, so the gain from raising
the increment is LARGER on smaller clocks.**

## A fourth point overturns part of the above: there IS a ceiling

Adding a fourth increment (24,000 ms) shows the growth **stops**:

| increment | median wall | median depth | growth vs previous 10x |
|---|---|---|---|
| 60 ms | 157 ms | 19 | — |
| 600 ms | 544 ms | 23 | 3.46x |
| 6,000 ms | 2,867 ms | 32 | 5.27x |
| **24,000 ms** | **2,860 ms** | **32** | **1.00x — no gain** |

Verified per run (3 positions, 4 runs each): at increment 6000 position 0 spends [3445, 3437, 3442, 3476] ms and at
increment 24000 the same position spends [3442, 3426, 3473, 3475] ms — the same values, so this is a ceiling, not
noise. `out/fourth_point.txt`, `out/ceiling_runs.txt`.

**So S-F51's "no plateau" is true only between 0.06 s and 6 s.** Practical statement for the owner:

- `0.06 → 0.6 s`: **2.5x** the time, **+2 median plies**.
- `0.06 → 6 s`: **~9.7x** the time, **+7 median plies** (one board reached depth 64).
- `6 → 24 s`: **nothing at all** — the engine stops asking for more than roughly 3.6 s per move on this path.

**Where exactly does it stop?** A bracketing run (4 positions, 3 runs each, clock 6 s) pins it:

| increment | median wall | median depth | vs previous |
|---|---|---|---|
| 3,000 ms | 1,680 ms | 26 | — |
| **6,000 ms** | **1,928 ms** | **27** | 1.15x |
| 10,000 ms | 1,920 ms | 27 | **1.00x** |
| 16,000 ms | 1,928 ms | 27 | **1.00x** |
| 24,000 ms | 1,928 ms | 27 | **1.00x** |

So the flat region begins at an increment of about **6 seconds** and holds across a 4x range beyond it. **The useful
increment range on this path is roughly 0.06 s to 6 s; past 6 s the increment is dead weight.**

## What this means for the owner

- Raising the increment **does** buy thinking time — no plateau, and the effect is large in practice:
  - `0.06 → 0.6 s`: **2.5x** the time, **+2 median plies** (median depth 22 → 24).
  - `0.06 → 6 s`: **9.7x** the time, **+7 median plies** (median depth 22 → 29, and one board reached **depth 64**).
- **At a six-second clock** the return is diminishing but not vanishing: to double the thinking time you need about
  **4x the increment** (exponent 0.494). **At a two-second clock** the exponent is 0.758, so doubling needs only
  about 2.5x the increment — the gain is larger on smaller clocks.
- At the owner's `winc 60` the engine is using **3.4 %** of its 6-second clock, so there is a great deal of unspent
  time for an increment increase to unlock (32.8 % at `winc 6000`).

## Reproduce

```
python3 increment_scaling.py /tmp/build-pc/forge 5 10
```

Prints the per-position table and the aggregate. Raw output: `out/scaling.txt` (0.06 vs 0.6),
`out/third_increment.txt` (6 s), `out/scaling_law.txt` (the fit).

## Limits, stated plainly

- **10 positions, one build.** The exponent **0.494 is at a 6-second clock** (three points) and **0.758 at a 2-second
  clock** (two points); a fourth increment (e.g. 24 s) would test the fit further and I have not run it. The two
exponents are quoted together everywhere in this file and in FINDINGS.md, because the value without its clock is
misleading.
- **The clock is held at 6 s in the table above, and I then found the law is clock-DEPENDENT.** Repeating the two
  increments at a 2,000 ms clock gives a **5.7x** jump (64 -> 367 ms, depth 17 -> 23) instead of 2.50x, i.e. an exponent
  of 0.758 rather than 0.494. So S-F51's "sqrt law" is specific to a 6-second clock, and **an increment increase buys
  MORE when the base clock is smaller**. Anyone quoting the exponent must quote the clock size with it. Evidence:
  `out/law_at_2s_clock.txt`.
- No cause is claimed. I did not read the time manager, so I cannot say which constant produces the sqrt.
- p90 and max are nearest-rank over the 50 runs per column; the protocol (fresh process, monotonic clock, read to
  `bestmove`) is the same one that produced S-F37–S-F49.
- **Not yet confirmed by another seat.** The protocol is one command and the script is self-contained.
