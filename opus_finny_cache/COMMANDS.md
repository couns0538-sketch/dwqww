# opus_finny_cache — COMMANDS (EXECUTED vs PREPARED-ONLY)

Every command runs from Git Bash. The PS 5.1 tools pin themselves to CPUs 12-15 at Idle and read both settings back.

## EXECUTED (2026-11-09, Vienna 19:03-19:07; logs in `logs/`)
```
# instrumented scratch copy of parent P (measurement only, never a candidate)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'D:\forge_jobs_20261107\opus2\out\scratch\rc_make.ps1'
# plain lock-line build of the scratch copy (pinned, Idle)
cd D:/forge_jobs_20261107/opus2/out/scratch/rc/src && MSYS_NO_PATHCONV=1 powershell.exe -NoProfile -ExecutionPolicy Bypass -File <tools>/run_pinned.ps1 \
  -Exe 'C:\msys64\ucrt64\bin\g++.exe' -WorkDir 'D:\forge_jobs_20261107\opus2\out\scratch\rc\src' \
  -ArgLine '-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -static -pthread -Iinclude src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp src/uci.cpp -o ../rc.exe' \
  -Out 'D:\forge_jobs_20261107\opus2\out\scratch\rc\build.log' -TimeoutSec 900
# counts: bench 16; 300 FENs go depth 13 (ucinewgame each); 20 FENs Threads 4 go movetime 500
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'D:\forge_jobs_20261107\opus2\out\scratch\rc_measure.ps1'
```
Parent P kit builds (pc1, pc2 = 4181a589…): `tools/kit_build.ps1 -SrcDir <P export> -Tag p1|p2`; summaries in `logs/parent/`.

## PREPARED-ONLY (for an owner who implements SPEC §3 on a king-dependent network; NOT run here)
```
# 1 exactness gate first: cached vs fresh refresh, every accumulator value, 12k FENs + long make/unmake walks
#   (a tool linked to the engine core; the v3 branch's forge_nnue_v3_tests walk is the model)
# 2 compile-time 0 build = parent byte for byte, both clean builds:
tools/kit_build.ps1 -SrcDir <tip export, FORGE_NNUE_FINNY 0> -Tag f0a ; ... -Tag f0b
# 3 gate build (switch flipped to 1 in a source copy), ON identity in the kit:
tools/kit_build.ps1 -SrcDir <tip export, FORGE_NNUE_FINNY 1> -Tag f1a -CheckOpt 'NnueFinnyCache=true' ; ... -Tag f1b
# 4 full 12k cold identity net on and off, option OFF and ON, and warm identity (the SMP pack's tools):
identity_check.ps1 -Exe <gate exe> -Tag gateON_neton -Mode cold -OutDir <dir> -Options 'NnueFinnyCache=true'
identity_check.ps1 -Exe <gate exe> -Tag gateON_warm  -Mode warm -OutDir <dir> -Options 'NnueFinnyCache=true' -Count 1000
```
