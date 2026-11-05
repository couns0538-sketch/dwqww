#!/usr/bin/env bash
# watch_after_moveaside_test.sh - bug hunt 2026-11-04 (BH-5 follow-up): queue_runner.sh starts the checkpoint watcher
# before the run; when the guard refuses, the runner moves <run>.guard.log aside and retries. Does the running
# gpu_ckpt_watch2.sh keep waiting through that and finish on the retried run's log? Stub files only (no checkpoints,
# so nothing is scored). Scratch D:/o30/tmp/watch_moveaside_bh (refused when it exists). Idle on O30_MASK.
set -u
[ -n "${O30_MASK:-}" ] || { echo "set O30_MASK" >&2; exit 78; }
A=/d/o30/wt/opus_30h/a; R=/d/o30/tmp/watch_moveaside_bh; run=rW_test
[ -e "$R" ] && { echo "refusing: $R exists" >&2; exit 2; }
mkdir -p "$R"
echo "watch2 md5 $(md5sum "$A/gpu_ckpt_watch2.sh" | cut -c1-32), $(date '+%F %T')"
echo "$(date '+%F %T') npt-like trainer running [stub]: not starting (yield)" > "$R/$run.guard.log"
WATCH_ROOT="$R" WATCH_MASK="$O30_MASK" WATCH_SLEEP=1 WATCH_MAX_MIN=2 bash "$A/gpu_ckpt_watch2.sh" "$run" rank4x2 > "$R/watch.log" 2>&1 &
wpid=$!
sleep 4
echo "after 4 s on the refused attempt's log: watcher alive = $(kill -0 $wpid 2>/dev/null && echo yes || echo no)"
mv "$R/$run.guard.log" "$R/$run.guard.log.refused1"
echo "moved aside: $(ls "$R" | tr '\n' ' ')"
sleep 3
echo "after 3 s with no guard log: watcher alive = $(kill -0 $wpid 2>/dev/null && echo yes || echo no)"
{ echo "$(date '+%F %T') start trainer pid 1 create_time 0.000 mask 0x2 cmd stub (the retry)"
  echo "$(date '+%F %T') end: trainer exit 0"; } > "$R/$run.guard.log"
wait $wpid; rc=$?
echo "watcher exit $rc (expected 0: it finished on the retried run's log)"
echo "watch.log:"; sed 's/^/   /' "$R/watch.log"
