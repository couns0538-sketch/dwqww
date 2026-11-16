#!/usr/bin/env bash
# exit_codes.sh — proves each repaired script returns DISTINCT codes:
#   0 = measured and agreed, 1 = measured and disagreed, 3 = nothing measured (no parse).
# Run from forge-combo29/swarm/05/
set -u
STUB="audit_failclosed/stub_no_score.sh"
REAL="/tmp/build-rel/forge"
echo "| script | no-parse exit | real exit | expected | verdict |"
echo "|---|---|---|---|---|"

row () { # name noparse_exit real_exit
  local want_np="$2" want_re="$3"
  local ok="ok"
  [ "$2" != "$want_np" ] && ok="**WRONG (no-parse should be $want_np)**"
  [ "$3" != "$want_re" ] && ok="**real exit $3, expected $want_re**"
  echo "| $1 | $2 | $3 | no-parse $want_np / real $want_re | $ok |"
}

# 1. honesty_safe.py
( cd audit19f12 && python3 honesty_safe.py "../$STUB" /tmp/x1 >/dev/null 2>&1 ); a=$?
( cd audit19f12 && python3 honesty_safe.py "$REAL" /tmp/x2 >/dev/null 2>&1 ); b=$?
row "audit19f12/honesty_safe.py" "$a" "$b" 3 0

# 2. mate_check.py  (stub dtm2 that prints nothing)
d=/tmp/xc_mc; rm -rf $d; mkdir -p $d
cp job1/mate_check.py job1/dtm2.py $d/ 2>/dev/null
cp job1/out/rows.jsonl $d/ 2>/dev/null
printf 'import sys\nsys.exit(0)\n' > $d/dtm2.py
( cd $d && python3 mate_check.py rows.jsonl o.txt 6 5 >/dev/null 2>&1 ); a=$?
cp job1/dtm2.py $d/dtm2.py
( cd $d && timeout 300 python3 mate_check.py rows.jsonl o.txt 24 60 >/dev/null 2>&1 ); b=$?
row "job1/mate_check.py" "$a" "$b" 3 1

# 3. crosscheck_mates.py
d=/tmp/xc_cc; rm -rf $d; mkdir -p $d
cp job1/crosscheck_mates.py job1/dtm2.py $d/
printf 'import sys\nsys.exit(0)\n' > $d/dtm2.py
( cd $d && python3 crosscheck_mates.py 5 "8/8/8/8/8/7k/8/4K2R w - - 0 1" >/dev/null 2>&1 ); a=$?
cp job1/dtm2.py $d/dtm2.py
( cd $d && timeout 200 python3 crosscheck_mates.py 5 "8/8/8/8/8/5k2/6q1/7K w - - 0 1" >/dev/null 2>&1 ); b=$?
row "job1/crosscheck_mates.py" "$a" "$b" 3 0

# 4 & 5. the two selftests
for pair in "dtm2_selftest.py:dtm2.py" "dtm_selftest.py:dtm.py"; do
  sel="${pair%%:*}"; chk="${pair##*:}"
  d="/tmp/xc_${chk%.py}"; rm -rf "$d"; mkdir -p "$d"
  cp job1/"$sel" "$d/"
  printf 'import sys\nsys.exit(0)\n' > "$d/$chk"
  ( cd "$d" && python3 "$sel" >/dev/null 2>&1 ); a=$?
  if [ "$chk" = "dtm2.py" ]; then cp job1/dtm2.py "$d/$chk"; else printf 'import sys\nprint("verdict: white MATES in 1 plies")\n' > "$d/$chk"; fi
  ( cd "$d" && timeout 300 python3 "$sel" >/dev/null 2>&1 ); b=$?
  row "job1/$sel" "$a" "$b" 3 0
done
