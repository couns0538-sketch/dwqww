# VERIFY t2

Branch `grok47/t2-badcap-bound` at `19195ffaf323303e5a025ff23e6dd323b784882c`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `ad702bf6` changes only `REPORT_t2.md`. The engine and the test were built and run again.

## Rule check

Files: `src/search.cpp`, `src/uci.cpp`, `tests_t2/losing_captures.cpp`, `losing_captures.expected.txt`, `losing_captures.uci`, `REPORT_t2.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 17 insertions, 3 deletions (`search.cpp` 4/2, `uci.cpp` 13/1).

## Safety

No network, process start, registry, environment access, or obfuscation. No file write. The UCI change joins a finite search when stdin ends instead of cancelling it:

```
src/uci.cpp:434
    if (finite_search && worker.joinable()) {
        worker.join();
```

`finite_search` is set only when the limits are not infinite and not ponder (`uci.cpp:358`).

## Build

The stated cmake line, without a compiler override, was run once on the lock tree:

```
cmake -S /tmp/wt-lock/forge-combo29 -B /tmp/wt-lock/build_clang -DCMAKE_BUILD_TYPE=Release
```

`/usr/bin/c++` is Clang 18.1.3. Configure exited 1 before any engine file was compiled:

```
/usr/bin/ld: cannot find -lstdc++: No such file or directory
```

`/proc/cpuinfo` has `avx512f`, so `-DFORGE_PORTABLE` and `-DFORGE_MARCH=x86-64-v3` were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t2-badcap-bound/forge-combo29 -B /tmp/wt-t2-badcap-bound/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t2-badcap-bound/build_rel -j4
cmake -S /tmp/wt-t2-badcap-bound/forge-combo29 -B /tmp/wt-t2-badcap-bound/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t2-badcap-bound/build_san -j4
```

Both configures exited 0 and both builds ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t2-badcap-bound/build_rel/forge
```

Exit 0. Stderr empty.

```
info string bench depth 11 nodes 312866 time 165 nps 1896157
info string bench depth 13 nodes 862329 time 438 nps 1968787
nodes 4865609
```


## Task test

Direct search, sanitizer objects except `uci.cpp.o`.

Branch, exit 0, stderr empty:

```
bestmove b4a3
```

That matches `tests_t2/losing_captures.expected.txt`.

Lock objects, exit 134:

```
SUMMARY: AddressSanitizer: SEGV /tmp/wt-lock/forge-combo29/src/search.cpp:469 in forge::MovePicker::next(bool)
```

UCI file with stdin closed and no `quit`, sanitizer binaries:

- Branch exit 0: `bestmove b4a3`. No sanitizer report.
- Lock exit 0: `bestmove h2f1`. No sanitizer report.

Release binaries, same redirect:

- Branch exit 0: `info depth 1 seldepth 9 score mate 1 nodes 186 ... pv b4a3` and `bestmove b4a3`.
- Lock exit 0: `bestmove h2f1`. Stderr empty. This run did not get the report's release-lock exit 139. Closing stdin still stops the lock search before the picker runs.

## Report claims

Reproduced: the direct lock search dies in `MovePicker::next`; this branch's depth-1 search prints mate 1, 186 nodes, and `bestmove b4a3`; the piped lock file returns `h2f1`; the three pins. Not reproduced: a release-lock segmentation fault from `forge < tests_t2/losing_captures.uci` (exit was 0). Not re-run: `go depth 20` then `quit`, and `go infinite` then EOF. No Elo or speed claim was checked.

## Pair

t2 is better than t1. Both widen the array. Only t2 finishes a finite `go` after stdin EOF.
