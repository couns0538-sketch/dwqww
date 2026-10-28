# S04fix — cold first-Board init: probe as a ctest target, test TIMEOUTs, ON build with MinGW

Branch `opus-sol-S04fix` = AL1 lock tree `d4f4312` + CI baseline `0d99f02` + Sol's S04 v2 patch (code parts,
verbatim, commit "Port Sol's S04 v2 patch") + the fix-ups S04-1 and S04-2.

`FORGE_ATTACKS_INIT_ONCE` (CMake option, default OFF; box recipe: `-DFORGE_ATTACKS_INIT_ONCE=1`) wraps the
existing attack-table initialization in `std::call_once` (Sol's change). OFF compiles the original code; the OFF
exe is the AL1 lock exe byte for byte apart from the PE timestamp/checksum.

## What the fix-ups add (only when the option is ON)

| Test | What it runs | TIMEOUT | Labels |
|---|---|---|---|
| `forge_sol_S04_cold_tsan_test_20261025` (Linux GNU/Clang) | Sol's cold test under ThreadSanitizer: 8 threads construct the first Board behind a barrier, check perft/FEN | 120 s | cold-init, tsan |
| `forge_sol_S04_cold_test_native` (MinGW, other toolchains) | the same source without TSan (MinGW has no TSan) | 120 s | cold-init, native |
| `forge_sol_S04_cold_probe` | the cold test in 1000 fresh processes (`tests/forge_sol_S04_cold_probe.cmake`, a CMake-script port of Sol's `forge_sol_S04_cold_runs_20261025.py`); stops at the first failing process and prints its exit code and streams | 3 s x runs + 120 s (3120 s) | cold-init, cold-probe, + tsan/native |

The TIMEOUT properties override ctest's `--timeout` default (CI passes `--timeout 600`, which would cut the TSan
probe off). `FORGE_S04_COLD_PROBE_RUNS` (cache variable, default 1000) sets the probe size.

## Run (PC, MinGW g++ 15.2, box flags; tools from `D:/grok-pc-data/dwqww/.claude/worktrees/b/tools`)

```sh
JOBS=1 nice -n 19 bash $T/cmake_build.sh "$PWD" /f/opus_scratch/build/sol_S04fix/cmake_on -DFORGE_ATTACKS_INIT_ONCE=ON
cd /f/opus_scratch/build/sol_S04fix/cmake_on && ctest -L cold-init --output-on-failure -V   # cold test + 1000-process probe
ctest --output-on-failure --timeout 900                                                   # full suite (4 known forge_tests lines)
nice -n 19 bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/sol_S04fix/forge_s04fix_ON.exe -DFORGE_ATTACKS_INIT_ONCE=1
```

Probe by hand on any cold-test exe: `cmake -DEXE=<exe> -DRUNS=1000 -P tests/forge_sol_S04_cold_probe.cmake`.

## Linux (CI)

`.github/workflows/opus-sol-s04fix-ci.yml` runs `opus_round1/sol_S04fix/ci_s04fix.sh release|asan|tsan` on every
code push to this branch: OFF build vs lock (binary and disassembly), ON identity (bench/perft pins), full ctest
with the known-failure check in Release, ASan+UBSan and TSan (each includes the TSan cold test and the
1000-process TSan probe), and a RED control in the TSan job (the cold test compiled with the option OFF must fail
under TSan). `opus-ci.yml` covers the default OFF build.

## Files

- `ci_s04fix.sh` — Linux CI driver (above).
- `logs/` — PC evidence: build, ctest, identity, OFF-vs-lock `cmp`, RED (planted bug) logs, toolchain.
- `forge_sol_S04_v3.patch` — the whole change vs the AL1 base (Sol's v2 code parts + the fix-ups), for review.
- `IDEA_SOURCE.md`, `REPORT.md`, `FILES.txt`, `SHA256SUMS`.
