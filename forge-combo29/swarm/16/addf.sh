#!/usr/bin/env bash
# addf.sh : append a findings row to THIS seat's FINDINGS.md, resolving the path absolutely.
# usage: cat row.txt | ./addf.sh      (or)   ./addf.sh < row.txt
# Exists because a relative `>> ../../FINDINGS.md` silently wrote rows OUTSIDE the seat folder three times.
set -eu
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HERE/FINDINGS.md"
[ -f "$TARGET" ] || { echo "STOP: $TARGET does not exist"; exit 1; }
NEW="$(cat)"
case "$NEW" in
  "| S-"*) ;;
  *) echo "STOP: input does not start with '| S-'"; exit 1 ;;
esac
ID="$(printf '%s' "$NEW" | cut -d'|' -f2 | tr -d ' ')"
if grep -q "^| $ID |" "$TARGET"; then
  echo "NOTE: $ID already present; appending anyway (a CORRECTED/QUALIFIED note shares its id)"
fi
printf '%s\n' "$NEW" >> "$TARGET"
echo "appended $ID to $TARGET"
