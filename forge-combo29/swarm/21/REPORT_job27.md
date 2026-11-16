# REPORT job27 — CHECK of seat 15's 15-F5 (terminal root walks the depth ladder)

**What was asked.** (Cycle step 2a.) Reproduce an unchecked finding from another seat with my own
harness. 15-F5's *new* part is the ladder claim: a terminal root "walks the whole depth ladder to 64
with `go nodes`/`go movetime` instead of answering at once". Its other part — `mate 0` / `cp 0` /
`0000` — I had already established is CORRECT (job20), and I withdrew my own claim that `mate 0`
was a fault.

**The answer.** **CONFIRMS 15-F5, on both builds.** A checkmated or stalemated root emits **64**
`info depth` lines (1 through 64) with 0 nodes on each under `go nodes 100` and `go movetime 50`,
and exactly N lines under `go depth N`. A normal root emits 2 / 9 / 4 lines for the same three go
forms, so the ladder walk is specific to the terminal path. The whole walk costs about **3 ms**, so
it is a real quirk but not a hang and not a practical problem.

**How sure.** High. Six cases per build (3 roots × 3 go forms), fresh process each, Threads 1, every
answer has one bestmove, and the walk is timed with a monotonic clock.

## Table (pasted from `job27/out/summary.md`)

| build | root | go | depth lines | max depth | nodes on last | bestmove |
|---|---|---|---|---|---|---|
| pc | checkmated | `go depth 4` | 4 | 4 | 0 | `0000` |
| pc | checkmated | `go nodes 100` | **64** | **64** | 0 | `0000` |
| pc | checkmated | `go movetime 50` | **64** | **64** | 0 | `0000` |
| pc | stalemated | `go depth 4` | 4 | 4 | 0 | `0000` |
| pc | stalemated | `go nodes 100` | **64** | **64** | 0 | `0000` |
| pc | stalemated | `go movetime 50` | **64** | **64** | 0 | `0000` |
| pc | normal | `go depth 4` | 4 | 4 | 404 | `e2e4` |
| pc | normal | `go nodes 100` | 2 | 2 | 54 | `d2d4` |
| pc | normal | `go movetime 50` | 9 | 9 | 9653 | `d2d4` |
| base | (the same nine rows) | | identical | identical | identical | identical |

Timing of the walk (monotonic, fresh process each):

| build | go | depth lines | ms |
|---|---|---|---|
| base | `go nodes 100` | 64 | 2.9 |
| base | `go movetime 50` | 64 | 3.5 |
| base | `go depth 64` | 64 | 2.8 |
| pc | `go nodes 100` | 64 | 2.6 |
| pc | `go movetime 50` | 64 | 3.0 |
| pc | `go depth 64` | 64 | 2.8 |

## Prediction outcome

P1–P6 all held, including P5: the PC build behaves identically, so the patch does **not** change the
terminal-root emit loop.

## Findings

`21-C10 | CONFIRMS 15-F5` — on both builds, terminal roots walk the full depth ladder to 64 under
`go nodes`/`go movetime`, with 0 nodes per line, in about 3 ms. Recorded together with my own
withdrawal of the `mate 0` part of that family, so nobody reads 15-F5 as also claiming the score is
wrong: the score is right, the ladder walk is the real (small) quirk.

## Suspicions, not proven

- The walk costs 3 ms here because nothing is searched. On a build where `should_stop()` were
  expensive it could matter, but I have no such build and did not test one.
- Whether a GUI that counts depth lines would misreport "depth 64" for a terminal position. That is
  a GUI question; the engine printing 64 lines is what I measured.

## What I did NOT do

- Did not test `go depth 200` (beyond the 64 clamp) or `go infinite` + `stop` on a terminal root.
- Did not read the emit loop to say why `should_stop()` does not break it — I measured the behaviour,
  which is what the check needs.

## What I am NOT sure about

- Whether 15-F5's author intended "walks the ladder" to mean something worse than 3 ms of output. If
  so, my CONFIRMS is of the weaker reading; the measurement supports only what the table shows.

## Times

see `job27/stamps.txt`.
