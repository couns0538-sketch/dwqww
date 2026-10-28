#!/usr/bin/env bash
# R3-3: build the five node-exact switch variants of one exported stack tree (one g++ at a time, nice 19)
# and record 5-depth prebench pins with the runner's Bench1 protocol: OFF (no options) and, where the switch adds
# a UCI option, ON with that option.  usage: run_switch_pins.sh <src_dir> <head_tag>
set -u
SRC=$1; TAG=$2
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
T=/f/opus_scratch/r3/R3-3/tools
B=/f/opus_scratch/build/r3_R3-3
O=/f/opus_scratch/r3/R3-3/pins
build() {  # name flag
  local free
  free=$(powershell -NoProfile -Command "[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)")
  echo "== build $1 ($2) free RAM ${free} GB $(date '+%F %T')"
  nice -n 19 bash /d/grok-pc-data/dwqww/.claude/worktrees/b/tools/build_pc.sh "$SRC" "$B/forge_r3probe_${TAG}_$1.exe" "$2"
}
for sw in "nnueo2:-DFORGE_NNUE_O2=1" "nozero:-DFORGE_NOZERO_MOVE_BUFFERS=1" "speedstack:-DFORGE_SPEEDSTACK=1" \
          "ttprefetch:-DFORGE_S13_TT_CHILD_PREFETCH=1" "lazyacc:-DFORGE_NNUE_LAZY_ACC=1"; do
  name=${sw%%:*}; flag=${sw#*:}
  build "$name" "$flag" || { echo "BUILD FAILED $name"; continue; }
  exe="$B/forge_r3probe_${TAG}_${name}.exe"
  case $name in
    ttprefetch) set_on="--set ON=TtChildPrefetch:true" ;;
    lazyacc) set_on="--set ON=NnueLazyAcc:true" ;;
    *) set_on="" ;;
  esac
  nice -n 19 $PY -I -B $T/measure_pins.py "$exe" "$O/switch_${TAG}_${name}.json" $set_on
  echo "sha256 $(sha256sum "$exe" | cut -d' ' -f1)"
done
echo "done $(date '+%F %T')"
