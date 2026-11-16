#!/usr/bin/env bash
# profile.sh EXE OUTDIR REPS : perf record of `bench 13` repeated REPS times (one process), text report only.
# The perf.data binary is deleted after the reports are written; nothing binary is committed.
set -u
EXE="${1:?exe}"; OUT="${2:?outdir}"; REPS="${3:-40}"
mkdir -p "$OUT"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
EXE_ABS="$(readlink -f "$EXE")"
{ for i in $(seq 1 "$REPS"); do echo "bench 13"; done; echo quit; } > "$OUT/bench13.stdin.txt"
{
  echo "exe $EXE_ABS"; sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "perf: $("$PERF" --version)"
  echo "perf_event_paranoid: $(cat /proc/sys/kernel/perf_event_paranoid)"
  echo "command: perf record -o DATA -F 999 -g -- EXE < bench13.stdin.txt   (DATA deleted after reports)"
  echo "stdin: \"bench 13\" x $REPS, then quit  (one engine process; bench builds its own Searcher(16) per line)"
  echo "options sent: none (bench takes no setoption; S14 not used by bench)"
  echo "cores: $(nproc)"; echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/profile.meta" 2>&1

"$PERF" record -o "$OUT/perf.data" -F 999 -- "$EXE_ABS" < "$OUT/bench13.stdin.txt" \
  > "$OUT/bench13.stdout.txt" 2> "$OUT/perf.record.stderr.txt"
echo "record exit $?" >> "$OUT/profile.meta"
"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --sort symbol \
  --percent-limit 0.5 > "$OUT/perf_symbols.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --sort symbol \
  > "$OUT/perf_symbols_all.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio -g graph,0.5,caller --sort symbol \
  > "$OUT/perf_callers.txt" 2>&1
rm -f "$OUT/perf.data"
date -u
grep -cE '^info string bench depth 13 nodes 862329' "$OUT/bench13.stdout.txt"
grep -E '^# Samples:' "$OUT/perf_symbols.txt"
