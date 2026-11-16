# REPORT_clockpath — the PC's MATCH path (6 s + 0.06 s) under PC20, Threads 1

**What was asked (my own priority from file 6):** the clock path `go wtime 6000 btime 6000 winc 60 binc 60` is
what the owner's strength matches use. Is it reproducible, and does it stay inside the clock?

**The answer: the BESTMOVE is perfectly reproducible (1 distinct move in 20 runs on all 4 positions), it never
comes near the clock, and the SCORE varies between two values because the search reaches depth 17 or 18.**

```
position  distinct bestmoves  distinct scores  depths     wall median   over 6060 ms
G0        1  (g7g6)          2  (-292,-294)    17,18      162.8 ms      0 of 20
G1        1  (b6b5)          2  (-256,-257)    17,18      299.8 ms      0 of 20
G6        1  (d6e6)          2  (22,33)        17,18      217.3 ms      0 of 20
G10       1  (e8d8)          2  (-11,0)        18,19      309.2 ms      0 of 20
```

**Two things matter here, and the second one is the finding.**

1. **The move is stable.** 20 runs per position, one distinct bestmove each, and the bestmove was inside its own
   PV on 80 of 80 runs — so the clock path never plays an unsearched move.
2. **The engine uses about 3 % to 5 % of the clock it is allowed.** A 6 s clock with a 0.06 s increment permits
   roughly 6.06 s for the move; the engine's own reported search time is 156–325 ms, i.e. **5 % of the budget at
   most**. Nothing comes close to losing on time (0 of 80 runs over 6060 ms), but the flip side is that the
   search is not using the time it has: it stops at depth 17–19 and the *depth it reaches varies*, which is why
   the score has two values per position. For a strength match this means the engine is effectively
   depth-bounded, not time-bounded, at 6 s with this machine's speed.

**My P2 was right in shape and wrong in cause.** I predicted a score spread because "small timing differences
change the depth reached"; the real cause is the same (the depth differs) but the timing is not tight — the
search finishes a depth and stops well short of the clock, so the *variation is in which depth it reaches*, not
in how much time it takes.

**P3 confirmed** (no run above 6.06 s) but the margin is enormous (max 325 ms), which I did not predict: I said
"median between 40 % and 65 % of the budget", actual 2.6 %–5.3 %. **P4 confirmed** (node spread 1.09x–2.17x
between fastest and slowest run, i.e. more than 20 %). **P1 and P5 confirmed exactly.**

**How sure:** high — 80 clock searches, four real-game positions, Threads 1, PC20, fresh process + `ucinewgame`.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-pc/forge   PC r15, sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
        none 312866 / S14 242796 / PC20 278024   (all match file 5)
settings PC20 + Threads 1 + Hash 16; go wtime 6000 btime 6000 winc 60 binc 60; 20 reps per position
clock: 6.00 s + 0.06 s increment, the PC's match path
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| bestmove determinism, 20 runs × 4 positions | done | `raw/clockpath.txt`, `run.log` | 1 distinct bestmove on all four |
| score variation | done | same | 2 distinct scores per position, from reaching depth 17 or 18 |
| clock safety | done | same | 0 of 80 runs over 6060 ms; wall max 325 ms |
| time actually used | done — bigger finding than expected | same | 156–325 ms of a 6060 ms allowance (2.6 %–5.3 %) |
| bestmove inside its own PV | done | same | 80/80 |
| low-time behaviour (0.1 s, 1 s) | NOT done | — | area 8's territory, and file 6 says a draw/timeout verdict there is settled |
| more than 4 positions | NOT done | — | 80 searches was the time budget |

## Findings

`S-F18 | 6 | the PC's match path (PC r15, PC20, Threads 1, Hash 16, `go wtime 6000 btime 6000 winc 60 binc 60`) is REPRODUCIBLE in the move (1 distinct bestmove over 20 runs on each of 4 real-game positions, and the bestmove is inside its own PV on 80/80 runs) but the engine uses only 156-325 ms of the 6060 ms it is allowed — 2.6% to 5.3% — stopping at depth 17-19, and because the depth it reaches varies the score has two distinct values per position; no run exceeds the clock (0 of 80) | clockpath/raw/clockpath.txt clockpath/run.log (again: `python3 clockpath/clockpath_test.py ~/builds/bld-pc/forge /tmp/o`) | NEW |`

## Suspicions, not proven

- That the 5 % clock usage is caused by a soft limit computed far below the remaining time (a time-manager
  question, area 8's). I measured the effect, not the cause.
- That the two-score spread would disappear with a fixed depth. Not tested here (my depth-10 sweep shows scores
  are stable when the depth is fixed, which supports it).

## What I did NOT do

- Did not investigate WHY only 3 %-5 % of the clock is used — that is the time manager (area 8), and I would only
  be guessing from the outside.
- Did not test at other clocks (1 s, 60 s), so I cannot say whether the fraction grows or shrinks.
- Did not test the increment actually being added across a sequence of moves in one process.

## What I am NOT sure about

- Whether the owner's matches use exactly this command or a `movestogo` variant; I used the file 6 description.

## Times

`clockpath/stamps.txt`, every line a `date -u`.
