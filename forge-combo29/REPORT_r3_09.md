# AspArmLate

`AspArmLate` is one UCI check option. It is off by default, so the root search used by `bench` and `go perft` is unchanged.

## Where the idea comes from

The rule is the one named in the task. It is the usual iterative-deepening aspiration policy, written for this engine and not taken from another engine's source, constants, or tables.

Early root iterations do not yet have a score that has been shown to lie inside the window that produced it, so those iterations use a full window (`-Infinite` .. `Infinite`). A narrow window, the existing `AspirationDelta` around the previous root score, is used only after one root score has come back strictly inside its window. If a search is still outside that window, the same widening already in this file runs again (`delta += delta / 2 + 4`). That attempt is not a finished iteration: the soft time limit does not stop the search on it. The hard limit, the node limit, and an external stop still abort as before.

With the option left off, the narrow window still opens at depth 4, which is the previous behaviour.

## What changed

- `forge-combo29/include/forge/search.hpp`: `tune::AspArmLate`, default false.
- `forge-combo29/src/search.cpp`: the flag, the root-window choice, and the soft-time gate.
- `forge-combo29/src/uci.cpp`: the option is printed by `uci` and accepted by `setoption`.
- `forge-combo29/tests_r3_09/asp_arm_late_test.cpp`: bench pins, 200 depth-10 searches, and 20 short clock searches.

The `src` and `include` diff against `e04556dd` is 33 changed lines. `CMakeLists.txt` was not edited.

`uci` prints:

```
option name AspArmLate type check default false
```

A value other than `true` or `false` is rejected and leaves the flag as it was. `setoption name AspArmLate value maybe` printed `invalid value for option AspArmLate`, and the following `bench 11` stayed 312866.

## Pins

Release build:

`cmake -S forge-combo29 -B build -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=g++`

`/usr/bin/c++` on this machine is Clang 18, and it does not find `libstdc++` (it selects the GCC 14 library directory, which has no `libstdc++.so`). The binary used here is g++ 13.3.0 with the flags above. Threads 1, Hash 16, OwnBook false, and every other option at default, including `AspArmLate` false.

Before the edit, and again after it with the option off:

- `bench 11` = 312866
- `bench 13` = 862329
- `go perft 5` from the start position = 4865609

Turning the option off again after a bench with it on repeated those same `bench 11` and `bench 13` counts.

## Sanitizer

`forge-combo29/tests_r3_09/asp_arm_late_test.cpp` was compiled with the same `FORGE_*` defines as the portable release build, plus `-O2 -fno-omit-frame-pointer -fno-sanitize-recover=address,undefined -fsanitize=address,undefined`, and `-DFORGE_UCI_NO_MAIN`. The binary links `libasan.so.8` and `libubsan.so.1`.

With `AspArmLate` on, 200 searches to depth 10 (Hash 16, one thread) each returned a move that is in the position's legal move list and passes `is_legal`. A further 20 searches on a 40 ms clock, also with the option on, did the same. The process exited 0 with no sanitizer report.

That run also printed the pins with the option off (`312866`, `862329`, `4865609`) and `818642` with it on, then `862329` again after the flag was cleared.

No strength claim. These checks are node counts, perft, legality, and a clean sanitizer run.

The same release pins and the same sanitizer binary were run again at 2026-11-14T14:15:43Z and at 2026-11-14T14:32:48Z. Each time `bench 11` was 312866, `bench 13` was 862329, perft 5 was 4865609, and `bench 13` with the option on was 818642. Each sanitizer run passed: 200 depth-10 searches, 0 illegal; 20 timed samples, 0 illegal. A last release pass at 2026-11-14T14:49:43Z matched those four numbers again, with the option off restoring `bench 11` and `bench 13`.

setoption name AspArmLate value true

bench 13 nodes 818642

## Follow-up redesign

The first version treated the depth-1 full-window score as the in-bounds score, so the option narrowed from depth 2 instead of depth 4. The soft-time gate never ran, because a finished iteration had already landed inside the window. That version is withdrawn. Its option-on bench 13 count of 818642 is not the current engine.

The option still defaults off. The narrow window still opens at depth 4. When `AspArmLate` is on, an iteration that fails high or low at least once makes the next iteration use a full window. The fail-high and fail-low widening inside an iteration is unchanged. The soft-time special case was removed.

Owner build on this host (AVX-512F and BMI2 present): default CMake release, `march=x86-64-v4`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`. No `CMakeLists.txt` edit and no extra `FORGE_*` override. The compiler is g++ 13.3.0 because `/usr/bin/c++` is Clang 18 and cannot link `libstdc++` here.

Option off, Threads 1, Hash 16, OwnBook false:

- bench 11 = 312866
- bench 13 = 862329
- go perft 5 from the start position = 4865609

Those three held after the option was turned on and then off.

Option on, same binary:

bench 13 nodes 870398

Five alternating `bench 13` runs on that binary, off/on/off/on/off, kept those node counts. The nps figures were 1684236, 1540527, 1694163, 1667429, and 1680953.

Screening is the same binary with the option on against the option off, `nodes 50000`, UHO_4060_v4 sequential pairs. It is a screen, not a strength claim. Chunk 001 (200 openings, 400 games) finished 109-102-189 for the option-on side, Elo 6.08 +/- 22.28 (95%), LOS 70.39%, pentanomial [6, 56, 71, 59, 8]. Chunk 002 finished 98-114-188, Elo -13.90 +/- 21.37 (95%), LOS 10.06%, pentanomial [9, 55, 84, 47, 5]. Together that is 207-216-377, Elo -3.91 +/- 15.45 (95%), LOS 30.98%, pentanomial [15, 111, 155, 106, 13]. Details are under `forge-combo29/tests_r3fu_09/screen/`.
