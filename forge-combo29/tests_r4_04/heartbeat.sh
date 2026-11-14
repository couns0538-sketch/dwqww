#!/usr/bin/env bash
# Push the branch at least every 30 minutes while the screen is running.
set -u
ROOT=/agent/repos/dwqww
TEST="$ROOT/forge-combo29/tests_r4_04"
FLAG=/tmp/r4_04/screen_running
cd "$ROOT"
for _ in $(seq 1 600); do
  if [ ! -f "$FLAG" ] && [ -f "$TEST/match_end_epoch" ]; then
    "$TEST/push.sh" "r4-04: ContHist4PlyRead screen heartbeat" || true
    exit 0
  fi
  last=0
  if [ -f /tmp/r4_04/last_push ]; then
    last=$(cat /tmp/r4_04/last_push)
  fi
  now=$(date +%s)
  if [ $((now - last)) -ge 1800 ]; then
    "$TEST/push.sh" "r4-04: ContHist4PlyRead screen heartbeat" || true
  fi
  sleep 60
done
