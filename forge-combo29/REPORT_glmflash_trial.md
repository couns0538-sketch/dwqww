# REPORT glmflash trial (ThreadSanitizer check of the NNUE v3 path)

Run: 2026-11-15, started 09:04:41 UTC, report written ~09:11 UTC.
Branch: `cursor/glmflash-trial-9ab9` (created from commit `6b98f217`, tip of
`for-fable-and-opus/astra-0017-v3-path`; no other branch touched). The PR tooling on this
cloud VM requires the `cursor/` prefix, so the planned name `for-fable-and-opus/glmflash-trial`
was renamed to this one and the rename is recorded in START.md as the task allows.
Note: an earlier push of the same commits under the planned name `for-fable-and-opus/glmflash-trial`
still exists on the remote — repository rules decline branch deletion ("Cannot delete this branch"),
so it stays; both names point to identical commits and the canonical trial branch is the cursor one.
Machine: cloud VM, Ubuntu 24.04.5 LTS, kernel 6.12.113+, 4 vCPU Intel Xeon with
AVX-512 + BMI2 (so no FORGE_PORTABLE needed), glibc 2.39, 16 GB RAM.

## 1. Table: step | status | evidence files | result in one line

Evidence files live in `forge-combo29/tests_glmflash_trial/` unless noted.

| step | status | evidence files | result in one line |
|---|---|---|---|
| START.md first commit | done | `tests_glmflash_trial/START.md` | committed first, three lines (understood / first action / placement decision). |
| 1 optimised build + bench 11, bench 13, perft 5 | done | `step1_commands_and_output.txt`, `build-opt.log` | all three numbers match the PC exactly: 312866 nodes, 862329 nodes, 4865609 nodes. |
| 2 net file via `fable_nnue_v3.py random` | done | `NETFILE.md` | net written (6309096 bytes, sha256 e3ef99b7264d9c079f1c1e5ea8732bd576803e7bbfb2b00d138e53465dc8b375, script checksum d80a4532f35587f); file NOT committed (binary rule). |
| 3 500 seeded legal positions | done | `make_positions.py`, `positions.txt`, `positions_validation.txt` | 500 unique legal FENs, seed 20261115, plies 8–60, 0 game-over, engine accepts them (`readyok` on spot checks). |
| 4 TSan build + 2 runs (2 and 4 threads) | done | `build-tsan.log`, `tsan_run.py`, `logs/tsan_t2_raw.log`, `logs/tsan_t4_raw.log` | both runs searched all 500 positions to depth 8 in one engine process each, waited for every `bestmove`, exit code 0, net loaded, no `info string ERROR NNUE v3`. |
| 5 read + group TSan output | done (result: zero reports) | `analyze_tsan.py`, `logs/summary_t2.txt`, `logs/summary_t4.txt`, `logs/tsan_control_race.cpp`, `logs/tsan_control_race.out`, `logs/summary_control.txt` | 0 ThreadSanitizer reports in both logs, so there is nothing to attribute to `nnue_v3.cpp`, `Worker::static_evaluate_v3`, or elsewhere; toolchain proven working by a positive control. |
| extra (beyond the task, clearly labeled) | done | `logs/tsan_t4_hist7_raw.log`, `logs/summary_t4_hist7.txt`, `logs/extra_bench_with_net.txt` | extra 4-thread run with `TSAN_OPTIONS=history_size=7` (more sensitive, still no suppression file): 500/500, exit 0, 0 reports; extra `bench 11` on the optimised build with NNUEArch true: 91949 nodes (random net, expected to differ). |

### Key details

- Step 1 build: `cmake -S forge-combo29 -B /tmp/glmflash/build-opt -DCMAKE_CXX_COMPILER=/usr/bin/g++ -DCMAKE_CXX_FLAGS="-DFORGE_NNUE_V3=1"`, then `cmake --build build-opt -j4` (exit 0). FORGE_MARCH stayed at the CMake default `x86-64-v4`; no CMakeLists.txt or source edit.
  - Compiler: `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0` (chosen explicitly: the machine's `/usr/bin/c++` is clang 18.1.3, which fails to link `-lstdc++` here — environment issue, reported as is; the CMakeLists allows "GCC or Clang").
  - C++ standard library: GNU libstdc++ — headers `libstdc++-13-dev 13.3.0-6ubuntu2~24.04.1`, runtime `libstdc++.so.6.0.33` (package `libstdc++6 14.2.0-4ubuntu2~24.04.1`), glibc 2.39.
  - Decision recorded: the task's `perft 5` prints nothing in this engine; its UCI grammar is `go perft <depth>` (uci.cpp reads `perft` only as the first word after `go`). I used `go perft 5` and got the PC number, which is the confirmation that this is the intended command.
- Step 2: exact command in `NETFILE.md`; run with `python3 -I` from `/tmp/glmflash/net` (outside the repository). The generating script was extracted from branch `fable/standalone-h512-20261111` (`git fetch origin fable/standalone-h512-20261111`, the only fetch besides my own push).
- Step 3: "game is over" judged by python-chess 1.11.2 `is_game_over()` (checkmate / stalemate / insufficient material / dead position; 50-move and repetition cannot trigger within 60 plies). python-chess was not preinstalled; installed during the trial with `pip3 install python-chess` (recorded in the script header).
- Step 4 build: manual g++ (exact command in `build-tsan.log`): `-std=c++20 -O2 -g -fsanitize=thread -march=x86-64-v4 -ffp-contract=off -fno-fast-math` plus the same defines CMake uses (`NDEBUG`, `FORGE_NNUE_HIDDEN=256`, `FORGE_NNUE_WEIGHTS="src/nnue_weights.inc"`, `FORGE_EXPOSE_TUNABLES=1`, `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1`, `FORGE_SPD_PREFETCH_EARLY=1`, `FORGE_SPD_SLIDER_PEXT=1`, `FORGE_SPD_NNUE_ZMM=1`, `FORGE_NNUE_V3=1`), `-DFORGE_NNUE_V3_VERIFY` NOT defined.
  - Decision recorded: a CMake-driven second build could not honor `-O1/-O2` because CMakeLists.txt hardcodes `-O3` in `target_compile_options`, which wins over anything passed via `CMAKE_CXX_FLAGS`; changing CMakeLists.txt is forbidden, so the TSan build drives g++ directly with the same defines.
- Step 4 runs (driver `tsan_run.py`; engine stdout teed verbatim, TSan stderr appended to the same raw log; commands sent only after the previous `bestmove`):
  - Threads 2: 500/500 positions, `info depth 8` in every search, net load line `info string NNUE v3: loaded v3 ... checksum d80a4532f35587f ... kernel avx512`, exit code 0, 51.9 s wall.
  - Threads 4: 500/500 positions, same load line, exit code 0, 53.4 s wall.
  - No `info string ERROR NNUE v3` in any run. `TSAN_OPTIONS` unset for both prescribed runs (defaults only, no suppression file).
- Step 5: both raw logs contain 0 `WARNING: ThreadSanitizer` lines and 0 report groups. Both logs are below 1 MB (487742 and 490483 bytes), so they are committed in full (the >1 MB trimming rule did not apply).
  - Trustworthiness of the null result, as evidence: (a) the TSan binary carries `__tsan` instrumentation symbols (21 in `nm`); (b) a positive control program with a deliberate data race (`logs/tsan_control_race.cpp`), compiled with the same flags on this machine, produces `WARNING: ThreadSanitizer: data race` and exit code 66 (`logs/tsan_control_race.out`); (c) the grouping analyzer was validated against that control report (parses 1 warning into 1 group with correct stacks).
- The engine source tree was not modified: `git diff 6b98f217 -- forge-combo29/src forge-combo29/include forge-combo29/CMakeLists.txt` is empty; only new files under `tests_glmflash_trial/` plus this report were added.

## 2. Minutes used per step (from shell timestamps) and in total

| part | minutes |
|---|---|
| setup, branch, START.md | ~1 |
| step 1 (build + bench/perft) | ~2 |
| step 2 (net) | ~1 |
| step 3 (positions) | ~2 |
| step 4 (TSan build, driver fix + smoke, two runs) | ~4 |
| step 5 (analysis, control, artifact copies) | ~3 |
| report + commit/push/PR | ~4 |
| **total** | **~17** |

(Budget was 1 hour with a 50-minute stop mark; well inside it.)

## 3. What I did not do

- Changed no engine source file, no header, and not CMakeLists.txt (nothing under `forge-combo29/src`, `forge-combo29/include` was touched).
- Did not commit the net file, any engine binary, or any non-text artifact.
- Did not use a TSan suppression file; left `TSAN_OPTIONS` unset in the two prescribed runs (the extra run only raised `history_size`, which is a sensitivity knob, not a suppression).
- Did not fetch or look at any branch other than `fable/standalone-h512-20261111` (needed for the net script) besides my own push of my branch.
- Did not read `handoff/fable-opus-combo29-all-20261114` or `FABLE_TO_glmflash_1.md` (the prompt says it appears after the trial).
- Did not judge or classify any race as harmless (none occurred; nothing to judge).
- Did not build with `FORGE_NNUE_V3_VERIFY` (explicitly excluded) and did not test depths other than 8 or thread counts other than 2/4 (not requested).
- Did not try to make the machine's clang link (environment packaging issue); used g++ for both builds instead.

## 4. What I am not sure about

- Zero reports means "ThreadSanitizer found nothing in the schedules that actually executed", not "the engine is provably race-free"; TSan can only see races whose unsynchronized concurrent accesses actually happen at runtime. The extra `history_size=7` run reduces (not removes) this limitation.
- TSan by default prints each distinct race once per process, so a "how often it occurred" count could only reflect what the tool printed; with zero reports this is moot here.
- I assume `go perft 5` is what the task's "perft 5" meant (see decision above); plain `perft 5` is silently accepted and prints nothing, which I report rather than paper over.
- "Game is over" was judged with python-chess's rules; the engine's own draw/adjudication rules may differ slightly, though every position was accepted and searched.
- I cannot verify the exact flags the PC used; my reproducibility evidence is that all three step-1 numbers match the PC exactly on this compiler/flags.
- Whether the machine's clang would link with extra flags was not investigated (out of scope; g++ worked and is allowed by the CMakeLists header).

## 5. Model name and version

The agent persona for this job is "glmflash". The model powering this agent, as I know it from my runtime information: **GLM 5.3 Flash** (I cannot independently verify the deployment build beyond that statement).
