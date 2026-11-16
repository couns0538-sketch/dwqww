#!/usr/bin/env bash
# board2.sh : pull every seat's FINDINGS.md (all seats, not only my area) into board2/, plus newest STATUS tail
set -u
OUT=board2
mkdir -p "$OUT"
date -u
taken=$(git ls-remote origin "refs/heads/for-fable-and-opus/swarm-*" | sed 's#.*/swarm-##' | sort)
for seat in $taken; do
  f="$OUT/seat_$seat.findings"
  if git fetch -q --depth 1 origin "for-fable-and-opus/swarm-$seat" 2>/dev/null; then
    git show "FETCH_HEAD:forge-combo29/swarm/$seat/FINDINGS.md" 2>/dev/null > "$f" || echo "(none)" > "$f"
  else
    echo "(unfetchable)" > "$f"
  fi
done
echo "=== all findings lines mentioning NEW, except seat 03:"
grep -H "NEW" "$OUT"/*.findings | grep -v "seat_03\." || echo "(none)"
