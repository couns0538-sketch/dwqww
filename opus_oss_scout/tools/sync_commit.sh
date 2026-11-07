#!/usr/bin/env bash
# sync_commit.sh "<commit subject>" [body file] - OSS scout job: stamp STATUS.md with the PC clock, mirror the
# handoff file and the own tools into the repo folder, and commit (no push; the push is typed literally).
# Times come from `date` at run time, never from typed text.
set -euo pipefail
SCOUT=/c/opus_5h/oss_scout
REPO=$SCOUT/repo
DEST=$REPO/opus_oss_scout
subject=${1:?commit subject}
body=${2:-}
now=$(date '+%Y-%m-%d %H:%M')
# Stamp the "Updated:" line of the master STATUS.md (first line that starts with "Updated:").
sed -i -E "0,/^Updated: .*\(PC clock\)/s//Updated: ${now} (PC clock)/" "$SCOUT/STATUS.md"
sed -i -E "s/^Updated: @NOW@ \(PC clock\)/Updated: ${now} (PC clock)/" "$SCOUT/STATUS.md"
mkdir -p "$DEST/tools"
cp "$SCOUT/STATUS.md" "$DEST/STATUS.md"
for f in "$SCOUT"/tools/*.ps1 "$SCOUT"/tools/*.py "$SCOUT"/tools/*.sh "$SCOUT"/tools/*.c; do
  [ -f "$f" ] || continue
  cp "$f" "$DEST/tools/"
done
if [ -d "$SCOUT/tools/abba" ]; then
  mkdir -p "$DEST/tools/abba"
  cp "$SCOUT"/tools/abba/*.py "$SCOUT"/tools/abba/*.ps1 "$DEST/tools/abba/" 2>/dev/null || true
fi
msg=$SCOUT/tmp/commit_msg.txt
printf '%s\n' "$subject" > "$msg"
if [ -n "$body" ] && [ -f "$body" ]; then printf '\n' >> "$msg"; cat "$body" >> "$msg"; fi
cd "$REPO"
git add -A opus_oss_scout
if git diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com commit -q -F "$msg"
git log --oneline -1
echo "stamped STATUS.md at ${now}"
