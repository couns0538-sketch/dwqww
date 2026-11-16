# seat 20 — job 53: the 0-node answer becomes COMMON under load (1/10 → 6/10), and only in the collapsed cell

The owner's question: measure the 0-node case with three background CPU hogs and report how many of ten runs give a
0-node answer versus an idle machine. If load makes it common, anyone analysing on a busy PC with MultiPV 8 and a
large Hash is at real risk of getting a move with no search behind it.

**Answer: yes — 6 of 10 under load against 1 of 10 idle, while the healthy cell stays 0 of 10 in both conditions.**

## The measurement (PC r15, PC20 options, Threads 1, `go wtime 5000 btime 5000`, 10 fresh processes per arm)

| cell | condition | **0-node answers** | node counts seen | moves seen |
|---|---|---|---|---|
| **Hash 2048 + MultiPV 8** | idle | **1 / 10** | 0, 220 | `b8a8`, `d5d4` |
| **Hash 2048 + MultiPV 8** | **3 CPU hogs** | **6 / 10** | 0, 67, 143 | `b8a8`, `d5d4` |
| Hash 16 + MultiPV 1 (healthy) | idle | **0 / 10** | 121,306 / 170,070 / 288,912 | `g7g6` |
| Hash 16 + MultiPV 1 (healthy) | 3 CPU hogs | **0 / 10** | 121,306 / 170,070 / 288,912 | `g7g6` |

## What this establishes
1. **The 0-node answer is a property of the collapsed cell, not of the machine.** The healthy cell never produced one
   (0/10 both conditions) even with three hogs running.
2. **Load makes it COMMON, not rare**: 10 % idle → **60 % under load**. On a busy PC the majority of such searches can
   return a move with no search behind it.
3. **The answer varies in the collapsed cell** (`b8a8` and `d5d4` both appear) while the healthy cell is a single
   move with a wide but sane node spread.
4. The mechanism fits S-C27's cause: the per-line `tt.clear()` for MultiPV 8 on a 2 GB table consumes the clock, and
   when the machine is contended the clock is gone before any depth is published — so the engine falls back to its
   first move with 0 nodes.

## The warning, stated so the owner can act on it
> **Analysing on a busy PC with MultiPV 8 and a large Hash (≥ 256 MB) can return a move with NO SEARCH BEHIND IT —
> 6 of 10 runs with three CPU hogs running, against 1 of 10 idle. The move can also differ between runs.**
> Use **MultiPV 1 at any Hash**, or **Hash ≤ 16 MB with MultiPV > 1**. The PC's own matches use MultiPV 1 and are
> unaffected.

## Honest details and limits
- **My harness refused once during the first attempt** with `no readyok` after 20 s under load. I raised the
  `isready` timeout to 120 s for the load arm **only** and printed that in the output: the engine was starved, not
  hung, and the 19-F12 discipline (never continue without a readyok, never invent an answer) is unchanged.
- Three hogs on a 4-core box; `Threads 1` means the engine contends with them for one core.
- One position, one clock (5 s). The *rate* (1/10 → 6/10) is this position's; the *behaviour* is what generalises.
- The healthy cell's node spread (121k–289k) is itself the clock-path irreproducibility I recorded as S-F49 — same
  cause, and it does not produce 0-node answers.
