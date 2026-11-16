# CHECK of seat 05's S-F8 — `go infinite` at a terminal root never answers

**Verdict: CONFIRMS S-F8.** Plus one fact the finding does not state: sending `stop` makes it
answer `bestmove 0000` immediately, so the search is waiting on the *infinite* gate, not stuck
in computation.

Harness: `check_s05f8.py`, written from the finding's command alone. Raw output:
`check_s05f8_release.txt`. Engine: release build `e06310ec…16a83` (the one with the four honesty
numbers exact).

## Results

```
=== A. go infinite at a terminal root, NO stop (the finding's command) ===
  05 stale   ABSENT (no bestmove in 12 s)
  15 stale   ABSENT (no bestmove in 12 s)

=== B. the same boards, bounded go ===
  05 stale   depth 5      bestmove after 0.001 s: bestmove 0000
  05 stale   nodes 100    bestmove after 0.001 s: bestmove 0000
  05 stale   movetime 50  bestmove after 0.001 s: bestmove 0000
  15 stale   depth 5      bestmove after 0.001 s: bestmove 0000
  15 stale   nodes 100    bestmove after 0.001 s: bestmove 0000
  15 stale   movetime 50  bestmove after 0.001 s: bestmove 0000

=== C. control: go infinite on a LIVE board, stop after 1 s ===
  live-board  bestmove after 1.000 s: bestmove d2d4

=== D. new: go infinite at a terminal root, then STOP after 1 s ===
  05 stale   bestmove after 1.001 s: bestmove 0000
  15 stale   bestmove after 1.001 s: bestmove 0000
```

Both boards are stalemate roots verified by python-chess (`gen_terminal.py` in job3 produced
`15 stale` = `7k/5Q2/6K1/8/8/8/8/8 b`; `05 stale` is the finding's own `8/8/8/8/8/6K1/8/Q5k1 b`).

The control in C matters: the same harness and the same `go infinite` produce a `bestmove` after
`stop` on a live board, so the ABSENT lines in A are a real absence and not the harness failing
to read. A `bestmove` that never arrives is reported as ABSENT and never as a zero.

## Interpretation (what is beyond the finding)

`go infinite` on a terminal root produces no `bestmove` until something sends `stop` — and then
it answers `bestmove 0000` at once. Combined with my job-3 finding 15-F5 (the same root walks the
depth ladder to 64 with `nodes 0` under `go nodes`/`go movetime`), the picture is: a terminal root
runs the iteration ladder instead of returning, and `infinite` has no ladder end, so only an
external `stop` can end it. That is consistent with the `limits.infinite` wait in the worker
thread (`src/uci.cpp`), but I did not read that code path to confirm the mechanism.

## My own error, recorded

The first two runs of this check reported **every** case as ABSENT, including `go depth 5`, which
contradicted my own job-3 result. The cause was `select()` on a buffered `TextIOWrapper`: bytes
already sitting in Python's buffer are invisible to `select`, so the reader missed them and hit the
deadline. Replaced with a reader thread on a queue. The buggy runs are not cited anywhere and their
output was discarded. This is the same "absent reported as a result" failure the coordinator warned
about, caught here only because the bounded cases were included as a self-control.
