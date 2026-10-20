# Pending frozen 6.4.13 validation

Implementation is prepared in the assigned working-tree paths; root must review, stage/commit the merge, and export that immutable revision before builds. No heavy build or GREEN is claimed by this file. Preserve existing frozen 886 builds, packages and `red-attempt1`.

Use a new source export and new build directories. Example root-selected paths below may be replaced consistently; do not point CMake at the live merge checkout or reuse an 886 build directory.

```bash
CLOCK_SOURCE=/workspace/.cloud-setup/forge-clock-contract-source
CLOCK_RELEASE=/workspace/.cloud-setup/forge-clock-contract-release
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/cmake -S "$CLOCK_SOURCE" -B "$CLOCK_RELEASE" -DCMAKE_BUILD_TYPE=Release '-DCMAKE_CXX_FLAGS=-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto' -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/cmake --build "$CLOCK_RELEASE" --parallel 2
PYTHONDONTWRITEBYTECODE=1 /workspace/.cloud-setup/venv/bin/ctest --test-dir "$CLOCK_RELEASE" --output-on-failure -j 1
```

The standalone automatic-origin witness uses real Searcher/Worker behavior. Its exported pthread_create symbol records actual libstdc++ helper admission and delegates via RTLD_NEXT without delay, failure injection or production hooks. Seven mode groups require the main Worker's origin to follow actual helper admission for untimed depth/nodes/mate, infinite-with-clock and ponder-with-clock; finite depth+movetime/depth+clock must begin before helper admission. It does not contain either new timestamp spelling, so the exact same source compiles against the old frozen header/core without ABI mixing.

Expected RED against exact frozen 886: five untimed/ponder FAIL lines and two finite timed PASS lines, exit 1. Expected GREEN against frozen new source: seven PASS lines and zero failures, exit 0.

```bash
CLOCK_DIAGNOSTICS=/workspace/.cloud-setup/forge-clock-contract-diagnostics
mkdir -p "$CLOCK_DIAGNOSTICS"
g++ -std=c++20 -O2 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto -Wall -Wextra -Wpedantic -Wconversion -Wshadow -I/workspace/.cloud-setup/forge-tt-single-worker-gated-source/include /workspace/dwqww/validation/upstream-clock-reconcile-20261020/automatic-origin-api.cpp /workspace/.cloud-setup/forge-tt-single-worker-gated-release/libforge_core.a -pthread -Wl,--export-dynamic-symbol=pthread_create -ldl -o "$CLOCK_DIAGNOSTICS/automatic-origin-red"
"$CLOCK_DIAGNOSTICS/automatic-origin-red"
g++ -std=c++20 -O2 -DNDEBUG -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto -Wall -Wextra -Wpedantic -Wconversion -Wshadow -I"$CLOCK_SOURCE/include" /workspace/dwqww/validation/upstream-clock-reconcile-20261020/automatic-origin-api.cpp "$CLOCK_RELEASE/libforge_core.a" -pthread -Wl,--export-dynamic-symbol=pthread_create -ldl -o "$CLOCK_DIAGNOSTICS/automatic-origin-green"
"$CLOCK_DIAGNOSTICS/automatic-origin-green"
```

These commands are displayed individually so the expected RED exit is not silently swallowed by a pipeline or a set-e chain. The execution wrapper must preserve all exit codes and stdout/stderr, recording old/new source/header/core/test/binary hashes before and after.

For actual UCI GREEN, reuse the exact immutable candidate-side script and exact accepted probe/shim source recorded in `red-attempt1`. Verify the saved shim hash against red `identity.json`, or rebuild the identical saved C source to a new diagnostics directory and record its new binary hash. The script refuses pre-existing output files. The below old temp shim still exists in the current session; future sessions must reconstruct it from the preserved source.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /workspace/dwqww/validation/upstream-clock-reconcile-20261020/red-attempt1/candidate-origin-probe.py "$CLOCK_RELEASE/forge" /tmp/forge-clock-red-gu5ljkgk/libdelay.so /workspace/dwqww/validation/upstream-clock-reconcile-20261020/red-attempt1/native_clock_probe.py /workspace/dwqww/validation/upstream-clock-reconcile-20261020/green-uci-attempt1
```

Expected GREEN: first timed info >=380ms, untimed depth-1 info <220ms at 440ms imposed admission, two engine exits 0, valid bestmoves and empty stderr. This reuses unchanged accepted `run_trial`; it is candidate-side origin validation, not the complete authentic-pre-fix-engine comparison or a deadline/strength test. Shared-host pauses may make the upper threshold inconclusive; preserve failures before deciding whether a changed resource state supports a fresh evidence directory.

Then run full ASan/UBSan CTest in another new build using existing pinned non-PIE options; preserve default TSan deadlock detection for relevant TT/lifecycle/API checks. Existing Windows build/validator checks must be repeated for the newly frozen 6.4.13 source before packaging, with a new package identity. None of these checks is a strength acceptance result; the ongoing frozen 886 match remains a separate experiment.

## Preserved diagnostic correction

The first executed Release witness attempt failed its validity check: all seven
rows observed zero helpers because GNU `--wrap` cannot rewrite calls originating
inside shared libstdc++. This was a diagnostic failure, not an engine RED result.
Its original driver, runner, output and direct symbol investigation remain in
`witnesses-release-attempt1/`. The corrected diagnostic exports `pthread_create`
from its executable and delegates through `dlsym(RTLD_NEXT)`; actual Forge builds
are unchanged. `run-witnesses.py release --attempt 2` observed three actual
helpers in every case, reproduced five old-core origin failures with two timed
passes, then passed all seven new-core cases, seven TT API groups and the exact
accepted candidate-side UCI probe. Both old/new source, headers and core hashes
remain frozen and unmixed. Attempt2 original commands and hashes are retained.
