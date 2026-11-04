#!/usr/bin/env bash
# test_smoke2m.sh OUT_DIR - self-test of smoke2m.py: stub engines that play an illegal move, crash, hang or write to
# stderr must FAIL; a legal stub and the lock exe copy (OFF, and with a live tunable) must PASS. Exit 0 = all as expected.
set -u
out=${1:?out dir}; [ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }; mkdir -p "$out"
D="$(cd "$(dirname "$0")" && pwd)"
PY=/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
LOCK=/d/o30/base/lock_copy.exe
for m in illegal crash hang stderr slow clockcheck legal; do cp "$D/test_data/stub_engine.py" "$out/stub_$m.py"; done
fails=0; n=0
case_() { name=$1; want=$2; shift 2; n=$((n + 1))
  "$PY" -I -B "$D/smoke2m.py" "$@" --out "$out/$name" > "$out/$name.txt" 2>&1; rc=$?
  if [ "$rc" = "$want" ]; then echo "PASS $name (exit $rc): $(tail -1 "$out/$name.txt")"; else echo "FAIL $name: exit $rc, want $want: $(tail -2 "$out/$name.txt" | tr '\n' ' ')"; fails=$((fails + 1)); fi; }
case_ stub_illegal 1 "$(cygpath -w "$out/stub_illegal.py")" --seconds 5 --random-plies 0 --max-plies 4
case_ stub_crash 1 "$(cygpath -w "$out/stub_crash.py")" --seconds 5 --random-plies 0 --max-plies 4
case_ stub_hang 1 "$(cygpath -w "$out/stub_hang.py")" --seconds 5 --random-plies 0 --max-plies 4 --tc 500+5
case_ stub_stderr 1 "$(cygpath -w "$out/stub_stderr.py")" --seconds 5 --random-plies 0 --max-plies 4
case_ stub_slow 1 "$(cygpath -w "$out/stub_slow.py")" --seconds 5 --random-plies 0 --max-plies 2 --tc 500+5 --timemargin 1000
case_ stub_clockcheck 0 "$(cygpath -w "$out/stub_clockcheck.py")" --seconds 8 --random-plies 0 --max-plies 12 --tc 4000+0
case_ stub_legal 0 "$(cygpath -w "$out/stub_legal.py")" --seconds 5 --random-plies 0 --max-plies 4
case_ missing_engine 2 'D:\o30\base\no_such.exe' --seconds 5
case_ bad_tc 2 "$(cygpath -w "$LOCK")" --tc 2000 --seconds 5
case_ lock_off 0 "$(cygpath -w "$LOCK")" --seconds 25 --threads 2 --mask 0x3 --idle
case_ lock_live_tunable 0 "$(cygpath -w "$LOCK")" --line 'LmrQuietBase=86' --seconds 25 --threads 2 --mask 0x3 --idle
case_ lock_bad_option 1 "$(cygpath -w "$LOCK")" --line 'LmrQuietBase=abc' --seconds 8 --threads 1 --mask 0x3 --idle
grep -q '"illegal": [1-9]' "$out/stub_illegal.json" || { echo "FAIL stub_illegal: no illegal move counted"; fails=$((fails + 1)); }
grep -q '"time_losses": [1-9]' "$out/stub_slow.json" || { echo "FAIL stub_slow: no time loss counted"; fails=$((fails + 1)); }
grep -q '"crashes": [1-9]' "$out/stub_crash.json" || { echo "FAIL stub_crash: no crash counted"; fails=$((fails + 1)); }
grep -q '"hangs": [1-9]' "$out/stub_hang.json" || { echo "FAIL stub_hang: no hang counted"; fails=$((fails + 1)); }
grep -q '"option_errors": [1-9]' "$out/lock_bad_option.json" || { echo "FAIL lock_bad_option: no option error counted"; fails=$((fails + 1)); }
echo "$((n - fails)) / $n cases as expected (+5 count checks)"
[ $fails = 0 ] && echo "ALL PASS" || echo "FAILURES: $fails"
exit $fails
