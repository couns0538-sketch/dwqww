#!/usr/bin/env bash
# check_kbmap.sh <king map> [mask=0x1] - Opus 30-h job: the proofs for a king map before any training with it:
#  1 the lock net written as v2 with this map + OB8 (every bucket a copy) gives the lock pins d11-d22 in the gate exe
#  2 a random net with this map: parity 10000/10000 on AVX2 / SSE / scalar vs the own reference + planted bug caught
#  3 accumulator walk (incremental + cache vs full refresh) with that random net, 500 games x 300 plies
#  4 o30_fit.py selfcheck with this map (the trainer's forward = the scorer's numbers)
# Writes under D:\o30\kbmap_<map>_<stamp>\ (nets too); prints PASS / FAIL per check; exit 0 only if all pass.
set -uo pipefail
map="$1"; mask="${2:-0x1}"
A=$(cd "$(dirname "$0")" && pwd); T="$A/../tools"
. "$T/idle.sh"; o30_pin_self "$mask" || { echo "cannot pin (fail closed)" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
EXE='D:\o30\w\v2p3_pc1\src_copy\forge_ltopgo_v2p3_pc1.exe'
out=/d/o30/kbmap_${map}_$(date +%H%M%S); mkdir -p "$out"; OW=$(cygpath -w "$out")
INC='D:\o30\repos\base\src\nnue_weights.inc'   # the lock net (md5 22b4b9e2), as o30_fit.py LOCK_INC
fail=0
"$PY" -I -B "$A/o30_v2net.py" from-lock "$INC" "$OW\\lock_${map}_ob8.nnue2" --kb-map "$map" --ob 8 > "$out/from_lock.txt" 2>&1 || fail=1
"$PY" -I -B "$A/o30_v2net.py" random "$OW\\rand_${map}_ob8_s31.nnue2" --seed 31 --kb-map "$map" --ob 8 > "$out/random.txt" 2>&1 || fail=1
r=$(powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Exe "$EXE" -Mask "$mask" \
    -Options "EvalFileV2=$OW\\lock_${map}_ob8.nnue2" -Expect 'd11=312866,d13=862329,d16=3024920,d20=12389307,d22=34048354' 2>&1)
echo "$r" > "$out/identity.txt"
echo "$r" | head -1 | grep -q '^pin_check PASS' && echo "PASS 1 lock net as $map/OB8 = lock pins d11-d22" || { echo "FAIL 1 identity"; echo "$r" | head -12; fail=1; }
if bash "$A/parity_o30.sh" "$out/parity" /c/o13/p4/fens10k.txt /d/o30/harness/h1 "$out/rand_${map}_ob8_s31.nnue2" > "$out/parity.txt" 2>&1 \
   && grep -q '^PARITY PASS' "$out/parity.txt" && grep -q 'planted bug caught' "$out/parity.txt"; then
  echo "PASS 2 parity: $(grep -c ' -> PASS' "$out/parity.txt") builds 10000/10000, planted bug caught"
else echo "FAIL 2 parity"; tail -6 "$out/parity.txt"; fail=1; fi
/d/o30/harness/h1/v2_eval_avx2.exe --walk "$OW\\rand_${map}_ob8_s31.nnue2" 77 500 300 > "$out/walk.txt" 2>&1
grep -q 'mismatches 0$' "$out/walk.txt" && echo "PASS 3 walk: $(tail -1 "$out/walk.txt")" || { echo "FAIL 3 walk"; tail -3 "$out/walk.txt"; fail=1; }
"$PY" -I -B "$A/o30_fit.py" selfcheck --kb-map "$map" --ob 8 > "$out/selfcheck.txt" 2>&1 && echo "PASS 4 trainer selfcheck: $(tail -1 "$out/selfcheck.txt")" || { echo "FAIL 4 selfcheck"; tail -5 "$out/selfcheck.txt"; fail=1; }
echo "KBMAP $map $([ $fail = 0 ] && echo PASS || echo FAIL) (evidence $OW)"
exit $fail
