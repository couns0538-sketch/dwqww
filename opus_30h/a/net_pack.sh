#!/usr/bin/env bash
# net_pack.sh <name> <net.nnue2> <engine exe that loads it (EvalFileV2)> <harness dir (v2_eval_{avx2,sse,scalar}.exe)>
# One step from a trained v2 net to its evidence folder D:\o30\nets\<name>\ (refused when it exists):
#   1. copy the net (never moved), header + checksum check (o30_v2net.py info), sha256 + md5;
#   2. parity: own float32 reference vs the engine's AVX2 / SSE / scalar kernels on 10,000 legal FENs + planted bug;
#   3. holdout scores (o30_score_v2.exe): S31 subset of 013/014 (vs the lock net's 0.014310 / 0.004572) and jobA val;
#   4. pin_check: OFF = lock pins (-Full), ON with the net: bench d11/d13/d16 twice (must be equal = deterministic),
#      perft = pins;
#   5. RESULT.json with every number.
# CPUs 0-1 at Idle (pin_check / lowrun). Exit 0 = every check passed.
set -uo pipefail
name="$1"; net="$2"; exe="$3"; harness="$4"
A=$(cd "$(dirname "$0")" && pwd); T="$A/../tools"
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
out=/d/o30/nets/$name
[ -e "$out" ] && { echo "refusing: $out exists" >&2; exit 2; }
mkdir -p "$out"
cp "$net" "$out/$name.nnue2"
N="$out/$name.nnue2"; NW=$(cygpath -w "$N"); EW=$(cygpath -w "$exe")
fail=0
"$PY" -I -B "$A/o30_v2net.py" info "$NW" > "$out/info.txt" || fail=1
sha=$(sha256sum "$N" | cut -c1-64); md5=$(md5sum "$N" | cut -c1-32)
bash "$A/parity_o30.sh" "$out/parity" /c/o13/p4/fens10k.txt "$harness" "$N" > "$out/parity.txt" 2>&1 || fail=1
S16P='F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos'; S16H='F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.hce'
/d/o30/tools_bin/o30_score_v2.exe --net "$NW" --pos "$S16P" --hce "$S16H" > "$out/score_s16.json" || fail=1
/d/o30/tools_bin/o30_score_v2.exe --net "$NW" --pos 'D:\o30\data\jobA_val.pos' --hce 'D:\o30\data\jobA_val.hce' > "$out/score_jobA_val.json" || fail=1
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Exe "$EW" -Full > "$out/pins_off.txt" 2>&1 || fail=1
for i in 1 2; do
  powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Exe "$EW" -Options "EvalFileV2=$NW" > "$out/pins_on_$i.txt" 2>&1 || fail=1
done
on1=$(grep '^bench' "$out/pins_on_1.txt" | awk '{print $2"="$3}' | paste -sd, -); on2=$(grep '^bench' "$out/pins_on_2.txt" | awk '{print $2"="$3}' | paste -sd, -)
[ -n "$on1" ] && [ "$on1" = "$on2" ] || { echo "ON bench differs between runs: $on1 / $on2"; fail=1; }
"$PY" -I -B - "$out" "$name" "$NW" "$sha" "$md5" "$EW" "$(sha256sum "$exe" | cut -c1-64)" "$on1" "$fail" <<'EOF'
import json, sys
out, name, net, sha, md5, exe, exe_sha, on1, fail = sys.argv[1:]
rec = {'name': name, 'net': net, 'sha256': sha, 'md5': md5, 'exe': exe, 'exe_sha256': exe_sha,
       'gate_option': f'EvalFileV2={net}', 'bench_on': on1,
       'info': open(f'{out}/info.txt').read().strip(),
       'parity': [l.strip() for l in open(f'{out}/parity.txt') if 'PASS' in l or 'FAIL' in l or 'planted' in l],
       'score_s16': json.loads(open(f'{out}/score_s16.json').read()),
       'score_jobA_val': json.loads(open(f'{out}/score_jobA_val.json').read()),
       'pins_off': open(f'{out}/pins_off.txt').read().splitlines()[0],
       'pins_on': open(f'{out}/pins_on_1.txt').read().splitlines()[0],
       'all_checks_passed': fail == '0'}
with open(f'{out}/RESULT.json', 'x', newline='\n') as f:
    json.dump(rec, f, indent=1)
print(json.dumps({k: rec[k] for k in ('name', 'sha256', 'bench_on', 'pins_off', 'pins_on', 'all_checks_passed')}, indent=1))
print('s16', rec['score_s16']['mse_b0.6'], rec['score_s16']['mse_b1.0'], 'jobA', rec['score_jobA_val']['mse_b0.6'])
EOF
exit $fail
