#!/usr/bin/env bash
# Stub of gpu_run_o30c.bat + o30_gpu_guard.py for the queue runners' retry test (bug hunt 2026-11-04). Like the bat it
# first refuses a run whose folder / .out / .guard.log exist ("ABORT: ... exists", exit 4), then creates <run>.out (the
# bat's redirect); like the guard it opens <run>.guard.log before its checks. Call 1 refuses as the guard does
# (exit 78); later calls write "start trainer" and "end:" lines and exit 0. No GPU, no trainer.
G="${RUNNER_ROOT:?}"; name="$1"
c="$G/calls.txt"; n=$(cat "$c" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "$c"
for f in "$G/$name" "$G/$name.out" "$G/$name.guard.log"; do
    if [ -e "$f" ]; then echo "stub call $n: ABORT: $(basename "$f") exists (the bat's check) -> exit 4"; exit 4; fi
done
echo "stub output of call $n" > "$G/$name.out"
if [ "$n" = 1 ]; then
    echo "$(date '+%F %T') npt-like trainer running [stub]: not starting (yield)" >> "$G/$name.guard.log"
    echo "stub call $n: guard refuses (exit 78)"
    exit 78
fi
mkdir "$G/$name"
echo "$(date '+%F %T') start trainer pid 1 create_time 0.000 mask 0x2 cmd stub" >> "$G/$name.guard.log"
sleep 1
echo "$(date '+%F %T') end: trainer exit 0" >> "$G/$name.guard.log"
echo "stub call $n: trainer started and ended (exit 0)"
exit 0
