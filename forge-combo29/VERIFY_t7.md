# VERIFY t7

Branch `grok47/t7-nnue-file` at `417f021f1ab98dbbbd2ba12b4dd061ab3e70199f`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `b56c6328` changes only `REPORT_t7.md`. The engine and the test were built and run again.

## Rule check

Files under `include/forge/nnue.hpp`, `src/nnue.cpp`, `src/uci.cpp`, `tests_t7/`, and `REPORT_t7.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 140 insertions, 11 deletions. `NnueFile` is a string option and its default is `<empty>`.

## Safety

No network, process start, registry, or environment access. The converter writes the path it is given:

```
tests_t7/forgenet_convert.cpp:40
    std::ofstream out(argv[1], std::ios::binary);
```

This run wrote `/tmp/t7.net` and the rejection files the test names under `/tmp` (`/tmp/forge-t7-b2.bin` and the bad-magic, bad-version, bad-hidden, and short files). A failed load returns before the active net is replaced. A successful load calls `searcher.clear()` (`src/uci.cpp:274` and `:279`).

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t7-nnue-file/forge-combo29 -B /tmp/wt-t7-nnue-file/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t7-nnue-file/build_rel -j4
cmake -S /tmp/wt-t7-nnue-file/forge-combo29 -B /tmp/wt-t7-nnue-file/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t7-nnue-file/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t7-nnue-file/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 172 nps 1818988
info string bench depth 13 nodes 862329 time 448 nps 1924841
nodes 4865609
```


`NnueFile` was left at `<empty>`. The pins match.

## Task test

`forgenet_convert /tmp/t7.net` exited 0. `nnue_file_test` linked to this commit's sanitizer objects, exit 0, stderr empty:

```
compiled 20
loaded 20
ok converted net matches compiled eval
changed 37
ok changed b2 changes eval
ok bad magic kept current net (wrong magic)
ok bad version kept current net (wrong version)
ok bad hidden kept current net (wrong size)
ok short file kept current net (wrong size)
ok missing file kept current net (cannot open)
restored 20
ok use_compiled restores eval
all checks passed
```

The same test against the lock headers failed to compile: `'load_file' is not a member of 'forge::nnue'`.

## Report claims

Reproduced: default pins, converted-net eval equal to the compiled net (20), a changed b2 (37), rejected magic/version/size/short/missing files, and restore. Not re-run: the report's changed-net bench of a different file. No Elo or speed claim was checked.

## Pair

t7 is the better engine change. A successful load calls `Searcher::clear()` (`uci.cpp:279`). t8 calls only `clear_hash()` (`uci.cpp:275`).
