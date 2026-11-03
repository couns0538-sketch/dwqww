#!/usr/bin/env bash
# measure_rates.sh STEP BASE_DIR - Opus R14-B item 2: the cost numbers for RELABEL_HANDOFF.md, measured, not estimated.
# Input for every step: BASE_DIR/in220k.txt = the first 220,000 lines of forge_selfplay_003.txt (not in the 1M proof;
# ~14 MB, so hashing the input stays out of the rates). Idle on CPUs 2-3 (mask 0xC) like a real job.
#   workers : 1 vs 2 probe workers on the same 20,000 rows, 20k nodes, order W1 W2 W2 W1 (ABBA against load drift);
#             every job is assembled and labels.tsv must have the same md5 in all four (labels do not depend on the
#             worker count)
#   nodes   : 1 worker, 10,000 rows (the first half of the same rows) at 5,000 and at 10,000 nodes
#   prepare : prepare alone on 200,000 rows, --jobs 1 vs 2 in the order 1 2 2 1; rows.tsv identical in all four
# Every job is a new folder under BASE_DIR (nothing reused or overwritten). Prints one summary line per job.
set -u
step=${1:?step}
base=${2:?base dir}
PY=${PY:-/c/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe}
R=$(cd "$(dirname "$0")" && pwd)/relabel2.py
P=${PROBE:-'C:\o13\p5\forge_data_probe.exe'}
SRC=/d/grok-pc-data/selfplay_out/forge_selfplay_003.txt
# bug hunt #15: an unknown step used to create BASE_DIR and write the 14 MB input before it was refused
case $step in workers | nodes | prepare) ;; *) echo "unknown step $step (workers | nodes | prepare)" >&2; exit 2 ;; esac
for f in "$PY" "$R" "$P" "$SRC"; do [ -f "$f" ] || { echo "not found: $f (set PY / PROBE)" >&2; exit 2; }; done
mkdir -p "$base"
in=$base/in220k.txt
if [ ! -e "$in" ]; then  # via .part: a killed head used to leave a short input that later runs reused silently
  [ -e "$in.part" ] && { echo "refusing: $in.part exists (left by an interrupted run) - move it aside" >&2; exit 2; }
  head -n 220000 "$SRC" > "$in.part" && mv "$in.part" "$in" || exit 2
fi
[ "$(wc -l < "$in")" = 220000 ] || { echo "$in does not hold 220,000 lines: not the measured input" >&2; exit 2; }
num() { sed -n "s/.*\"$2\": \([0-9]*\).*/\1/p" "$1" | head -1; }   # num FILE KEY: first integer value of KEY
same() {  # same WHAT FILE...: the files must be byte-identical; was printed for the reader only (bug hunt #15)
  local what=$1 n; shift
  n=$(for f in "$@"; do md5sum < "$f"; done | sort -u | wc -l)
  if [ "$n" = 1 ]; then echo "PASS $what identical in all $#"; else echo "FAIL $what: $n different versions in $#"; exit 1; fi
}
job() {  # job NAME ROWS NODES WORKERS
  local j=$base/$1
  [ -e "$j" ] && { echo "refusing existing $j" >&2; exit 2; }
  "$PY" -I -B "$R" prepare --job "$j" --run-id "$1" --rows "$2" --selfplay "$in" >/dev/null || exit $?
  local t0 t1
  t0=$(date +%s.%N)
  "$PY" -I -B "$R" run --job "$j" --run-id "$1" --probe "$P" --nodes "$3" --workers "$4" --mask 0xC \
    --shard-size 10000 >/dev/null || exit $?
  t1=$(date +%s.%N)
  "$PY" -I -B "$R" assemble --job "$j" --run-id "$1" >/dev/null || exit $?
  local rows nodes_total
  rows=$(num "$j/prepare.json" rows)
  nodes_total=$(for s in "$j"/shards/shard_?????/summary.json; do num "$s" nodes_total; done | awk '{t += $1} END {print t}')
  awk -v n="$1" -v r="$rows" -v nd="$3" -v w="$4" -v a="$t0" -v b="$t1" -v nt="$nodes_total" \
      -v md5="$(md5sum < "$j/final/labels.tsv" | cut -c1-32)" -v now="$(date '+%T')" \
      'BEGIN {printf "%s rows=%d nodes=%d workers=%d run_wall_s=%.1f rows_per_hour=%.0f mean_nodes=%.0f labels_md5=%s %s\n",
              n, r, nd, w, b - a, r * 3600 / (b - a), nt / r, md5, now}'
}
case $step in
  workers)
    for spec in "w1a 1" "w2a 2" "w2b 2" "w1b 1"; do set -- $spec; job "$1" 20000 20000 "$2"; done
    same labels.tsv "$base"/w1a/final/labels.tsv "$base"/w2a/final/labels.tsv "$base"/w2b/final/labels.tsv \
      "$base"/w1b/final/labels.tsv ;;
  nodes)
    job n5k 10000 5000 1
    job n10k 10000 10000 1 ;;
  prepare)  # --jobs 1 vs 2 in the order 1 2 2 1; rows.tsv must be the same file in all four
    for spec in "p1a 1" "p2a 2" "p2b 2" "p1b 1"; do
      set -- $spec
      j=$base/prep200k_$1
      [ -e "$j" ] && { echo "refusing existing $j" >&2; exit 2; }
      t0=$(date +%s.%N)
      "$PY" -I -B "$R" prepare --job "$j" --run-id "prep200k_$1" --rows 200000 --jobs "$2" \
        --selfplay "$in" >/dev/null || exit $?
      t1=$(date +%s.%N)
      awk -v n="$1" -v w="$2" -v r="$(num "$j/prepare.json" rows)" -v a="$t0" -v b="$t1" -v now="$(date '+%T')" \
        -v h="$(sha256sum < "$j/rows.tsv" | cut -c1-16)" \
        'BEGIN {printf "prep200k_%s jobs=%d rows=%d wall_s=%.1f rows_per_hour=%.0f rows_tsv=%s %s\n", n, w, r, b - a, r * 3600 / (b - a), h, now}'
    done
    same rows.tsv "$base"/prep200k_p1a/rows.tsv "$base"/prep200k_p2a/rows.tsv "$base"/prep200k_p2b/rows.tsv \
      "$base"/prep200k_p1b/rows.tsv ;;
  *) echo "unknown step $step" >&2; exit 2 ;;
esac
