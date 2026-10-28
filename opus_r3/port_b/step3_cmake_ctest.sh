#!/usr/bin/env bash
# port_b step 3: full CMake build of all targets (JOBS=1) + full ctest + known-failure check, in three
# configurations: default, FORGE_DATAGEN=ON (S32), FORGE_ATTACKS_INIT_ONCE=ON (S04fix; + the cold-init tests).
# S37 has no CMake option (forge_nnue_microbench is always built; its CTest runs in every configuration).
# Sequential, nice 19, free RAM >= 6 GB before every heavy step. Test temp files go to F:, not C:.
set -u
W=/f/opus_scratch/worktrees/opus_r3_port_b
T=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
B=/f/opus_scratch/build/r3_port_b
L=/f/opus_scratch/r3/port_b
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PATH="/c/msys64/ucrt64/bin:$VSCM/CMake/bin:$VSCM/Ninja:$PATH"
mkdir -p $L/tmp
export TMP='F:\opus_scratch\r3\port_b\tmp' TEMP='F:\opus_scratch\r3\port_b\tmp' TMPDIR='F:\opus_scratch\r3\port_b\tmp'
ram() { powershell -NoProfile -Command "[math]::Floor((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB)"; }
waitram() { local gb; while :; do gb=$(ram | tr -d '\r'); [ "${gb:-0}" -ge 6 ] && { echo "free RAM ${gb} GB"; break; }; echo "free RAM ${gb} GB < 6, waiting"; sleep 60; done; }
step() { echo "== $(date '+%F %T') $*"; }

cd "$W"
echo "head $(git rev-parse HEAD)"

run_cfg() {  # <name> [extra cmake args...]
  local name=$1; shift
  local BD=$B/$name
  waitram
  step "cmake build $name (JOBS=1) $*"
  JOBS=1 nice -n 19 bash $T/cmake_build.sh "$W" "$BD" "$@" > $L/cmake_$name.log 2>&1
  local rc=$?
  echo "build rc=$rc"; cat $L/cmake_$name.log
  cp "$BD.configure.log" $L/$name.configure.log; cp "$BD.build.log" $L/$name.build.log
  echo "compiler warnings: $(grep -c 'warning:' $BD.build.log) (by file:)"
  grep 'warning:' $BD.build.log | sed -E 's/^.*\/(src|tests|tools|include)\//\1\//; s/:[0-9]+:[0-9]+: warning:.*\[(-W[^]]*)\]$/ \2/' | sort | uniq -c
  echo "targets built: $(grep -cE 'Linking CXX executable' $BD.build.log)"
  [ $rc -eq 0 ] || return 1
  waitram
  step "ctest $name (--output-on-failure --timeout 600)"
  (cd "$BD" && nice -n 19 ctest --output-on-failure --timeout 600) > $L/ctest_$name.log 2>&1
  echo "ctest rc=$?"
  grep -E "tests passed|tests failed|Total Test time" $L/ctest_$name.log
  grep -E "^\s*[0-9]+/[0-9]+ Test" $L/ctest_$name.log | grep -vE "Passed" || true
  nice -n 19 $PY -I -B $W/opus_round1/ci/check_known_failures.py $L/ctest_$name.log > $L/known_$name.log 2>&1
  echo "known-failure check rc=$?"; cat $L/known_$name.log
}

run_cfg cmake
run_cfg cmake_datagen -DFORGE_DATAGEN=ON
run_cfg cmake_initonce -DFORGE_ATTACKS_INIT_ONCE=ON
step "cold-init tests verbose (ctest -L cold-init -V) + their properties"
waitram
(cd $B/cmake_initonce && ctest --show-only=json-v1 -L cold-init) > $L/cold_tests_show_only.json 2>&1
(cd $B/cmake_initonce && nice -n 19 ctest -L cold-init -V) > $L/ctest_initonce_cold_V.log 2>&1
echo "cold-init rc=$?"; grep -E "Test #|Passed|Failed|COLD_PROBE|tests passed|Timeout" $L/ctest_initonce_cold_V.log | tail -12
step "STEP3 DONE"
