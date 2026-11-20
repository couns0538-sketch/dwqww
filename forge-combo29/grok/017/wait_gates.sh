#!/usr/bin/env bash
# Sleep to minute 60, fetch the handoff, then sleep to minute 75.
set -u
REPO=$(cat ~/grok_repo.txt)
OUT="$REPO/forge-combo29/grok/$(cat ~/grok_seat.txt)/gate_notes.txt"
cd "$REPO"
python3 - << 'PY'
import time
from datetime import datetime, timezone
target = datetime(2026, 11, 20, 8, 52, 30, tzinfo=timezone.utc)
delay = (target - datetime.now(timezone.utc)).total_seconds()
if delay > 0:
    time.sleep(delay)
PY
{
  echo "minute60 $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114 || echo "FETCH_FAIL"
  git ls-tree -r --name-only FETCH_HEAD | grep -E 'FABLE_TO_grok_[0-9]+\.md$' | sort -t_ -k4 -n | tail -n 5
  newest=$(git ls-tree -r --name-only FETCH_HEAD | grep -E 'FABLE_TO_grok_[0-9]+\.md$' | sort -t_ -k4 -n | tail -n 1 || true)
  echo "newest ${newest:-none}"
  if [ -n "${newest:-}" ]; then
    git show "FETCH_HEAD:$newest" | head -n 5
    first=$(git show "FETCH_HEAD:$newest" | head -n 1)
    echo "first $first"
    case "$first" in
      STOP*) echo "ACTION stop" ;;
      *) echo "ACTION continue" ;;
    esac
  else
    echo "ACTION continue"
  fi
} > "$OUT"
python3 - << 'PY'
import time
from datetime import datetime, timezone
target = datetime(2026, 11, 20, 9, 7, 30, tzinfo=timezone.utc)
delay = (target - datetime.now(timezone.utc)).total_seconds()
if delay > 0:
    time.sleep(delay)
PY
echo "minute75 $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"
echo READY >> "$OUT"
