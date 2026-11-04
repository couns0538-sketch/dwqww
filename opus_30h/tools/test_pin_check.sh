#!/usr/bin/env bash
# test_pin_check.sh OUT_DIR - self-test of pin_check.ps1 on the lock exe copy (D:\o30\base\lock_copy.exe, sha256 fd3a5190...).
# Every case has an expected exit code; a planted failure must fail. Exit 0 = all cases as expected.
set -u
out=${1:?out dir}; [ -e "$out" ] && { echo "refusing existing $out" >&2; exit 2; }; mkdir -p "$out"
PC="$(cygpath -w "$(cd "$(dirname "$0")" && pwd)/pin_check.ps1")"
LOCK='D:\o30\base\lock_copy.exe'
W="$(cygpath -w "$out")"
fails=0; n=0
case_() { name=$1; want=$2; shift 2; n=$((n + 1))
  powershell -NoProfile -ExecutionPolicy Bypass -File "$PC" "$@" > "$out/$name.txt" 2>&1; rc=$?
  if [ "$rc" = "$want" ]; then echo "PASS $name (exit $rc): $(head -1 "$out/$name.txt")"; else echo "FAIL $name: exit $rc, want $want: $(head -3 "$out/$name.txt" | tr '\n' ' ')"; fails=$((fails + 1)); fi; }
case_ lock_plain 0 -Exe "$LOCK"
grep -q '^pin_check PASS' "$out/lock_plain.txt" || { echo "FAIL lock_plain: no PASS line"; fails=$((fails + 1)); }
case_ live_tunable 0 -Exe "$LOCK" -Options 'LmrQuietBase=86' -Json "$W\\live.json"
grep -q '^pin_check LIVE' "$out/live_tunable.txt" || { echo "FAIL live_tunable: no LIVE line"; fails=$((fails + 1)); }
case_ dead_default 1 -Exe "$LOCK" -Options 'LmrQuietBase=85'
grep -q 'dead option' "$out/dead_default.txt" || { echo "FAIL dead_default: no 'dead option' problem"; fails=$((fails + 1)); }
case_ wrong_expect 1 -Exe "$LOCK" -Expect 'd11=312867'
case_ right_expect 0 -Exe "$LOCK" -Options 'LmrQuietBase=86' -Expect "d11=$(grep -o '"d11": *[0-9]*' "$out/live.json" | grep -o '[0-9]*$')"
case_ unknown_option 1 -Exe "$LOCK" -Options 'NoSuchOption=1'
case_ bad_value 1 -Exe "$LOCK" -Options 'LmrQuietBase=abc'
case_ out_of_range 1 -Exe "$LOCK" -Options 'LmrQuietBase=999'
case_ missing_exe 2 -Exe 'D:\o30\base\no_such.exe'
case_ json_exists 2 -Exe "$LOCK" -Json "$W\\live.json"
case_ bad_option_syntax 2 -Exe "$LOCK" -Options 'LmrQuietBase'
case_ not_an_engine 1 -Exe 'C:\Windows\System32\whoami.exe' -TimeoutSec 20
echo "$((n - fails)) / $n cases as expected"
[ $fails = 0 ] && echo "ALL PASS" || echo "FAILURES: $fails"
exit $fails
