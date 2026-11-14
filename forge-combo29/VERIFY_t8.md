# VERIFY t8

Branch `grok47/t8-nnue-file` at `7d3b7dfc1a3ac2d345a033743d7e1edc2542d465`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `62997d98` changes only `REPORT_t8.md`. The engine and the test were built and run again.

## Rule check

Files under `include/forge/nnue.hpp`, `src/nnue.cpp`, `src/uci.cpp`, `tests_t8/`, and `REPORT_t8.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 137 insertions, 13 deletions. `NnueFile` defaults to `<empty>`.

## Safety

No network, process start, registry, or environment access. `nnue_convert` writes its argv path. The test also writes sibling files next to that net (`net_path + ".huge"` and the other rejection names). This run used `/tmp/t8.net`. A failed `load_file` leaves the current net in place. A successful load calls `searcher.clear_hash()` only (`src/uci.cpp:275`).

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t8-nnue-file/forge-combo29 -B /tmp/wt-t8-nnue-file/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t8-nnue-file/build_rel -j4
cmake -S /tmp/wt-t8-nnue-file/forge-combo29 -B /tmp/wt-t8-nnue-file/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t8-nnue-file/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t8-nnue-file/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 161 nps 1943267
info string bench depth 13 nodes 862329 time 426 nps 2024246
nodes 4865609
```


`NnueFile` was left at `<empty>`. The pins match.

## Task test

`nnue_convert /tmp/t8.net` exited 0. `nnue_file_test` needs `-I` on `src` because it includes `nnue_weights.inc`. Linked to this commit's sanitizer objects, exit 0, stderr empty. It printed `PASS`. The expects compare the loader's error string with `nnue: bad magic`, `nnue: unsupported version`, `nnue: wrong size`, and `nnue: cannot open file`, and they reject a file over 2MiB. Those expects passed.

Lock headers, with `-I` on the lock `src` so the weights header is found: `'load_file' is not a member of 'forge::nnue'`. Compile exit 1.

## Report claims

Reproduced: converted net matches the built-in eval on startpos and Kiwipete, the rejection strings above, the 2MiB rejection, restore through an empty path, and the three pins. Not re-run: a bench after loading a shifted net. No Elo or speed claim was checked.

## Pair

t7 is better. This branch clears only the hash after a successful load, so correction histories stay. The rejection test here is stricter than t7.
