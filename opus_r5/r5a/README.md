# opus_r5/r5a — gate-ready singles (how to run)

Branch `opus-r5a-singles` (base `origin/forge-bundle-int` b7c17722). Results and evidence: `REPORT.md`; gate pack:
`GATE_SPECS.md` + `gate_specs.json`; idea sources: `IDEA_SOURCE.md`. All commands from the worktree root, Git Bash,
BelowNormal, at most 3 threads in total. `PY` = `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe`.

| step | command | output |
|---|---|---|
| build (PC lock flags, 3 compiles) | `bash opus_r5/r5a/tools/build_r5a.sh "$PWD" /f/opus_scratch/r5/r5a/exe/<name>.exe` | exe, sha256, FMA count |
| identity | `$PY -I -B <lock>/2_build/uci_check.py <exe> --full` | ALL OK = bench d11-d22 + perft pins |
| M1 option benches | `$PY -I -B opus_r5/r5a/tools/m1_option_bench.py <exe> --config CorrMargins=1:0 ...` | ON benches, go depth 10, same-process restore |
| M2/M5 unit + UCI tests | CMake target `forge_r5a_options_tests`, `ctest -R forge_r5a_options_tests` (or run it with the forge exe path) | ALL OK |
| CTest on 3 CPUs | `cmd //c opus_r5/r5a/tools/run_ctest_3cpu.cmd <build dir> <log>` | all tests but forge_tests (4 threads; CI runs it) |
| M3 smoke, one option | `$PY -I -B opus_r5/r5a/smoke.py <exe> --name corrext1 --opt CorrExt=1 --out opus_r5/r5a/smoke/corrext1` | games.pgn, summary.json, exit 0 = PASS |
| M3 smoke, all | `bash opus_r5/r5a/tools/smoke_all.sh <exe> "$PWD" corrext1=CorrExt:1 ...` (PAUSE / STOP_ALL files in `/f/opus_scratch/r5/r5a/smoke_ctl`) | one folder per config |
| M3 table | `$PY -I -B opus_r5/r5a/tools/smoke_table.py opus_r5/r5a` | smoke/SMOKE_RESULTS.md + REPORT block |
| M4 gate pack | `$PY -I -B opus_r5/r5a/tools/make_gate_specs.py opus_r5/r5a` | GATE_SPECS.md, gate_specs.json |
| M5 checks | `bash opus_r5/r5a/tools/m5_verify.sh "$PWD"` (while the smoke is paused) | build, identity, scale/threshold benches, CTest |
| CPU temperature | `bash opus_r5/r5a/tools/cpu_temp.sh` | HWiNFO "CPU IOD Hotspot" (rule sensor) + Tctl/Tdie |

Never run Sol's lock / PGO / delivery scripts from here; this folder writes only to itself and F:\opus_scratch\r5.
