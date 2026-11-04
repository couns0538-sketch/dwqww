#!/usr/bin/env bash
# step.sh <log> <expected seconds> -- <program> [args ...]
# Checks of the GPU-trained v2 nets (2026-11-04): runs ONE check at Idle on CPU 0 (mask 0x1) through
# D:/a14/tools/opus_lowrun.py, after (1) waiting until no forge-v2-bullet process has CPU 0 in its mask (bullet_cpu0.ps1,
# polled every 15 s, at most WAIT_MAX s) and (2) a deadline check: the step is not started when now + expected seconds
# is past HARD_END (PC clock, default 14:03; no computation after 14:05). Writes the clock, the command line, the CPU-0
# sharers and the CPU 0/1 busy sample before, and the clock, exit code and md5 of the log after, into <log>.
# Exit: the program's exit code; 75 = not started (deadline), 76 = not started (trainer wait timed out), 2 = usage.
set -u
[ $# -ge 4 ] || { echo "usage: step.sh <log> <expected seconds> -- <program> [args ...]" >&2; exit 2; }
log="$1"; expected="$2"; shift 2
[ "$1" = "--" ] && shift
HARD_END="${HARD_END:-14:03}"
WAIT_MAX="${WAIT_MAX:-1200}"
PY=D:/a14/runtime/python/python.exe
LOW=D:/a14/tools/opus_lowrun.py
S=D:/o30/checks_gpu/scripts
PS="powershell -NoProfile -ExecutionPolicy Bypass -File"
[ -e "$log" ] && { echo "step.sh: $log exists (never overwritten)" >&2; exit 2; }
end_s=$(date -d "today $HARD_END" +%s)
{
  echo "step.sh start $(date '+%Y-%m-%d %H:%M:%S') (PC clock), hard end $HARD_END, expected ${expected} s"
  echo "command: $PY -I -B $LOW --mask 0x1 -- $*"
} > "$log"
# START_AT (HH:MM, optional): the compute window opens then - wait for it first
if [ -n "${START_AT:-}" ]; then
  start_s=$(date -d "today $START_AT" +%s)
  while [ "$(date +%s)" -lt "$start_s" ]; do sleep 10; done
  echo "window open $(date '+%H:%M:%S') (START_AT $START_AT)" >> "$log"
fi
waited=0
while true; do
  out=$($PS "$(cygpath -w "$S/bullet_cpu0.ps1")" -Cpu 0 2>&1); rc=$?
  if [ "$rc" = 0 ]; then break; fi
  if [ "$waited" -ge "$WAIT_MAX" ]; then
    echo "$out" >> "$log"; echo "step.sh: trainer still on CPU 0 after ${waited} s - not started" | tee -a "$log"; exit 76
  fi
  if [ "$waited" = 0 ]; then echo "$out" >> "$log"; echo "waiting for the trainer to leave CPU 0 ..." >> "$log"; fi
  sleep 15; waited=$((waited + 15))
done
now_s=$(date +%s)
if [ $((now_s + expected)) -gt "$end_s" ]; then
  echo "step.sh: $(date '+%H:%M:%S') + ${expected} s would pass $HARD_END - not started" | tee -a "$log"; exit 75
fi
{
  echo "--- before ($(date '+%H:%M:%S'), waited ${waited} s for the trainer):"
  echo "$out"
  $PS "$(cygpath -w "$S/cpu_busy.ps1")" -Cpus 0,1 -Samples 3 2>&1
  echo "--- run start $(date '+%Y-%m-%d %H:%M:%S')"
} >> "$log"
"$PY" -I -B "$LOW" --mask 0x1 -- "$@" >> "$log" 2>&1
rc=$?
{
  echo "--- run end $(date '+%Y-%m-%d %H:%M:%S') exit $rc"
  $PS "$(cygpath -w "$S/bullet_cpu0.ps1")" -Cpu 0 2>&1 | grep -v '^no forge' | sed 's/^/after: /'
} >> "$log"
echo "step.sh: exit $rc, log $log md5 $(md5sum "$log" | cut -c1-32)"
exit $rc
