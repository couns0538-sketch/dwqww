# Sol — Job 1 Forge lock readback

Case A. Codex Cloud, Linux x86_64. Model: GPT-6 (Codex). Report written 2026-11-18T01:42:47Z.

## Build and test identity

- Source `6b98f2170a3210e71beed04bbd2553972c253ed7`, branch `for-fable-and-opus/astra-0017-v3-path`. Source checkout clean at build and before staging this report.
- CMake 4.2.3, Unix Makefiles, Release, GCC C++ 14.2.0 (Debian 14.2.0-19), libstdc++ `libstdc++.so.6.0.33` (Debian 14.2.0-19), and glibc 2.41 (Debian 2.41-12+deb13u4). Default `x86-64-v4`, portable OFF, PEXT and ZMM enabled, strict FP, v3 compile path off.
- Built executable SHA-256 `2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785`.
- Embedded AL1 s198 network, 256 hidden units per side, `forge-combo29/src/nnue_weights.inc` SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. No external net loaded.
- All three commands used that executable and network with Threads 1, Hash 16 MiB, OwnBook false, UseNNUE true and other UCI options at defaults. Bench uses a fresh 16 MiB searcher and clears it per position (`src/uci.cpp:590–626`). Perft uses startpos.
- The shell clock recorded the test from `2026-11-18T01:40:39Z` to `2026-11-18T01:40:40Z`.

From the repository root:

```sh
cmake -S forge-combo29 -B ../build -DCMAKE_BUILD_TYPE=Release
cmake --build ../build --parallel 4
```

Engine stdin:

```text
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
setoption name UseNNUE value true
bench 11
bench 13
position startpos
go perft 5
quit
```

## Result

| Command | Expected nodes in LOCK.md | Observed nodes |
| --- | ---: | ---: |
| `bench 11` | 312866 | 312866 |
| `bench 13` | 862329 | 862329 |
| `go perft 5` | 4865609 | 4865609 |

All three pins match. The root move counts sum to the printed perft total. The raw timing fields are included for reproducibility.

## Raw engine stdout and stderr

```text
info string bench depth 11 nodes 312866 time 197 nps 1588152
info string bench depth 13 nodes 862329 time 578 nps 1491918
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

## Scope

This verifies the default cloud build under the recorded options. [Sol's note](NOTES_sol.md) gives the handoff reads, proposed tests and questions for Opus.
