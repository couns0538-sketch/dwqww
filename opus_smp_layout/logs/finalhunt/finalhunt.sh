#!/usr/bin/env bash
# Final 30-minute bug hunt, run part (opus2, candidate 30119af = 89cddf7 + two comment lines). Everything pinned to
# CPUs 12-15 at Idle by the tools / run_pinned.ps1. Outputs in D:\forge_jobs_20261107\opus2\out\finalhunt. Cooperative
# stop: D:/forge_jobs_20261107/opus2/out/finalhunt/STOP. Never ends a process, never deletes.
set -u
cd /d/forge_jobs_20261107/opus2/out || exit 1
T='D:\forge_jobs_20261107\opus2\repo\opus_smp_layout\tools'
FH='D:\forge_jobs_20261107\opus2\out\finalhunt'
G='D:\forge_jobs_20261107\opus2\out\exe\forge_smpgate_2940fb05.exe'
RP="$T\\run_pinned.ps1"
GXX='C:\msys64\ucrt64\bin\g++.exe'
R='D:\forge_jobs_20261107\opus2\repo'
ps1() { MSYS_NO_PATHCONV=1 powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$@"; }
stop_check() { if [ -e finalhunt/STOP ]; then echo "STOP seen before: $1"; exit 0; fi; }
now() { curl -sI https://api.github.com/zen | grep -i '^date:' | tr -d '\r'; }
echo "finalhunt start $(now)"
# 1. the comment-only commit must give the same gate exe
stop_check kit
ps1 "$T\\kit_build.ps1" -SrcDir 'D:\forge_jobs_20261107\opus2\out\src\j1' -Tag j1c -CheckOpt 'TtLockless=true' > logs/kit_j1c.log 2>&1
echo "kit j1c exit=$? | $(grep -o 'RESULT [A-Z]*' logs/kit_j1c.log | tail -1) | sha256 $(sha256sum k/j1c/src_copy/forge_ltopgo_j1c.exe | cut -c1-64)"
# 2. preprocessed code of the enc5 and the comment-fix gate trees
stop_check pp
ps1 "$T\\pp_identity.ps1" -TreeA 'D:\forge_jobs_20261107\opus2\out\src\h1' -TreeB 'D:\forge_jobs_20261107\opus2\out\src\j1' -OutDir "$FH\\pp_h1_j1" > finalhunt/pp_h1_j1.txt 2>&1
echo "pp h1 vs j1: $(tail -1 finalhunt/pp_h1_j1.txt)"
# 3-5. adversarial UCI cases, setoption during search, special modes (gate 2940fb05)
stop_check uci
ps1 'D:\forge_jobs_20261107\opus2\out\bughunt\bughunt_extra.ps1' -Exe "$G" -OutDir "$FH" > finalhunt/bughunt_extra.run.txt 2>&1; echo "bughunt_extra exit=$?"
ps1 'D:\forge_jobs_20261107\opus2\out\bughunt\setoption_during_search.ps1' -Exe "$G" -OutDir "$FH" > finalhunt/setoption_during_search.run.txt 2>&1; echo "setoption_during_search exit=$?"
ps1 "$FH\\special_modes5.ps1" -OutDir "$FH" > finalhunt/special_modes.run.txt 2>&1; echo "special_modes exit=$?"
# 6. Threads 8 lockless stress (oversubscribed smoke), 1500 cycles, seed 99
stop_check stress
ps1 "$T\\uci_lifecycle_stress.ps1" -Exe "$G" -Tag fh_T8_ON -OutDir "$FH" -Options 'TtLockless=true' -ThreadSet '8' -Cycles 1500 -Seed 99 > finalhunt/fh_T8_ON.run.txt 2>&1
echo "T8 stress: $(tail -1 finalhunt/fh_T8_ON.run.txt)"
# 7. 6 s fixture, -O3 -DNDEBUG test build of the candidate tree
stop_check fixture
FLAGS='-std=c++20 -O3 -DNDEBUG -DFORGE_SMP_LAYOUT=1 -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Wall -Wextra -Iinclude'
CORE='src/bitboard.cpp src/board.cpp src/book.cpp src/eval.cpp src/eval_params.cpp src/nnue.cpp src/search.cpp'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$RP" -Exe "$GXX" -WorkDir "$R" -ArgLine "$FLAGS tests/tt_lockless_tests.cpp $CORE -static -o D:/forge_jobs_20261107/opus2/out/finalhunt/fh_tt_lockless_tests.exe" -Out "$FH\\fh_tt_lockless_build.log" -TimeoutSec 1800
echo "build fixture exit=$?"
export FORGE_TT_LOCKLESS_SECONDS=6
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$RP" -Exe "$FH\\fh_tt_lockless_tests.exe" -Out "$FH\\fh_tt_lockless_6s.log" -TimeoutSec 1800
echo "fixture 6 s exit=$? | $(tail -1 finalhunt/fh_tt_lockless_6s.log)"
unset FORGE_TT_LOCKLESS_SECONDS
# 8. the other trial_w6 TT configuration: FORGE_SPD_TT_NOTLS=0 + FORGE_SMP_LAYOUT=1, plain -O2 engine, pins both modes
stop_check notls0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$RP" -Exe "$GXX" -WorkDir "$R" -ArgLine "-std=c++20 -O2 -DNDEBUG -DFORGE_SMP_LAYOUT=1 -DFORGE_SPD_TT_NOTLS=0 -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread -Wall -Wextra -Iinclude $CORE src/uci.cpp -static -o D:/forge_jobs_20261107/opus2/out/finalhunt/fh_notls0.exe" -Out "$FH\\fh_notls0_build.log" -TimeoutSec 1800
echo "build notls0 exit=$? warnings=$(grep -c 'warning' finalhunt/fh_notls0_build.log.stderr.txt)"
ps1 "$T\\identity_check.ps1" -Exe "$FH\\fh_notls0.exe" -Tag fh_notls0_false -Mode pins -OutDir "$FH" > finalhunt/fh_notls0_false.run.txt 2>&1 &
ps1 "$T\\identity_check.ps1" -Exe "$FH\\fh_notls0.exe" -Tag fh_notls0_true -Mode pins -OutDir "$FH" -Options 'TtLockless=true' > finalhunt/fh_notls0_true.run.txt 2>&1 &
wait
echo "notls0 pins false: $(cut -c1-80 finalhunt/fh_notls0_false.run.txt)"
echo "notls0 pins true:  $(cut -c1-80 finalhunt/fh_notls0_true.run.txt)"
echo "finalhunt end $(now)"
echo FINALHUNT_DONE
