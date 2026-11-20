#!/usr/bin/env bash
# Same runner and sanitizer flags as run_asan.sh, on the one-FEN heap overrun.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
nm -C /tmp/forge-asan-bad/forge | grep -c __asan_ > "$DIR/scratch_nm_count.txt" || true
export ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
set +e
python3 "$DIR/search_positions.py" /tmp/forge-asan-bad/forge "$DIR/scratch.fen" 10 "$DIR/scratch_asan.txt" "setoption name IdeaS27 value true"
code=$?
set -e
{
  echo "exe /tmp/forge-asan-bad/forge"
  echo "asan_symbol_count $(cat "$DIR/scratch_nm_count.txt")"
  echo "runner_exit $code"
  echo "ASAN_OPTIONS $ASAN_OPTIONS"
  echo "UBSAN_OPTIONS $UBSAN_OPTIONS"
} >> "$DIR/scratch_asan.txt.meta"
echo "SCRATCH_RUN_EXIT $code"
grep -n -E "AddressSanitizer|heap-buffer-overflow|runtime error" "$DIR/scratch_asan.txt" | head -n 20 || true
