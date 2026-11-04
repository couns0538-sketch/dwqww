#!/usr/bin/env bash
# gpu_ckpt_watch.sh <run> <kb map one|rank4|rank4x2> [--mirror] - Opus 30-h job, GPU window: export + score every
# checkpoint of D:\o30\gpu\<run> as it lands (Idle, CPU 2), until the run's guard log has its "end:" line and every
# checkpoint is scored. Per checkpoint: export_v2r.py -> D:\o30\gpu\<run>_nets\<ckpt>.nnue2, o30_score_v3 on the S31
# subset and jobA val (per-row dumps), o30_paired.py vs the lock net's dumps; one line per checkpoint in
# D:\o30\gpu\<run>_scores.tsv: ckpt, S31 b0.6, b1.0, paired S31 diff + z, jobA, paired jobA diff + z.
set -uo pipefail
run="$1"; kb="$2"; mir="${3:-}"
A=/d/o30/wt/opus_30h/a; T="$A/../tools"
. "$T/idle.sh"; o30_pin_self 0x4 || { echo "watch: cannot pin to Idle / CPU 2" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
dir=/d/o30/gpu/$run; nets=/d/o30/gpu/${run}_nets; tsv=/d/o30/gpu/${run}_scores.tsv
mkdir -p "$nets"
[ -f "$tsv" ] || printf 'ckpt\ts31_b06\ts31_b10\tpaired_s31\tz_s31\tjobA_b06\tpaired_jobA\tz_jobA\tsha256\n' > "$tsv"
S16P='F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos'; S16H='F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.hce'
score_one() {
  local ck="$1" name; name=$(basename "$ck")
  [ -f "$nets/$name.done" ] && return 0
  [ -f "$ck/quantised.bin" ] || return 1
  local N="$nets/$name.nnue2"; local NW; NW=$(cygpath -w "$N")
  "$PY" -I -B "$A/export_v2r.py" "$(cygpath -w "$ck/quantised.bin")" "$NW" --kb-map "$kb" $mir > "$nets/$name.export.txt" 2>&1 || return 1
  /d/o30/tools_bin/o30_score_v3.exe --net "$NW" --pos "$S16P" --hce "$S16H" --dump "$(cygpath -w "$nets/$name.s16.f64")" > "$nets/$name.s16.json" || return 1
  /d/o30/tools_bin/o30_score_v3.exe --net "$NW" --pos 'D:\o30\data\jobA_val.pos' --hce 'D:\o30\data\jobA_val.hce' \
    --dump "$(cygpath -w "$nets/$name.jobA.f64")" > "$nets/$name.jobA.json" || return 1
  "$PY" -I -B "$A/o30_paired.py" "$(cygpath -w "$nets/$name.s16.f64")" 'D:\o30\dumps\s16_lock.f64' > "$nets/$name.paired_s16.json" || return 1
  "$PY" -I -B "$A/o30_paired.py" "$(cygpath -w "$nets/$name.jobA.f64")" 'D:\o30\dumps\jobA_lock.f64' > "$nets/$name.paired_jobA.json" || return 1
  "$PY" -I -B - "$nets" "$name" "$(sha256sum "$N" | cut -c1-64)" >> "$tsv" <<'EOF'
import json, sys
d, n, sha = sys.argv[1:4]
s = json.load(open(f'{d}/{n}.s16.json')); j = json.load(open(f'{d}/{n}.jobA.json'))
ps = json.load(open(f'{d}/{n}.paired_s16.json')); pj = json.load(open(f'{d}/{n}.paired_jobA.json'))
def g(p, *keys):
    for k in keys:
        if k in p: return p[k]
    return ''
print('\t'.join(str(x) for x in (n, s['mse_b0.6'], s['mse_b1.0'], g(ps, 'diff_a_minus_b'), g(ps, 'z'),
                                 j['mse_b0.6'], g(pj, 'diff_a_minus_b'), g(pj, 'z'), sha)))
EOF
  touch "$nets/$name.done"
}
while true; do
  for ck in $(ls -d "$dir"/*-[0-9]* 2>/dev/null | sort -t- -k2 -n); do
    # a checkpoint directory is complete once its quantised.bin has stopped growing for 20 s
    q="$ck/quantised.bin"; [ -f "$q" ] || continue
    age=$(( $(date +%s) - $(stat -c %Y "$q") )); [ "$age" -ge 20 ] || continue
    score_one "$ck" || echo "$(date '+%F %T') score failed for $ck" >> "$tsv.errors"
  done
  if grep -q ' end: ' "/d/o30/gpu/$run.guard.log" 2>/dev/null; then
    left=0
    for ck in "$dir"/*-[0-9]*; do [ -f "$nets/$(basename "$ck").done" ] || left=1; done
    [ "$left" = 0 ] && break
  fi
  sleep 60
done
echo "$(date '+%F %T') watch $run done"
