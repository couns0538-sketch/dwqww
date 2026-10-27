#!/usr/bin/env bash
# S13 evidence driver (Windows PC, MSYS2 ucrt64 g++ 15.2). Correctness only; nothing here is timed for
# speed (nps_onoff.py does that). All output goes to <out_dir> (F:\opus_scratch).
#   build     : PC-recipe exes (b/tools/build_pc.sh): default build (switch off) and -DFORGE_S13_TT_CHILD_PREFETCH=1
#   identity  : default exe vs the lock exe (bytes, disassembly) + AL1 identity; switch-on exe AL1 identity
#               with TtChildPrefetch off and on (bench d11..d22, perft5 startpos + kiwipete)
#   ctest     : CMake builds (b/tools/cmake_build.sh, JOBS=1) default and switch on, ctest + known-failure
#               check, the probe output and its link maps
#   negative  : Sol's NEGATIVE_DIAGNOSTIC: a copy of HEAD with the two new prefetch statements removed (option
#               kept) must fail the probe's coverage checks
#   codegen   : codegen_compare.sh lock exe vs the switch-on exe; prefetch instructions in Worker::search
# usage: run_s13_evidence.sh <step> <out_dir>      (run from the worktree root; HEAD must be clean)
set -uo pipefail
STEP=$1; OUT=$2
ROOT=$(pwd)
JOB="$ROOT/opus_round1/sol_S13"
TOOLS=/d/grok-pc-data/dwqww/.claude/worktrees/b/tools
LOCK_EXE=/d/grok-pc-data/dwqww/.claude/worktrees/b/base/forge_h256_s198.exe
VSCM="/c/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$OUT/logs"
L="$OUT/logs"
stamp() { echo "# $1; HEAD $(git -C "$ROOT" rev-parse --short HEAD); $(date -u +%FT%TZ); machine exclusive: no"; }
case "$STEP" in
  build)
    { stamp "PC-recipe build, default (no switch)"; nice -n 19 bash "$TOOLS/build_pc.sh" "$ROOT" "$OUT/forge_s13_default.exe"; } > "$L/build_pc_default.log" 2>&1
    { stamp "PC-recipe build, -DFORGE_S13_TT_CHILD_PREFETCH=1"; nice -n 19 bash "$TOOLS/build_pc.sh" "$ROOT" "$OUT/forge_s13_on.exe" -DFORGE_S13_TT_CHILD_PREFETCH=1; } > "$L/build_pc_switch_on.log" 2>&1
    cat "$L/build_pc_default.log" "$L/build_pc_switch_on.log" ;;
  identity)
    export PATH=/c/msys64/ucrt64/bin:$PATH
    { stamp "default build vs lock exe b/base/forge_h256_s198.exe"
      echo "lock    sha256 $(sha256sum "$LOCK_EXE" | cut -d' ' -f1) size $(stat -c %s "$LOCK_EXE")"
      echo "default sha256 $(sha256sum "$OUT/forge_s13_default.exe" | cut -d' ' -f1) size $(stat -c %s "$OUT/forge_s13_default.exe")"
      echo "cmp -l (offset, octal bytes) of the two exes:"; cmp -l "$LOCK_EXE" "$OUT/forge_s13_default.exe"
      echo "objdump -p Time/Date stamps:"; for e in "$LOCK_EXE" "$OUT/forge_s13_default.exe"; do objdump -p "$e" | grep -m1 'Time/Date'; done
      a=$(objdump -d "$LOCK_EXE" | tail -n +3 | sha256sum | cut -c1-64); b=$(objdump -d "$OUT/forge_s13_default.exe" | tail -n +3 | sha256sum | cut -c1-64)
      echo "objdump -d (whole binary, without the file-name line) sha256: lock $a default $b $([ "$a" = "$b" ] && echo IDENTICAL || echo DIFFERENT)"
      echo "## AL1 identity of the default exe (standard uci_check.py --full)"; nice -n 19 python "$ROOT/opus_round1/ci/uci_check.py" "$OUT/forge_s13_default.exe" --full; echo "exit $?"
    } > "$L/identity_default_vs_lock.log" 2>&1
    tail -14 "$L/identity_default_vs_lock.log"
    for mode in off on; do
      set_arg=(); [ "$mode" = on ] && set_arg=(--set TtChildPrefetch=true)
      { stamp "AL1 identity, switch-on exe, TtChildPrefetch $mode"; echo "exe sha256 $(sha256sum "$OUT/forge_s13_on.exe" | cut -d' ' -f1)"
        nice -n 19 python "$JOB/uci_check_opt.py" "$OUT/forge_s13_on.exe" --full \
          --expect-option "option name TtChildPrefetch type check default false" "${set_arg[@]}"; echo "exit $?"; } > "$L/identity_switch_on_$mode.log" 2>&1
      tail -9 "$L/identity_switch_on_$mode.log"
    done
    { stamp "UCI session, switch-on exe: option list, invalid value, active line once per process"
      printf 'uci\nsetoption name TtChildPrefetch value maybe\nsetoption name TtChildPrefetch value true\nsetoption name Hash value 16\nisready\nposition startpos\ngo depth 8\nisready\nposition startpos moves e2e4\ngo depth 8\nisready\nbench 8\nquit\n' |
        "$OUT/forge_s13_on.exe" | grep -E 'option name (TtChildPrefetch|UseNNUE|Clear Hash)|info string|bestmove|uciok'
      echo "## default exe: the option is not advertised and is ignored"
      printf 'uci\nsetoption name TtChildPrefetch value true\nisready\nbench 8\nquit\n' | "$OUT/forge_s13_default.exe" | grep -E 'TtChildPrefetch|info string|uciok'
    } > "$L/uci_session_switch_on.log" 2>&1
    cat "$L/uci_session_switch_on.log" ;;
  ctest)
    for cfg in default switch_on; do
      extra=(); [ "$cfg" = switch_on ] && extra=(-DFORGE_S13_TT_CHILD_PREFETCH=ON)
      { stamp "CMake build $cfg (b/tools/cmake_build.sh, JOBS=1) ${extra[*]}"; JOBS=1 nice -n 19 bash "$TOOLS/cmake_build.sh" "$ROOT" "$OUT/cm_$cfg" "${extra[@]}"
        cat "$OUT/cm_$cfg.configure.log" "$OUT/cm_$cfg.build.log"; } > "$L/cmake_build_$cfg.log" 2>&1
      tail -1 "$L/cmake_build_$cfg.log"
      { stamp "forge_tt_prefetch_probe ($cfg)"; nice -n 19 "$OUT/cm_$cfg/forge_tt_prefetch_probe.exe"; echo "exit $?"
        echo "## archive members linked into the probe (search.cpp.obj must not appear)"
        grep -oE 'libforge_core\.a\([a-z_]+\.cpp\.obj\)' "$OUT/cm_$cfg/forge_tt_prefetch_probe.map" | sort -u
        echo "search.cpp.obj from the archive: $(grep -c 'libforge_core.a(search.cpp.obj)' "$OUT/cm_$cfg/forge_tt_prefetch_probe.map")"
      } > "$L/probe_$cfg.log" 2>&1
      tail -4 "$L/probe_$cfg.log"
      (cd "$OUT/cm_$cfg" && export PATH="$VSCM/CMake/bin:$PATH" && { stamp "ctest $cfg (CMake Release, g++ 15.2)"; nice -n 19 ctest --output-on-failure --timeout 600; }) > "$L/ctest_$cfg.log" 2>&1
      python "$ROOT/opus_round1/ci/check_known_failures.py" "$L/ctest_$cfg.log" > "$L/ctest_known_$cfg.log" 2>&1
      grep -E "tests passed" "$L/ctest_$cfg.log"; cat "$L/ctest_known_$cfg.log"
    done ;;
  negative)
    M="$OUT/negative"; mkdir -p "$M/tree"
    git -C "$ROOT" archive HEAD | tar -x -m -C "$M/tree"
    python - "$M/tree/src/search.cpp" <<'EOF'
import sys
from pathlib import Path
p = Path(sys.argv[1]); t = p.read_bytes()
line = b"if (s13_tt_child_prefetch_) shared_.tt.prefetch(board.key());"
if t.count(line) != 2: raise SystemExit("expected exactly the two new prefetch statements")
p.write_bytes(t.replace(line, b"/* S13 negative diagnostic: new child prefetch removed */"))
print("removed the two new prefetch statements (option kept)")
EOF
    { stamp "negative diagnostic: the two new prefetch statements removed in a copy of HEAD, option kept"
      diff "$ROOT/src/search.cpp" "$M/tree/src/search.cpp"
      JOBS=1 nice -n 19 bash "$TOOLS/cmake_build.sh" "$M/tree" "$M/cm" -DFORGE_S13_TT_CHILD_PREFETCH=ON 2>&1 | tail -1
      echo "## probe on the negative copy (coverage checks must FAIL)"; nice -n 19 "$M/cm/forge_tt_prefetch_probe.exe"; echo "probe exit $?"
    } > "$L/negative_diagnostic.log" 2>&1
    grep -E "^(FAIL|PASS|ALL|FAILURES|probe exit|null-move)" "$L/negative_diagnostic.log" ;;
  codegen)
    export PATH=/c/msys64/ucrt64/bin:$PATH
    { stamp "codegen_compare.sh A = lock exe ($(sha256sum "$LOCK_EXE" | cut -c1-16)...), B = S13 switch-on PC exe"
      bash "$JOB/codegen_compare.sh" "$LOCK_EXE" "$OUT/forge_s13_on.exe"
      for e in "$LOCK_EXE" "$OUT/forge_s13_default.exe" "$OUT/forge_s13_on.exe"; do
        objdump -d -C --no-show-raw-insn "$e" > "$OUT/$(basename "$e").dis"
        for f in "forge::Worker::search(forge::Board&" "forge::Worker::qsearch("; do
          n=$(awk -v pat="$f" 'index($0,"<"pat)>0 && /^[0-9a-f]+ </ {p=1; next} /^[0-9a-f]+ </{p=0} p' "$OUT/$(basename "$e").dis" | grep -c 'prefetch')
          echo "$(basename "$e"): prefetch instructions in $f...): $n"
        done
      done
    } > "$L/codegen_lock_vs_s13on.log" 2>&1
    cat "$L/codegen_lock_vs_s13on.log" ;;
  *) echo "unknown step $STEP"; exit 2 ;;
esac
