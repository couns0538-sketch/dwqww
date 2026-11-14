# VERIFY t4

Branch `grok47/t4-clock-parse` at `a72b477095b70c0cc99d57caf98901a0c5891fce`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `0ccc839b` changes only `REPORT_t4.md`. The engine and the tests were built and run again. `t3` is still `5e7fda21` and was rebuilt only for the pair commands below.

## Rule check

Files: `include/forge/go_numbers.hpp`, `include/forge/search.hpp`, `src/uci.cpp`, `tests_t4/check_clock.cpp`, `clock_commands.txt`, `clock_expected.txt`, `go_numbers_test.cpp`, `REPORT_t4.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 111 insertions, 24 deletions. Under the 300-line cap.

## Safety

No network, process start, registry, environment access, obfuscation, or file write. `go_numbers_test` and `check_clock` read integers and engine stdout. They do not start a process.

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
cmake -S /tmp/wt-t4-clock-parse/forge-combo29 -B /tmp/wt-t4-clock-parse/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t4-clock-parse/build_rel -j4
cmake -S /tmp/wt-t4-clock-parse/forge-combo29 -B /tmp/wt-t4-clock-parse/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t4-clock-parse/build_san -j4
```

Both configures exited 0 and both builds ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t4-clock-parse/build_rel/forge
```

Exit 0. Stderr empty.

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 440 nps 1959838
nodes 4865609
```


## Task test

`go_numbers_test.cpp` against this include tree printed `pass`, exit 0. Against the lock include tree:

```
fatal error: forge/go_numbers.hpp: No such file or directory
```

Compile exit 1.

`check_clock` read a live transcript. Commands in `clock_commands.txt` were sent one at a time, and the next command waited for `bestmove`. Checker stdout:

```
ok 1 wall_ms 1.81796 depth 8 best d2d4
ok 2 wall_ms 27.8392 depth 12 best e2e4
ok 3 wall_ms 27.4161 depth 12 best e2e4
ok 4 wall_ms 27.7865 depth 12 best e2e4
ok 5 wall_ms 27.8701 depth 12 best e2e4
ok 6 wall_ms 0.003806 depth 3 best e2e4
ok 7 wall_ms 80.4781 depth 14 best e2e4
ok 8 wall_ms 79.8218 depth 14 best e2e4
ok 9 wall_ms 79.7947 depth 14 best e2e4
ok 10 wall_ms 1.05576 depth 6 best d2d4
ok 11 wall_ms 0.542675 depth 6 best d2d4
ok 12 wall_ms 0.808114 depth 6 best d2d4
ok 13 wall_ms 0.510466 depth 6 best d2d4
ok 14 wall_ms 0.807053 depth 6 best d2d4
ok 15 wall_ms 7.57773 depth 10 best e7e6
ok 16 wall_ms 7.37808 depth 10 best e7e6
ok 17 wall_ms 29.0717 depth 12 best e2e4
ok 18 wall_ms 119.765 depth 15 best e2e4
ok 19 wall_ms 27.5872 depth 12 best e2e4
ok 20 wall_ms 27.6657 depth 12 best e2e4
ok 21 wall_ms 7.36549 depth 10 best e7e6
ok 22 wall_ms 0.261441 depth 5 best c2c4
ok 23 wall_ms 120.144 depth 15 best e2e4
pass
```

Engine exit 0, checker exit 0, no go timeout, stderr empty. The depth-8 line is `info depth 8 seldepth 13 score cp 26 nodes 4099 ... pv d2d4 ...`. The depth-12 line is `info depth 12 seldepth 23 score cp 30 nodes 56720 ... pv e2e4 ...`.

## Report claims

Reproduced: `go depth +8` reaches depth 8; `go depth 12 wtime 3000000000` reaches depth 12 with 56720 nodes; the lock's same wtime command stopped at depth 6 (`nodes 1703`, `bestmove d2d4`); all 23 expected searches passed; the three pins. The wall times above are this run's checker output, not a speed comparison. No Elo claim was checked.

## Pair

t4 is better than t3. On this machine, t3's `go depth +8` printed only `info depth 1 ... nodes 26` and `bestmove d2d4`. t3's `go depth 12 wtime 3000000000` did reach depth 12. t4 does both, and the leading plus is the part t3 still misses.
