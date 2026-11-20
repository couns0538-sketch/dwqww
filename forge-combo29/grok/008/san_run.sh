#!/usr/bin/env bash
# Same runner for the real sanitizer build and the scratch build.
# Leak reports at process exit are turned off. The scratch heap read is the proof the sanitizer reports.
set -u
export ASAN_OPTIONS=detect_leaks=0:abort_on_error=1:halt_on_error=1
export UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1
DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$DIR/depth_sum.py" "$@"
status=$?
echo "san_run_exit=$status"
exit "$status"
