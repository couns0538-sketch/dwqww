#!/usr/bin/env bash
# Same runner for the real sanitizer pass and the deliberate heap-overflow copy.
# Usage: asan_runner.sh EXE FENS DEPTH RAW [Name=value ...]
set -u
EXE="$1"
FENS="$2"
DEPTH="$3"
RAW="$4"
shift 4
S=$(cat ~/grok_seat.txt)
DIR="$(cat ~/grok_repo.txt)/forge-combo29/grok/$S"
export ASAN_OPTIONS="${ASAN_OPTIONS:-detect_leaks=0:halt_on_error=1:abort_on_error=1}"
export UBSAN_OPTIONS="${UBSAN_OPTIONS:-halt_on_error=1:print_stacktrace=1}"
nm -C "$EXE" | grep -c __asan_ > "$RAW.asan_count" || true
{
  echo "exe=$EXE"
  echo "asan_symbols=$(cat "$RAW.asan_count")"
  echo "ASAN_OPTIONS=$ASAN_OPTIONS"
  echo "UBSAN_OPTIONS=$UBSAN_OPTIONS"
} > "$RAW.runner_meta"
python3 "$DIR/depth_set.py" "$EXE" "$FENS" "$DEPTH" "$RAW" "$@" > "$RAW.rows" || echo "runner_exit=$?" >> "$RAW.runner_meta"
echo "sanitizer_lines=$(grep -E -c 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error' "$RAW" || true)" >> "$RAW.runner_meta"
echo "---- runner_meta ----"
cat "$RAW.runner_meta"
echo "---- sanitizer hits ----"
grep -E -n 'AddressSanitizer|UndefinedBehaviorSanitizer|runtime error' "$RAW" | head -n 20 || true
