#!/usr/bin/env bash
# runner_retry_test.sh - bug hunt 2026-11-04: does a run refused at start (guard exit 78) really start on the retry?
# Runs the fix-list version of queue_runner.sh (commit 73e4c828), the fixed queue_runner.sh and the fixed
# queue_runner2.sh against runner_retry_stub.sh (the bat's existence checks + a guard that refuses once).
# Scratch: D:/o30/tmp/runner_retry_bh (refused when it exists). Idle on O30_MASK (required; the runners pin to it).
set -u
[ -n "${O30_MASK:-}" ] || { echo "set O30_MASK" >&2; exit 78; }
H=$(cd "$(dirname "$0")" && pwd); A=/d/o30/wt/opus_30h/a; R=/d/o30/tmp/runner_retry_bh
[ -e "$R" ] && { echo "refusing: $R exists" >&2; exit 2; }
mkdir -p "$R"
git -C /d/o30/wt show 73e4c828:opus_30h/a/queue_runner.sh > "$R/queue_runner_73e4c828.sh"
INIT='D:\o30\gpu\init_lockkb8'
run_case() {   # <label> <runner script> <plan file name>
    local label="$1" runner="$2" plan="$3" root="$R/$1"
    mkdir -p "$root"
    echo "$(date '+%F %T') end: fake previous run" > "$root/prev.guard.log"
    echo "rX_test rank4x2 200 1 0.00002 $INIT" > "$root/$plan"
    echo "== $label: $(basename "$runner") md5 $(md5sum "$runner" | cut -c1-32)"
    RUNNER_ROOT="$root" RUNNER_PLAN="$root/$plan" RUNNER_CMD="$H/runner_retry_stub.sh" RUNNER_NO_WATCH=1 \
        RUNNER_RETRY_SLEEP=2 bash "$runner" "$root/prev.guard.log" 23:59 2>&1 | sed 's/^/   /'
    echo "   runner exit ${PIPESTATUS[0]}; stub calls: $(cat "$root/calls.txt")"
    for f in done failed skipped refused; do
        [ -f "$root/${plan%.txt}.$f" ] && echo "   ${plan%.txt}.$f: [$(tr '\n' ' ' < "$root/${plan%.txt}.$f")]"
    done
    echo "   files: $(cd "$root" && ls -d rX_test* | tr '\n' ' ')"
    for f in "$root"/rX_test.runner.txt; do [ -f "$f" ] && echo "   last runner.txt: $(tr '\n' ' ' < "$f")"; done
}
echo "runner retry test $(date '+%F %T'), O30_MASK $O30_MASK, stub md5 $(md5sum "$H/runner_retry_stub.sh" | cut -c1-32)"
run_case old_runner1 "$R/queue_runner_73e4c828.sh" plan.txt
run_case new_runner1 "$A/queue_runner.sh" plan.txt
run_case new_runner2 "$A/queue_runner2.sh" plan2.txt
echo "expected: old_runner1 call 2 aborts (exit 4, plan.failed); new_runner1 and new_runner2 start the run on call 2"
