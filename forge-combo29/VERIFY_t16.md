# VERIFY t16

Branch `grok47/t16-option-handling` at `0b329db6d99961ea2b4797fec066d6a80da854f8`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **PASS**.

The commit since `c3468fc9` changes only `REPORT_t16.md`. The engine and the transcripts were built and run again.

## Rule check

Files: `src/uci.cpp` and `tests_t16/*`, plus `REPORT_t16.md`. All mode 100644. `tests_t16/start h2h4.book` is 16 bytes, mode 100644, not an executable, archive, script, workflow, or Python file. Engine source: 44 insertions, 46 deletions.

## Safety

No network, process start, registry, environment access, obfuscation, or file write in the diff. The engine reads the book path the transcript sets. `check_lines` only reads the two files it is given.

## Build

The stated cmake line without a compiler override failed on the lock tree (`/usr/bin/ld: cannot find -lstdc++: No such file or directory`, Clang 18.1.3). `/proc/cpuinfo` has `avx512f`, so portable march flags were not added. g++ 13.3.0:

```
cmake -S /tmp/wt-t16-option-handling/forge-combo29 -B /tmp/wt-t16-option-handling/build_rel -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build /tmp/wt-t16-option-handling/build_rel -j4
cmake -S /tmp/wt-t16-option-handling/forge-combo29 -B /tmp/wt-t16-option-handling/build_san -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -g"
cmake --build /tmp/wt-t16-option-handling/build_san -j4
```

Both ended `Built target forge`.


## Pins

```
printf 'setoption name Threads value 1\nsetoption name Hash value 16\nsetoption name OwnBook value false\nbench 11\nbench 13\nposition startpos\ngo perft 5\nquit\n' | /tmp/wt-t16-option-handling/build_rel/forge
```

Exit 0.

```
info string bench depth 11 nodes 312866 time 163 nps 1919423
info string bench depth 13 nodes 862329 time 430 nps 2005416
nodes 4865609
```


## Task test

Sanitizer binaries, cwd `/tmp/wt-t16-option-handling`, so `forge-combo29/tests_t16/start h2h4.book` resolves. `check_lines` is the branch's checker.

This commit:

- `options.in.txt` matched `options.expected.txt` (`cmp` exit 0).
- `clamp.in.txt` matched `clamp.expected.txt` (`cmp` exit 0), including `info string invalid value for option LmrQuietBase`.
- `ownbook.in.txt` against `ownbook.spec.txt`: `ok 54 lines`, exit 0.
- `search.in.txt` against `search.spec.txt`: `ok 7 lines`, exit 0.

No ASan/UBSan report.

Lock sanitizer binary, same inputs:

- options transcript is not exact. It drops invalid-value lines for Hash, Threads, Move Overhead, Book Depth, Book Variety, and the tunables.
- clamp transcript is missing `info string invalid value for option LmrQuietBase` (`cmp` exit 1).
- ownbook spec, exit 1: missing `invalid value for option Book Depth` and `Book Variety`.
- search spec, exit 1: missing `invalid value for option Threads` and `unknown option Not During Search`.

## Report claims

Reproduced: the four transcripts on this commit, and the lock failures above. The first attempt was run from `tests_t16/` and could not load the book, because the path in the transcript is relative to the worktree root. The results above are the rerun from that root. No Elo or speed claim was checked.
