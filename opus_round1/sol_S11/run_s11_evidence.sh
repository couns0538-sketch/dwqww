#!/usr/bin/env bash
# S11 evidence driver (Windows PC, MSYS2 ucrt64 g++ 15.2). Correctness only: nothing here is timed
# for speed (see nps_onoff.py / nps_ab.py for that). All output goes to <out_dir> (F:\opus_scratch).
#   build     : PC-recipe exe (b/tools/build_pc.sh) + scalar-NNUE exe (build_pc_scalar_nnue.sh)
#   identity  : AL1 identity (bench d11..d22, perft5 startpos + kiwipete) of both exes, MaterialKeyTable off and on
#   ctest     : CMake build (b/tools/cmake_build.sh, JOBS=1), ctest, known-failure check, material key test log
#   mutation  : two planted bugs in a copy of HEAD (key relabelling; two material classes merged)
#   codegen   : codegen_compare.sh lock exe vs the PC-recipe exe + corrected_eval/update_correction diffs
# usage: run_s11_evidence.sh <step> <out_dir>      (run from the worktree root; HEAD must be clean)
set -uo pipefail
STEP=$1; OUT=$2
ROOT=$(pwd)
JOB="$ROOT/opus_round1/sol_S11"
TOOLS=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LOCK_EXE=/d/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_h256_s198.exe
EPD="$ROOT/tools/openings/forge-10000.epd"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT/logs"
L="$OUT/logs"
stamp() { echo "# $1; HEAD $(git -C "$ROOT" rev-parse --short HEAD); $(date -u +%FT%TZ); machine exclusive: no"; }
case "$STEP" in
  build)
    { stamp "PC-recipe build (b/tools/build_pc.sh)"; nice -n 19 bash "$TOOLS/build_pc.sh" "$ROOT" "$OUT/forge_s11.exe"; } > "$L/build_pc.log" 2>&1
    { stamp "scalar-NNUE build (build_pc_scalar_nnue.sh)"; nice -n 19 bash "$JOB/build_pc_scalar_nnue.sh" "$ROOT" "$OUT/scalar/forge_s11_scalar_nnue.exe"; } > "$L/build_scalar_nnue.log" 2>&1
    cat "$L/build_pc.log" "$L/build_scalar_nnue.log" ;;
  identity)
    for exe in forge_s11 scalar/forge_s11_scalar_nnue; do
      tag=$([ "$exe" = forge_s11 ] && echo pc || echo scalar)
      for mode in off on; do
        set_arg=(); [ "$mode" = on ] && set_arg=(--set MaterialKeyTable=true)
        { stamp "AL1 identity, $exe.exe, MaterialKeyTable $mode"; echo "exe sha256 $(sha256sum "$OUT/$exe.exe" | cut -d' ' -f1)"
          nice -n 19 python "$JOB/uci_check_opt.py" "$OUT/$exe.exe" --full \
            --expect-option "option name MaterialKeyTable type check default false" "${set_arg[@]}"; echo "exit $?"; } > "$L/identity_${tag}_$mode.log" 2>&1
        tail -9 "$L/identity_${tag}_$mode.log"
      done
    done
    { stamp "standard uci_check.py --full (no options), PC-recipe exe"; nice -n 19 python "$ROOT/opus_round1/ci/uci_check.py" "$OUT/forge_s11.exe" --full; echo "exit $?"; } > "$L/identity_pc_standard_tool.log" 2>&1
    tail -2 "$L/identity_pc_standard_tool.log" ;;
  ctest)
    VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
    { stamp "CMake build (b/tools/cmake_build.sh, JOBS=1)"; JOBS=1 nice -n 19 bash "$TOOLS/cmake_build.sh" "$ROOT" "$OUT/cm"; cat "$OUT/cm.configure.log" "$OUT/cm.build.log"; } > "$L/cmake_build.log" 2>&1
    tail -1 "$L/cmake_build.log"
    { stamp "forge_material_key_tests (release)"; nice -n 19 "$OUT/cm/forge_material_key_tests.exe" "$EPD"; echo "exit $?"; } > "$L/material_key_tests_release.log" 2>&1
    tail -3 "$L/material_key_tests_release.log"
    (cd "$OUT/cm" && export PATH="$VSCM/CMake/bin:$PATH" && { stamp "ctest (CMake Release, g++ 15.2)"; nice -n 19 ctest --output-on-failure --timeout 600; }) > "$L/ctest_release.log" 2>&1
    python "$ROOT/opus_round1/ci/check_known_failures.py" "$L/ctest_release.log" > "$L/ctest_known_release.log" 2>&1
    grep -E "tests passed|^Total" "$L/ctest_release.log"; cat "$L/ctest_known_release.log" ;;
  mutation)
    for n in 1 2; do
      M="$OUT/mutant$n"; mkdir -p "$M/tree"
      git -C "$ROOT" archive HEAD | tar -x -m -C "$M/tree"
      python "$JOB/plant_bug.py" "$n" "$M/tree/include/forge/material_key_table.hpp"
      { stamp "mutation $n (plant_bug.py $n)"
        diff "$ROOT/include/forge/material_key_table.hpp" "$M/tree/include/forge/material_key_table.hpp"
        if [ "$n" = 1 ]; then
          JOBS=1 nice -n 19 bash "$TOOLS/cmake_build.sh" "$M/tree" "$M/cm" | tail -1
          echo "## forge_material_key_tests on mutant $n (must FAIL)"
          nice -n 19 "$M/cm/forge_material_key_tests.exe" "$M/tree/tools/openings/forge-10000.epd"; echo "test exit $?"
        fi
        nice -n 19 bash "$TOOLS/build_pc.sh" "$M/tree" "$M/forge_s11_mutant$n.exe"
        echo "## mutant $n PC exe, MaterialKeyTable off (must stay exact)"
        nice -n 19 python "$JOB/uci_check_opt.py" "$M/forge_s11_mutant$n.exe"; echo "exit $?"
        echo "## mutant $n PC exe, MaterialKeyTable on (mutant 1: relabelling, bench cannot see it; mutant 2: must MISMATCH)"
        nice -n 19 python "$JOB/uci_check_opt.py" "$M/forge_s11_mutant$n.exe" --set MaterialKeyTable=true; echo "exit $?"
      } > "$L/mutation_check$n.log" 2>&1
      grep -E "^(FAIL|bench d1[136]|ALL OK|MISMATCH|test exit|exit|count domain|boards: key)" "$L/mutation_check$n.log"
    done ;;
  codegen)
    export PATH=/c/msys64/ucrt64/bin:$PATH
    { stamp "codegen_compare.sh A = lock exe b/base/forge_h256_s198.exe ($(sha256sum "$LOCK_EXE" | cut -c1-16)...), B = S11 PC-recipe exe, option code present, default OFF"
      bash "$JOB/codegen_compare.sh" "$LOCK_EXE" "$OUT/forge_s11.exe"
      echo; echo "# S11 exe: symbols (material_key is inlined, as in the lock: no material_key symbol)"
      nm -C "$OUT/forge_s11.exe" | grep -E "material_key|matkey|corrected_eval|update_correction"
      echo; echo "# call sites of corrected_eval / update_correction / material_key"
      for e in "$LOCK_EXE" "$OUT/forge_s11.exe"; do
        echo "## $(basename "$e")"
        objdump -d -C --no-show-raw-insn "$e" | awk '/^[0-9a-f]+ </ {f=$0} /call/ && (/corrected_eval|material_key|update_correction/) {sub(/^[0-9a-f]+ /,"",f); print f " calls " $NF}' | sort | uniq -c
      done
      norm() { awk -v pat="$2" 'index($0,"<"pat)>0 && /^[0-9a-f]+ </ {p=1; next} /^[0-9a-f]+ </{p=0} p' "$1" | sed -E 's/^\s*[0-9a-f]+:\s*//; s/<[^>]*>//g; s/#.*$//; s/0x[0-9a-f]+/IMM/g; s/^(j[a-z]+|call|jmp)\s+[0-9a-f]+/\1 ADDR/; s/\s+/ /g; s/ $//'; }
      objdump -d -C --no-show-raw-insn "$LOCK_EXE" > "$OUT/lock.dis"; objdump -d -C --no-show-raw-insn "$OUT/forge_s11.exe" > "$OUT/s11.dis"
      for f in "forge::Worker::corrected_eval(" "forge::Worker::update_correction(" "forge::Worker::search(forge::Board&" "forge::Worker::qsearch("; do
        echo; echo "# normalised diff lock -> S11: $f"; norm "$OUT/lock.dis" "$f" > "$OUT/a.s"; norm "$OUT/s11.dis" "$f" > "$OUT/b.s"; diff "$OUT/a.s" "$OUT/b.s"
      done
      echo; echo "# S11 corrected_eval (raw)"; awk '/<forge::Worker::corrected_eval\(.*>:$/ {p=1} p {print} p && /^$/ {exit}' "$OUT/s11.dis"
    } > "$L/codegen_lock_vs_s11.log" 2>&1
    sed -n 1,26p "$L/codegen_lock_vs_s11.log" ;;
  *) echo "unknown step $STEP"; exit 2 ;;
esac
