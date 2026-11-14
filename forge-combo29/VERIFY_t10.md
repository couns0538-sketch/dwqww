# VERIFY t10

Branch `grok47/t10-multipv` at `935b359e528cd1cbf188af6be26d5a906c53d5b0`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

Files: `include/forge/search.hpp`, `src/search.cpp`, `src/uci.cpp`, `tests_t10/multipv_test.cpp`, `REPORT_t10.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 134 insertions, 12 deletions. Under the 300-line cap.

## Safety

`MultiPV` is a search limit and an info-line field. The test redirects `std::cout` into a string and says it does not start a process or write a file. No network, process start, registry, environment access, or obfuscation.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

Option left unset (default 1):

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 445 nps 1937817
nodes 4865609
```

There is no `grok47/t9*` branch. Tasks 6, 7, 8, and 10 all kept these three counts with their new behavior at its default.

## Task test

Sanitizer objects. Branch exit 0, no sanitizer report. The last lines were:

```
nodes560 best e2e4 score 18 nodes 560 lines 3
ok a node limit keeps the last complete MultiPV set
ok MultiPV stays inside searchmoves
ok a check search ranks the legal evasions
failures=0
```

Lock include tree, compile failed: `'struct forge::SearchLimits' has no member named 'multipv'`.

Sanitizer UCI, default option, `go depth 2` from the start position:

```
info depth 1 seldepth 1 score cp 1 nodes 26 nps 26000 hashfull 0 time 1 pv d2d4
info depth 2 seldepth 2 score cp 49 nodes 54 nps 54000 hashfull 0 time 1 pv d2d4 d7d6
bestmove d2d4
```

No `multipv` token. The lock printed the same moves, scores, and node counts on those two lines.

## Report claims

Reproduced: default pins, MultiPV 1 matching a default search inside the C++ test, the test failing to compile on the lock, and a depth-2 UCI line with no multipv token. Not re-run as a separate UCI session: the report's MultiPV 2..8 transcripts. The C++ test did exercise MultiPV 3, 8, a drawn root, a node limit, and searchmoves, and printed `failures=0`. No Elo or speed claim was checked.
