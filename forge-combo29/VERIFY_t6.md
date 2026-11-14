# VERIFY t6

Branch `grok47/t6-fixed-node-score` at `9b0e6ae1176fa875a89e6cf15d4208a1656fa020`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `tests_t6/fixed_nodes.cpp`, `REPORT_t6.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 14 insertions, 4 deletions. `stopped_by_nodes_` is set only in the node-limit branch of `should_stop`, and a node-limit abort no longer publishes the partial root move.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The test searches in-process.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 162 nps 1931271
info string bench depth 13 nodes 862329 time 435 nps 1982365
nodes 4865609
```

The new behavior is behind a node limit. Bench and perft do not set one, and the pins match. There is no t9 branch to compare.

## Task test

Sanitizer objects. Branch, exit 0, no sanitizer report:

```
PASS fixed-node score and move agree checks 176
```

Lock objects, exit 1, no sanitizer crash. Sample failures, then the summary:

```
nodes 155 depth 2 score 49 move c2c4 finished-score 49 finished-move d2d4 FAIL
FAIL failures 27 checks 176
```

The test fails on the lock and passes on the branch.

## Report claims

Reproduced: a node budget between two finished iterations keeps the finished score and move on this commit and not on the lock; a budget of 1 node publishes depth 0 and score 0 (`nodes 1 depth 0 score 0 move a2a3` on the start position); bench and perft pins match. No Elo or speed claim was checked.
