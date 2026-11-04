#!/usr/bin/env bash
# gpu_ckpt_watch2.sh = gpu_ckpt_watch.sh with the independent review's fixes W2-01 (a retry first moves the failed try's
# outputs aside as <file>.try<N> - the exporter and the scorer refuse existing outputs, so retries could never succeed),
# W2-05 (WATCH_MASK required: the old defaults 0x4 / CPU 2 landed on a sanity-match CPU), W2-06 (the new guard's
# "guard exits" line counts as a guard-exit) and W2-07 (TSV rows LF). New name because watchers of running GPU runs
# execute the old file (bash reads a running script lazily).
# gpu_ckpt_watch.sh <run> <kb map one|rank4|rank4x2|rank4x4|rank4x8> [--mirror] - Opus 30-h job, GPU window: export +
# score every checkpoint of <root>\<run> as it lands (Idle), until the run's guard log has its "end:" line and every
# checkpoint is scored. Per checkpoint: export_v2r.py -> <root>\<run>_nets\<ckpt>.nnue2, o30_score_v3 on the S31
# subset and jobA val (per-row dumps), o30_paired.py vs the lock net's dumps; one line per checkpoint in
# <root>\<run>_scores.tsv: ckpt, S31 b0.6, b1.0, paired S31 diff + z, jobA, paired jobA diff + z.
# A checkpoint gets <ckpt>.done only when every step, the TSV line included, exited 0 (CR item 12).
# Bounded (CR item 12): a checkpoint that fails WATCH_TRIES times gets <ckpt>.gaveup and a GIVE UP line; the watch
# itself gives up (exit 3) after WATCH_MAX_MIN minutes without the guard's end line, or at once (exit 4) when the guard
# log shows an ABORT / guard-exit line (no end line will come). Exit 5 = run ended but some checkpoint was given up.
# Env: WATCH_MASK (CPU mask, default 0x4 = CPU 2), WATCH_ROOT (default /d/o30/gpu), WATCH_MAX_MIN (default 720),
# WATCH_TRIES (default 3), WATCH_SLEEP (seconds between scans, default 60), WATCH_TEST_FAIL_TSV=1 (test only: the
# TSV step exits 1).
set -uo pipefail
run="$1"; kb="$2"; mir="${3:-}"
A=/d/o30/wt/opus_30h/a; T="$A/../tools"
[ -n "${WATCH_MASK:-}" ] || { echo "watch: set WATCH_MASK (no default: CPUs 0-2 and 6 run sanity matches)" >&2; exit 78; }
MASK="$WATCH_MASK"; ROOT="${WATCH_ROOT:-/d/o30/gpu}"; MAXMIN="${WATCH_MAX_MIN:-720}"; TRIES="${WATCH_TRIES:-3}"
. "$T/idle.sh"; o30_pin_self "$MASK" || { echo "watch: cannot pin to Idle / $MASK" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
dir=$ROOT/$run; nets=$ROOT/${run}_nets; tsv=$ROOT/${run}_scores.tsv; glog=$ROOT/$run.guard.log
mkdir -p "$nets"
[ -f "$tsv" ] || printf 'ckpt\ts31_b06\ts31_b10\tpaired_s31\tz_s31\tjobA_b06\tpaired_jobA\tz_jobA\tsha256\n' > "$tsv"
S16P='F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos'; S16H='F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.hce'
score_one() {
  local ck="$1" name; name=$(basename "$ck")
  [ -f "$nets/$name.done" ] && return 0
  [ -f "$ck/quantised.bin" ] || return 1
  # W2-01: outputs of an earlier failed try are moved aside (never deleted) so the exporter / scorer can write again
  local tries f; tries=$(cat "$nets/$name.fails" 2>/dev/null || echo 0)
  if [ "$tries" -gt 0 ]; then
    for f in "$nets/$name".*; do
      case "$f" in *.fails|*.gaveup|*.try[0-9]*) ;; *) [ -e "$f" ] && mv "$f" "$f.try$tries" ;; esac
    done
  fi
  local N="$nets/$name.nnue2"; local NW; NW=$(cygpath -w "$N")
  "$PY" -I -B "$A/export_v2r.py" "$(cygpath -w "$ck/quantised.bin")" "$NW" --kb-map "$kb" $mir > "$nets/$name.export.txt" 2>&1 || return 1
  /d/o30/tools_bin/o30_score_v3.exe --net "$NW" --pos "$S16P" --hce "$S16H" --dump "$(cygpath -w "$nets/$name.s16.f64")" > "$nets/$name.s16.json" || return 1
  /d/o30/tools_bin/o30_score_v3.exe --net "$NW" --pos 'D:\o30\data\jobA_val.pos' --hce 'D:\o30\data\jobA_val.hce' \
    --dump "$(cygpath -w "$nets/$name.jobA.f64")" > "$nets/$name.jobA.json" || return 1
  "$PY" -I -B "$A/o30_paired.py" "$(cygpath -w "$nets/$name.s16.f64")" 'D:\o30\dumps\s16_lock.f64' > "$nets/$name.paired_s16.json" || return 1
  "$PY" -I -B "$A/o30_paired.py" "$(cygpath -w "$nets/$name.jobA.f64")" 'D:\o30\dumps\jobA_lock.f64' > "$nets/$name.paired_jobA.json" || return 1
  local failarg="${WATCH_TEST_FAIL_TSV:-0}"   # test hook: 1 = the TSV step always fails, once = only on the first try
  if [ "$failarg" = once ]; then if [ "$tries" -eq 0 ]; then failarg=1; else failarg=0; fi; fi
  "$PY" -I -B - "$nets" "$name" "$(sha256sum "$N" | cut -c1-64)" "$failarg" >> "$tsv" <<'EOF' || return 1
import json, sys
sys.stdout.reconfigure(newline=chr(10))   # W2-07: LF rows like the header
d, n, sha, fail = sys.argv[1:5]
if fail == '1':
    sys.exit('test: the TSV step is made to fail (WATCH_TEST_FAIL_TSV=1)')
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
t0=$(date +%s); gave=0
while true; do
  for ck in $(ls -d "$dir"/*-[0-9]* 2>/dev/null | sort -t- -k2 -n); do
    # a checkpoint directory is complete once its quantised.bin has stopped growing for 20 s
    q="$ck/quantised.bin"; [ -f "$q" ] || continue
    age=$(( $(date +%s) - $(stat -c %Y "$q") )); [ "$age" -ge 20 ] || continue
    b=$(basename "$ck"); [ -f "$nets/$b.gaveup" ] && continue
    if ! score_one "$ck"; then
      n=$(( $(cat "$nets/$b.fails" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$nets/$b.fails"
      echo "$(date '+%F %T') score failed for $ck (try $n of $TRIES)" >> "$tsv.errors"
      if [ "$n" -ge "$TRIES" ]; then
        touch "$nets/$b.gaveup"; gave=1
        echo "$(date '+%F %T') GIVE UP on $ck after $n failed tries (no .done written)" | tee -a "$tsv.errors"
      fi
    fi
  done
  if grep -q ' end: ' "$glog" 2>/dev/null; then
    left=0
    for ck in "$dir"/*-[0-9]*; do
      [ -e "$ck" ] || continue
      b=$(basename "$ck"); [ -f "$nets/$b.done" ] || [ -f "$nets/$b.gaveup" ] || left=1
    done
    [ "$left" = 0 ] && break
  elif grep -q -E 'ABORT|GUARD EXIT WHILE THE TRAINER RUNS|guard exits' "$glog" 2>/dev/null; then
    echo "$(date '+%F %T') GIVE UP: the guard log of $run has an ABORT / guard-exit line; no end line will come" | tee -a "$tsv.errors"
    exit 4
  fi
  if [ $(( ($(date +%s) - t0) / 60 )) -ge "$MAXMIN" ]; then
    echo "$(date '+%F %T') GIVE UP: no end line in $glog after $MAXMIN min (WATCH_MAX_MIN)" | tee -a "$tsv.errors"
    exit 3
  fi
  sleep "${WATCH_SLEEP:-60}"
done
if [ "$gave" = 1 ] || ls "$nets"/*.gaveup > /dev/null 2>&1; then
  echo "$(date '+%F %T') watch $run done, some checkpoints given up (see $tsv.errors)"; exit 5
fi
echo "$(date '+%F %T') watch $run done"
