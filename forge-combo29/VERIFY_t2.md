# VERIFY t2

Branch `grok47/t2-badcap-bound` at `ad702bf619532194df10c6f643c9dada9e4b8c55`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. Better than t1.

## Rule check

Files: `src/search.cpp`, `src/uci.cpp`, `tests_t2/losing_captures.cpp`, `losing_captures.expected.txt`, `losing_captures.uci`, `REPORT_t2.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 17 insertions, 3 deletions.

## Safety

`search.cpp` widens `bad_captures_` to `MoveList::Capacity`, same as t1. `uci.cpp` adds `finite_search` and, on stdin EOF, joins a finite non-ponder worker instead of calling `stop_search()`. `quit`, `stop`, infinite, and ponder still abort. No network, process start, registry, environment access, or new file write. The test does not start a process.

## Build

Same Clang failure (`cannot find -lstdc++`), then g++ Release and ASan/UBSan configures. Both `Built target forge`.

## Pins

```
info string bench depth 11 nodes 312866 time 164 nps 1907719
info string bench depth 13 nodes 862329 time 436 nps 1977818
nodes 4865609
```

## Task test

Direct search, sanitizer objects.

Branch, exit 0, no sanitizer report:

```
bestmove b4a3
```

That matches `tests_t2/losing_captures.expected.txt`.

Lock objects, exit 134:

```
SUMMARY: AddressSanitizer: SEGV /tmp/verify/src/forge-combo29/src/search.cpp:469 in forge::MovePicker::next(bool)
```

UCI file piped with stdin closed and no `quit`, sanitizer binaries:

- Branch exit 0: `bestmove b4a3`. No sanitizer report.
- Lock exit 0: `bestmove h2f1`. No sanitizer report.

The lock UCI path stops the search when the pipe ends, so it never reaches the overflow. The direct call does, and dies. The branch finishes the depth-1 search.

## Report claims

Reproduced: the lock direct search dies; this commit returns `b4a3`; a piped finite `go` on the lock does not reach that move; bench and perft pins match. Not reproduced as a separate claim: any speed or Elo sentence. The report's stored ASan stack was not byte-compared.

## Pair

t2 is better than t1. Both remove the 64-slot write. Only t2 makes `forge < losing_captures.uci` actually run the search that hits the bug.
