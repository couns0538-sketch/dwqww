#!/usr/bin/env bash
# AddressSanitizer + UBSan build, IdeaS27 on, first 100 of G at depth 10.
set -u
S=$(cat ~/grok_seat.txt)
cd "$(cat ~/grok_repo.txt)"
DIR="forge-combo29/grok/$S"
head -n 100 /tmp/G.epd > "$DIR/g_first100.epd"
nm -C /tmp/forge-asan/forge | grep -c __asan_ > "$DIR/asan_nm_count.txt" || true
export ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:abort_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
set +e
python3 "$DIR/search_positions.py" /tmp/forge-asan/forge "$DIR/g_first100.epd" 10 "$DIR/asan_g100_d10.txt" "setoption name IdeaS27 value true"
code=$?
set -e
{
  echo "asan_symbol_count $(cat "$DIR/asan_nm_count.txt")"
  echo "runner_exit $code"
  echo "ASAN_OPTIONS $ASAN_OPTIONS"
  echo "UBSAN_OPTIONS $UBSAN_OPTIONS"
} >> "$DIR/asan_g100_d10.txt.meta"
echo "ASAN_RUN_EXIT $code"
