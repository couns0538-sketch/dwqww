#!/usr/bin/env bash
# net_pack.sh <name> <net.nnue2> <engine exe that loads it (EvalFileV2)> <harness dir (v2_eval_{avx2,sse,scalar}.exe)>
# One step from a trained v2 net to its evidence folder D:\o30\nets\<name>\ (refused when it exists):
#   1. copy the net (never moved), header + checksum check (o30_v2net.py info), sha256 + md5;
#   2. parity: own float32 reference vs the engine's AVX2 / SSE / scalar kernels on 10,000 legal FENs + planted bug;
#   3. holdout scores (o30_score_v3.exe, per-row dumps): S31 subset of 013/014 (vs the lock net's 0.014310 / 0.004572)
#      and jobA val; paired differences vs the lock net (o30_paired.py) and the written offline rule's verdict;
#   4. pin_check: OFF = lock pins (-Full), ON with the net: bench d11/d13/d16 twice (must be equal = deterministic),
#      perft = pins;
#   5. RESULT.json with every number.
# Idle on O30_MASK (required; review W2-05) for every step, pin_check included. Exit 0 = every check passed.
set -uo pipefail
name="$1"; net="$2"; exe="$3"; harness="$4"
A=$(cd "$(dirname "$0")" && pwd); T="$A/../tools"
# pin this shell first: every program below (python, scorer, harness, powershell) inherits Idle + the mask (O30_MASK)
# review W2-05: no default mask - the old default 0x3 landed on the CPUs of running sanity matches
[ -n "${O30_MASK:-}" ] || { echo "net_pack: set O30_MASK (the CPU mask for every step; no default)" >&2; exit 78; }
. "$T/idle.sh"; o30_pin_self "$O30_MASK" || { echo "net_pack: cannot pin to Idle / $O30_MASK (fail closed)" >&2; exit 78; }
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
/d/o30/tools_bin/o30_score_v3.exe --net "$NW" --pos "$S16P" --hce "$S16H" --dump "$(cygpath -w "$out/s16.f64")" > "$out/score_s16.json" || fail=1
/d/o30/tools_bin/o30_score_v3.exe --net "$NW" --pos 'D:\o30\data\jobA_val.pos' --hce 'D:\o30\data\jobA_val.hce' \
  --dump "$(cygpath -w "$out/jobA_val.f64")" > "$out/score_jobA_val.json" || fail=1
# paired vs the lock net's per-row dumps (same scorer, same rows; D:\o30\dumps\*_lock.f64 = 0.014310027 / 0.013272058)
"$PY" -I -B "$A/o30_paired.py" "$(cygpath -w "$out/s16.f64")" 'D:\o30\dumps\s16_lock.f64' > "$out/paired_s16.json" || fail=1
"$PY" -I -B "$A/o30_paired.py" "$(cygpath -w "$out/jobA_val.f64")" 'D:\o30\dumps\jobA_lock.f64' > "$out/paired_jobA_val.json" || fail=1
# pin_check.ps1 sets its own mask (default 0x3): pass the same override as this shell (O30_MASK), or it lands on 0-1
PCMASK="$O30_MASK"
powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Exe "$EW" -Full -Mask "$PCMASK" > "$out/pins_off.txt" 2>&1 || fail=1
for i in 1 2; do
  powershell -NoProfile -ExecutionPolicy Bypass -File "$(cygpath -w "$T/pin_check.ps1")" -Exe "$EW" -Options "EvalFileV2=$NW" -Mask "$PCMASK" > "$out/pins_on_$i.txt" 2>&1 || fail=1
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
# the written offline rule (a/RESULTS.md): S31 b0.6 >= 2e-5 below the lock net AND paired jobA z <= +2. A net that fails
# it is still packaged; the verdict is recorded, never used to drop the net.
ps = json.loads(open(f'{out}/paired_s16.json').read()); pj = json.loads(open(f'{out}/paired_jobA_val.json').read())
rec['paired_s16_vs_lock'] = ps
rec['paired_jobA_val_vs_lock'] = pj
rec['offline_rule'] = {'s16_b06_diff': ps['diff_a_minus_b'], 's16_z': ps['z'], 'jobA_b06_diff': pj['diff_a_minus_b'],
                       'jobA_z': pj['z'], 'pass': ps['diff_a_minus_b'] <= -2e-5 and pj['z'] is not None and pj['z'] <= 2.0}
with open(f'{out}/RESULT.json', 'x', newline='\n') as f:
    json.dump(rec, f, indent=1)
print(json.dumps({k: rec[k] for k in ('name', 'sha256', 'bench_on', 'pins_off', 'pins_on', 'all_checks_passed')}, indent=1))
print('s16', rec['score_s16']['mse_b0.6'], rec['score_s16']['mse_b1.0'], 'jobA', rec['score_jobA_val']['mse_b0.6'])
print('offline rule', json.dumps(rec['offline_rule']))
EOF
exit $fail
