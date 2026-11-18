# sol3 — Job 1 Forge lock pins

Case A. Codex Cloud on Linux x86_64. Model GPT-6 (Codex).

## Build and test identity

- Source `for-fable-and-opus/astra-0017-v3-path` at `6b98f2170a3210e71beed04bbd2553972c253ed7`. Clean tracked source at configure and before recording results. CMake 4.2.3, Unix Makefiles, Release, GCC C++ 14.2.0 (Debian 14.2.0-19), libstdc++ `libstdc++.so.6.0.33` (Debian 14.2.0-19), glibc 2.41 (Debian `2.41-12+deb13u4`). Default `x86-64-v4`, PEXT and ZMM enabled, strict floating point, v3 compile path off.
- Linux binary SHA-256 `2f545495d4e3e2b59af49fbb18212ec2ed8ae297d801e58647cfea37cd18e785`. The build matches the SHA-256 in Sol’s separate Job 1 report.
- Embedded AL1 s198, 256 hidden units per side, weights-source SHA-256 `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. No external net.
- Each command used a fresh engine process and explicitly set Threads 1, Hash 16 MiB, MultiPV 1, OwnBook false and UseNNUE true. Other options at defaults. `bench` creates and resets its own 16 MiB searcher per test position (`src/uci.cpp:599–619`). Perft uses startpos.
- Commands ran from `2026-11-18T06:36:47Z` to `2026-11-18T06:36:49Z` using the shell clock.

```sh
cmake -S forge-combo29 -B /workspace/work/build-sol3 -DCMAKE_BUILD_TYPE=Release
cmake --build /workspace/work/build-sol3 --parallel 4
```

Each process received these commands first. It then received its command below and `quit`.

```text
setoption name Threads value 1
setoption name Hash value 16
setoption name MultiPV value 1
setoption name OwnBook value false
setoption name UseNNUE value true
isready
```

## Facts

| Command | Lock expectation | Observed nodes |
| --- | ---: | ---: |
| `bench 11` | 312866 | 312866 |
| `bench 13` | 862329 | 862329 |
| `position startpos` then `go perft 5` | 4865609 | 4865609 |

All pins match `LOCK.md`. I summed the perft root rows independently and got 4865609. All three processes exited with empty stderr. Timing fields are raw measurements from this Linux session.

## Raw stdout

### `bench 11`

```text
readyok
info string bench depth 11 nodes 312866 time 469 nps 667091
```

### `bench 13`

```text
readyok
info string bench depth 13 nodes 862329 time 1204 nps 716220
```

### `position startpos` then `go perft 5`

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

[First note, source observations and deciding tests](NOTES_sol3.md)
