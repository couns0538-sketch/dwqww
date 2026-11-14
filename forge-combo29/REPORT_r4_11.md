# R4 finding 11 — `params::name` negative index

Base: `e04556ddc3a430b2e751159b0d46111ef56c8b89`  
Audit: `302a08a272fbe8e8c4463731f3b9cd72d72d3f48` (`audit/lock-source`), finding 11 and `forge-combo29/tests_audit/proof_eval_param_name_oob.cpp` only.

## Bug

`forge::params::name(int)` in `src/eval_params.cpp` treated every `index < KnightMobility` as a piece-square name. A negative index was not rejected. For `index <= -64`, `index / 64` is negative, `static_cast<std::size_t>` wraps, and the 6-element `pieces` array is read before its start. For `-63 <= index <= -1` the read stays in the array and the function returns a name such as `PawnPsqt[-1]` instead of `Unknown`.

## Reproduction on the base

Built and run before the fix, from `e04556dd`, with the audit proof:

```bash
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
  -Iforge-combo29/include /tmp/r4_11/proof_eval_param_name_oob.cpp \
  forge-combo29/src/eval_params.cpp -o /tmp/r4_11/proof_eval_param_name_oob
/tmp/r4_11/proof_eval_param_name_oob
```

Exit code 1. AddressSanitizer and UBSan:

```text
forge-combo29/src/eval_params.cpp:30:23: runtime error: load of address 0x7f6b78b001c8 with insufficient space for an object of type 'const char *'
==2397==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7f6b78b001c8
READ of size 8 at 0x7f6b78b001c8 thread T0
    #0 forge::params::name(int) forge-combo29/src/eval_params.cpp:30
    #1 main /tmp/r4_11/proof_eval_param_name_oob.cpp:19
  [464, 512) 'pieces' (line 29) <== Memory access at offset 456 underflows this variable
SUMMARY: AddressSanitizer: stack-buffer-overflow forge-combo29/src/eval_params.cpp:30 in forge::params::name(int)
```

## Fix

One guard at the start of `name`. In-range names are unchanged. `index >= Count` already fell through to `Unknown`.

```cpp
if (index < 0 || index >= Count) return "Unknown";
```

No search option was added. `CMakeLists.txt` was not edited, and the test configure does not pass any `-DFORGE_*` value.

The same proof command after the fix prints `Unknown`, writes nothing to stderr, and exits 0.

## Checks

`forge-combo29/tests_r4_11/run.sh` configures the existing CMake file with g++ (the proof compiler; `/usr/bin/c++` on this image is Clang without its sanitizer runtime), `-fsanitize=address,undefined`, and `-fno-sanitize-recover=address,undefined`. It does not change lock `FORGE_*` defaults. The test exits 1 on a failed check. A sanitizer finding aborts with a non-zero status.

`tests_r4_11/r4_11_test.cpp` calls `name` for `-128..-1`, other out-of-range indices, and the in-range piece-square and term names. It then checks the lock pins and runs 200 depth-10 searches. Each `best_move` and every PV move must be legal.

Result, exit 0:

```text
names checked failures 0
pins bench11 312866 bench13 862329 perft5 4865609
searches 25 legal_ok 1
searches 50 legal_ok 1
searches 75 legal_ok 1
searches 100 legal_ok 1
searches 125 legal_ok 1
searches 150 legal_ok 1
searches 175 legal_ok 1
searches 200 legal_ok 1
searches 200 depth 10 legal_ok 1 total_nodes 4020860
PASS
```

Pins `312866`, `862329`, and `4865609` are unchanged.
