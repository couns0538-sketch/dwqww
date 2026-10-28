# port_b (R3-1): S32 datagen, S37 microbench, S04fix cold-init probe on the R3 stack — how to build and run

Branch `opus-r3-port-b` = `2432670b` + three `--no-ff` merges: `opus-sol-S32`, `opus-sol-S37`, `opus-sol-S04fix`.
All three features are off by default; the default engine is the stack's engine (byte-identical build).

## Build (PC box recipe, MSYS2 ucrt64 g++ 15.2)
```
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
nice -n 19 bash $T/build_pc.sh "$PWD" <out>/forge.exe                                             # default
FORGE_EXTRA_SRCS=src/datagen.cpp nice -n 19 bash $T/build_pc.sh "$PWD" <out>/forge_datagen.exe -DFORGE_DATAGEN=1
nice -n 19 bash $T/build_pc.sh "$PWD" <out>/forge_initonce.exe -DFORGE_ATTACKS_INIT_ONCE=1
nice -n 19 bash opus_round1/sol_S37/build_microbench_pc.sh "$PWD" <out>/mb_avx2.exe avx2              # or scalar
```
CMake: `forge_datagen`, `forge_datagen_tests` and `forge_nnue_microbench` are always built; `-DFORGE_DATAGEN=ON` adds
the datagen command to `forge` itself; `-DFORGE_ATTACKS_INIT_ONCE=ON` switches the attack-table init to
`std::call_once` and registers the cold-init tests (`ctest -L cold-init`: the cold first-Board test, TSan variant on
Linux GNU/Clang and native elsewhere, and the 1000-process probe `forge_sol_S04_cold_probe`).

## Run
- Datagen (S32): `forge_datagen.exe datagen --out <dir>/<prefix> --games N [--nodes 5000] [--seed S] [--text]` writes
  `<prefix>_NNN.pos/.hce/.info[/.txt]` + `<prefix>.games` (see `opus_round1/sol_S32/README.md`; `--convert` turns
  "FEN | score | result" text into `.pos/.hce`). Without the `datagen` argument the exe is the UCI engine.
- Microbench (S37): `forge_nnue_microbench --wac tools/nnue_microbench_wac300.epd [--positions 10000] [--repeats 15]
  [--check-only] [--json out.json]` (see `opus_round1/sol_S37/README.md`).
- Cold probe (S04fix): in a `-DFORGE_ATTACKS_INIT_ONCE=ON` CMake build, `ctest -L cold-init -V`
  (`FORGE_S04_COLD_PROBE_RUNS`, default 1000).

## Verification scripts (this folder)
- `step2_switch_builds.sh`: switch-ON PC builds, `uci_check.py --full`, the S32 determinism run reproduced against
  S32's recorded sha256, the S37 microbench build + check/timed runs. (Its RAM guard overwrote the datagen loop
  variable, so its datagen part is superseded by `step2b_datagen_determinism.sh`.)
- `step2b_datagen_determinism.sh`: the S32 determinism run into `det_a`/`det_b`, all runs compared file by file with
  S32's recorded sha256, then a reused prefix must be refused.
- `step3_cmake_ctest.sh`: full CMake build of all targets (JOBS=1) + full ctest + `check_known_failures.py` in the
  default, `FORGE_DATAGEN=ON` and `FORGE_ATTACKS_INIT_ONCE=ON` configurations, then `ctest -L cold-init -V`.
- `step3b_smp_flake_check.sh [N]`: runs `forge_smp_tests` N times alternately from the default and the ON build dir
  (the SmpExactNodes overshoot bound is load-sensitive on a busy PC at Idle priority).
Logs: `logs/` (copies of `F:\opus_scratch\r3\port_b\`); builds in `F:\opus_scratch\build\r3_port_b\`.
