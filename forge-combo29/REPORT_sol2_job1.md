# sol2 — Job 1 plain-build pins

Case A. Sol2 runs in Codex Cloud on Linux x86-64 using GPT-6 (Codex). All three requested reference counts matched. [First note and proposed checks](NOTES_sol2.md)

| Command | Lock nodes | Observed nodes |
|---|---:|---:|
| `bench 11` | 312866 | 312866 |
| `bench 13` | 862329 | 862329 |
| `position startpos` followed by `go perft 5` | 4865609 | 4865609 |

## Build and options for every row

- Source branch `for-fable-and-opus/astra-0017-v3-path`, commit `6b98f2170a3210e71beed04bbd2553972c253ed7`, tree `7a3ea967d52dd440794ef149f78f46b3c94e32b2`. Built from the clean `forge-combo29` checkout with CMake 3.31.10 using Unix Makefiles, `/usr/bin/c++` GCC 14.2.0 (Debian 14.2.0-19), GNU libstdc++ `libstdc++.so.6.0.33`, and glibc 2.41 (`libc6` package `2.41-12+deb13u4`). [Plain CMake build](CMakeLists.txt) · [Expected counts and embedded-net identity](LOCK.md)
- Release and C++20, `-O3 -DNDEBUG -ffp-contract=off -fno-fast-math -march=x86-64-v4`, native default PEXT and NNUE ZMM, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, and `FORGE_EXPOSE_TUNABLES=1`. No extra compile defines or flags. No PGO or LTO. Default v3 build switch is zero. Binary SHA-256 `2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785`. [NNUE compile default](include/forge/nnue.hpp#L10)
- Embedded AL1 s198, 256 hidden units per side, `src/nnue_weights.inc` SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. No external weights. Fresh process per command with Threads 1, Hash 16 MiB, MultiPV 1, OwnBook false, UseNNUE true, and remaining UCI settings at defaults. Bench creates a separate 16 MiB searcher and clears it before each of its eight FENs. Perft is a move-generation count. [Bench driver](src/uci.cpp#L590-L626)
- Cloud host AMD EPYC 9V74, BMI2 and AVX-512 present. Counts are the result. The raw timing fields are single runs on this host, with no comparative timing or owner-PC measurement.

## Commands and raw output

Configured from `forge-combo29` with `cmake -S . -B /workspace/work/sol2-build -DCMAKE_BUILD_TYPE=Release`. Built with `cmake --build /workspace/work/sol2-build --parallel 3` using a task-local CMake binary. Each UCI process received this prefix, then the named command, then `quit`. For perft, the command was `position startpos` followed by `go perft 5`.

```text
setoption name Threads value 1
setoption name Hash value 16
setoption name MultiPV value 1
setoption name OwnBook value false
setoption name UseNNUE value true
isready
```

All three processes exited zero with empty stderr. The following blocks preserve stdout verbatim.

### `bench 11`

```text
readyok
info string bench depth 11 nodes 312866 time 261 nps 1198720
```

### `bench 13`

```text
readyok
info string bench depth 13 nodes 862329 time 621 nps 1388613
```

### `go perft 5`

```text
readyok
a2a3: 181046
b2b3: 215255
c2c3: 222861
d2d3: 328511
e2e3: 402988
f2f3: 178889
g2g3: 217210
h2h3: 181044
a2a4: 217832
b2b4: 216145
c2c4: 240082
d2d4: 361790
e2e4: 405385
f2f4: 198473
g2g4: 214048
h2h4: 218829
b1a3: 198572
b1c3: 234656
g1f3: 233491
g1h3: 198502
nodes 4865609
```

## Clock receipts

Build start and end from the cloud clock.

```text
2026-11-18T06:36:58Z
2026-11-18T06:37:07Z
```

Report written at 2026-11-18T06:40:38Z.
