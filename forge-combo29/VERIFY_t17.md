# VERIFY t17

Branch `grok47/t17-rules-suite` at `3438c19e92b3f3919b1cd089b2e7e3162bbeee45`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `include/forge/board.hpp` (a `friend struct BoardStateProbe;`), `tests_t17/rules_suite.cpp`, `REPORT_t17.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 3 insertions, 0 deletions. The report's URLs are in the report, not in code that runs.

## Safety

The header change is a friend declaration so the test can compare private board fields. The test prints results and does not write files. No network, process start, registry, environment access, or obfuscation.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 174 nps 1798080
info string bench depth 13 nodes 862329 time 509 nps 1694163
nodes 4865609
```

## Task test

`rules_suite.cpp` linked to this commit's sanitizer objects, exit 0, no sanitizer report. The perft lines and the summary:

```
PASS PERFT start depth 5 engine 4865609 expected 4865609
PASS PERFT kiwipete depth 4 engine 4085603 expected 4085603
PASS PERFT pos3 depth 5 engine 674624 expected 674624
PASS PERFT pos4 depth 4 engine 422333 expected 422333
PASS PERFT pos5 depth 4 engine 2103487 expected 2103487
PASS PERFT pos6 depth 4 engine 3894594 expected 3894594
RESULT PASS fails=0
```

The same test against the lock header failed to compile: `'std::array<forge::Piece, 64> forge::Board::squares_' is private within this context`. It does not fail at runtime on the lock. The report says no rule fault was found, so a lock failure was not what the task claimed. The suite passes on this commit, whose engine diff is only the friend.

## Report claims

Reproduced: the six perft counts, `RESULT PASS fails=0`, and the pins. The external perft pages cited in the report were not fetched again. No Elo or speed claim was checked.
