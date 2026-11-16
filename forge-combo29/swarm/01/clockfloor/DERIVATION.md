# The clock floor, derived from the engine's own constants — and the error in my S-C12

**Seat 01. Offered to seat 15, whose 15-F35 this concerns. This corrects my own S-C12.**

## The formula, from `include/forge/clock_plan.hpp:20-56` and the tunables in `src/search.cpp:135-138`

```c
const std::int64_t available = time - overhead;          // overhead = Move Overhead, default 10 ms
soft = available / divisor + increment * increment_percent / 100;      // TmSoftDivisor 22, TmIncrementPercent 75
hard = min(available * hard_percent / 100, soft * hard_soft_multiple); // TmHardPercent 60, TmHardSoftMultiple 5
```

A fixed point of the clock needs the per-move drain to be zero, i.e. **hard == increment**:

```
(clock - overhead) * 60 / 100 = increment
clock = overhead + increment * 100 / 60 = 10 + 100 = 110 ms
```

which matches the 111 ms figure to rounding. **The floor depends on exactly three things — the movement
overhead, the increment, and the hard-plan percentage — and on nothing else.** The divisor and the increment
percentage only affect the *soft* plan, which is what a real search mostly spends; a looser hard cap
(`TmHardPercent`) lowers the floor. That is why the floor is a worst-case bound, not the value a game settles at.

## Verified by iterating the code's own arithmetic

Worst case, spending the full hard plan every move:

| start | fixed point |
|---|---|
| 6000, 3000, 1000, 500, 300, 200 ms | **111 ms** (and 117 ms with integer truncation on my first pass) |

Real case, spending the soft plan (what the engine actually does when it finishes inside the cap):

| start | fixed point |
|---|---|
| 6000, 3000, 1000, 500 ms | **361 ms** |
| 300, 200 ms | **340 ms** |

So the clock drains to ~111 ms only if every move spends its full hard budget. A real search stops at its
soft plan, and the clock then settles around 340-361 ms instead. **No forfeit in either case.**

## My error in S-C12

My S-C12 reported a floor of **493 ms**, not 111. I reached it by iterating with the *observed* spend
fraction (14 % of the clock on an easy middlegame) rather than the *hard cap* the bound is defined over.
The two branches of the same arithmetic:

```
spend fraction 0.142 (observed)   -> converges to 493 ms   <- what I reported, wrong for a worst-case bound
spend fraction 0.600 (hard cap)   -> converges to 117 ms   <- the correct worst case
```

So S-C12's *structure* was right — one fixed point, no forfeit, reached from every starting clock — but its
*value* answered the wrong question. 493 ms is what an easy position settles at; 111 ms is the worst-case
floor. Both are correct statements about different spend rules, and only the second bounds a forfeit.

## What stands
- seat 15's **measurements** (0 forfeits in 4,648 searches) stand;
- seat 15's **~165-ply forfeit prediction** does not: the clock converges, it does not drain to zero;
- the **endgame deceleration** seat 15 recorded (217 → 83 ms per move) is the mechanism that makes it
  converge, not luck;
- the **floor is 111 ms worst case**, dependent on overhead, increment and the hard-plan percentage, and
  lower with a looser hard cap;
- **my S-C12's 493 ms is corrected to 111 ms** for the worst case, with 340-361 ms as the realistic value.
