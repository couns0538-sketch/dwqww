# VERIFY t1

Branch `grok47/t1-capture-overflow` at `59480d0461c55629321b1741dce74b3bec76c06a`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `48644054` changes only `REPORT_t1.md`. The engine and the test were built and run again.

## Rule check

Files against the lock: `src/search.cpp`, `tests_t1/bad_capture_overflow.cpp`, `REPORT_t1.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 4 insertions, 2 deletions.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. The only engine edit widens the array:

```
src/search.cpp:578
    std::array<Move, MoveList::Capacity> bad_captures_;
```

The lock still writes with no bound (`src/search.cpp:469`: `bad_captures_[bad_count_++] = move;`). The test searches in-process.

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
cmake -S /tmp/wt-t1-capture-overflow/forge-combo29 -B /tmp/wt-t1-capture-overflow/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t1-capture-overflow/build_rel -j4
cmake -S /tmp/wt-t1-capture-overflow/forge-combo29 -B /tmp/wt-t1-capture-overflow/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t1-capture-overflow/build_san -j4
```

Both configures exited 0 and both builds ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t1-capture-overflow/build_rel/forge
```

Exit 0. Stderr empty.

```
info string bench depth 11 nodes 312866 time 167 nps 1873449
info string bench depth 13 nodes 862329 time 454 nps 1899403
nodes 4865609
```


## Task test

`tests_t1/bad_capture_overflow.cpp` linked to the sanitizer objects except `uci.cpp.o`, with the lock compile definitions. `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1`.

Branch, exit 0, stderr empty:

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
SUMMARY: AddressSanitizer: SEGV /tmp/wt-lock/forge-combo29/src/search.cpp:469 in forge::MovePicker::next(bool)
```

The test fails on the lock and passes on the branch.

## Report claims

Reproduced: 68 losing captures, the lock ASan SEGV in `MovePicker::next`, this commit's `bestmove d3b1` with exit 0 and no sanitizer report, and the three pins. Not checked as a speed result: the report's nps figures. No Elo claim was checked.

## Pair

t2 is the better of the two. t1 only widens the array. On the lock, piping `tests_t2/losing_captures.uci` and closing stdin returns `bestmove h2f1` and never reaches the overflow. t2 returns `bestmove b4a3`.
