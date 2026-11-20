#!/usr/bin/env bash
# honesty.sh EXE TAG OUTDIR
# One fresh engine process per line. No setoption. "uci" is sent so the raw
# file contains "id name"; it sets nothing.
set -u
EXE="$1"
TAG="$2"
OUTDIR="$3"
SHA=$(sha256sum "$EXE" | awk '{print $1}')
run_one() {
  local name="$1"
  local cmd="$2"
  local out="$OUTDIR/honesty_${TAG}_${name}.txt"
  local meta="$OUTDIR/honesty_${TAG}_${name}.meta"
  printf 'uci\n%s\nquit\n' "$cmd" | "$EXE" > "$out" 2>&1
  local idline
  idline=$(grep -m1 '^id name ' "$out" || true)
  {
    echo "exe: $EXE"
    echo "sha256: $SHA"
    echo "id name: ${idline#id name }"
    echo "option lines sent: none"
    echo "commands: uci / $cmd / quit"
  } > "$meta"
}
run_one bench11 "bench 11"
run_one bench13 "bench 13"
run_one bench16 "bench 16"
run_one perft5 "go perft 5"
