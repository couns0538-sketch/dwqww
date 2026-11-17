# status — UBSan sweep (swarm/ubsan)

**State at 07:25Z: in progress. Branch pushed early on purpose so the work is not lost.**

## Build (verbatim)

- repo `couns0538-sketch/dwqww`, engine `forge-combo29/`, audit base **`6b98f2170a3210e71beed04bbd2553972c253ed7`**
- compiler `/usr/bin/g++` **13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1)**, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`
- cmake 3.28.3, `-DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4`
- sanitizer flags, exact:
  `-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g`
- resolved `CXX_FLAGS` from `flags.make`:
  `-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4`
- runtime env: `UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0:report_error_type=1`
  `ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:detect_stack_use_after_return=1`
- binary sha256 `3104e9a5616ee6d4670b8aa97586be7d185b3a4d97cde8e155c0ca298c2cbcaa`
- baseline (no sanitizer) sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`

## Proven so far

- sanitizer linked: `nm | grep -c __ubsan_` = **15** (sanitizer build), **0** (baseline); `__asan_` = 35 / 0
- 12 planted UB classes, one per check class, all caught by the same runner; control build clean
- exit-time-only plant: caught by drain-to-EOF, missed by a `bestmove`-then-kill reader (contrast recorded)
- four pins on the sanitizer build: 312866 / 862329 / 3024920 / 4865609 — **all match**

## Still to do

- full 12-phase workload (running)
- widened arithmetic arm (`float-cast-overflow`, `float-divide-by-zero`, which plain `-fsanitize=undefined` does **not** include in GCC)
