# VERIFY t5

Branch `grok47/t5-krk-mate` at `143edfb6e85ed5c8bc83c58aa786ac7dbad61f32`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `tests_t5/krk_mate_test.cpp`, `REPORT_t5.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 51 insertions, 22 deletions.

## Safety

Helpers no longer store into the transposition table or refresh generation. Every search clears that worker's histories. A node-limited search does not launch helpers. No network, process start, registry, environment access, obfuscation, or file write. The test searches in-process.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 162 nps 1931271
info string bench depth 13 nodes 862329 time 436 nps 1977818
nodes 4865609
```

## Task test

`tests_t5/krk_mate_test.cpp` linked to sanitizer objects.

Lock, exit 1, no sanitizer diagnostic besides the test's own FAIL lines:

```
history FAIL
history FAIL
threads FAIL
threads FAIL
threads FAIL
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 10 cp 22 d2d4 total 30000
node budget FAIL
FAILED 6
```

One of the three history positions printed `history ok` before the failures. The third threads position also printed `threads ok`.

This commit, sanitizer link, exit 0, no ASan/UBSan report:

```
history ok
history ok
history ok
threads ok
threads ok
threads ok
threads ok
nodes-30k threads 1 depth 11 cp 24 d2d4 total 30000
nodes-30k threads 2 depth 11 cp 24 d2d4 total 30000
node budget ok
```

The same source linked to this commit's release objects (no sanitizer) also printed `node budget ok` and `ok`, exit 0. Threads 2 used the same depth, score, move, and 30000 nodes as threads 1.

## Report claims

Reproduced: the lock fails history, helper mate agreement, and the node budget; this commit passes those checks; bench and perft pins match. Not reproduced: the report's own release run, which printed `nodes-30k threads 2 depth 10 ... total 30861` and `FAILED 1`. This run's release link did not fail that check. No Elo or speed claim was checked.
