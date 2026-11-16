#!/usr/bin/env bash
# profile_drive.sh EXE FENS OUTDIR DEPTH LIMIT : profile a correctly-driven search (waits for bestmove).
#
# The driver must wait for `bestmove` after every `go` (19-F12: a terminator sent during a search makes this
# build answer a fabricated `bestmove a2a3` with 0 nodes). drive_search.py does that; this script runs it
# under perf so the samples belong to real searches, and refuses to report if any search came out at 0 nodes.
set -u
EXE="${1:?exe}"; FENS="${2:?fens}"; OUT="${3:?outdir}"; DEPTH="${4:-12}"; LIMIT="${5:-200}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$OUT"
PERF=/usr/lib/linux-tools/6.8.0-149-generic/perf
EXE_ABS="$(readlink -f "$EXE")"
{
  echo "exe $EXE_ABS"; sha256sum "$EXE_ABS"
  printf 'uci\nquit\n' | "$EXE_ABS" 2>&1 | tr -d '\r' | grep -E '^id name'
  echo "perf: $("$PERF" --version)"; echo "perf_event_paranoid: $(cat /proc/sys/kernel/perf_event_paranoid)"
  echo "driver: drive_search.py (waits for bestmove after every go — see 19-F12)"
  echo "positions: first $LIMIT of $FENS ; depth $DEPTH ; S14 + OwnBook false ; isready after every command"
  echo "command: perf record -o DATA -F 1999 -g -- python3 drive_search.py EXE FENS OUT $DEPTH $LIMIT"
  echo "cores: $(nproc)"; echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/profile.meta" 2>&1

"$PERF" record -o "$OUT/perf.data" -F 1999 -g -- \
  python3 "$HERE/drive_search.py" "$EXE_ABS" "$FENS" "$OUT/drive" "$DEPTH" "$LIMIT" \
  > "$OUT/driver.log" 2> "$OUT/perf.record.stderr.txt"
echo "record exit $?" >> "$OUT/profile.meta"

"$PERF" report -i "$OUT/perf.data" --stdio --no-children -g none --sort symbol > "$OUT/perf_symbols_all.txt" 2>&1
"$PERF" report -i "$OUT/perf.data" --stdio --children --sort symbol > "$OUT/perf_children.txt" 2>&1
rm -f "$OUT/perf.data"
date -u
grep -E "searches reporting 0 nodes|refusal lines|total nodes" "$OUT/drive/results.txt"
grep -E '^# Samples:' "$OUT/perf_symbols_all.txt"
