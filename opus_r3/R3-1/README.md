# R3-1 integration stack — how to use and re-check it

Branch `opus-r3-stack` = `d4f4312` + O3 + every passed O/C/opus-sol feature, each behind its own option, all OFF by
default (REPORT.md lists them). Build exactly like the lock:

    nice -n 19 bash D:/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh "$PWD" <out.exe> [-DSWITCH=1 ...]

Build switches (default off): `FORGE_NNUE_O2`, `FORGE_NOZERO_MOVE_BUFFERS`, `FORGE_S13_TT_CHILD_PREFETCH` (+ UCI
`TtChildPrefetch`), `FORGE_SPEEDSTACK`, `FORGE_NNUE_LAZY_ACC` (+ UCI `NnueLazyAcc`), `FORGE_PROF` (needs
`FORGE_EXTRA_SRCS=src/profile.cpp` for build_pc.sh; UCI `Profile`, command `bench_prof`). CMake: the same names as
`-D<NAME>=ON`.

Checks (tools/ in this folder, scratch logs under `F:\opus_scratch\r3\logs`):
- identity: `uci_check.py <exe> --full` (lock archive `2_build/uci_check.py`) -> ALL OK;
- options with recorded branch ON pins: `tools/nnue_pins_check.sh <exe>` (NNUE smoke nets) and
  `tools/branch_crosscheck.sh <exe>` (builds the branch exes from their worktrees and compares bench nodes);
- `tools/bench_opts.py <exe> --opt Name=value ... --depths 11,13,16` for any option set;
- CTest exactly as CI: `tools/run_ctest.sh <cmake build dir> <log>` (known-failure check included).

Merge helpers used to build the stack: `tools/union_conflicts.py` (union of two-sided additions),
`tools/uci_ours_plus.py` (keeps the stack's uci.cpp and re-inserts a branch's option/handler runs),
`tools/port_search_hunks.py` (places single-file search.cpp hunks in the O3 module that holds their exact context,
applies them with `patch -F0`), `tools/check_ifdef_blocks.py` (balanced #if checks for the `diff -D` O2 switch).
