# R3-1 port C: S-A2 NnueInt16 + S-A4 H512 on the R3 stack

Branch `opus-r3-port-c` = `2432670b` (opus-r3-cifix = opus-r3-stack `467a59b3` + CMake test fix)
+ merge of `origin/opus-sol-SA2` (`1c1a44ed`) + merge of `origin/opus-sol-SA4` (`2e3a36f2`) + this folder.
The main session merges this branch into `opus-r3-stack`.

## What the stack gets
| feature | how to switch it on | default |
|---|---|---|
| S-A2 NnueInt16: integer inference with the compiled-in net's int16 weights, int32 accumulators (UCI `NnueInt16`, check) | build switch `FORGE_NNUE_INT16` (CMake `-DFORGE_NNUE_INT16=ON`, PC recipe `-DFORGE_NNUE_INT16=1`), then `setoption name NnueInt16 value true` | switch off: the option does not exist and the exe is the previous stack exe (PE timestamp aside) |
| S-A2 trainer `--weight-clip` | `opus_round1/sol_SA2/trainer_v3c_clip.py` (renamed copies only, see its README) | off |
| S-A4 another net include file, e.g. H512 | `-DFORGE_NNUE_WEIGHTS='"<net.inc>"'` (CMake `-DFORGE_NNUE_WEIGHTS_FILE=<net.inc>`) plus `-UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512` | unset: `src/nnue_weights.inc` (H256 lock net) |

All combine with `FORGE_NNUE_O2` (O2 accumulator kernels). NnueInt16 applies to the compiled-in network only:
a v2 net (`NNUEFile` + `NNUEKingBuckets` ...) keeps its float path, as with S41 NetScale.

## Build
```sh
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
nice -n 19 bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/<job>/forge.exe                      # default
nice -n 19 bash $T/build_pc.sh "$PWD" /f/.../forge_int16.exe -DFORGE_NNUE_INT16=1 [-DFORGE_NNUE_O2=1]
nice -n 19 bash $T/build_pc.sh "$PWD" /f/.../forge_h512.exe -UFORGE_NNUE_HIDDEN -DFORGE_NNUE_HIDDEN=512 \
    '-DFORGE_NNUE_WEIGHTS="F:/opus_scratch/sol_SA4/nets/h512_widened_lock_split.inc"' -DFORGE_NNUE_INT16=1
JOBS=1 nice -n 19 bash $T/cmake_build.sh "$PWD" /f/.../cmake [-DFORGE_NNUE_O2=ON] [-DFORGE_NNUE_INT16=ON]
```

## CMake / CTest (every configuration)
- `forge_nnue_int16_tests`, `forge_nnue_int16_scalar_tests` (`-mno-avx2`), `forge_nnue_h512_tests` (synthetic H512
  net from `forge_nnue_gen_net`): SA2's unit test; each target compiles `src/nnue.cpp`, `board.cpp`, `bitboard.cpp`
  itself with `FORGE_NNUE_INT16=1` and the configuration's `FORGE_NNUE_O2` state.
- `nnue_int16_uci_regression`: SA2's UCI regression on `forge_int16` (= the core's sources and settings plus the
  switch; in a `-DFORGE_NNUE_INT16=ON` configuration on `forge` itself).
- `nnue_int16_uci_absent` (switch-off configurations): `forge` does not list NnueInt16, a setoption for it changes
  nothing, bench stays at the lock pins.

## Checks in this folder
- `bench_expect.py <exe> [--opt N=v ...] --expect d=nodes,... [--need "info string text"]`: bench pins + the info
  lines that prove which net / mode was active.
- `mutation_check_port_c.py <worktree> <new out dir> [--o2]`: SA2's five engine mutants plus a port mutant, built
  with the switch (and O2); each must make `tests/nnue_int16_tests.cpp` fail, the control must pass.
- `tools/`: the merge resolvers and the run scripts that produced `logs/` (paths are the PC's; builds go to
  `F:\opus_scratch\build\r3_port_c`, dumps and nets to `F:\opus_scratch\r3\port_c`).
