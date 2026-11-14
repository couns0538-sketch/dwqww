#!/usr/bin/env bash
# Commit the screen report and logs, then push. Serialized with a lock.
set -u
ROOT=/agent/repos/dwqww
TEST="$ROOT/forge-combo29/tests_r4_04"
BRANCH=grok47/r4-04-screen-ch4
LOCK=/tmp/r4_04/git.lock
msg="${1:-r4-04: ContHist4PlyRead screen update}"
mkdir -p /tmp/r4_04
exec 9>"$LOCK"
flock 9
cd "$ROOT"
python3 "$TEST/summarize.py"
git add -- forge-combo29/REPORT_r4_04.md forge-combo29/tests_r4_04
if git diff --cached --quiet; then
  echo "push: nothing to commit"
  exit 0
fi
git commit -m "$msg"
delay=0
for attempt in 1 2 3 4 5; do
  if [ "$delay" -ne 0 ]; then
    sleep "$delay"
  fi
  if git push -u origin "$BRANCH"; then
    date +%s > /tmp/r4_04/last_push
    exit 0
  fi
  delay=$((delay == 0 ? 4 : delay * 2))
done
echo "push failed" >&2
exit 1
