#!/usr/bin/env bash
# test_o30tuned.sh <exe with O30Tuned> <TUNED_OPTIONS.txt> [mask=0x1] - Opus 30-h job: the checks of an O30Tuned exe.
#  1 OFF (O30Tuned untouched): pin_check -Full = the lock pins (d11-d22, perft)
#  2 O30Tuned=true: bench d11/d13/d16 == bench with the explicit Name=Value list of TUNED_OPTIONS.txt (one switch = the set)
#  3 O30Tuned=true then false: bench = the lock pins (false restores the lock values)
#  4 an invalid value prints `info string invalid value for option O30Tuned`; the option is advertised by `uci`
# Prints PASS / FAIL per check and O30TUNED PASS / FAIL; exit 0 only on PASS. Idle on <mask> (pin_check -Mask).
set -uo pipefail
exe="$1"; tuned="$2"; mask="${3:-0x1}"
T=$(cd "$(dirname "$0")/../tools" && pwd)
. "$T/idle.sh"; o30_pin_self "$mask" || { echo "cannot pin (fail closed)" >&2; exit 78; }
PC() { powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Exe "$(cygpath -w "$exe")" -Mask "$mask" "$@"; }
PINS='d11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354'
list=$(grep -E '^[A-Za-z][A-Za-z0-9]*=-?[0-9]+$' "$tuned" | paste -sd ';' -)
[ -n "$list" ] || { echo "no Name=Value lines in $tuned" >&2; exit 2; }
fail=0
r1=$(PC -Full 2>&1); echo "$r1" | head -1 | grep -q '^pin_check PASS' && echo "PASS 1 OFF pins (-Full)" || { echo "FAIL 1 OFF pins"; echo "$r1"; fail=1; }
on=$(PC -Options 'O30Tuned=true' 2>&1); ex=$(PC -Options "$list" 2>&1)
b_on=$(echo "$on" | grep '^bench' | awk '{print $2"="$3}' | paste -sd, -); b_ex=$(echo "$ex" | grep '^bench' | awk '{print $2"="$3}' | paste -sd, -)
if [ -n "$b_on" ] && [ "$b_on" = "$b_ex" ] && [ "$b_on" != "d11=312866,d13=862329,d16=3024920" ]; then
  echo "PASS 2 O30Tuned=true == explicit list ($b_on), differs from the lock"
else echo "FAIL 2 O30Tuned=true ($b_on) vs explicit list ($b_ex)"; echo "$on" | head -3; echo "$ex" | head -3; fail=1; fi
r3=$(PC -Options 'O30Tuned=true;O30Tuned=false' -Expect 'd11=312866,d13=862329,d16=3024920' 2>&1)
echo "$r3" | head -1 | grep -q '^pin_check PASS' && echo "PASS 3 true then false = the lock pins" || { echo "FAIL 3"; echo "$r3"; fail=1; }
out=$( (printf 'uci\n'; sleep 1; printf 'setoption name O30Tuned value maybe\nisready\n'; sleep 1; printf 'quit\n') | "$exe" 2>&1)
if echo "$out" | grep -q '^option name O30Tuned type check default false' && echo "$out" | grep -q 'invalid value for option O30Tuned'; then
  echo "PASS 4 advertised + invalid value rejected"
else echo "FAIL 4"; echo "$out" | grep -E 'O30Tuned|invalid' ; fail=1; fi
echo "O30TUNED $([ $fail = 0 ] && echo PASS || echo FAIL) exe $exe ($(sha256sum "$exe" | cut -c1-16)...) set: $list"
exit $fail
