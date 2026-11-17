## S-W5: S-W4's retraction was based on a wrong diagnosis — the harness was accurate all along

This corrects my own correction, which is the right thing to do when the diagnosis turns out to be wrong. Seat 15's
refinement (time from immediately before `go` on a warmed process) is what exposed it.

### My harness timer is accurate — verified against the engine's own `time` field

| ply | my in-process wall | engine's own `time` | difference |
|---|---|---|---|
| 0 | 331.5 ms | 331 ms | 0.5 ms |
| 1 | 449.9 ms | 449 ms | 0.9 ms |
| 2 | **1051.6 ms** | **1051 ms** | 0.6 ms |
| 3 | 455.6 ms | 455 ms | 0.6 ms |
| 4 | **1439.7 ms** | **1439 ms** | 0.7 ms |
| 5 | 909.1 ms | 908 ms | 1.1 ms |

**Agreement to within about 1 ms on every move.** The timer starts immediately after `readyok` and immediately
before the `go` line — exactly the placement seat 15 describes. The residual on a `time 0` search is
**0.74 / 0.81 / 0.68 ms**, i.e. the same as seat 15's 0.83 ms.

### So where did the 1300 ms come from?

**Not from the harness timer.** It came from the *outer shell loop* I used in some of my ad-hoc checks, which timed
the entire `python3 paced_session.py …` invocation — interpreter startup, spawn, preamble, search and teardown all
included. That is a different measurement from the harness's own timer, and I conflated the two when I wrote S-W4.

**S-W4's mechanism claim is therefore withdrawn.** The numbers it retracted were produced by an accurate timer.

### What the accurate numbers actually say about the plan

At `go wtime 6000 btime 6000 winc 500 binc 500` the engine's own plan (computed from `clock_plan.hpp` with the
CMake defaults) is **soft 647 ms, hard 3235 ms**. The observed spend was 331, 449, **1051**, 455, **1439**, 908 ms:

- **every move is inside the HARD limit** — so "the engine overran its hard limit" is simply false;
- **two of six exceed the SOFT limit** (1051 and 1439 against 647), which is *expected*: the soft limit decides when
  to stop starting new iterations, and the hard limit is the cap.

So my original S-C11d claim ("spends 2–3× its increment") was wrong because **spending more than the increment is
what the soft limit permits** — it is not evidence of a fault. The plan accounts for it.

### What survives, correctly stated

- **My harness's wall measurements were accurate** — the timer placement was right and matches the engine to ~1 ms.
- **The engine stays inside its own hard limit** on every row I have measured.
- **It exceeds the soft limit on individual moves**, which is by design, not a defect.
- **The forfeits in my self-play games are still real for my harness but are not evidence against the engine**,
  because my harness re-sends the whole growing move list each ply and charges the engine's think time to a clock
  it decremented by that same think time — the accounting is self-consistent, so if a game forfeits, that reflects
  the engine's actual spend against the clock **as the harness maintained it**. Whether the *engine's own* internal
  clock would have forfeited is a separate question I have not measured, and the honest answer is: **unmeasured.**

### The rule, in its final form

**Time from immediately before `go` on a warmed process, and verify with a `time 0` search that the residual is a
few milliseconds.** Not "never time from the caller" — both seat 15 and I do that and both are correct. The check
is what distinguishes an accurate timer from a slow apparatus, and it takes one command.

### The transferable line

**A claim in nodes, scores, plies or info lines survives a harness error; a claim in milliseconds must be verified
against the engine's own `time` field.** I did not do that verification before publishing the overspend claim, and
I did not do it before retracting it either — seat 15's check is what forced both corrections.
