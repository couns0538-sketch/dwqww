# Final-tree sanitizer soak preparation

Preparation only. No engine, compiler, test, Git mutation or root-state write was performed. Root must accept the final Step 2 tree and its gates before using these commands. The absolute Job A deadline remains **2026-11-15 02:19:40 UTC**; this preparation does not extend it.

`play_driver.cpp` is an unchanged copy of the proven old `tests_astra_mateguard/play_driver.cpp`; `harness-origin.txt` pins its bytes and original location. Root can publish this new copy under `forge-combo29/tests_astra_parity/`. Do not overwrite any existing test. The tools here are VM-only scripts; publish only inert `.mjs.txt` copies if desired.

The driver creates one `Searcher` per process, clears it at each new game, and reuses it without clearing between every subsequent move. This already exercises lazy accumulator state across sequential positions and search calls. It does not prove reuse across arbitrary unrelated root positions. No extra warm-Searcher feature was added.

## Preliminary Step 1 use while its recorder question is pending

Root separately authorized independent preliminary self-play on the frozen Step 1 tree. This is not final-tree validation and does not waive the equality gate. Use the distinct `step1` stage, build directories, binary paths, labels and seeds:

```text
node /workspace/work/parity-run/command.mjs step1-asan-configure /workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake -S forge-combo29 -B /workspace/work/parity-run/builds/step1-asan -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF -DCMAKE_EXPORT_COMPILE_COMMANDS=ON '-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -g -fsanitize=address,undefined -fno-omit-frame-pointer' -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined
node /workspace/work/parity-run/command.mjs step1-asan-build /workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake --build /workspace/work/parity-run/builds/step1-asan -j4
node /workspace/work/parity-run/command.mjs step1-asan-driver node /workspace/work/parity-soak-preparation/build-play.mjs asan --execute-build-authorized step1
node /workspace/work/parity-soak-preparation/run-play.mjs 0 --execute-authorized step1
node /workspace/work/parity-soak-preparation/audit-play.mjs 0 step1
```

`soak-plan-step1.txt` has separately declared seeds 202611144101 through 202611144112 and labels beginning `step1-parity-`. Other indices retain the same group mapping as the final plan; TSan indices require the analogous `step1-tsan` build. Preliminary provenance pins the actual source bytes. Any later engine change causes the launcher to reject these preliminary build inputs. No preliminary result counts toward a final-tree soak.

## Build commands, each recorded and bounded separately

Run from `/workspace/work/dwqww-parity`. `command.mjs` records command, timestamps, full stdout/stderr, exit, signal and hashes, and applies a 440-second timeout. Its labels must be fresh. All CMake build folders and binaries remain outside the Git tree. The core uses Release definitions including NDEBUG; the driver translation unit uses `-UNDEBUG`, matching the previously exercised setup. No CMake source change is required.

```text
node /workspace/work/parity-run/command.mjs final-asan-configure /workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake -S forge-combo29 -B /workspace/work/parity-run/builds/final-asan -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF -DCMAKE_EXPORT_COMPILE_COMMANDS=ON '-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -g -fsanitize=address,undefined -fno-omit-frame-pointer' -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=address,undefined
node /workspace/work/parity-run/command.mjs final-asan-build /workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake --build /workspace/work/parity-run/builds/final-asan -j4
node /workspace/work/parity-run/command.mjs final-asan-driver node /workspace/work/parity-soak-preparation/build-play.mjs asan --execute-build-authorized
node /workspace/work/parity-run/command.mjs final-tsan-configure /workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake -S forge-combo29 -B /workspace/work/parity-run/builds/final-tsan -DCMAKE_BUILD_TYPE=Release -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF -DCMAKE_EXPORT_COMPILE_COMMANDS=ON '-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1 -g -fsanitize=thread -fno-omit-frame-pointer' -DCMAKE_EXE_LINKER_FLAGS=-fsanitize=thread
node /workspace/work/parity-run/command.mjs final-tsan-build /workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake --build /workspace/work/parity-run/builds/final-tsan -j4
node /workspace/work/parity-run/command.mjs final-tsan-driver node /workspace/work/parity-soak-preparation/build-play.mjs tsan --execute-build-authorized
```

Build one mode at a time. The driver builder verifies expected CMake flags, links the seven matching instrumented engine objects excluding UCI main, and pins every source/header, object, harness, flags file and resulting binary. It refuses to overwrite a prior binary/provenance record. A failed attempt's output must be retained; root must use a fresh build output for a retry rather than discarding it. Old instrumented builds occupied about 61 MB plus roughly 26 MB for the two self-play drivers; the VM had 3.1 GB free at preparation time. This is a storage observation, not a build result for the new tree.

## Run and audit one batch

`soak-plan.txt` declares 12 batches, unique seeds 202611144001 through 202611144012, 180 seconds each. Eight ASAN/UBSAN groups cover Threads 1/2 × nodes 2000/20000 × both options off/on. Four TSan groups cover Threads 2/4 × depth 9 × both options off/on. The two options are HindsightDepth and MateAlphaGuard; all others retain defaults. The compile guard is 1, and runtime MateAlphaGuard remains false in the off groups.

```text
node /workspace/work/parity-soak-preparation/run-play.mjs 0 --execute-authorized
node /workspace/work/parity-soak-preparation/audit-play.mjs 0
```

Use indices 0 through 11, sequentially, auditing each finalized command before the next. Root must save the auditor stdout as immutable `.txt`, merge accepted counts into its own state/report, package raw logs and provenance, and checkpoint on its normal cadence. The launcher writes only a fresh provenance file and invokes the existing root command recorder; it never writes root state or Git. It verifies frozen input hashes before every run and refuses to start without 475 seconds remaining. The driver's 180-second budget is checked between whole games, so a batch can exceed three minutes while finishing its current game. The outer 440-second limit still applies. A killed attempt is excluded from completed totals and retained, with no invented counts. The 12 target batches take at least 36 minutes plus game completion/build/audit overhead; do not promise they fit the remaining budget without reading the clock.

`audit-play.mjs` scans all stdout/stderr for sanitizer/abort diagnostics, verifies configuration, summary, traces and game termination accounting, and returns a row for root. Exit 0 means that batch passed its bounded checks; exit 1 means incomplete or findings. Validation assertions must be treated as recorder failures, with output retained. Every sanitizer diagnostic remains reportable even if the attempt was incomplete. No absence of observed reports proves universal race freedom.

## Fault handling and repetition

Every search emits its exact FEN, complete start-position move history, seed, game, ply, thread count and options before entering the search. Keep full raw output and the build/binary pins. A single-game replay uses the same binary/options/seed with `--first-game N --games 1 --seconds 180 --trace`; use ten fresh processes and unique labels, each bounded by the root recorder. It recreates the per-game RNG and cleared Searcher. It does not recreate earlier games' process allocation history or guarantee the same multi-thread interleaving. Report actual repeat counts and this limit. Do not drop a sanitizer report merely because it fails to repeat. A timed-out batch can be rerun in full with the same seed under a fresh label; do not double count its partial results. The supplied launcher deliberately rejects duplicate labels, so a retry requires a separately retained declaration/command rather than editing the original plan or output.

With no fault and time remaining, root can declare another immutable plan with fresh seeds and labels. Do not change this original declaration or infer extra completed work from its preparation.

## Preparation verification actually run

All three JavaScript syntax checks passed. The read-only auditor was exercised on all 12 retained old self-play logs and reconstructed exactly 708 completed games and 97,576 searches; these are old regression-fixture counts, not new-tree results. The only regression adaptation changed the root/log and plan locations. Both new stage plans have 12 unique labels/seeds and the intended 8 ASAN/4 TSan groups. The copied C++ source is byte-identical to its pinned predecessor. No new engine, compiler or test execution was performed. Full commands and outputs are in `syntax-checks.txt` and `regression/`; code-path integration with a newly built driver remains for root.
