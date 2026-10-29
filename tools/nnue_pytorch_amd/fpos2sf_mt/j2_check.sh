#!/usr/bin/env bash
# R7 J2 checks: fpos2sf_mt vs Grok Bot's fpos2sf.exe (byte identity, timing) and the decode verify.
# usage: j2_check.sh <fpos2sf_mt.exe> <old fpos2sf.exe> <shard.pos (Windows path)> <work dir (Windows path)>
# Every step prints one line; the script ends with "J2 CHECK PASS" only if every identity/verify step passed.
set -uo pipefail
NEW=$1; OLD=$2; IN=$3; W=$4
HERE=$(cd "$(dirname "$0")" && pwd -W 2>/dev/null || pwd)
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
fail=0
secs() { local s e; s=$(date +%s%N); "$@" > /dev/null 2>&1; local rc=$?; e=$(date +%s%N); echo "$(( (e - s) / 1000000 )) ms rc=$rc"; }
same() {  # same <label> <a> <b>
  local a b; a=$(sha256sum < "$2" | cut -c1-64); b=$(sha256sum < "$3" | cut -c1-64)
  if [ "$a" = "$b" ]; then echo "$1: identical sha256 $a ($(stat -c %s "$2") bytes)"; else echo "$1: DIFFERENT $a vs $b"; fail=1; fi
}
verify() {  # verify <label> <args...>
  local label=$1; shift
  local out; out=$(nice -n 10 "$NEW" --verify "$@" 2>&1); echo "$label: $out" | tr '\n' ' '; echo
  echo "$out" | grep -q "VERIFY OK" || fail=1
}
echo "== full shard, binpack"
echo "old fpos2sf (1 thread): $(secs nice -n 10 "$OLD" "$IN" "$W/old_full.binpack")"
echo "new fpos2sf_mt --threads 1: $(secs nice -n 10 "$NEW" "$IN" "$W/new_full_t1.binpack" --threads 1)"
echo "new fpos2sf_mt --threads 3: $(secs nice -n 10 "$NEW" "$IN" "$W/new_full_t3.binpack" --threads 3)"
same "old vs new t1" "$W/old_full.binpack" "$W/new_full_t1.binpack"
same "old vs new t3" "$W/old_full.binpack" "$W/new_full_t3.binpack"
verify "verify new t3 (decode + loader reader)" "$IN" "$W/new_full_t3.binpack" --threads 3
verify "verify old (decode + loader reader)" "$IN" "$W/old_full.binpack" --threads 3
echo "== .bin output, 1M"
echo "old .bin: $(secs nice -n 10 "$OLD" "$IN" "$W/old_1M.bin" --max 1000000)"
echo "new .bin t3: $(secs nice -n 10 "$NEW" "$IN" "$W/new_1M.bin" --max 1000000 --threads 3)"
same "old vs new .bin" "$W/old_1M.bin" "$W/new_1M.bin"
verify "verify new .bin" "$IN" "$W/new_1M.bin" --max 1000000 --threads 3
echo "== skip/stride/ply/score-mult/max + fen-out"
nice -n 10 "$OLD" "$IN" "$W/old_sel.binpack" --skip 7 --stride 3 --max 500000 --ply 17 --score-mult 2.5 --fen-out "$W/old_sel.txt" > /dev/null 2>&1
nice -n 10 "$NEW" "$IN" "$W/new_sel.binpack" --skip 7 --stride 3 --max 500000 --ply 17 --score-mult 2.5 --fen-out "$W/new_sel.txt" --threads 3 > /dev/null 2>&1
same "old vs new selection binpack" "$W/old_sel.binpack" "$W/new_sel.binpack"
same "old vs new selection fen-out" "$W/old_sel.txt" "$W/new_sel.txt"
verify "verify selection" "$IN" "$W/new_sel.binpack" --skip 7 --stride 3 --max 500000 --ply 17 --score-mult 2.5 --threads 3
echo "== planted bad records (200k-record copy)"
"$PY" -I -B "$HERE/make_bad_pos.py" "$IN" "$W/bad200k.pos" 200000
o=$(nice -n 10 "$OLD" "$W/bad200k.pos" "$W/old_bad.binpack" 2>&1); echo "old: $o"
n=$(nice -n 10 "$NEW" "$W/bad200k.pos" "$W/new_bad.binpack" --threads 3 2>&1 | head -1); echo "new: $n"
echo "$o" | grep -q "bad=6 " || { echo "old tool did not report bad=6"; fail=1; }
echo "$n" | grep -q "bad=6 " || { echo "new tool did not report bad=6"; fail=1; }
same "old vs new with bad records" "$W/old_bad.binpack" "$W/new_bad.binpack"
verify "verify with bad records" "$W/bad200k.pos" "$W/new_bad.binpack" --threads 3
echo "== planted output corruption (verify must FAIL)"
"$PY" -I -B -c "import sys; d=bytearray(open(sys.argv[1],'rb').read()); d[8+34*777+5]^=0x10; open(sys.argv[2],'xb').write(d)" "$W/new_bad.binpack" "$W/corrupt.binpack"
c=$(nice -n 10 "$NEW" --verify "$W/bad200k.pos" "$W/corrupt.binpack" --threads 3 2>&1); echo "corrupt: $c" | tr '\n' ' '; echo
echo "$c" | grep -q "VERIFY FAILED" || { echo "corruption NOT detected"; fail=1; }
[ $fail = 0 ] && echo "J2 CHECK PASS" || echo "J2 CHECK FAIL"
