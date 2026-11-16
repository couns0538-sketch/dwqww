#!/usr/bin/env bash
# annotate.sh EXE OUTDIR REPS : perf record of `bench 13` x REPS, then `perf annotate --stdio` (whole binary,
# symbol-by-symbol) and a compressed hot-instruction extract. Text only; perf.data is deleted afterwards.
set -u
EXE="${1:?exe}"; OUT="${2:?outdir}"; REPS="${3:-15}"
mkdir -p "$OUT"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
HERE="$(cd "$(dirname "$0")" && pwd)"
EXE_ABS="$(readlink -f "$EXE")"
{ for i in $(seq 1 "$REPS"); do echo "bench 13"; done; echo quit; } > "$OUT/bench13.stdin.txt"
{
  echo "exe $EXE_ABS"; sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "perf: $("$PERF" --version)"; echo "perf_event_paranoid: $(cat /proc/sys/kernel/perf_event_paranoid)"
  echo "command: perf record -o DATA -F 1999 -g -- EXE < bench13.stdin.txt ; perf annotate -i DATA --stdio"
  echo "stdin: \"bench 13\" x $REPS, then quit"; echo "options sent: none"
  echo "cores: $(nproc)"; echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/annotate.meta" 2>&1
"$PERF" record -o "$OUT/perf.data" -F 1999 -g -- "$EXE_ABS" < "$OUT/bench13.stdin.txt" \
  > "$OUT/bench13.stdout.txt" 2> "$OUT/perf.record.stderr.txt"
echo "record exit $?" >> "$OUT/annotate.meta"
"$PERF" annotate -i "$OUT/perf.data" --stdio > "$OUT/annotate_full.txt" 2>&1
rm -f "$OUT/perf.data"
python3 "$HERE/hot_lines.py" "$OUT/annotate_full.txt" "$OUT/hot_instructions.txt"
# the full annotate text is huge; keep only the compact extract and the two summaries
"$PERF" report -i /dev/null --help > /dev/null 2>&1 || true
rm -f "$OUT/annotate_full.txt"
date -u
grep -cE '^info string bench depth 13 nodes 862329' "$OUT/bench13.stdout.txt"
wc -l "$OUT/hot_instructions.txt"
