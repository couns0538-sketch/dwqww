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

## Re-check

Done on this branch without switching away from it. The unfixed engine was built from commit `e04556dd` in a temporary tree, not by checking out another branch.

The audit proof against that unfixed tree printed `score=31871 is_mate_score=0` again. The test in `tests_r3_21` linked to those unfixed objects exits 1 with `FAIL mate crossed MateInMaxPly and came back as 31871`. Linked to this branch's objects it prints `PASS` and exits 0.

`score_from_tt` is the only conversion. Quiescence and the main search both call it, and both already ignore `ValueNone`. A same-ply mate still round-trips: depth 18 found `mate 1`, `mate 2`, `mate 17`, and an already-mated `mate 0` with the same node counts, PVs, and best moves as the unfixed binary.

Pins, three times, Threads 1, Hash 16, OwnBook false:

| run | perft 5 | bench 11 | bench 13 |
| --- | ---: | ---: | ---: |
| unfixed `e04556dd` | 4865609 | 312866 | 862329 |
| this branch, run 1 | 4865609 | 312866 | 862329 |
| this branch, run 2 | 4865609 | 312866 | 862329 |
| this branch, run 3 | 4865609 | 312866 | 862329 |

Separate `go depth 11` and `go depth 13` searches of the eight bench positions matched the unfixed binary on seldepth, score, nodes, PV, and best move. The depth-13 node counts add up to 862329. The same match holds at depth 16 and depth 18 for those eight positions plus a mate in one, a position that is already checkmate, and king and rook versus king. No option was added. The required pins do not move, so the check stays on.

A table of every store ply `0..127`, every mate distance `0..128`, both signs, and every read ply `0..127`, passed through the same `int16` clamp the table uses, produced no centipawn result. The new code either keeps a mate score or returns `ValueNone`. That table is a check of this function's arithmetic, not a second copy in the engine.

The loss side of the same position shows the mirror image. After `g3g4`, a stored score of `-31872` is read at ply 1. The unfixed code returns `31871` with `is_mate_score=0`. This branch returns `0`. A stored loss of `-31990`, which still fits after adding one ply, returns `31989` and is a mate on both binaries.

Depth 20 and depth 22 match the unfixed binary on the start position, the bench endgame, the bench position that is mate in 2, king and rook versus king (`mate 17`), and the mate in 1. Node counts, scores, PVs, and best moves are the same. The start position at depth 22 is 3618801 nodes on both. Depth 24 matches too, including the start position at 8969513 nodes and kiwipete at 7927001 nodes.

A temporary counter inside `score_from_tt`, removed before the next build, fired 0 times across perft 5, bench 11, bench 13, and a depth-22 king-and-rook mate. Those bench and perft commands still printed 4865609, 312866, and 862329 while the counter was present. After deleting the counter and rebuilding, the same three numbers came back. The default searches do not enter the new branch, which is why the pins stay put without an option.

The proof test, rebuilt from this tree with AddressSanitizer and UndefinedBehaviorSanitizer, printed `PASS` and exited 0.

## Not verified

- The cmake command with the default `c++` compiler. It does not link here. The binaries above were built with GCC 13.3.0 and the flags in `CMakeLists.txt`.
- A mate score created by search at ply close to 128. Depth 18 does find real mates, and those searches matched the unfixed binary, but that is not the same as a 127-ply mate being read again on a deeper path.
- More than one thread. `score_from_tt` has no thread-local data, and the required run is one thread.
- Games or Elo.
