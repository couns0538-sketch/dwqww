# Forge correctness resume (2026-11-13)

Starting revision: `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a`.
Work branch: `cursor/forge-correctness-20261113-e6b6` (not the Fable branch, not a lock branch).

## Build

- CPU: 4-thread Intel Xeon (family 6 model 207), AVX-512F and BMI2 present. `nproc` = 4.
- Compiler: g++ 13.3.0. `/usr/bin/c++` is Clang 18.1.3 and cannot link (`-lstdc++` missing), so CMake is invoked with `-DCMAKE_CXX_COMPILER=g++`.
- Flags: `-O3 -DNDEBUG -std=c++20 -ffp-contract=off -fno-fast-math -march=x86-64-v4`
- Defines: `FORGE_NNUE_HIDDEN=256 FORGE_EXPOSE_TUNABLES=1 FORGE_SPD_TT_NOTLS=1 FORGE_SPD_NO_ZERO_MOVELISTS=2 FORGE_SEARCH_SPEED2=1 FORGE_SPD_PREFETCH_EARLY=1 FORGE_SPD_SLIDER_PEXT=1 FORGE_SPD_NNUE_ZMM=1`
- `FORGE_PORTABLE` is off. This CPU can run the PEXT and AVX-512 kernels. The regression target also passes `-D_GLIBCXX_ASSERTIONS`.

## Fixed and tested: deferred-capture buffer overrun

`MovePicker::bad_captures_` was `std::array<Move, 64>` and every SEE-losing noisy move was written with `bad_captures_[bad_count_++]` and no limit. The same defect was recorded on `fable-review-buffix` (`ab2aa56b`) and called unfixed in the lock (`5f29788c`). It was not fixed on this tree.

Reproduction, before the fix, exit 134:

- FEN `3r4/Pn1Q1p2/1Q1n1QpN/1p1Q1pRB/1Qbp1QpN/2bQ1pRB/3r1QpK/2k2q2 w - - 0 1`
- census: not in check, 69 noisy moves, 68 SEE-losing, 68 of them legal
- `std::array<forge::Move, 64>::operator[]` assertion in libstdc++

After sizing the buffer to `MoveList::Capacity` (256): the same search finishes, `bestmove=d3b1 depth=3 nodes=396`. Logs: `bad_capture_before.txt`, `bad_capture_after.txt`.

`scripts/check_pins.sh` on this binary: PINS MATCH combo29.

- net on: 312866, 862329, 3024920, 12389307, 34048354
- net off: 375354, 907205, 2448617, 13573040, 24506465
- startpos perft 5: 4865609

No Elo claim. The normal benches do not reach 65 deferred captures, so their node counts stay the lock pins.

## Reproduced, not fixed yet

- `position startpos moves NOTAMOVE` leaves the previous position in place. From a checkmate, the following `go depth 1` still prints `score mate 0` and `bestmove 0000`.
- `go perft 8` does not observe `stop`. Two seconds after `stop` the process was still inside perft and had printed nothing.

## Not this tree

`opus-r5d-matefix` (`48bc43bc`) fixes a bare-king mate miss on the Opus R3 search, not on `forge-combo29/src/search.cpp`. Not ported. No KRK miss has been measured here yet.
