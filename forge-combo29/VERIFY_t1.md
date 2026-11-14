# VERIFY t1

Branch `grok47/t1-capture-overflow` at `48644054dd67fd5abf547cd00de1c9943411baf9`.
Base `lock/combo29-20261110` at `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. Compared with t2, t2 is the better fix (see the end).

## Rule check

Files against the lock: `forge-combo29/src/search.cpp`, `forge-combo29/tests_t1/bad_capture_overflow.cpp`, `forge-combo29/REPORT_t1.md`. All mode 100644. No executable, archive, script, workflow, or Python file. Engine source: 4 insertions, 2 deletions in `search.cpp`.

## Safety

The engine diff only replaces both `std::array<Move, 64> bad_captures_` declarations with `std::array<Move, MoveList::Capacity>`. No network, process start, registry, environment access, obfuscation, or file write. The test calls `Searcher::search` in-process.

## Build

Stated configure, default compiler:

```
cmake -S forge-combo29 -B build_rel -DCMAKE_BUILD_TYPE=Release
```

Clang 18.1.3 failed the compiler test: `/usr/bin/ld: cannot find -lstdc++`. Retried with `-DCMAKE_CXX_COMPILER=g++`. Release and the sanitizer configure (`-DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"`) both ended `Built target forge`.

## Pins

Release, `Threads 1`, `Hash 16`, `OwnBook false`:

```
info string bench depth 11 nodes 312866 time 169 nps 1851278
info string bench depth 13 nodes 862329 time 440 nps 1959838
nodes 4865609
```

Same three node counts on the lock (312866, 862329, 4865609).

## Task test

Linked `tests_t1/bad_capture_overflow.cpp` with the sanitizer objects (uci.cpp.o omitted) and the lock's compile definitions.

Branch, exit 0, no ASan/UBSan report:

```
in_check 0
losing_captures 68
bestmove d3b1
nodes 176
```

Lock objects, exit 134:

```
in_check 0
losing_captures 68
SUMMARY: AddressSanitizer: SEGV /tmp/verify/src/forge-combo29/src/search.cpp:469 in forge::MovePicker::next(bool)
```

The test fails on the lock and passes on the branch. It checks that the move is legal, not a specific move.

## Report claims

Reproduced: the position has 68 losing captures; the lock search dies in `MovePicker::next`; this commit searches it; bench 11/13 and perft 5 stay on the lock pins. Not claimed as Elo or speed. The report's own nps figures were not rechecked as a speed result.

## Pair

t1 only widens the array. t2 does that and keeps a finite `go` alive when stdin closes. On the lock, piping `tests_t2/losing_captures.uci` and closing stdin returns `bestmove h2f1` with no sanitizer report, because EOF aborts the search before the overflow. t2 returns `bestmove b4a3`. t2 is the better of the two.
