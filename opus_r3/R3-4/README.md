# R3-4: SPSA tuning tool and the 20 advertised search constants

The tool and its documentation live in `tools/spsa/` (see `tools/spsa/README.md`: how to run a real session,
the example config for the 20 parameters, suggested TC and game counts, the table of the 20 with
default/min/max/c_end/r_end). This folder holds the job's evidence tools and logs.

| file | what |
|---|---|
| `REPORT.md` | results, acceptance table, findings, open items (added from the agent's hand-back) |
| `IDEA_SOURCE.md` | sources |
| `run_cmake_ctest.sh` | the full local CMake build (all targets, JOBS=1) + ctest + known-failure check used before the push |
| `codegen_r3_4.sh` | machine code of all eight search instances, both qsearch instances, the root search and other hot functions, before vs after |
| `r3_4_sensitivity_scan.py` | bench-node change per candidate constant for a ±10% step (one engine process) |
| `r3_4_mutation_check.py` | planted bugs in the tool and in the engine source the tests read; each must fail the tests |
| `dryrun_nodes.json` | the nodes-limited smoke session used for the priority samples |
| `logs/` | build, identity, codegen, NPS, sensitivity, dry runs, tests, CMake/CTest, CI |

## Reproduce (PC; every command under `nice -n 19`, outputs under `F:\opus_scratch`)
```
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
FC=C:/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe
LA=D:/grok-pc-data/dwqww/.claude/worktrees/b/pkg/forge_LOCK_AL1_s198_FULL_20261026_1039
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
# engine (box recipe) and identity
bash $T/build_pc.sh "$PWD" /f/opus_scratch/build/r3_R3-4/forge_r3_4.exe
$PY -I -B $LA/2_build/uci_check.py F:/opus_scratch/build/r3_R3-4/forge_r3_4.exe --full          # ALL OK
# codegen and NPS against the base (base exe built from `git archive <base> src include`)
PATH=/c/msys64/ucrt64/bin:$PATH bash opus_r3/R3-4/codegen_r3_4.sh <base.exe> <new.exe> <out dir>
$PY -I -B opus_round1/sol_S29/nps_ab.py <base.exe> <new.exe> 10 16 20
# sensitivity scan
$PY -I -B opus_r3/R3-4/r3_4_sensitivity_scan.py <new.exe> --depth 13 --json <out.json>
# tests (30), with the engine check, and the planted-bug check
$PY -I -B tools/spsa/test_opus_spsa.py --root <dir> --engine <new.exe>
$PY -I -B opus_r3/R3-4/r3_4_mutation_check.py "$PWD" <new dir>
# dry run: 2 iterations, stop, restart (resumes from state.json), status
$PY -I -B tools/spsa/opus_spsa.py --config tools/spsa/opus_spsa_forge20.json --workdir <W> --dry-run --engine <new.exe> --fastchess $FC --stop-after 2
$PY -I -B tools/spsa/opus_spsa.py --config tools/spsa/opus_spsa_forge20.json --workdir <W> --dry-run --engine <new.exe> --fastchess $FC
$PY -I -B tools/spsa/opus_spsa.py --workdir <W> --dry-run --status
```
