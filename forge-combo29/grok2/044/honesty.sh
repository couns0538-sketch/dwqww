#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# One fresh engine process per line. No setoption is sent.
set -u
EXE=$1
TAG=$2
OUT=$3
sha=$(sha256sum "$EXE" | awk '{print $1}')
idline=$(printf 'uci\nquit\n' | "$EXE" | grep -m1 '^id name ')
run() {
  cmd=$1
  stem=$2
  printf '%s\nquit\n' "$cmd" | "$EXE" > "$OUT/${stem}.txt"
  {
    echo "exe: $EXE"
    echo "sha256: $sha"
    echo "id name: ${idline#id name }"
    echo "command: $cmd"
    echo "options:"
  } > "$OUT/${stem}.meta"
  echo "$stem"
  grep -E 'bench depth |^nodes ' "$OUT/${stem}.txt" | tail -n 1
}
run "bench 11" "honesty_${TAG}_bench11"
run "bench 13" "honesty_${TAG}_bench13"
run "bench 16" "honesty_${TAG}_bench16"
run "go perft 5" "honesty_${TAG}_perft5"
