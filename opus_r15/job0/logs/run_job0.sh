#!/usr/bin/env bash
# R15 Job 0: re-verify the R14-B Code Review fixes from fresh clones (outputs only under D:/o15/job0).
set -u
J=/d/o15/job0
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
export TMP='D:\o15\tmp' TEMP='D:\o15\tmp'
echo "start $(date '+%F %T')"
for b in fast-loader status; do
  [ -e "$J/clone_$b" ] || git clone -q --shared --no-checkout /d/grok-pc-data/dwqww "$J/clone_$b"
  git -C "$J/clone_$b" -c core.autocrlf=false checkout -q "origin/opus-r14b-$b" 2>&1 | tail -1
  echo "clone $b at $(git -C "$J/clone_$b" rev-parse HEAD)"
done
L1=$J/clone_fast-loader/opus_r14b/item1
T=$J/clone_status/opus_r14b/tools
fails=0
run() { name=$1; shift; echo "=== $name $(date '+%T')"; "$@" > "$J/$name.log" 2>&1; rc=$?
        echo "$name exit $rc: $(grep -c '^PASS' "$J/$name.log") PASS lines, $(grep -c '^FAIL' "$J/$name.log") FAIL lines; last: $(tail -1 "$J/$name.log")"
        [ $rc = 0 ] || fails=$((fails + 1)); }
run test_installer bash "$L1/tools/test_installer.sh" "$J/out_test_installer"
run test_scope "$PY" -I -B "$L1/tools/test_scope.py"
run test_cli "$PY" -I -B "$L1/tools/test_cli.py" "$J/out_test_cli"
run test_tools bash "$T/test_tools.sh" "$J/out_test_tools"
echo "end $(date '+%F %T') failures $fails"
exit $fails
