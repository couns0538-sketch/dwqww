# Linux final-network trial runner: preparation only

`run_linux_trial.py` is prepared and AST-checked. It has not been executed, exported source, compiled an engine or run an engine/test. Root must first provide the explicit chosen immutable include path and SHA256. The independent source review is a preparation check, not a native qualification.

Use a fresh output directory outside the repository. Do not run an old/default-network qualification or reuse any prior build directory. An include identical to the accepted network is intentionally rejected as a purported new-network trial. Source metadata remains 6.4.24; no version or search edits are allowed.

```bash
/workspace/.cloud-setup/nnue-pipeline-20261023-venv/bin/python -B \
  /workspace/forge-nnue-handoff-20261023/linux-final-net-trial-preparation-attempt1/run_linux_trial.py \
  --inc /ABSOLUTE/ROOT_SELECTED_FROZEN.inc \
  --sha256 ROOT_SUPPLIED_LOWERCASE_64_HEX_SHA256 \
  --out /workspace/.cloud-setup/nnue-final-linux-NETSHA12-attempt1
```

`PINS.json` freezes the exact runner, unchanged Windows preparation `export_trial.py`, existing include parser, and eleven actual tool files (compiler driver/backend, CMake, CTest, Make, two Python interpreter paths, Git, ar, ranlib and ld). It also identifies the original Release and 14-test ASan CMake caches. Pinned hashes are checked before starting and before/after commands. Compiler/tool version queries are part of a future actual run; no compiler was invoked during this preparation.

The shared helper exports the original Git blobs at `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`, including all original build/test fixtures, then changes exactly `src/nnue_weights.inc`. It validates residual mode and H128. Historical tracked pyc files are omitted explicitly, and `PYTHONDONTWRITEBYTECODE=1` prevents new ones. The runner checks the exact source file set, SHA256 values and Git permission modes after every stage. It performs no Git/index/write operation and never edits source to force a pass.

The future run serially builds the complete engine/tests twice in fresh directories:

| Profile | Configuration | Extra flags |
| --- | --- | --- |
| Release | `Release`, GCC14, Unix Makefiles, parallel1 | `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto` |
| ASan/UBSan | separate `RelWithDebInfo`, same compiler, parallel1 | same strict flags plus `-fno-pie`, link `-no-pie`, `FORGE_ENABLE_SANITIZERS=ON` |

`FORGE_NATIVE=OFF`, explicit C++20 and `CMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF` are required. Actual compilation records are inspected for strict float/no-LTO flags and C++20; every ASan translation unit and engine link must carry both address/undefined instrumentation. Sanitizer execution explicitly uses `ASAN_OPTIONS=detect_leaks=1:halt_on_error=1:abort_on_error=1` and `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1`. Historical caches supply the flags; historical passes do not qualify the new network.

For each build, discovery must report exactly the original fourteen names: the nine C++ tests (`forge_tests`, correction history, runtime PSQT, pawn span, nearest pawn, PV metadata, TT coherence, rule50 and legal witness) and five Python checks (match tools, Windows validation tool tests, UCI, ponder and OwnBook regressions). The serial execution must return0 and produce fourteen passing, non-skipped JUnit cases. Original perft expectations remain inside the unchanged `forge_tests` binary. No individual result is borrowed from the old network.

After both complete correctness suites pass, two fresh Release engine processes receive the original `bench 11\nquit\n` bytes. The first valid positive node signature is unknown until that actual execution. `evidence/FIRST-BENCH11.json` freezes it with source/net/binary/stdout hashes before the second process runs. The repeat must match it. No old Linux/Windows signature is required, and bench nodes are not NPS or Elo evidence.

Every command retains exact arguments, declared environment overrides, stdin bytes/hash, original stdout/stderr and actual return-code/time receipt. Timeouts kill and reap only the owned process group, preserve evidence and fail; there is no automatic retry. Source/net/tool changes fail the gate. Final `evidence/RESULT.json` is published atomically without overwrite. It keeps speed/Elo conclusions null and promotion false. Build inventories preserve exact binaries, core archives, objects, flags, link commands, CMakeCache, compile commands, original regression logs and JUnit evidence.

Root owns execution after network selection, publication and acceptance. A future pass would establish actual Linux correctness/repeatability for those bytes. It would establish no Windows/Ryzen qualification, inference parity not separately performed by this runner, speedup, Elo gain or Stockfish result.
