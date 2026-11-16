#!/usr/bin/env bash
# profile_cg.sh EXE OUTDIR REPS : perf record WITH callchains of `bench 13` x REPS, caller tree kept as text.
# The perf.data binary is deleted after the reports; only text is kept.
set -u
EXE="${1:?exe}"; OUT="${2:?outdir}"; REPS="${3:-20}"
mkdir -p "$OUT"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
EXE_ABS="$(readlink -f "$EXE")"
{ for i in $(seq 1 "$REPS"); do echo "bench 13"; done; echo quit; } > "$OUT/bench13.stdin.txt"
{
  echo "exe $EXE_ABS"; sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "perf: $("$PERF" --version)"; echo "perf_event_paranoid: $(cat /proc/sys/kernel/perf_event_paranoid)"
  echo "command: perf record -o DATA -F 999 -g -- EXE < bench13.stdin.txt   (DATA deleted after reports)"
  echo "stdin: \"bench 13\" x $REPS, then quit"
  echo "options sent: none"; echo "cores: $(nproc)"; echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/profile.meta" 2>&1
"$PERF" record -o "$OUT/perf.data" -F 999 -g -- "$EXE_ABS" < "$OUT/bench13.stdin.txt" \
  > "$OUT/bench13.stdout.txt" 2> "$OUT/perf.record.stderr.txt"
echo "record exit $?" >> "$OUT/profile.meta"
"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --sort symbol \
  > "$OUT/perf_symbols_all.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --children --sort symbol > "$OUT/perf_children.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio -g graph,0.5,caller,function --sort symbol \
  > "$OUT/perf_caller_tree.txt" 2>&1
rm -f "$OUT/perf.data"
date -u
grep -cE '^info string bench depth 13 nodes 862329' "$OUT/bench13.stdout.txt"
grep -E '^# Samples:' "$OUT/perf_symbols_all.txt"
