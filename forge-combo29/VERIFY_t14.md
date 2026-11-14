# VERIFY t14

Branch `grok47/t14-eval-command` at `ed31021d6d3ea68e7dc626f21eb3d8379e23e653`.
Base `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Verdict: **FIX NEEDED**.

## Rule check

Allowed files: `include/forge/eval.hpp`, `src/eval.cpp`, `src/uci.cpp`, `tests_t14/eval_cases.txt`, `tests_t14/test_eval.cpp`, `REPORT_t14.md`. Engine source: 47 insertions, 0 deletions.

Outside the allowed set:

- `forge-combo29/CMakeLists.txt`
- `forge-combo29/README.md`

No executable, archive, script, workflow, or Python file. Modes are 100644. The CMake change adds `test_t14_eval` and `ctest`. The feature does not need that file to compile; the test links the engine objects directly.

## Safety

`eval` prints `Evaluator::static_eval_components` for the current position. The comment says it does not write a transposition table, history, or pawn cache. No network, process start, registry, environment access, or file write in the engine. The test reads `eval_cases.txt`.

## Build

Clang configure failed (`cannot find -lstdc++`). g++ Release and ASan/UBSan both built `forge` and `test_t14_eval`.

## Pins

```
info string bench depth 11 nodes 312866 time 166 nps 1884734
info string bench depth 13 nodes 862329 time 441 nps 1955394
nodes 4865609
```

## Task test

Sanitizer `test_t14_eval` with `tests_t14/eval_cases.txt`, exit 0, no sanitizer report:

```
ok 30 positions, 10 mirrors, 3 in check, promotions white 2 black 1
```

The same test against the lock include tree failed to compile: `'EvalComponents' in namespace 'forge' does not name a type`.

Sanitizer UCI on this commit:

```
position startpos
eval
info string eval hce 18 nnue 20 total 38
position fen 4k3/8/8/8/8/8/8/4K2r w - - 0 1
eval
info string eval hce -438 nnue 95 total -343 incheck 1
```

The lock binary's `eval` command produced no output.

## Report claims

Reproduced: the 30-position test, the `eval` line shape, the lock not compiling the test, and the pins. Not checked against an external eval oracle beyond the test's own expected file. No Elo or speed claim was checked.

## What to fix

Remove the `CMakeLists.txt` and `README.md` edits from the branch. Keep the command, the header, and `tests_t14/`. The test already passes when compiled against the sanitizer objects without those two files being required at runtime.
