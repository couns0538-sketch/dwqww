#!/usr/bin/env bash
# soup_score.sh <name> <kb map> <quantised.bin> <quantised.bin> ... - Opus 30-h job: average checkpoints of one shape
# (o30_soup.py) into C:\o30g\gpu\soups\<name>\<name>-1\quantised.bin and score it with the same code as every GPU
# checkpoint (gpu_ckpt_watch2.sh with WATCH_ROOT=C:\o30g\gpu\soups: export, S31 + jobA, paired vs the lock net, TSV
# line in C:\o30g\gpu\soups\<name>_scores.tsv). Idle on O30_MASK (default 0x38). Refuses an existing <name>.
set -uo pipefail
name="$1"; kb="$2"; shift 2
A=/d/o30/wt/opus_30h/a; T="$A/../tools"; R=/c/o30g/gpu/soups
. "$T/idle.sh"; o30_pin_self "${O30_MASK:-0x38}" || { echo "soup_score: cannot pin (fail closed)" >&2; exit 78; }
PY=C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe
[ -e "$R/$name" ] && { echo "refusing: $R/$name exists" >&2; exit 2; }
mkdir -p "$R/$name/$name-1"
args=()
for q in "$@"; do args+=("$(cygpath -w "$q")"); done
"$PY" -I -B "$A/o30_soup.py" --kb-map "$kb" --out "$(cygpath -w "$R/$name/$name-1/quantised.bin")" "${args[@]}" \
  > "$R/$name.soup.txt" 2>&1 || { cat "$R/$name.soup.txt"; exit 3; }
cat "$R/$name.soup.txt"
touch -d '-1 minute' "$R/$name/$name-1/quantised.bin"   # the watcher waits until a checkpoint is 20 s old
printf '%s\n' "$(date '+%F %T') soup $name of $# checkpoints (no trainer)" "$(date '+%F %T') end: soup written" > "$R/$name.guard.log"
WATCH_ROOT="$R" WATCH_MASK="${O30_MASK:-0x38}" WATCH_SLEEP=5 bash "$A/gpu_ckpt_watch2.sh" "$name" "$kb" > "$R/$name.watch.log" 2>&1
rc=$?
tail -1 "$R/${name}_scores.tsv"
echo "watch exit $rc"
exit $rc
