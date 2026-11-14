# VERIFY t20

Branch `grok47/t20-repeatable-search` at `9f48a760552c385e98a18f29b6733c36c067cbdf`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `tests_t20/repeat_mate_test.cpp` and `REPORT_t20.md` only. Both mode 100644. No engine diff (`git diff` of `src` and `include` is empty). No executable, archive, script, workflow, or Python.

## Safety

The test links the engine and searches in-process. It does not write files, start a process, use the network, or read the environment. There is no engine diff to quote.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`. The binaries match the lock's source, so the pins matching is expected.

## Pins

```
info string bench depth 11 nodes 312866 time 185 nps 1691167
info string bench depth 13 nodes 862329 time 528 nps 1633198
nodes 4865609
```

## Task test

`repeat_mate_test.cpp` linked to this commit's sanitizer objects and, separately, to the lock's sanitizer objects. Both exited 0 with no sanitizer report, and both ended:

```
PASS in-game state carries: nodes 13102 then 1774, after ucinewgame 13102
PASS hash resize: generation 2 -> 0, probe miss, hashfull 0, history kept (76 entries); Clear Hash generation 0 probe miss, history kept (95); depth 10 after resize matches ucinewgame, nodes 13102
PASS go mate
PASS stalemate KPk bestmove 0000 score cp 0 depth 64
PASS stalemate KQk bestmove 0000 score cp 0 depth 64
PASS checkmate KQk bestmove 0000 score mate 0 depth 64
t20 result: PASS
```

The test does not fail on the lock. The report says no engine change was required because `ucinewgame` already calls `Searcher::clear()`. That is what this run shows.

## Report claims

Reproduced: the test passes with no source change; a second depth-10 start-position search in the same game drops from 13102 nodes to 1774 and returns to 13102 after the clear; `go mate` and the terminal positions in the test pass. No Elo or speed claim was checked.
