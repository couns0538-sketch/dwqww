#!/usr/bin/env bash
# Run depth_harness.py on a sanitizer build and record the asan symbol count
# in that run's .meta. Usage: asan_depth.sh EXE FENS DEPTH PREFIX [options...]
set -u
EXE="$1"
FENS="$2"
DEPTH="$3"
PREFIX="$4"
shift 4
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
D="forge-combo29/grok/$S"
COUNT=$(nm -C "$EXE" | grep -c __asan_ || true)
python3 "$D/depth_harness.py" "$EXE" "$FENS" "$DEPTH" "$PREFIX" "$@"
STATUS=$?
{
  echo "nm_asan_count=$COUNT"
  echo "nm_command=nm -C $EXE | grep -c __asan_"
} >> "${PREFIX}.meta"
echo "nm_asan_count=$COUNT harness_status=$STATUS"
exit "$STATUS"
