# VERIFY t18

Branch `grok47/t18-uci-fuzz` at `e73c7e6febaaf1f5794ceb3f229766ae80b20e00`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `d1d10b3e` changes only `REPORT_t18.md`. The engine and the test were built and run again.

## Rule check

Files: `REPORT_t18.md`, `include/forge/uci.hpp`, `src/uci.cpp`, `tests_t18/uci_fuzz.cpp`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 39 insertions, 0 deletions. The cmake build does not define `FORGE_UCI_TEST_LOOP`, so the shipped binary keeps the lock's `main` reading stdin.

## Safety

The engine diff is an `#if` around the existing loop (`src/uci.cpp`, `FORGE_UCI_TEST_LOOP` default 0). No network, registry, environment access, obfuscation, or file write. The test does not start a process. It runs the loop on another thread and feeds an in-memory stream. `std::remove` in the test is the algorithm that strips a newline, not a filesystem remove.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t18-uci-fuzz/forge-combo29 -B /tmp/wt-t18-uci-fuzz/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t18-uci-fuzz/build_rel -j4
cmake -S /tmp/wt-t18-uci-fuzz/forge-combo29 -B /tmp/wt-t18-uci-fuzz/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t18-uci-fuzz/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t18-uci-fuzz/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 449 nps 1920554
nodes 4865609
```


No new UCI option. The pins match.

## Task test

`src/uci.cpp` was compiled again with the sanitizer flags plus `-DFORGE_UCI_TEST_LOOP=1 -DFORGE_UCI_NO_MAIN`, and linked with `tests_t18/uci_fuzz.cpp` and the sanitizer objects except the cmake `uci.cpp.o`.

Stderr:

```
seed=361192554478 generated_lines=200000
part_a hand_written=193
part_a cases=193 ok time_ms=176
part_b 10000
part_b 20000
part_b 30000
part_b 40000
part_b 50000
part_b 60000
part_b 70000
part_b 80000
part_b 90000
part_b 100000
part_b 110000
part_b 120000
part_b 130000
part_b 140000
part_b 150000
part_b 160000
part_b 170000
part_b 180000
part_b 190000
part_b seed=361192554478 lines=200000 ok time_ms=231080
SANITIZERS clean
```

Exit 0. The `time_ms` figures are the test's own log, not a speed comparison. Stderr has no AddressSanitizer or UndefinedBehaviorSanitizer diagnostic. `SANITIZERS clean` is the test's last line.

Lock include tree:

```
fatal error: forge/uci.hpp: No such file or directory
```

Compile exit 1.

## Report claims

Reproduced: 193 hand-written cases and 200000 generated lines, exit 0, no sanitizer diagnostic, and the three pins. The test's `time_ms` values were not compared with anything. No Elo claim was checked.
