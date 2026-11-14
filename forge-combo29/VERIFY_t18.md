# VERIFY t18

Branch `grok47/t18-uci-fuzz` at `d1d10b3efa267de6e17f3bcb10b9564d714a4c05`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

## Rule check

`git diff --name-status 16833ecc...d1d10b3e`:

```
A	forge-combo29/REPORT_t18.md
A	forge-combo29/include/forge/uci.hpp
M	forge-combo29/src/uci.cpp
A	forge-combo29/tests_t18/uci_fuzz.cpp
```

All mode 100644. No executable, archive, script, workflow, or Python file is in the diff. Engine source: `uci.hpp` 11 insertions, `uci.cpp` 28 insertions (39 changed lines). Under the 300-line cap. `FORGE_UCI_TEST_LOOP` is default 0, so the release binary keeps `main` reading `std::cin`.

## Safety

The engine diff is an `#if` around the existing loop. No network use, registry or environment access, obfuscated code, or file write. The test does not start a process. It runs the loop on another thread and feeds that thread an in-memory stream (`tests_t18/uci_fuzz.cpp:256-263`):

```
void start() {
    thread_ = std::thread([this] {
        std::string error;
        try {
            FeedBuf buf(queue_);
            std::istream in(&buf);
            in.tie(&std::cout);
            const int code = forge::uci_loop(in);
```

Generated lines can set `Book File` to a `nosuch-` name. That uses the existing option. The new code does not write a file.

## Build

Clang 18.1.3 failed the stated cmake line with `cannot find -lstdc++` (see VERIFY_t12.md). g++ 13.3.0:

```
cmake -S /tmp/wt-t18/forge-combo29 -B /tmp/wt-t18/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t18/build_rel -j
cmake -S /tmp/wt-t18/forge-combo29 -B /tmp/wt-t18/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t18/build_san -j
```

Both ended `Built target forge` and `BUILD_EXIT:0`. Portable march flags were not added (`avx512f` is present). The cmake build does not define `FORGE_UCI_TEST_LOOP`, so the shipped binary is the default-off loop.

## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t18/build_rel/forge
```

```
info string bench depth 11 nodes 312866 time 159 nps 1967710
info string bench depth 13 nodes 862329 time 429 nps 2010090
nodes 4865609
```

Exit 0. Same three counts as the lock. No new UCI option, so tasks 6, 7, 8, and 10 are unchanged at their defaults. There is no `grok47/t9` branch.

## Task test

`src/uci.cpp` was compiled again with the sanitizer flags plus `-DFORGE_UCI_TEST_LOOP=1 -DFORGE_UCI_NO_MAIN`, and linked with `tests_t18/uci_fuzz.cpp` and the sanitizer objects except the cmake `uci.cpp.o`. `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1`.

```
/tmp/tests/t18_branch
```

Stderr:

```
seed=361192554478 generated_lines=200000
part_a hand_written=193
part_a cases=193 ok time_ms=196
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
part_b seed=361192554478 lines=200000 ok time_ms=236183
SANITIZERS clean
```

Exit 0. The process stderr has no AddressSanitizer or UndefinedBehaviorSanitizer diagnostic. `SANITIZERS clean` is the test's own last line. `go wtime 3000000000` is one of the 193 hand-written lines (`uci_fuzz.cpp:463`) and did not crash or trip the test's 5 second hang check.

Lock include tree:

```
fatal error: forge/uci.hpp: No such file or directory
```

Compile exit 1. The test does not compile on the lock and passes here.

## Report claims

Reproduced: the three pin counts, 193 hand-written cases, 200000 generated lines, seed `361192554478`, and a clean sanitizer run. The report's `time_ms=216664` was not the number this run printed (`236183`); that is the timer output, not a result being checked. Not checked: the numeric value stored for `wtime 3000000000` (the report says an out-of-range token becomes 0), ThreadSanitizer, `bench` deeper than 2 under the sanitizer, and `go perft` above depth 2 under the sanitizer. No Elo or speed claim was checked.
