#!/usr/bin/env bash
# Honesty check. Fresh process per line. No setoption.
set -u
EXE=/agent/repos/base/forge-combo29/build/forge
D="$(cat ~/grok2_repo.txt)/forge-combo29/grok2/$(cat ~/grok2_seat.txt)"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
ID=$(printf 'uci\nquit\n' | "$EXE" | awk -F'id name ' '/^id name /{print $2; exit}')
for side in B P; do
  for spec in "bench11:bench 11" "bench13:bench 13" "bench16:bench 16" "perft5:go perft 5"; do
    tag=${spec%%:*}
    cmd=${spec#*:}
    out="$D/honesty_${side}_${tag}.txt"
    meta="$D/honesty_${side}_${tag}.meta"
    printf '%s\nquit\n' "$cmd" | "$EXE" > "$out"
    {
      echo "exe: $EXE"
      echo "sha256: $SHA"
      echo "id name: $ID"
      echo "options:"
      echo "(none)"
      echo "command: $cmd"
    } > "$meta"
  done
done
grep -H -E 'nodes ' "$D"/honesty_*.txt
