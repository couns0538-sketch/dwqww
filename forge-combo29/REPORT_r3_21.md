# r3-21: mate scores from the hash table

## Where the idea comes from

Finding 6 of the source audit on `audit/lock-source` at commit `302a08a272fbe8e8c4463731f3b9cd72d72d3f48`, in `forge-combo29/AUDIT_lock_source.md`. The failing case is `forge-combo29/tests_audit/proof_mate_score_ply_underflow.cpp` on that commit. That branch was read only. Nothing here was taken from another engine. The repair is the check that finding describes: if putting ply back onto a stored mate score leaves the mate band, do not use the score.

## What was wrong

`MateInMaxPly` is `MateValue - MaxPly` (`32000 - 128 = 31872`). `is_mate_score` is true only at or outside that line. `score_to_tt` stores a mate as `score + ply` (or `score - ply` for a loss). `score_from_tt` used to reverse that with no further check.

A stored mate of `31873` (`MateInMaxPly + 1`, mate distance 127) read at ply 2 became `31871`. That is below `MateInMaxPly`, so the rest of the search treated it as a centipawn score: it was not shifted again when stored by the parent, and the root printed `score cp 31871`. The loss side is the same mistake in the other direction (`-31872 + ply` steps inside the band).

## Reproduction on the base

Base commit `e04556ddc3a430b2e751159b0d46111ef56c8b89`, before this change. The audit proof, built with the portable search flags and the combo29 NNUE weights, printed:

```text
Seeded ply-2 TT entry with score=31873 (is_mate_score=1)
info depth 1 seldepth 1 score cp -48 nodes 2 nps 2000 hashfull 0 time 1 pv g3g4
info depth 2 seldepth 2 score cp 31871 nodes 5 nps 2500 hashfull 0 time 2 pv g3g4 h6h5
Root search returned: score=31871 is_mate_score=0 best=g3g4
```

Same pins as the end of this report: perft 5 = 4865609, bench 11 = 312866, bench 13 = 862329.

## The change

`score_from_tt` in `forge-combo29/src/search.cpp` still subtracts ply from a winning mate and adds ply to a losing mate. If that result is inside the centipawn range, it returns `ValueNone`. Callers already treat `ValueNone` as "no usable score", and they still keep the stored move and static eval. A mate that remains at or outside `MateInMaxPly` is unchanged. No UCI option. The default search does not hit this edge at the pinned depths, so the three node counts stayed the same and the fix is always on.

## Test

`forge-combo29/tests_r3_21/proof_mate_score_ply_underflow.cpp` keeps the audit position, the seed `MateInMaxPly + 1`, and the depth-2 search. It fails if the root comes back as `31871` or as any mate or other huge score. On the fixed engine that search returns `score=0 is_mate_score=0 best=g3g4` (the proof stores eval 0 next to the fake mate; once the mate is ignored, quiescence stands on that eval). Depth 1 is still `cp -48`, because it never reaches the seeded node.

The same file checks three neighbours:

- A stored win of `MateValue - 10` at that ply-2 node still returns `31988`, which is a mate.
- At the position after `g3g4` (no capture, so depth 1 is a stand-pat), a stored loss of `-MateInMaxPly` no longer comes back as the centipawn score `31871`.
- A stored loss of `-(MateValue - 10)` at that node still comes back as the mate score `31989`.

`CMakeLists.txt` is unchanged, so the test is not part of the engine target. Build and run:

```bash
g++ -std=c++20 -O2 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -ffp-contract=off -fno-fast-math -march=x86-64-v3 \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 \
  -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 \
  -DFORGE_SPD_SLIDER_PEXT=0 -DFORGE_SPD_NNUE_ZMM=0 \
  -DFORGE_NNUE_WEIGHTS=\"$PWD/forge-combo29/src/nnue_weights.inc\" \
  -Iforge-combo29/include forge-combo29/tests_r3_21/proof_mate_score_ply_underflow.cpp \
  forge-combo29/src/bitboard.cpp forge-combo29/src/board.cpp \
  forge-combo29/src/eval.cpp forge-combo29/src/eval_params.cpp \
  forge-combo29/src/nnue.cpp forge-combo29/src/search.cpp \
  -lpthread -o /tmp/proof_mate_score_ply_underflow
/tmp/proof_mate_score_ply_underflow
```

That run printed `PASS` under AddressSanitizer and UndefinedBehaviorSanitizer. A release link against the built engine objects printed `PASS` as well.

## Pins

Protocol: `Threads 1`, `Hash 16`, `OwnBook false`, every other option left at default. `bench` constructs its own 16 MB searcher. Perft is from the start position.

Before the change and after it:

| check | nodes |
| --- | ---: |
| `go perft 5` | 4865609 |
| `bench 11` | 312866 |
| `bench 13` | 862329 |

## Build note

The requested CMake line was used with `CXX=g++` (GCC 13.3.0):

```bash
cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3
cmake --build build -j
```

On this machine `/usr/bin/c++` is Clang 18, and it looks for `libstdc++` in the GCC 14 directory, which has no `libstdc++.so`. The link failed before any engine object was built. GCC 13 is the compiler that actually produced the binary above. The flags in `CMakeLists.txt` are the ones that ran (`-O3 -ffp-contract=off -fno-fast-math -march=x86-64-v3`, portable PEXT/ZMM switches off).

## Not verified

- The cmake command with the default `c++` compiler. It does not link here.
- A mate score created by a real search near ply 128, rather than a score written into the table by the test. Bench 11 and bench 13 do not reach a mate that close to `MaxPly`, which is why their node counts did not move.
- More than one thread. `score_from_tt` has no thread-local data, and the required run is one thread.
- Games or Elo.
