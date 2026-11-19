#!/usr/bin/env bash
set -euo pipefail
cd /workspace/work/sol-job41
limit=$1
case "$limit" in
    N2) ;;
    N1) test -s prediction.push.stamp ;;
    *) exit 2 ;;
esac
test -s step0.push.stamp
test "$(nproc)" = "$(cat pin-evidence/nproc.txt)"
cutoff=$(( $(cat claim.epoch) + 3000 ))
test "$(date +%s)" -lt "$cutoff"
export PYTHONPATH=/workspace/work/sol-job3/deps PYTHONDONTWRITEBYTECODE=1
driver=/workspace/work/sol-job40/run_cell40.py
mkdir -p raw
mkdir "raw/$limit"
date -u +%FT%TZ > "$limit.wrapper.start.stamp"

run() {
    local label=$1
    shift
    printf '%s %s %s starts\n' "$(date -u +%FT%TZ)" "$limit" "$label"
    python3 -u "$driver" "$limit" --output "raw/$limit/$label" --deadline "$cutoff" "$@" \
        > "raw/$limit/$label.driver.out" 2>&1
}

run BASE-a & a=$!
run BASE-b & b=$!
if [[ "$limit" == N2 ]]; then
    run EvalSwingMax300 --option EvalSwingMax 300 & known=$!
    run LmrQuietBase101 --option LmrQuietBase 101 & control=$!
fi
status=0
wait "$a" || status=$?
wait "$b" || status=$?
if [[ "$limit" == N2 ]]; then
    wait "$known" || status=$?
    wait "$control" || status=$?
fi
date -u +%FT%TZ > "$limit.wrapper.end.stamp"
printf '%s %s exits %d\n' "$(cat "$limit.wrapper.end.stamp")" "$limit" "$status"
printf '%d\n' "$status" > "$limit.wrapper.exit"
exit "$status"
