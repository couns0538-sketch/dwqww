# swarm/64 — exact, machine-checkable MultiPV/Hash advice

Seat 64. Branch `for-fable-and-opus/swarm-64`. Base commit `6b98f2170a3210e71beed04bbd2553972c253ed7`.

## What was asked

Turn "`MultiPV 1` at any Hash, or `Hash 16` MB with multiple lines" into an
inequality a machine can check, from a fine grid at a fixed node budget.

## Environment, and why it matters to reproduce this

- The engine's own `CMakeLists.txt` wants `-march=x86-64-v4` (AVX-512F + BMI2).
  This host has both, so the lock ISA path is used, not the portable one.
- `/usr/bin/c++` on this image is **clang 18 whose default C++ include path points
  at `/usr/lib/gcc/x86_64-linux-gnu/14/`, which does not exist**. A plain
  `cmake -S . -B build` therefore fails with `'array' file not found`. Build with
  `-DCMAKE_CXX_COMPILER=/usr/bin/g++` (GCC 13.3, whose headers are present) and
  `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`.
- Pins confirmed before any measurement: `go perft 5` = 4865609 on startpos.

## Measurement rules actually enforced

| rule | how |
|---|---|
| Threads 1 | `setoption name Threads value 1` every session |
| fixed node budget, never a clock | `go nodes 200000` only |
| fresh process per cell | one `subprocess` per engine run, `quit` at the end |
| validate every FEN | `positions.py`, python-chess, plus per-PV replay |
| read `invalid FEN` replies | scanned in the position reply **and** the go output |
| print denominators as literals | every summary prints `n/N` |
| prove every script can fail | `grid.py --selftest`, `prove_driver.py` |
| wait for `bestmove` with a timeout | `Engine.go_nodes`, raises on timeout or EOF |

## Two corrections to the brief, both measured here

**(a) The `invalid FEN` diagnostic is emitted exactly once, not twice.**

The task brief said to scan both streams because the diagnostic appears in
whichever one you read. Measured (`grid.py --selftest`):

```
selftest A (isready after position): position=1 go=0
selftest B (no isready): go=1
```

With `isready` after `position` it is in the position reply and **not** in the go
output; without `isready` it is in the go output only. Scanning both is still the
correct defence — each single-stream scan misses one case — but the reason is
"the diagnostic moved", not "it is duplicated". Asserting it appears twice would
be a checker that always fails.

**(b) `go nodes 200000` does not search 200000 nodes.**

It stops when a *finished iteration* exceeds the budget, so a cell reports
174930 or 180348 or 199619 nodes. The budget is a ceiling on a discretised
iterative-deepening ladder, and the ladder step is large. Two consequences that
the whole grid depends on:

- **ms alone is not comparable across cells.** A cell that reached depth 14 did
  more work than one that reached depth 11. Every cell therefore records
  `nodes` and `depth` alongside `ms`, and the analysis reports both
  ms-versus-MPV1 and ns-per-node.
- **The budget is shared.** `extra_nodes_ += alt.nodes` and `should_stop` tests
  `total_nodes() + extra_nodes_ + pending_nodes`, so the alternate lines are
  charged against the same 200000. MultiPV spends the same budget on *fewer,
  shallower* lines. That is why node counts **fall** as MultiPV rises.

## Patch A: what it changes, and a caution

`patches/patch-a-no-line-clear.patch.txt` removes only
`alt_shared->tt.clear()` before each alternate line, keeping `alt_worker->clear()`
(the history-counter reset, which is not a table wipe).

**It is not output-preserving.** Measured over 6 positions x {(64,3),(256,6),(16,2),(64,1)}:

- MultiPV 1 rows: **6/6 identical** nodes, depth and move. That is the control —
  the patch does not touch the primary path, and it proves the harness compares
  like with like.
- MultiPV > 1 rows: **15/18 identical best moves (83.3%)**, and where it differs
  it reaches a *deeper* depth for the same nodes (e.g. Hash 256 MPV 6: depth 10 ->
  11, 44875 -> 88914 nodes, 1421 -> 299 ms).

So the patch buys depth by reusing the alternate table across lines at one
depth. Any speed claim about it must say "at equal nodes, deeper", not "same
work, faster". This is the honest framing and it is the one used in FINDINGS.

## Files

| path | role |
|---|---|
| `positions.py` | the 6 FENs + python-chess validation, exits non-zero on any bad FEN |
| `ucidrv.py` | UCI process driver: timeouts, EOF detection, both-stream refusal scan |
| `prove_driver.py` | proves the driver's four claims, including that they can fail |
| `grid.py` | the grid runner, `--selftest` first, JSON out |
| `analysis.py` | medians, the K fit, misclassification counts |
| `patches/patch-a-no-line-clear.patch.txt` | the one-line-clear removal, as text |
