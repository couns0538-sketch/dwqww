# REPORT_clock_scale — does the engine's clock usage scale with the clock? (follow-up to S-F18)

**What was asked (my own follow-up):** S-F18 found the PC's match path uses only 2.6 %–5.3 % of a 6 s clock. Is
that a hardware ceiling (the search finishes a depth and stops) or a time-manager soft limit?

**The answer: it is the TIME MANAGER, not a hardware ceiling. The fraction barely moves across a 30x range of
clock sizes.**

```
clock            allowed   engine time (median)   % of allowed   depths     over-clock
1000+10 ms        1010 ms        28.0 ms             2.77 %      13         0/5
3000+30 ms        3030 ms        72.0 ms             2.38 %      15,16      0/5
6000+60 ms        6060 ms       159.0 ms             2.62 %      17         0/5
30000+300 ms     30300 ms      1312.0 ms             4.33 %      25,26      0/5
```

Over a **30x** range of allocated time the engine uses **2.38 %–4.33 %** — it scales roughly linearly with the
clock (28 → 72 → 159 → 1312 ms) while the fraction stays in a narrow band. A hardware ceiling would show the
fraction FALLING as the clock grows (fixed search time against a bigger budget); it does not. So the engine is
choosing to stop early at every clock size, and the bestmove stayed identical (1 distinct) at every clock.

**Why this matters for the owner.** The PC's matches run at 6 s + 0.06 s. On this 4-core machine the engine
spends ~160 ms per move and reaches depth 17. If the PC's machine is faster, it reaches more depth in the same
160 ms; if slower, less. Either way the match outcome depends on a *soft* limit, not on the machine's ability to
use the clock — so an engine-vs-engine result at 6 s measures the time manager's aggressiveness as much as
search quality. That is a testable claim about the owner's own matches, and it is not something I can check
without the PC's games.

**How sure:** high — 20 clock searches across 4 clock sizes, Threads 1, PC20, one real-game position, every run
deterministic in the move with 0 over-clock.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; one position (G0) across four clock sizes; 5 reps each
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 1 s / 3 s / 6 s / 30 s clocks, 5 reps each | done | `raw/clock_scale.txt`, `scale.log` | fraction 2.38 %–4.33 % across a 30x range |
| over-clock safety | done | same | 0 of 20 runs over its allowance |
| bestmove stability across clock sizes | done | same | 1 distinct bestmove at every clock |
| more than one position | NOT done | — | one position × 4 clocks × 5 reps |

## Findings

`S-F19 | 6 | the engine's clock usage is a TIME-MANAGER soft limit, not a hardware ceiling: across a 30x range of allocated time (1.0 s, 3.0 s, 6.0 s, 30.0 s) on the PC build under PC20 at Threads 1 the engine uses 28 / 72 / 159 / 1312 ms — 2.38 % to 4.33 % of the allowance in every case — so it scales linearly with the clock instead of hitting a fixed ceiling, and it never exceeds the clock (0 of 20 runs); the bestmove was identical at every clock size | clockpath/raw/clock_scale.txt clockpath/scale.log (again: `python3 clockpath/clock_scale.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That the +1.5 points of fraction at 30 s reflects a different iteration ladder rather than a deliberately
  looser soft limit at long clocks. Not investigated (time-manager code is area 8's).
- That the same ratio holds on the PC's faster machine. The RATIO may be machine-independent while the absolute
  depth is not; untested.

## What I did NOT do

- Did not read the time-manager code to explain the band; I measured the behaviour only.
- Did not test other positions, `movestogo`, or the increment's effect across a move sequence.

## What I am NOT sure about

- Whether a 6 s match on the owner's PC is dominated by this soft limit in practice. The claim follows from the
  measurement but the consequence for real games is inference, not measurement.

## Times

`clockpath/stamps.txt`, every line a `date -u`.
