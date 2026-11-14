# VERIFY t8

Branch `grok47/t8-nnue-file` at `62997d98344c5cbacb289512b77d88025abcce8a`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**. t7 is the better engine change.

## Rule check

Files under `include/forge/nnue.hpp`, `src/nnue.cpp`, `src/uci.cpp`, `tests_t8/`, and `REPORT_t8.md`. All mode 100644. No executable, archive, script, workflow, or Python. Engine source: 137 insertions, 13 deletions.

## Safety

`load_file` reads only the given path:

```
std::ifstream input(name, std::ios::binary);
```

Files larger than 2MiB are rejected before the weights are swapped. Test writes are `std::ofstream` to `argv[1]` and to `net_path` plus a suffix, including `net_path + ".huge"`. No network, process start, registry, environment access, or obfuscation.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both `Built target forge`.

## Pins

Default option:

```
info string bench depth 11 nodes 312866 time 162 nps 1931271
info string bench depth 13 nodes 862329 time 438 nps 1968787
nodes 4865609
```

Release binary, converted lock net:

```
info string loaded nnue /tmp/verify/work/t8.net
info string bench depth 11 nodes 312866 time 162 nps 1931271
```

Sanitizer binary: same bench 11 node count. Missing file: `info string nnue: cannot open file`.

## Task test

`nnue_convert` wrote the net. `nnue_file_test` on this commit's sanitizer objects printed `PASS`, exit 0, no sanitizer report, including exact strings `nnue: bad magic`, `nnue: unsupported version`, `nnue: wrong size`, and `nnue: cannot open file`, and the 2MiB rejection.

Lock include tree: `'load_file' is not a member of 'forge::nnue'`.

## Report claims

Reproduced: default pins, converted-net bench 11, the rejection strings in `expected_uci.txt`, and the lock test not compiling. Bench 13 and perft were run with the option unset, not again after the load. No Elo or speed claim was checked.

## Pair

t8's test covers more bad files than t7. The engine change is the weaker one: a successful load calls `clear_hash()` and leaves correction histories in place. t7 calls `Searcher::clear()`.
