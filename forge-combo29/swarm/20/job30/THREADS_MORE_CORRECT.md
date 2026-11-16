# seat 20 — job 30: multithreading makes this mate score MORE CORRECT, and the distance is STABLE

The observation (my S-F37) is now a planted, ten-repetition measurement. **The short version: at Threads ≥ 2 the
engine gives the true mate distance `mate -4` in 10/10 runs on every arm, while Threads 1 gives the wrong `mate -7`
in 10/10. The DISTANCE is stable; the NODE COUNT is not, and the MOVE varies.**

Threads stated in every line (this job is explicitly about threading, which the swarm rule permits). Fresh process
per run. `go depth 12` on `8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1`. `mate -4` = 8 plies = the true forced distance,
proved independently by exhaustive search in job16.

## Rule-1 planting (done first, as required)

| planted engine | ten runs | detector verdict |
|---|---|---|
| fake engine, score RANDOM per run | `mate -7, -7, -7, -12, -9, -12, -9, -7, -12, -4` — **4 distinct scores**, nodes 3,432,737–27,019,461 | **flagged variable** ✓ |
| fake engine, score CONSTANT | `mate -4` ten times, nodes 20,000 ten times | **passed as stable** ✓ |

The detector is therefore shown able to fire and able to stay quiet before any real arm is reported.

## The real arms — ten runs each

| build | Threads | scores (10 runs) | distinct scores | moves seen | nodes |
|---|---|---|---|---|---|
| base | no option | `mate -7` ×10 | **1** | c2b1 | **15,465** (identical ×10) |
| base | 1 | `mate -7` ×10 | **1** | c2b1 | **15,465** (identical ×10) |
| base | 2 | `mate -4` ×10 | **1** | c2c3 | 48,340–57,782 (**10 distinct**) |
| base | 4 | `mate -4` ×10 | **1** | c2b2, c2c3 | 72,413–97,541 (**10 distinct**) |
| base | 8 | `mate -4` ×10 | **1** | c2b2, c2c3 | 74,565–90,030 (**10 distinct**) |
| pc-r15 | no option | `mate -7` ×10 | **1** | c2b1 | 28,084 (identical ×10) |
| pc-r15 | 1 | `mate -7` ×10 | **1** | c2b1 | 28,084 (identical ×10) |
| pc-r15 | 2 | `mate -4` ×10 | **1** | c2c3 | 47,097–56,195 (**10 distinct**) |
| pc-r15 | 4 | `mate -4` ×10 | **1** | c2b2, c2c3 | 74,007–105,508 (**10 distinct**) |
| pc-r15 | 8 | `mate -4` ×10 | **1** | c2b1, c2c3 | 67,885–80,586 (**10 distinct**) |

## The four conclusions, kept separate

1. **The mate distance is STABLE at Threads ≥ 2** — 10/10 `mate -4` on five different arms (base 2/4/8, pc 2/4/8),
   and 10/10 `mate -7` at Threads 1 and at the default. This is **not** the score spread seat 04 and seat 28 found:
   their spread was across *different* scores; here one score is returned every time. So the S-F37 sentence holds
   and is not a nondeterminism artefact: **a multi-threaded search is reliably MORE CORRECT on this position.**
2. **The node count is NOT stable at Threads ≥ 2** — ten distinct values in every multithreaded arm, and the range
   is wide (base T4: 72,413–97,541). That reproduces seat 04's warning exactly and means no node-count claim may be
   made above Threads 1.
3. **The MOVE varies at Threads ≥ 2** (c2b2 vs c2c3 at T4; c2b1 vs c2c3 at pc T8) — so a bestmove comparison across
   thread counts is meaningless, even though the *score* is now right.
4. **The PC r15 build behaves identically to the base tree in this respect** — both give `mate -7` at Threads 1 and
   `mate -4` at Threads ≥ 2. So `MateAlphaGuard` (my S-F38) and multithreading are **independent routes to the same
   correct answer**: the guard gets there single-threaded, extra threads get there by searching a different tree.

## Why this matters, and its honest limits
The mechanism is the same breadth effect I documented in S-F18: the true mate is reachable only by a line that
single-threaded depth-12 alpha-beta does not visit. Multithreading changes which lines get visited, and on this
board the extra lines are the ones that find black's faster mate.

**Limits I will not paper over:**
- **One position.** This is a single forced-mate board; I have not shown that Threads ≥ 2 is generally more accurate,
  and a breadth change can as easily *miss* something. The claim is: on this board, reliably, yes.
- **No general quality claim.** "Multithreaded is more correct" must not be quoted as an engine-wide statement.
  The honest form is: "on this board the single-threaded depth-12 answer is wrong and the multithreaded one is
  right, in 10/10 runs each."
- **Not a recommendation to play multithreaded.** It also means the engine's *score* changes with the thread count,
  which is a reproducibility problem for every match result.
- Only `mate` scores were compared; no cp scores were used above Threads 1 anywhere in this job.

Raw: `job30/plant_threads_mate.json`, `job30/run.log`. Script: `job30/plant_threads_mate.py`.
