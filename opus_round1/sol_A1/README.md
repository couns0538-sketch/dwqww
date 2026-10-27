# opus_round1/sol_A1 — Astra A1: correction-history / history rework (UCI `HistRework`)

New UCI option `HistRework` (spin 0..3, default 0 = the AL1 s198 lock search). Levels 1..3:
- a butterfly-history twin keyed by "from/to square attacked by a lesser enemy piece", blended into
  `quiet_history` (50 / 75 / 100 %);
- a pawn-structure x non-pawn-material correction table with a gravity update (weight 50 / 75 / 100).

Design, overflow proof and tuning ranges: `forge_astra_A1_design_20261027.md`. Gate plan:
`forge_astra_A1_sprt_plan_20261027.md`. Patch vs the lock tree: `forge_astra_A1_corrhist_20261027.patch`.
UNPROVEN: no gate was run, no Elo or speed claim.

## Files
| path | content |
|---|---|
| `forge_astra_A1_corrhist_20261027.patch` | `git diff 1aa5d20 <engine commit> -- src include tests CMakeLists.txt` (engine + test) |
| `forge_astra_A1_design_20261027.md` | idea, IDEA_SOURCE summary, why not a resubmission, overflow proof, tuning ranges |
| `forge_astra_A1_sprt_plan_20261027.md` | which value to gate first at 10+0.1 [0,10] cap 1500, the longer-TC confirm |
| `IDEA_SOURCE.md` | sources and in-house history read |
| `tools/bench_sweep.py` | ON/OFF bench node sweep (one fresh engine per value), blowup flag at 1.5x |
| `tools/build_test.sh` | direct g++ build of `forge_hist_rework_tests` |
| `tools/mutation_check.py` | planted-bug check: baseline passes, 12 mutants must fail the test |
| `tools/ubsan_local.sh` | MinGW UBSan (trap mode) engine + test build, bench at `HistRework=3` with tunables at max |
| `tsan_extra.sh` + `tools/smp_smoke.py` | CI TSan hook: HistRework 0/3 with Threads 1/1/4 (legal bestmoves, Threads-1 determinism) |
| `logs/` | PC step logs (build, identity, sweeps, ctest, mutation, UBSan, warnings, patch apply) |
| `logs/ci/run40515121020_opus-ci/` | GitHub CI artifacts of the engine commit: release identity + ctest, ASan+UBSan ctest, TSan ctest + hook |

Engine sources touched:
- `include/forge/hist_rework.hpp` (new, the pure helpers);
- `include/forge/search.hpp` (table type and Worker members);
- `src/search.cpp` (guarded hooks);
- `src/uci.cpp` (option);
- `tests/hist_rework_tests.cpp` (new) and `CMakeLists.txt` (test target).

## How to reproduce (PC, Git Bash; every command at Idle priority)
```
W=/f/opus_scratch/worktrees/opus_sol_a1; T=D:/grok-pc-data/dwqww/.claude/worktrees/b/tools
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
# 1. box-recipe build (prints sha256 and the FMA count, must be 0)
nice -n 19 bash $T/build_pc.sh $W /f/opus_scratch/build/A1/forge_a1.exe
# 2. OFF identity: must print ALL OK
nice -n 19 $PY -I -B $LA/2_build/uci_check.py /f/opus_scratch/build/A1/forge_a1.exe --full
# 3. ON sweep (d11/13/16/20/22, values 0..3)
nice -n 19 $PY -I -B $W/opus_round1/sol_A1/tools/bench_sweep.py /f/opus_scratch/build/A1/forge_a1.exe
# 4. CMake + CTest (only the 4 known forge_tests lines may fail)
JOBS=1 nice -n 19 bash $T/cmake_build.sh $W /f/opus_scratch/build/A1/cmake
#    then, with PATH as in cmake_build.sh: cd /f/opus_scratch/build/A1/cmake && ctest --output-on-failure --timeout 900
# 5. planted bugs, local UBSan
nice -n 19 $PY -I -B $W/opus_round1/sol_A1/tools/mutation_check.py $W /f/opus_scratch/build/A1/mutation
nice -n 19 bash $W/opus_round1/sol_A1/tools/ubsan_local.sh $W /f/opus_scratch/build/A1/ubsan $PY /f/opus_scratch/sol_A1/ubsan_logs
```
For a gate, set the option on the candidate only: `setoption name HistRework value 2` (fastchess
`option.HistRework=2`). `uci` lists `option name HistRework type spin default 0 min 0 max 3`.
