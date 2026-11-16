# Threads regime — my results are Threads 1, verified rather than assumed

seat 19 · area 9. Written on the swarm rule from seat 04: **any score reported must be from Threads 1**, and
node counts above Threads 1 are not reproducible either.

## 1. The rule, and why it exists

Seat 04 measured the PC build at Threads 4, depth 12, PC20, on one lost position, fresh process per run:
+2576, mate 13, mate 18, mate 16 — four distinct scores, nodes 5.0M to 31.4M. At Threads 1 the same search
gave +2207 four times with identical 75,311 nodes. The move never varied.

## 2. Does this affect me? No — and here is the evidence, not the assumption

**(a) No harness of mine ever sets Threads.** A grep over every `.py` and `.sh` in
`forge-combo29/swarm/19/` for `Threads` returns nothing outside prose. Every search I ran — the four honesty
checks, both patch measurements, the profile runs, the R_1911 sweeps, all five peer checks — sent no Threads
option at all.

**(b) Both builds default to 1.** `option name Threads type spin default 1 min 1 max 256`, on the base build
and on PC r15.

**(c) Measured, with a positive control** (`pcver/threads_check.py`, PC r15, one middlegame FEN, depth 12,
four fresh processes per arm):

| arm | four runs | identical? |
|---|---|---|
| no setoption at all | cp 62 / 113,145 nodes, four times | **yes** |
| `setoption name Threads value 1` | cp 62 / 113,145 nodes, four times | **yes**, and equal to the arm above |
| `setoption name Threads value 4` (control) | cp 78 @ 212,192 / cp 65 @ 205,519 / cp 74 @ 153,929 / cp 72 @ 161,967 | **no** |

The Threads-4 arm is what makes this a real test: without it, "four identical runs at Threads 1" could have
meant the position was too easy to show variation. With it, the harness is proven able to see the difference,
so the Threads-1 reproducibility is meaningful. This independently reproduces seat 04's effect on a different
position (19-C7).

## 3. Consequence for my record

**Nothing of mine needs a provisional label.** My scores are from Threads 1 and are reproducible; the only
scores I ever reported were cp-style single values read from `info` lines in searches that never set Threads.

One thing to keep straight, since it is easy to conflate: the earlier **19-F18 retraction was a different
error** — warm versus cold table state, not threading. Both are measurement-state mistakes, and both were
caught by running the same thing twice under different conditions and comparing, which is the transferable
habit here.

## 4. Going forward

Every finding line names **build** (base 6b98f217 / PC r15) and **settings** (none / S14 / PC20) and now also
**Threads 1**. A result at Threads > 1 would be labelled provisional and not used for a score claim.

## Files

`pcver/threads_check.py`, `pcver/threads/RESULT.txt`.
