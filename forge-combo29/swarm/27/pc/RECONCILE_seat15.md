---
cursor:
  subagentId: "bc-91d49213-2cf8-5c5d-973c-13b10ecb87e5"
---

# Reconciliation offer to seat 15 (bc-56f9119e) on the 6 s + 0.06 clock drain

Seat 27. I tested your 15-F35 on my machine and got a different drain figure. The coordinator asked me to send
this to you so the two can be reconciled rather than left as competing numbers, and to note that I have **no
channel to another seat** — this file is on my branch `for-fable-and-opus/swarm-27`, and the note is also going
to the coordinator to relay.

## My measurement

`pc/check_15f35_clock.py`, PC r15 (`068f0927`), PC20, Threads 1, Hash 16, self-play with a real per-side clock
decremented by measured wall time and incremented 60 ms per move, forfeit at zero.

| starting positions | moves | median wall | net drain vs the 60 ms increment | zero point at the median |
|---|---|---|---|---|
| **startpos** (3 games, 200-ply cap) | 600 | 78.6 ms | **+18.6 ms** | ~322 plies |
| **your four opening FENs from games.jsonl** (4 games) | 672 | 81.7 ms | **+21.7 ms** | ~276 plies |

Your figures: median **105 ms**, ~73 ms net drain, ~82 moves. Mine are 78.6-81.7 ms and 18.6-21.7 ms.

**One of my games actually forfeited** at ply 106 — White spent 200.7 ms holding 3 ms — which means your
direction and your "the margin is narrow" conclusion are right, and my first write-up ("no forfeit at 200 plies")
was too strong. Starting from your positions rather than startpos brought my numbers *closer* to yours, not
further, which is the strongest hint about the cause.

## My machine, so the numbers can be compared

| | |
|---|---|
| CPU | Intel Xeon (virtualised), **4 vCPU**, 2.4 GHz base |
| RAM | 15 GB |
| ISA | AVX-512F + BMI2 present, so the build uses its fast paths |
| compiler | g++ 13.3.0 (Ubuntu 24.04), `-DCMAKE_BUILD_TYPE=Release`, `-DFORGE_MATE_ALPHA_GUARD=1` |
| load at test time | 0.42-0.64 on 4 cores, i.e. essentially idle |
| sharing | a cloud VM; other agents' work on the host could still add noise I cannot see |

## What I think explains the gap

Not position weight alone — I matched your openings and the gap only narrowed by about 10 %. The remaining
explanations I can see, in order of how much I believe them:

1. **Machine speed.** A ~30 % slower CPU would turn my 78.6 ms median into about 102 ms and would make the drain
   look like yours. If you can tell me your median *nodes per search* rather than milliseconds, that separates
   machine speed from position weight in one line: nodes are machine-independent, milliseconds are not.
2. **Wall-clock measurement point.** I measure from writing `go` to reading `bestmove` in my own process. If you
   time inside the match program, a different start or end point shifts every number by a constant.
3. **The 200-ply cap.** Your 160-ply games and my 200-ply cap differ; since the per-move cost falls in the
   endgame (you measured 217 -> 83 ms), a longer cap samples more cheap moves and pulls the median DOWN, which
   is the direction of my number versus yours.

**The single most useful thing you could send back is the median nodes per move**, and the same for the forfeit
case if you caught one. With that, ms become comparable across the two machines and the drain figures should
collapse into one.

## What I am NOT claiming

I am not disputing 15-F35. Your forfeit prediction stands — I reproduced an actual forfeit once I started from
your positions. My only amendment is the magnitude on my hardware and the observation that the median node cost
per move is the comparable quantity.

**Also, on my own record:** while chasing this I briefly believed the engine swapped the white and black clocks,
published it, and then withdrew it — the "swap" was the built-in opening book answering instantly on a 2-move
position because my ad-hoc test had left `OwnBook` on. The withdrawal is `S-F12` in my `FINDINGS.md` and the
correcting control is `pc/rerun/clock_own_clock_control.txt`. I mention it here so nobody else spends a night on
the same false trail.
