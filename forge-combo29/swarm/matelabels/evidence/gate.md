# Gate evidence — four honesty pins before any recording

Build identity is recorded here so every number in `FINDINGS.md` can be traced
to one binary.

## Build

```
engine folder : forge-combo29/
audit base    : 6b98f2170a3210e71beed04bbd2553972c253ed7
compiler      : g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
cmake         : -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DFORGE_MARCH=x86-64-v4
link          : LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
engine binary : sha256 e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id name       : Chess Engine Forge 6.4.24 candidate
```

Compile flags actually used (`build/CMakeFiles/forge.dir/flags.make`):

```
-DFORGE_EXPOSE_TUNABLES=1 -DFORGE_NNUE_HIDDEN=256
-DFORGE_NNUE_WEIGHTS=".../src/nnue_weights.inc"
-DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_NNUE_ZMM=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2
-DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_TT_NOTLS=1 -DNDEBUG
-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4
```

## The four pins

`bench N` was sent **on stdin as a UCI command**, never as argv. Piping `quit`
into a live search is what makes the engine fabricate a `bestmove`; the gate run
below therefore uses a single stdin stream ending in `quit`, and every `bench`
completed before it (the bench command is not a live search, so the brief's rule
1 does not bite here -- but the same trap *was* reproduced separately, see
`engine-refusal-and-trap.txt`).

| pin | expected | measured | verdict |
|---|---|---|---|
| `bench 11` | 312,866 | **312,866** | MATCH |
| `bench 13` | 862,329 | **862,329** | MATCH |
| `bench 16` | 3,024,920 | **3,024,920** | MATCH |
| `go perft 5` | 4,865,609 | **4,865,609** | MATCH |

Raw output:

```
info string bench depth 11 nodes 312866 time 242 nps 1292834
info string bench depth 13 nodes 862329 time 572 nps 1507568
info string bench depth 16 nodes 3024920 time 1839 nps 1644872
nodes 4865609
```

All four match. Recording was permitted from this point on.
