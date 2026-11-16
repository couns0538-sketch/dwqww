#!/usr/bin/env bash
# machine_clean.sh — seat 20: is this machine fit to MEASURE on right now?
#
# Why: I lost a probe (and nearly a finding) to a leaked `forge` process of my own that sat at 97-99 % of a core for
# 3,400 s. It silently degraded depths AND timings. Run this before and after any timing/depth measurement.
#
# Exit 0 = clean. Exit 1 = busy (do not trust a timing/depth number taken now).
set -u
THRESH_LOAD="${1:-2.0}"     # loadavg threshold for a 4-core box; pass a higher number on a bigger machine
fail=0

echo "== forge processes (should be none between runs)"
procs=$(ps -eo pid,etime,pcpu,comm | awk '$4 ~ /forge/ && $3 > 1.0')
if [ -n "$procs" ]; then
  echo "  BUSY:"; echo "$procs" | sed 's/^/    /'
  echo "  -> an engine process is burning CPU. Kill it (kill -9 <pid>) and its parent python before measuring."
  fail=1
else
  echo "  none above 1% CPU (good)"
fi

echo "== other heavy processes (>50% CPU, any program)"
heavy=$(ps -eo pid,pcpu,comm --sort=-pcpu | awk 'NR>1 && $2 > 50.0' | head -5)
if [ -n "$heavy" ]; then
  echo "$heavy" | sed 's/^/    /'
  echo "  -> something is using a core; note it before trusting timings."
else
  echo "  none (good)"
fi

echo "== load average / cores"
read -r la _ < /proc/loadavg
cores=$(nproc)
echo "  loadavg 1min = $la ; cores = $cores ; threshold = $THRESH_LOAD"
awk -v la="$la" -v t="$THRESH_LOAD" 'BEGIN{ if (la+0 > t+0) { print "  -> ABOVE threshold: a timing/depth run now is unreliable"; exit 1 } else print "  loaded within threshold (good)" }' || fail=1

echo
if [ "$fail" -eq 0 ]; then
  echo "CLEAN: safe to measure."
else
  echo "NOT CLEAN: do not trust a timing or depth number taken now."
fi
exit "$fail"
